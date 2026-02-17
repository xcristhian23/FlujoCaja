import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
import zipfile
from io import BytesIO
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import os

# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

st.set_page_config(page_title="Control de Caja Comparativo", layout="wide")

# --------------------------------------------------
# CREAR CARPETA DATA SI NO EXISTE
# --------------------------------------------------

if not os.path.exists("data"):
    os.makedirs("data")

pio.kaleido.scope.default_format = "png"
pio.kaleido.scope.default_scale = 2

# --------------------------------------------------
# UTILIDADES
# --------------------------------------------------

def normalizar(col):
    return col.lower().replace(" ", "_").replace("/", "").replace("°", "")

def cargar_excel(archivo, tipo):
    df = pd.read_excel(archivo)
    df.columns = [normalizar(c) for c in df.columns]

    obligatorias = ["fecha", "total_general_s"]
    for c in obligatorias:
        if c not in df.columns:
            st.error(f"❌ Falta la columna obligatoria: {c}")
            st.stop()

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])

    df["total_general_s"] = (
        df["total_general_s"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .astype(float)
    )

    df["anio_mes"] = df["fecha"].dt.to_period("M").astype(str)
    df["tipo_archivo"] = tipo

    return df

def formato_moneda(x):
    return f"S/ {x:,.2f}"

# --------------------------------------------------
# UI
# --------------------------------------------------

st.title("💰 Sistema Control de Caja – Comparativo Ejecutivo")

# --------------------------------------------------
# --------------------------------------------------
# CARGA O RECUPERACIÓN DE ARCHIVOS
# --------------------------------------------------

ruta_ej = "data/ejecutado.xlsx"
ruta_pr = "data/proyectado.xlsx"

# 🔴 BOTÓN PARA LIMPIAR ARCHIVOS
st.sidebar.divider()
st.sidebar.subheader("⚙️ Administración")

if st.sidebar.button("🗑️ Limpiar archivos guardados"):

    # 🔹 Eliminar archivos
    if os.path.exists(ruta_ej):
        os.remove(ruta_ej)

    if os.path.exists(ruta_pr):
        os.remove(ruta_pr)

    # 🔹 Limpiar session_state completo
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    # 🔹 Limpiar parámetros de la URL
    st.query_params.clear()

    st.success("Archivos y filtros eliminados correctamente")

    st.rerun()


col1, col2 = st.columns(2)

with col1:
    archivo_ej = st.file_uploader("📂 Cargar Excel Ejecutado", type=["xlsx"])

    if archivo_ej:
        with open(ruta_ej, "wb") as f:
            f.write(archivo_ej.getbuffer())
        st.success("Ejecutado guardado correctamente")

with col2:
    archivo_pr = st.file_uploader("📂 Cargar Excel Proyectado", type=["xlsx"])

    if archivo_pr:
        with open(ruta_pr, "wb") as f:
            f.write(archivo_pr.getbuffer())
        st.success("Proyectado guardado correctamente")


if os.path.exists(ruta_ej) and os.path.exists(ruta_pr):

    df_ej = cargar_excel(ruta_ej, "Ejecutado")
    df_pr = cargar_excel(ruta_pr, "Proyectado")


    df = pd.concat([df_ej, df_pr], ignore_index=True)

    # Crear columnas auxiliares de mes UNA SOLA VEZ en el dataframe base
    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    df["mes_num"] = df["fecha"].dt.month
    df["mes_nombre"] = df["mes_num"].map(meses_es)

    # --------------------------------------------------
    # MANEJO GLOBAL DE ESTADO EN URL (COMPARTIBLE)
    # --------------------------------------------------

    query_params = st.query_params

    
    def guardar_parametro(nombre, valor):

        # Si está vacío o es "Todos", eliminar de URL
        if not valor or valor == "Todos" or valor == ["Todos"]:
            if nombre in st.query_params:
                del st.query_params[nombre]
            return

        # Si es lista, convertir correctamente
        if isinstance(valor, list):
            st.query_params[nombre] = valor
        else:
            st.query_params[nombre] = str(valor)


    def obtener_parametro(nombre):
        return query_params.get(nombre)

    
    # --------------------------------------------------
    # CONFIGURACIÓN DE FILTROS
    # --------------------------------------------------

    st.sidebar.header("🎛️ Configuración de filtros")

    columnas_disponibles = [
        c for c in df.columns
        if c not in ["total_general_s", "tipo_archivo"]
    ]

    columnas_url = obtener_parametro("columnas")

    if columnas_url:
        if isinstance(columnas_url, str):
            columnas_url = columnas_url.split(",")

    # Inicializar columnas en session_state solo una vez
    if "columnas_filtro" not in st.session_state:

        if columnas_url:
            st.session_state.columnas_filtro = columnas_url
        else:
            st.session_state.columnas_filtro = [
                c for c in [
                    "costo__gasto",
                    "clasificacion_1",
                    "clasificacion_flujo2"
                ] if c in columnas_disponibles
            ]

    columnas_filtro = st.sidebar.multiselect(
        "Selecciona columnas para filtrar",
        columnas_disponibles,
        key="columnas_filtro"
    )


    guardar_parametro("columnas", columnas_filtro)


    st.sidebar.divider()
    st.sidebar.subheader("🔍 Filtros")

    df_filtrado = df.copy()

    # --------------------------------------------------
    # RECUPERAR FILTROS DESDE URL
    # --------------------------------------------------

    query_params = st.query_params
    modo_ejecutivo = obtener_parametro("ejecutivo") == "1"

    # --------------------------------------------------
    # FILTRO POR MES (COMBOBOX)
    # --------------------------------------------------

    # Diccionario meses en español
    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    # Crear columnas auxiliares si no existen
    # df_filtrado["mes_num"] = df_filtrado["fecha"].dt.month
    # df_filtrado["mes_nombre"] = df_filtrado["mes_num"].map(meses_es)

    st.sidebar.divider()
    st.sidebar.subheader("📅 Filtro por Mes")

    meses_disponibles = (
        df_filtrado["mes_nombre"]
        .dropna()
        .unique()
        .tolist()
    )

    # Ordenar meses correctamente
    meses_disponibles = sorted(
        meses_disponibles,
        key=lambda x: list(meses_es.values()).index(x)
    )
    mes_url = obtener_parametro("mes")
    if mes_url:
        mes_seleccionado = mes_url

    mes_anterior = st.session_state.get("mes_anterior", None)

    mes_seleccionado = st.sidebar.selectbox(
        "Seleccionar mes",
        options=["Todos"] + meses_disponibles,
        disabled=modo_ejecutivo,
        key="mes_selector"
    )

    # Detectar cambio de mes
    if mes_seleccionado != mes_anterior:

        st.session_state["mes_anterior"] = mes_seleccionado

        if mes_seleccionado != "Todos":

            df_mes_temp = df[df["mes_nombre"] == mes_seleccionado]

            if not df_mes_temp.empty:
                nueva_fecha_inicio = df_mes_temp["fecha"].min().date()
                nueva_fecha_fin = df_mes_temp["fecha"].max().date()

                st.query_params["fecha_inicio"] = str(nueva_fecha_inicio)
                st.query_params["fecha_fin"] = str(nueva_fecha_fin)

        else:
            if "fecha_inicio" in st.query_params:
                del st.query_params["fecha_inicio"]
            if "fecha_fin" in st.query_params:
                del st.query_params["fecha_fin"]


    if mes_seleccionado != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado["mes_nombre"] == mes_seleccionado
        ]
    # 🔹 Guardar versión solo con filtro de mes
    df_para_fechas = df_filtrado.copy()


    # --------------------------------------------------
    # --------------------------------------------------
    # FILTROS DINÁMICOS EN CASCADA (COMO SISTEMA ORIGINAL)
    # --------------------------------------------------

    for col in columnas_filtro:

        valores = sorted(df_filtrado[col].dropna().unique())
        key = f"filtro_{col}"
        opciones = ["Todos"] + list(valores)

        if key not in st.session_state:
            st.session_state[key] = []

        def actualizar_columnas():
            st.session_state.columnas_visibles = st.session_state.columnas_selector

        # Callback para comportamiento "Todos"
        def on_change_callback(col=col, valores=valores, key=key):

            seleccion = st.session_state[key]

            if "Todos" in seleccion:
                # Reemplazar por todos los valores reales
                st.session_state[key] = list(valores)


        # Recuperar desde URL
        # Recuperar desde URL SOLO la primera vez
        valor_url = obtener_parametro(col)

        if key not in st.session_state:

            if valor_url:
                if isinstance(valor_url, str):
                    valor_url = [valor_url]
                st.session_state[key] = valor_url
            else:
                st.session_state[key] = []


        seleccion = st.sidebar.multiselect(
            f"{col.replace('_', ' ').title()}",
            options=opciones,
            key=key,
            disabled=modo_ejecutivo,
            on_change=on_change_callback
        )


        guardar_parametro(col, seleccion)

        if mes_seleccionado != "Todos":
            guardar_parametro("mes", mes_seleccionado)
        else:
            if "mes" in st.query_params:
                del st.query_params["mes"]


        # Aplicar filtro
        valores_seleccionados = st.session_state[key]

        # Si selecciona "Todos" o no hay selección → no aplicar filtro
        if valores_seleccionados and "Todos" not in valores_seleccionados:

            df_filtrado = df_filtrado[
                df_filtrado[col].isin(valores_seleccionados)
            ]


    
    # --------------------------------------------------
    # RANGO DE FECHAS (VERSIÓN SEGURA)
    # --------------------------------------------------

    if not df_para_fechas.empty:

        fecha_min = df_para_fechas["fecha"].min()
        fecha_max = df_para_fechas["fecha"].max()


        if pd.notna(fecha_min) and pd.notna(fecha_max):

            fecha_inicio_url = obtener_parametro("fecha_inicio")
            fecha_fin_url = obtener_parametro("fecha_fin")

            # Valores base del dataset actual
            min_date = fecha_min.date()
            max_date = fecha_max.date()

            # Si hay valores en URL, intentar usarlos
            if fecha_inicio_url and fecha_fin_url:

                try:
                    fecha_inicio = pd.to_datetime(fecha_inicio_url).date()
                    fecha_fin = pd.to_datetime(fecha_fin_url).date()

                    # 🔥 CLAMP: forzar dentro del rango permitido
                    fecha_inicio = max(min_date, min(fecha_inicio, max_date))
                    fecha_fin = max(min_date, min(fecha_fin, max_date))

                    fechas_default = (fecha_inicio, fecha_fin)

                except:
                    fechas_default = (min_date, max_date)

            else:
                fechas_default = (min_date, max_date)

            fechas = st.sidebar.date_input(
                "Rango de fechas",
                value=fechas_default,
                min_value=min_date,
                max_value=max_date,
                disabled=modo_ejecutivo
            )

            if len(fechas) == 2:

                guardar_parametro("fecha_inicio", str(fechas[0]))
                guardar_parametro("fecha_fin", str(fechas[1]))

                df_filtrado = df_filtrado[
                    (df_filtrado["fecha"] >= pd.to_datetime(fechas[0])) &
                    (df_filtrado["fecha"] <= pd.to_datetime(fechas[1]))
                ]


    if df_filtrado.empty:
        st.warning("⚠ No hay datos con los filtros actuales.")
        st.stop()

    # --------------------------------------------------
    # MODO COMPARACIÓN
    # --------------------------------------------------

    modo_url = obtener_parametro("modo")
    modo_opciones = ["Sin comparación", "Por día", "Por mes"]

    modo = st.sidebar.radio(
        "📊 Comparar por",
        modo_opciones,
        index=modo_opciones.index(modo_url)
        if modo_url in modo_opciones else 0,
        disabled=modo_ejecutivo
    )


    guardar_parametro("modo", modo)

    # --------------------------------------------------
    # GENERAR LINK COMPARTIBLE
    # --------------------------------------------------

    from urllib.parse import urlencode

    st.sidebar.divider()
    st.sidebar.subheader("🔗 Compartir vista")

    params = {}

    for k, v in st.query_params.items():
        if isinstance(v, list):
            params[k] = v
        else:
            params[k] = v

    query_string = urlencode(params, doseq=True)

    url_actual = f"?{query_string}" if query_string else ""

    st.sidebar.text_input(
        "📎 Link con filtros aplicados",
        value=url_actual
    )

    if not modo_ejecutivo:
        params_ejecutivo = params.copy()
        params_ejecutivo["ejecutivo"] = "1"

        query_ejecutivo = urlencode(params_ejecutivo, doseq=True)
        url_ejecutivo = f"?{query_ejecutivo}"

        st.sidebar.text_input(
            "🔒 Link Vista Ejecutiva (bloqueado)",
            value=url_ejecutivo
        )


    columnas_grupo = columnas_filtro.copy()

    if modo == "Por día":
        columnas_grupo.append("fecha")

    if modo == "Por mes":
        columnas_grupo.append("anio_mes")

    if not columnas_grupo:
        columnas_grupo = ["fecha"]

    # --------------------------------------------------
    # KPI GENERALES
    # --------------------------------------------------

    resumen = (
        df_filtrado
        .groupby("tipo_archivo", as_index=False)["total_general_s"]
        .sum()
    )

    total_ej = resumen[resumen["tipo_archivo"]=="Ejecutado"]["total_general_s"].sum()
    total_pr = resumen[resumen["tipo_archivo"]=="Proyectado"]["total_general_s"].sum()

    diferencia = total_ej - total_pr
    variacion = (diferencia / total_pr * 100) if total_pr != 0 else 0
    cumplimiento = (total_ej/total_pr * 100) if total_ej != 0 else 0
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💵 Ejecutado", formato_moneda(total_ej))
    col2.metric("📊 Proyectado", formato_moneda(total_pr))
    col3.metric("📉 Diferencia", formato_moneda(diferencia))
    col4.metric("📈 % CUMP.", f"{cumplimiento:,.2f}%")

    # --------------------------------------------------
    # INGRESOS VS EGRESOS
    # --------------------------------------------------

    if "ingresoegreso" in df_filtrado.columns:

        ie = (
            df_filtrado
            .groupby(["tipo_archivo","ingresoegreso"], as_index=False)["total_general_s"]
            .sum()
        )

        fig_ie = px.bar(
            ie,
            x="ingresoegreso",
            y="total_general_s",
            color="tipo_archivo",
            barmode="group",
            title="Ingresos vs Egresos Comparativo"
        )

        st.plotly_chart(fig_ie, use_container_width=True)

    # --------------------------------------------------
    # TABLA COMPARATIVA
    # --------------------------------------------------

    tabla = (
        df_filtrado
        .groupby(columnas_grupo + ["tipo_archivo"], as_index=False)["total_general_s"]
        .sum()
    )

    tabla = tabla.pivot_table(
        index=columnas_grupo,
        columns="tipo_archivo",
        values="total_general_s",
        fill_value=0
    ).reset_index()

    # --------------------------------------------------
    # ASEGURAR QUE SIEMPRE EXISTAN AMBAS COLUMNAS
    # --------------------------------------------------

    if "Ejecutado" not in tabla.columns:
        tabla["Ejecutado"] = 0

    if "Proyectado" not in tabla.columns:
        tabla["Proyectado"] = 0

    # --------------------------------------------------
    # CÁLCULOS SEGUROS
    # --------------------------------------------------

    tabla["Diferencia"] = tabla["Ejecutado"] - tabla["Proyectado"]

    tabla["% CUMP."] = tabla.apply(
        lambda row: (row["Ejecutado"] / row["Proyectado"] * 100)
        if row["Proyectado"] != 0 else 0,
        axis=1
    )
    # --------------------------------------------------
    # AGREGAR MES SELECCIONADO EN RESULTADO
    # --------------------------------------------------

    if mes_seleccionado != "Todos":
        tabla.insert(0, "Mes Seleccionado", mes_seleccionado)

    st.subheader("📊 Resultado Comparativo")

    def color_diferencia(val):
        if val < 0:
            return "color: #BE2323"
        elif val > 0:
            return "color: green"
        return ""

    st.dataframe(
        tabla.style
        .format({
            "Ejecutado": lambda x: f"S/. {x:,.2f}" if pd.notnull(x) else "",
            "Proyectado": lambda x: f"S/. {x:,.2f}" if pd.notnull(x) else "",
            "Diferencia": lambda x: f"S/. {x:,.2f}" if pd.notnull(x) else "",
            "% CUMP.": lambda x: f"{x:,.2f} %" if pd.notnull(x) else ""
        })
        .applymap(color_diferencia, subset=["Diferencia"]),
        use_container_width=True
    )

    # --------------------------------------------------
    # GRÁFICO COMPARATIVO
    # --------------------------------------------------

    #if modo != "Sin comparación":

    eje = "fecha" if modo=="Por día" else "anio_mes"

    graf = (
        df_filtrado
        .groupby([eje,"tipo_archivo"], as_index=False)["total_general_s"]
        .sum()
    )

    fig_bar = px.bar(
        graf,
        x=eje,
        y="total_general_s",
        color="tipo_archivo",
        barmode="group",
        title="Comparación Ejecutado vs Proyectado"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.info("👆 Carga ambos archivos para comenzar el análisis comparativo")
