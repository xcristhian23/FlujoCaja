import streamlit as st
import pandas as pd
import plotly.express as px

from io import BytesIO
import zipfile
import plotly.express as px


from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO
from datetime import datetime
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle


st.set_page_config(page_title="Control de Caja", layout="wide")

# --------------------------------------------------
# Utilidades
# --------------------------------------------------
def normalizar(col):
    return (
        col.lower()
        .replace(" ", "_")
        .replace("/", "")
        .replace("°", "")
    )

# --------------------------------------------------
# Cargar Excel
# --------------------------------------------------
def cargar_excel(archivo):
    df = pd.read_excel(archivo)
    df.columns = [normalizar(c) for c in df.columns]

    obligatorias = ["fecha", "total_general_s"]
    for c in obligatorias:
        if c not in df.columns:
            st.error(f"❌ Falta la columna obligatoria: {c}")
            st.stop()

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["total_general_s"] = (
        df["total_general_s"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .astype(float)
    )

    df["anio_mes"] = df["fecha"].dt.to_period("M").astype(str)

    return df

# --------------------------------------------------
# UI
# --------------------------------------------------
st.title("💰 Sistema de Control de Caja")
st.caption("Filtros dinámicos tipo Excel + comparaciones")

archivo = st.file_uploader("📂 Cargar Excel", type=["xlsx"])

if archivo:
    df = cargar_excel(archivo)
    st.success(f"✅ {len(df)} registros cargados")

    # --------------------------------------------------
    # CONFIGURACIÓN DE FILTROS
    # --------------------------------------------------
    st.sidebar.header("🎛️ Configuración de filtros")

    columnas_disponibles = [
        c for c in df.columns
        if c not in ["total_general_s", "anio_mes"]
    ]

    columnas_filtro = st.sidebar.multiselect(
        "Selecciona columnas para filtrar",
        columnas_disponibles,
        default=[
            c for c in [
                "costo__gasto",
                "clasificacion_1",
                "clasificacion_flujo2"
            ] if c in columnas_disponibles
        ]
    )

    st.sidebar.divider()
    st.sidebar.subheader("🔍 Filtros")

    # --------------------------------------------------
    # FILTROS DINÁMICOS EN CASCADA
    # --------------------------------------------------
    df_filtrado = df.copy()

    for col in columnas_filtro:
        valores = sorted(df_filtrado[col].dropna().unique())

        seleccion = st.sidebar.multiselect(
            f"{col.replace('_', ' ').title()}",
            valores
        )

        if seleccion:
            df_filtrado = df_filtrado[df_filtrado[col].isin(seleccion)]

    # --------------------------------------------------
    # FECHA
    # --------------------------------------------------
    fecha_min = df_filtrado["fecha"].min()
    fecha_max = df_filtrado["fecha"].max()

    fechas = st.sidebar.date_input(
        "Rango de fechas",
        [fecha_min, fecha_max],
        min_value=fecha_min,
        max_value=fecha_max
    )

    if len(fechas) == 2:
        df_filtrado = df_filtrado[
            (df_filtrado["fecha"] >= pd.to_datetime(fechas[0])) &
            (df_filtrado["fecha"] <= pd.to_datetime(fechas[1]))
        ]

    # --------------------------------------------------
    # COMPARACIONES
    # --------------------------------------------------
    modo = st.sidebar.radio(
        "📊 Comparar por",
        ["Sin comparación", "Por día", "Por mes"]
    )

    # --------------------------------------------------
    # INGRESOS / EGRESOS / SALDO
    # --------------------------------------------------
    st.subheader("📌 Resumen General")

    if "ingresoegreso" not in df_filtrado.columns:
        st.error("❌ No existe la columna INGRESO/EGRESO en el Excel")
    else:
        total_ingresos = df_filtrado[
            df_filtrado["ingresoegreso"].str.upper() == "INGRESO"
        ]["total_general_s"].sum()

        total_egresos = df_filtrado[
            df_filtrado["ingresoegreso"].str.upper() == "EGRESO"
        ]["total_general_s"].sum()

        saldo = total_ingresos + total_egresos

        col1, col2, col3 = st.columns(3)

        col1.metric("💵 Total Ingresos", f"S/ {total_ingresos:,.2f}")
        col2.metric("💸 Total Egresos", f"S/ {total_egresos:,.2f}")
        col3.metric("⚖️ Saldo", f"S/ {saldo:,.2f}")

    # Grafico ingreso y egresos
    # --------------------------------------------------
    st.subheader("💼 Distribución de Ingresos y Egresos")

    df_ie = pd.DataFrame({
        "Tipo": ["Ingresos", "Egresos"],
        "Monto": [total_ingresos, abs(total_egresos)]
    })

    fig_pie = px.pie(
    df_ie,
    names="Tipo",
    values="Monto",
    hole=0.5,
    title="Ingresos vs Egresos",
    color="Tipo",
    color_discrete_map={
        "Ingresos": "#5095B4",   # verde claro
        "Egresos": "#BE2323"     # rojo claro
    }
    )

    st.plotly_chart(fig_pie, use_container_width=True)

    # --------------------------------------------------
    # TABLA DINÁMICA
    # --------------------------------------------------
    st.subheader("📊 Resultado")

    columnas_grupo = columnas_filtro.copy()

    if modo == "Por día":
        columnas_grupo.append("fecha")

    if modo == "Por mes":
        columnas_grupo.append("anio_mes")

    if not columnas_grupo:
        columnas_grupo = ["fecha"]

    # --------------------------------------------------
    # TABLA DINÁMICA ORDENADA + EGRESOS EN ROJO
    # --------------------------------------------------

    columnas_groupby = columnas_grupo.copy()

    if "ingresoegreso" not in columnas_groupby:
        columnas_groupby.append("ingresoegreso")

    tabla = (
        df_filtrado
        .groupby(columnas_groupby, as_index=False)["total_general_s"]
        .sum()
    )

    # Ordenar por costo__gasto si existe
    if "costo__gasto" in tabla.columns:
        tabla = tabla.sort_values(
            by=["costo__gasto", "total_general_s"],
            ascending=[True, False]
        )
    else:
        tabla = tabla.sort_values("total_general_s", ascending=False)

    # Formato moneda
    tabla["total_general_s_fmt"] = tabla["total_general_s"].map(
        lambda x: f"S/ {x:,.2f}"
    )

    # --- Estilo condicional ---
    def pintar_egresos(row):
        if row["ingresoegreso"].upper() == "EGRESO":
            return ["color: #BE2323"] * len(row)
        return [""] * len(row)

    tabla_estilizada = (
        tabla
        .drop(columns=["total_general_s"])
        .rename(columns={"total_general_s_fmt": "TOTAL"})
        .style
        .apply(pintar_egresos, axis=1)
    )

    st.dataframe(tabla_estilizada, use_container_width=True)

        # --------------------------------------------------
        # DETALLE
        # --------------------------------------------------
    with st.expander("🔍 Ver detalle completo"):
            st.dataframe(df_filtrado, use_container_width=True)

    st.subheader("📈 Visualización de Resultados")

    # Definir eje X
    if "clasificacion_1" in tabla.columns:
        eje_x = "clasificacion_1"
    else:
        eje_x = columnas_grupo[0]

    fig_bar = px.bar(
        tabla,
        x=eje_x,
        y="total_general_s",
        text_auto=".2s",
        labels={
            "total_general_s": "Total S/"
        },
        title="Total por Clasificación"
    )

    # 👉 Personalizar el hover (tooltip)
    fig_bar.update_traces(
        hovertemplate=
            "<b>%{x}</b><br>" +
            "Total: S/ %{y:,.2f}" +
            "<extra></extra>"
    )

    fig_bar.update_layout(
        xaxis_title=None,
        height=500
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    #Exportacion

    def exportar_dashboard(tabla, total_ingresos, total_egresos, saldo, fig_pie, fig_bar):
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:

            # -----------------------------
            # Excel
            # -----------------------------
            excel_buffer = BytesIO()

            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:


                # Resumen
                df_resumen = pd.DataFrame({
                    "Concepto": ["Total Ingresos", "Total Egresos", "Saldo"],
                    "Monto": [
                        f"S/ {total_ingresos:,.2f}",
                        f"S/ {total_egresos:,.2f}",
                        f"S/ {saldo:,.2f}"
                    ]
                })

                df_resumen.to_excel(writer, sheet_name="Resumen", index=False)

                # Resultado filtrado
                tabla_export = tabla.copy()
                tabla_export["total_general_s"] = tabla_export["total_general_s"].map(
                    lambda x: f"S/ {x:,.2f}"
                )

                tabla_export.to_excel(
                    writer,
                    sheet_name="Resultado_Filtrado",
                    index=False
                )

            excel_buffer.seek(0)
            zipf.writestr("control_caja.xlsx", excel_buffer.read())

            # -----------------------------
            # Gráficos
            # -----------------------------
            zipf.writestr(
                "grafico_ingresos_egresos.png",
                fig_pie.to_image(format="png", scale=2)
            )

            zipf.writestr(
                "grafico_resultados.png",
                fig_bar.to_image(format="png", scale=2)
            )

        zip_buffer.seek(0)
        return zip_buffer

        #boton

        st.divider()
    st.subheader("📤 Exportar Dashboard")

    zip_file = exportar_dashboard(
        tabla=tabla,
        total_ingresos=total_ingresos,
        total_egresos=total_egresos,
        saldo=saldo,
        fig_pie=fig_pie,
        fig_bar=fig_bar
    )

    st.download_button(
        label="📦 Descargar Excel + Gráficos",
        data=zip_file,
        file_name="control_caja_dashboard.zip",
        mime="application/zip"
    )

    #Generacion pdf
    def exportar_pdf_ejecutivo(
        total_ingresos,
        total_egresos,
        saldo,
        tabla_resumen,
        fig_pie,
        fig_bar,
        ultima_fecha
    ):
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()
        story = []

    # -------------------------------
    # TÍTULO
    # -------------------------------
        story.append(Paragraph("<b>REPORTE EJECUTIVO – CONTROL DE CAJA</b>", styles["Title"]))
        story.append(Spacer(1, 12))

        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        fecha_ultima = ultima_fecha.strftime("%d/%m/%Y")

        story.append(
            Paragraph(
                f"Fecha de generación: {fecha_generacion} al {fecha_ultima}",
                styles["Normal"]
            )
        )


        story.append(Spacer(1, 12))

        # -------------------------------
        # KPIs
        # -------------------------------
        kpi_data = [
            ["Total Ingresos", f"S/ {total_ingresos:,.2f}"],
            ["Total Egresos", f"S/ {abs(total_egresos):,.2f}"],
            ["Saldo", f"S/ {saldo:,.2f}"]
        ]

        tabla_kpi = Table(kpi_data, colWidths=[7*cm, 6*cm])
        tabla_kpi.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("FONT", (0,0), (-1,-1), "Helvetica"),
            ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ]))

        story.append(tabla_kpi)
        story.append(Spacer(1, 16))

        # -------------------------------
        # EXPORTAR GRÁFICOS A IMAGEN
        # -------------------------------
        pie_img = BytesIO()
        bar_img = BytesIO()

        fig_pie.write_image(pie_img, format="png", width=600, height=400)
        fig_bar.write_image(bar_img, format="png", width=700, height=450)

        pie_img.seek(0)
        bar_img.seek(0)

        story.append(Paragraph("<b>Distribución de Ingresos y Egresos</b>", styles["Heading2"]))
        story.append(Spacer(1, 8))
        story.append(Image(pie_img, width=14*cm, height=9*cm))
        story.append(Spacer(1, 16))

        story.append(Paragraph("<b>Resultados según filtros</b>", styles["Heading2"]))
        story.append(Spacer(1, 8))
        story.append(Image(bar_img, width=15*cm, height=9*cm))
        story.append(Spacer(1, 16))

    # -------------------------------
    # TABLA RESUMEN (MEJORADA)
    # -------------------------------
        story.append(Paragraph("<b>Resumen de Resultados</b>", styles["Heading2"]))
        story.append(Spacer(1, 8))

        # Estilo para celdas (wrap automático)
        cell_style = ParagraphStyle(
            name="CellStyle",
            fontSize=9,
            leading=11
        )

    # Convertir dataframe a tabla con Paragraph (wrap)
    #tabla_resumen = tabla_resumen.drop(columns=["ingresoegreso"])

        data = []
        data.append([
            Paragraph(f"<b>{col}</b>", cell_style)
            for col in tabla_resumen.columns
        ])

        for _, row in tabla_resumen.iterrows():

            es_egreso = (
                str(row.get("ingresoegreso", "")).upper() == "EGRESO"
            )

            fila = []
            for val in row:
                color = "#BE2323" if es_egreso else "#000000"
                fila.append(
                    Paragraph(
                        f'<font color="{color}">{val}</font>',
                        cell_style
                    )
                )

            data.append(fila)


        # Definir anchos proporcionales (AJUSTA SI QUIERES)
        num_cols = len(tabla_resumen.columns)
        page_width = A4[0] - 4*cm   # márgenes
        col_widths = [page_width / num_cols] * num_cols

        tabla_res = Table(
            data,
            colWidths=col_widths,
            repeatRows=1
        )

        tabla_res.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("FONT", (0,0), (-1,0), "Helvetica-Bold"),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("ALIGN", (1,1), (-1,-1), "LEFT"),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 6),
        ]))

        story.append(tabla_res)


        # -------------------------------
        doc.build(story)
        buffer.seek(0)

        return buffer

    st.subheader("📤 Exportación")

    tabla_pdf = (
        tabla
        .drop(columns=["total_general_s"])
        .rename(columns={"total_general_s_fmt": "TOTAL"})
    )

    ultima_fecha = df_filtrado["fecha"].max()

    pdf_buffer = exportar_pdf_ejecutivo(
        total_ingresos=total_ingresos,
        total_egresos=total_egresos,
        saldo=saldo,
        tabla_resumen=tabla_pdf,
        fig_pie=fig_pie,
        fig_bar=fig_bar,
        ultima_fecha=ultima_fecha
    )


    st.download_button(
        "📄 Descargar PDF Ejecutivo",
        data=pdf_buffer,
        file_name="reporte_control_caja.pdf",
        mime="application/pdf"
    )
