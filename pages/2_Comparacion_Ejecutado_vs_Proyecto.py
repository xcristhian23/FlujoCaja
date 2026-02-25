import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
import zipfile
from io import BytesIO
from datetime import datetime
import streamlit.components.v1 as components
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
# CONTROL DE ACCESO MULTIROL
# --------------------------------------------------

# --------------------------------------------------
# USUARIOS Y ROLES
# --------------------------------------------------
# =====================================================
# 🔐 SISTEMA DE ROLES (IGUAL AL SISTEMA ANTIGUO)
# =====================================================

USUARIOS = {
    "admin": {
        "password": "finanzas2026.",
        "rol": "admin"
    },
    "operador": {
        "password": "operador2026.",
        "rol": "operador"
    }
}

# Rol por defecto = lectura
if "rol" not in st.session_state:
    st.session_state["rol"] = "lectura"

# --------------------------------------------------
# DEFINICIÓN DE MODOS
# --------------------------------------------------

modo_lectura = st.session_state["rol"] == "lectura"
es_admin = st.session_state["rol"] == "admin"
es_operador = st.session_state["rol"] == "operador"

# =====================================================
# 🔐 LOGIN SOLO SI ESTÁ EN LECTURA
# =====================================================

if st.session_state["rol"] == "lectura":

    with st.sidebar:
        st.subheader("🔐 Acceso al Sistema")

        filtros_actuales = dict(st.query_params)

        with st.form("login_form"):

            usuario_input = st.text_input("Usuario")
            password_input = st.text_input("Contraseña", type="password")

            submit = st.form_submit_button("Ingresar")

            if submit:
                if usuario_input in USUARIOS:
                    if password_input == USUARIOS[usuario_input]["password"]:

                        # 🔥 GUARDAR FILTROS ACTUALES
                        st.session_state["filtros_guardados"] = filtros_actuales
                        st.session_state["rol"] = USUARIOS[usuario_input]["rol"]

                        st.success("Acceso concedido")
                        st.rerun()
                    else:
                        st.error("Contraseña incorrecta")
                else:
                    st.error("Usuario no existe")


# --------------------------------------------------
# INFO USUARIO
# --------------------------------------------------

if st.session_state["rol"] != "lectura":

    st.sidebar.success(f"👤 Rol: {st.session_state['rol']}")

    if st.sidebar.button("Cerrar sesión"):
        st.session_state["rol"] = "lectura"
        st.rerun()

else:
    st.sidebar.info("🔒 Vista en modo lectura")



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

if st.session_state["rol"] == "admin":
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
    archivo_ej = st.file_uploader(
        "📂 Cargar Excel Ejecutado",
        type=["xlsx"],
        disabled=not es_admin
        )



    if archivo_ej:
        with open(ruta_ej, "wb") as f:
            f.write(archivo_ej.getbuffer())
        st.success("Ejecutado guardado correctamente")

with col2:
    archivo_pr = st.file_uploader("📂 Cargar Excel Proyectado", type=["xlsx"],
        disabled=not es_admin
    )
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

    # =====================================================
    # 🔁 RESTAURAR FILTROS DESPUÉS DEL LOGIN
    # =====================================================

    if "filtros_guardados" in st.session_state:

        filtros = st.session_state["filtros_guardados"]

        for k, v in filtros.items():
            st.query_params[k] = v

            if k != "columnas":
                if isinstance(v, str):
                    v = [v]

                st.session_state[f"filtro_{k}"] = v

        

        if "columnas" in filtros:
            columnas = filtros["columnas"]

            if isinstance(columnas, str):
                columnas = columnas.split(",")

            st.session_state["columnas_filtro"] = columnas

        del st.session_state["filtros_guardados"]

    def guardar_parametro(nombre, valor):

        if not valor or valor == "Todos" or valor == ["Todos"]:
            if nombre in st.query_params:
                del st.query_params[nombre]
            return

        if isinstance(valor, list):
            st.query_params[nombre] = ",".join(map(str, valor))
        else:
            st.query_params[nombre] = str(valor)


    def obtener_parametro(nombre):
        return query_params.get(nombre)

    if obtener_parametro("view") == "1":
        st.session_state["rol"] = "lectura"
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
        key="columnas_filtro",
        disabled=modo_lectura
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

    opciones_mes = ["Todos"] + meses_disponibles

    if mes_url in opciones_mes:
        index_mes = opciones_mes.index(mes_url)
    else:
        index_mes = 0

    mes_seleccionado = st.sidebar.selectbox(
        "Seleccionar mes",
        options=opciones_mes,
        index=index_mes,
        disabled=modo_lectura,
        key="mes_selector"
    )

    if not modo_lectura:
        guardar_parametro("mes", mes_seleccionado)


    # Detectar cambio de mes
    if mes_seleccionado != "Todos" and not modo_lectura:

        df_mes_temp = df[df["mes_nombre"] == mes_seleccionado]

        if not df_mes_temp.empty:

            nueva_fecha_inicio = df_mes_temp["fecha"].min().date()
            nueva_fecha_fin = df_mes_temp["fecha"].max().date()

            guardar_parametro("fecha_inicio", nueva_fecha_inicio)
            guardar_parametro("fecha_fin", nueva_fecha_fin)

    # 🔥 IMPORTANTE:
    # Si es "Todos" NO borramos fecha_inicio ni fecha_fin
    # Dejamos que el date_input controle eso

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

        def actualizar_columnas():
            st.session_state.columnas_visibles = st.session_state.columnas_selector

        # Callback para comportamiento "Todos"
        def on_change_callback(col=col, valores=valores, key=key):

            seleccion = st.session_state[key]

            if "Todos" in seleccion:
                # Reemplazar por todos los valores reales
                st.session_state[key] = list(valores)


        # Recuperar desde URL SOLO la primera vez
        if key not in st.session_state:

            valor_url = obtener_parametro(col)

            if valor_url:
                if isinstance(valor_url, str):
                    valor_url = valor_url.split(",")

                st.session_state[key] = valor_url


        seleccion = st.sidebar.multiselect(
            f"{col.replace('_', ' ').title()}",
            options=opciones,
            key=key,
            disabled=modo_lectura,
            on_change=on_change_callback
        )


        if not modo_lectura:
            guardar_parametro(col, seleccion)

    
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
                disabled=modo_lectura
            )

            if len(fechas) == 2:

                if not modo_lectura:
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
            disabled=modo_lectura
    )


    if not modo_lectura:
        guardar_parametro("modo", modo)

    # --------------------------------------------------
    # GENERAR LINK COMPARTIBLE
    # --------------------------------------------------

    # --------------------------------------------------
    # LINK COMPARTIBLE REAL (FUNCIONA EN CLOUD)
    # --------------------------------------------------

    #if not params_lectura:

    st.sidebar.divider()
    st.sidebar.subheader("🔗 Compartir vistas")

    components.html(
        """
        <script>
        const url = window.parent.location.href;
        const container = window.parent.document.querySelector('section.main');
        </script>
        """,
        height=0,
    )

    st.sidebar.markdown(
        """
        <a href="" onclick="
        const url = new URL(window.location.href);
        url.searchParams.set('view','1');
        navigator.clipboard.writeText(url.toString());
        return false;">
            📋 Copiar URL modo lectura
        </a>
        """,
        unsafe_allow_html=True
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
    col4.metric("📈 % Cumplimiento.", f"{cumplimiento:,.2f}%")

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

    tabla["% Cumplimiento"] = tabla.apply(
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
            "% Cumplimiento": lambda x: f"{x:,.2f} %" if pd.notnull(x) else ""
        })
        .applymap(color_diferencia, subset=["Diferencia"]),
        use_container_width=True
    )

    # ----------------------------------------
    # Selector dinámico de dimensión
    # ----------------------------------------

    # ----------------------------------------
    # Selector dinámico de dimensión (CON URL)
    # ----------------------------------------

    columnas_posibles = [
        col for col in df_filtrado.columns
        if col not in ["total_general_s", "tipo_archivo"]
    ]

    key_agrupar = "agrupar_por"

    # 🔹 Restaurar desde URL solo la primera vez
    if key_agrupar not in st.session_state:

        valor_url = obtener_parametro(key_agrupar)

        if valor_url and valor_url in columnas_posibles:
            st.session_state[key_agrupar] = valor_url
        else:
            st.session_state[key_agrupar] = columnas_posibles[0]

    # --------------------------------------------------
        # DETALLE
        # --------------------------------------------------
    with st.expander("🔍 Ver detalle completo"):
            st.dataframe(df_filtrado, use_container_width=True)

    st.subheader("📈 Visualización de Gráfico")

    # Definir eje X
    if "clasificacion_1" in tabla.columns:
        eje_x = "clasificacion_1"
    else:
        eje_x = columnas_grupo[0]

    #fig_bar = px.bar(
    #    tabla,
    #    x=eje_x,
    #    y="total_general_s",
    #    text_auto=".2s",
    #    labels={
    #        "total_general_s": "Total S/"
    #    },
    #    title="Total por Clasificación"
    #)

    # 👉 Personalizar el hover (tooltip)
     #fig_bar.update_traces(
     #    hovertemplate=
     #        "<b>%{x}</b><br>" +
      #       "Total: S/ %{y:,.2f}" +
       #      "<extra></extra>"
  #   )

   #  fig_bar.update_layout(
    #     xaxis_title=None,
    #     height=500
   #  )

   #  st.plotly_chart(fig_bar, use_container_width=True)

    columna_descripcion = st.selectbox(
        "Agrupar gráfico por:",
        columnas_posibles,
        key=key_agrupar,
        disabled=modo_lectura
    )

    # 🔹 Guardar en URL solo si NO está en modo lectura
    if not modo_lectura:
        guardar_parametro(key_agrupar, columna_descripcion)
    
    # --------------------------------------------------
    # GRÁFICO EJECUTIVO PROFESIONAL
    # --------------------------------------------------

    st.subheader("📊 FC Ejecutado vs FC Presupuesto")

    # ----------------------------------------
    # Definir columna descripción dinámica
    # ----------------------------------------

    if columna_descripcion:

        # ----------------------------------------
        # Agrupar datos
        # ----------------------------------------

        graf_base = (
            df_filtrado
            .groupby([columna_descripcion, "tipo_archivo"], as_index=False)["total_general_s"]
            .sum()
        )

        graf_pivot = graf_base.pivot_table(
            index=columna_descripcion,
            columns="tipo_archivo",
            values="total_general_s",
            fill_value=0
        ).reset_index()

        # Asegurar columnas
        if "Ejecutado" not in graf_pivot.columns:
            graf_pivot["Ejecutado"] = 0

        if "Proyectado" not in graf_pivot.columns:
            graf_pivot["Proyectado"] = 0

        # ----------------------------------------
        # Métricas adicionales
        # ----------------------------------------

        graf_pivot["Diferencia"] = graf_pivot["Ejecutado"] - graf_pivot["Proyectado"]

        graf_pivot["% Cumplimiento"] = graf_pivot.apply(
            lambda row: (row["Ejecutado"] / row["Proyectado"] * 100)
            if row["Proyectado"] != 0 else 0,
            axis=1
        )

        # ----------------------------------------
        # Ordenar de mayor a menor impacto
        # ----------------------------------------

        graf_pivot = graf_pivot.sort_values(
            by="Ejecutado",
            ascending=False
        )

        # ----------------------------------------
        # Crear gráfico
        # ----------------------------------------

        import plotly.graph_objects as go

        fig = go.Figure()

        # ----------------------------------------
        # BARRA REAL
        # ----------------------------------------

        fig.add_trace(go.Bar(
            x=graf_pivot[columna_descripcion],
            y=graf_pivot["Ejecutado"].apply(lambda x: abs(x) if x != 0 else 0.0001),
            name="FC REAL",
            marker_color="#1F4E79",
            width=0.25,
            offsetgroup="1",
            text=[f"S/ {v:,.0f}" for v in graf_pivot["Ejecutado"]],
            texttemplate="%{text}",
            textposition="outside",
            textangle=90,
            constraintext="none",
            textfont=dict(
                size=16,
                color="#1F4E79",
                family="Arial Black"
            ),
            cliponaxis=False
        ))

        # ----------------------------------------
        # BARRA PRESUPUESTO
        # ----------------------------------------

        fig.add_trace(go.Bar(
            x=graf_pivot[columna_descripcion],
            y=graf_pivot["Proyectado"].apply(lambda x: abs(x) if x != 0 else 0.0001),
            name="PRESUPUESTO",
            marker_color="#ED7D31",
            width=0.25,
            offsetgroup="2",
            text=[f"S/ {v:,.0f}" for v in graf_pivot["Proyectado"]],
            texttemplate="%{text}",
            textposition="outside",
            textangle=90,
            constraintext="none",
            textfont=dict(
                size=13,
                color="#ED7D31",
                family="Arial Black"
            ),
            cliponaxis=False
        ))
        
        fig.add_trace(go.Bar(
            x=graf_pivot[columna_descripcion],
            y=graf_pivot["% Cumplimiento"].apply(lambda x: x if x != 0 else 0.0001),
            name="% Cumplimiento",
            marker_color="#70AD47",
            width=0.25,
            offsetgroup="3",
            text=[f"{v:.0f}%" for v in graf_pivot["% Cumplimiento"]],
            texttemplate="%{text}",
            textposition="outside",
            textangle=90,
            textfont=dict(
                size=13,
                color="#2E7D32",
                family="Arial Black"
            ),
            cliponaxis=False
        ))


        # ----------------------------------------
        # Layout ejecutivo
        # ----------------------------------------

        fig.update_layout(
            barmode="group",
            title=dict(
                text="FC Ejecutado vs FC Presupuesto",
                x=0.5,
                xanchor="center",
                font=dict(size=20)
            ),
            xaxis_title="",
            yaxis_title="Monto (S/)",
            yaxis2=dict(
                title="% Cumplimiento",
                overlaying="y",
                side="right",
                showgrid=False,
                showticklabels=False,   # 🔥 quita 0,100,200
                zeroline=False,         # 🔥 quita línea base
                #range=[0, 120],   # 🔥 rango fijo
                #range=[0, max(120, graf_pivot["% Cumplimiento"].max() * 1.2)],
                range=[0, max(130, graf_pivot["% Cumplimiento"].max() * 1.25)],
                tickformat=".0f"
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.05,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(
                tickangle=-25
            ),
            template="plotly_white",
            height=650
        )

        max_y = graf_pivot[["Ejecutado","Proyectado"]].abs().max().max()

        fig.update_layout(
            yaxis=dict(
                range=[0, max_y * 1.35],
                showgrid=False,        # 🔥 quita líneas horizontales
                showticklabels=False,  # 🔥 quita 0, 1M, 2M
                zeroline=False         # 🔥 quita línea en cero
            )
        )

        st.plotly_chart(fig, use_container_width=True)
        
else:
    st.info("👆 Carga ambos archivos para comenzar el análisis comparativo")
