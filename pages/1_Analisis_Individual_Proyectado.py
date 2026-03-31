import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import plotly.express as px
import streamlit.components.v1 as components
import plotly.io as pio

pio.kaleido.scope.default_format = "png"
pio.kaleido.scope.default_scale = 2
pio.kaleido.scope.default_width = 600
pio.kaleido.scope.default_height = 400

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO

from datetime import datetime
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

import json
import uuid

def guardar_vista(filtros):

    view_id = uuid.uuid4().hex[:8]  # 8 caracteres

    ruta = f"data/views/{view_id}.json"

    with open(ruta, "w") as f:
        json.dump(filtros, f)

    return view_id

def cargar_vista(view_id):

    ruta = f"data/views/{view_id}.json"

    if os.path.exists(ruta):

        with open(ruta) as f:
            return json.load(f)

    return None

st.set_page_config(page_title="Control de Caja 2026", layout="wide")
st.markdown("""
<style>

/* ================================
   🌙 TEMA GLOBAL DARK PRO
   ================================ */

html, body, [class*="css"] {
    font-family: "Segoe UI", Roboto, sans-serif;
    background-color: #0f172a;
    color: #e2e8f0;
}

/* Ocultar fondo blanco default */
.main {
    background-color: #0f172a !important;
}

/* ================================
   🎛️ ADMINISTRACIÓN - VISIBILIDAD PRO
   ================================ */

/* Sidebar base */
section[data-testid="stSidebar"] {
    background: linear-gradient(90deg,#1F4E79,#2E75B6);
}

/* 🔥 TÍTULOS (más visibles) */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
    font-weight: 600;
}

/* 🔥 LABELS (ANTES GRIS, AHORA BLANCO SUAVE) */
section[data-testid="stSidebar"] label {
    color: #f1f5f9 !important;
    font-size: 13px;
    font-weight: 500;
}

/* 🔥 TEXTO GENERAL (más claro) */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    color: #e2e8f0 !important;
}

/* 🔥 INPUTS (alto contraste) */
section[data-testid="stSidebar"] input {
    background-color: #020617 !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    border: 1px solid #334155 !important;
}

/* 🔥 SELECT / MULTISELECT */
section[data-testid="stSidebar"] div[data-baseweb="select"] {
    background-color: #020617 !important;
    color: #ffffff !important;
    border-radius: 10px !important;
}

/* 🔥 TEXTO DENTRO DEL SELECT (MUY IMPORTANTE) */
section[data-testid="stSidebar"] div[data-baseweb="select"] span {
    color: #ffffff !important;
}

/* 🔥 PLACEHOLDER */
section[data-testid="stSidebar"] input::placeholder {
    color: #94a3b8 !important;
}

/* 🔥 TAGS (valores seleccionados) */
section[data-testid="stSidebar"] span[data-baseweb="tag"] {
    background-color: #3b82f6 !important;
    color: white !important;
    font-weight: 500;
}

/* 🔥 BOTONES */
section[data-testid="stSidebar"] .stButton>button {
    background: #2563eb;
    color: white !important;
    border-radius: 8px;
    border: none;
    font-weight: 500;
}

/* 🔥 HOVER */
section[data-testid="stSidebar"] .stButton>button:hover {
    background: #1d4ed8;
}

/* 🔥 RADIO BUTTON (Comparar por) */
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    color: #e2e8f0 !important;
}

/* 🔥 DATE INPUT */
section[data-testid="stSidebar"] .stDateInput input {
    color: white !important;
}

/* 🔥 DIVIDER */
section[data-testid="stSidebar"] hr {
    background: rgba(255,255,255,0.1);
}

/* ================================
   💰 KPI CARDS POWER BI
   ================================ */

.card-hover {
    background: linear-gradient(145deg, #1e293b, #0f172a);
    color: #e2e8f0;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.05);
    transition: all 0.25s ease;
}

.card-hover:hover {
    transform: translateY(-6px) scale(1.01);
    box-shadow: 0 15px 35px rgba(0,0,0,0.4);
}

/* ================================
   📊 SECCIONES
   ================================ */

.section-default {
    background: linear-gradient(145deg, #1e293b, #0f172a);
    padding: 14px 18px;
    border-radius: 12px;
    border-left: 4px solid #3b82f6;
}

/* ================================
   📈 DATAFRAME PRO
   ================================ */

[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.05);
    background: #020617;
}

/* ================================
   📊 BOTONES (EXPORTAR)
   ================================ */

.stDownloadButton>button {
    background: linear-gradient(90deg, #16a34a, #166534);
    color: white !important;
    border-radius: 10px;
    border: none;
}

.stDownloadButton>button:hover {
    transform: scale(1.02);
}

/* ================================
   📉 GRÁFICOS
   ================================ */

.js-plotly-plot {
    border-radius: 14px;
    background: #020617 !important;
}

/* ================================
   ✨ SCROLL PRO
   ================================ */

::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-thumb {
    background: #475569;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #64748b;
}

/* ================================
   🔥 TITULOS MÁS PREMIUM
   ================================ */

h1, h2, h3 {
    letter-spacing: 0.3px;
}

/* ================================
   🧠 KPI COLORES INTELIGENTES
   ================================ */

.kpi-ingreso {
    border-left: 5px solid #16a34a !important;
}

.kpi-egreso {
    border-left: 5px solid #dc2626 !important;
}

.kpi-saldo {
    border-left: 5px solid #3b82f6 !important;
}

</style>
""", unsafe_allow_html=True)
# --------------------------------------------------
# USUARIOS Y ROLES
# --------------------------------------------------

USUARIOS = {
    "admin": {
        "password": "fin2026.",
        "rol": "admin"
    },
    "operador": {
        "password": "operador2026.",
        "rol": "operador"
    }
}

if "rol" not in st.session_state:
    st.session_state["rol"] = "lectura"

st.info(f"Usuario activo: {st.session_state['rol'].upper()}")

# sincronizar URL Y session_state con esos filtros
if "filtros_guardados" in st.session_state:

    filtros = st.session_state["filtros_guardados"]

    for k, v in filtros.items():

        if isinstance(v, list):
            st.query_params[k] = ",".join(v)
        else:
            st.query_params[k] = str(v)

        # reconstruir session_state
        if k != "columnas":
            st.session_state[f"filtro_{k}"] = v if isinstance(v, list) else [v]

        if k != "columnas":
            if isinstance(v, str):
                v = [v]

            st.session_state[f"filtro_{k}"] = v

    # Sincronizar mes si existe
    if "mes" in filtros:
        st.session_state["mes_seleccionado"] = filtros["mes"]

    # Sincronizar columnas si existen
    if "columnas" in filtros:
        columnas = filtros["columnas"]

        if isinstance(columnas, str):
            columnas = columnas.split(",")

        st.session_state["columnas_filtro"] = columnas

    del st.session_state["filtros_guardados"]

import os
from urllib.parse import urlencode

# --------------------------------------------------
# CREAR CARPETA DATA SI NO EXISTE
# --------------------------------------------------
if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists("data/views"):
    os.makedirs("data/views")

ruta_excel = "data/control_caja_proyectado.xlsx"

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
col1, col2 = st.columns([6,1])

with col1:
    st.markdown("""
    <div style="
    background: linear-gradient(90deg,#1F4E79,#2E75B6);
    padding:18px;
    border-radius:10px;
    margin-bottom:15px;
    color:white">

    <h2 style="margin:0">💰 Control de Caja  –  Proyectado 2026 💰</h2>
    <span style="font-size:14px;opacity:0.9">
    Análisis Financiero Proyectado
    </span>

    </div>
    """, unsafe_allow_html=True)

with col2:
    st.image("data/img/cvp.png", width=210)


# --------------------------------------------------
# LOGIN PARA MODO EDICIÓN
# --------------------------------------------------

if st.session_state["rol"] == "lectura":

    with st.sidebar:
        st.subheader("🔐 Acceso al Sistema")

        # 🔹 Guardar filtros actuales
        filtros_actuales = {}

        for k, v in st.query_params.items():
            if isinstance(v, list):
                filtros_actuales[k] = v.copy()
            else:
                # Si viene como string separado por coma
                if "," in str(v):
                    filtros_actuales[k] = str(v).split(",")
                else:
                    filtros_actuales[k] = [v]

        with st.form("login_form"):

            usuario_input = st.text_input("Usuario", key="login_user")
            password_input = st.text_input("Contraseña", type="password", key="login_pass")

            submit = st.form_submit_button("Ingresar")

            if submit:
                if usuario_input in USUARIOS:
                    if password_input == USUARIOS[usuario_input]["password"]:

                        # 🔹 GUARDAR FILTROS ANTES DEL LOGIN
                        st.session_state["filtros_guardados"] = filtros_actuales
                        st.session_state["rol"] = USUARIOS[usuario_input]["rol"]
                        st.success("Acceso concedido")
                        st.rerun()
                    else:
                        st.error("Contraseña incorrecta")
                else:
                    st.error("Usuario no existe")

modo_lectura = st.session_state["rol"] == "lectura"
es_admin = st.session_state["rol"] == "admin"
es_operador = st.session_state["rol"] == "operador"

st.caption("Filtros dinámicos")

# --------------------------------------------------
# ADMINISTRACIÓN
# --------------------------------------------------
if es_admin:
    st.sidebar.divider()
    st.sidebar.subheader("⚙️ Administración")

    if st.sidebar.button("🗑️ Limpiar archivos guardados"):

        if os.path.exists(ruta_excel):
            os.remove(ruta_excel)

        # limpiar filtros
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        st.query_params.clear()

        st.success("Archivos y filtros eliminados correctamente")
        st.rerun()
# --------------------------------------------------
# CARGA O RECUPERACIÓN DE ARCHIVO
# --------------------------------------------------

if es_admin:
    archivo = st.file_uploader("📂 Cargar/Subir Excel", type=["xlsx"])
else:
    archivo = None

# --------------------------------------------------
# SI SE CARGA ARCHIVO NUEVO
# --------------------------------------------------
if archivo is not None and not st.session_state.get("archivo_guardado", False):

    with open(ruta_excel, "wb") as f:
        f.write(archivo.getbuffer())

    st.session_state["archivo_guardado"] = True
    st.session_state["mensaje_mostrado"] = False

    st.success("Archivo guardado correctamente")

# --------------------------------------------------
# CARGAR ARCHIVO SI EXISTE
# --------------------------------------------------
if os.path.exists(ruta_excel):

    df = cargar_excel(ruta_excel)

    # 🔥 Limpiar filtros SOLO si se cargó archivo nuevo
    if st.session_state.get("archivo_guardado", False) and not st.session_state.get("filtros_reseteados", False):

        for key in list(st.session_state.keys()):
            if key.startswith("filtro_"):
                del st.session_state[key]

        st.session_state["filtros_reseteados"] = True

    if not st.session_state.get("mensaje_mostrado", False):
        st.success(f"✅ {len(df)} registros cargados")
        st.session_state["mensaje_mostrado"] = True

    # --------------------------------------------------
    # MANEJO GLOBAL DE URL
    # --------------------------------------------------

    query_params = st.query_params

    # --------------------------------------------------
    # RESTAURAR FILTROS DESDE URL CORTA
    # --------------------------------------------------

    if "v" in query_params:

        filtros_guardados = cargar_vista(query_params["v"])

        if filtros_guardados:

            for k, v in filtros_guardados.items():

                if isinstance(v, list):
                    st.query_params[k] = ",".join(v)
                else:
                    st.query_params[k] = str(v)

            del st.query_params["v"]
    # --------------------------------------------------
    # VARIABLES POR DEFECTO (para modo lectura)
    # --------------------------------------------------

    columnas_filtro = []
    mes_seleccionado = "Todos"
    modo = "Sin comparación"
    df_filtrado = df.copy()

    def guardar_parametro(nombre, valor):

        if not valor or valor == "Todos" or valor == ["Todos"]:
            if nombre in st.query_params:
                del st.query_params[nombre]
            return

        if isinstance(valor, list):
            st.query_params[nombre] = valor
        else:
            st.query_params[nombre] = str(valor)

    def obtener_parametro(nombre):
        return query_params.get(nombre)
    # --------------------------------------------------
    # CONFIGURACIÓN DE FILTROS
    # --------------------------------------------------
    if not modo_lectura:
        st.sidebar.header("🎛️ Configuración De Filtros")


    columnas_disponibles = [
        c for c in df.columns
        if c not in ["total_general_s", "anio_mes"]
    ]

    # --------------------------------------------------
    # COLUMNAS PARA FILTRAR (ARREGLADO SIN DOBLE CLICK)
    # --------------------------------------------------

    if "columnas_filtro" not in st.session_state:

        columnas_url = obtener_parametro("columnas")

        if columnas_url:
            if isinstance(columnas_url, str):
                columnas_url = columnas_url.split(",")

            st.session_state["columnas_filtro"] = [
                c for c in columnas_url if c in columnas_disponibles
            ]
        else:
            st.session_state["columnas_filtro"] = [
                c for c in [
                    "costo__gasto",
                    "clasificacion_1",
                    "clasificacion_flujo2"
                ] if c in columnas_disponibles
            ]
    if not modo_lectura:
        columnas_filtro = st.sidebar.multiselect(
            "Selecciona columnas para filtrar",
            columnas_disponibles,
            default=st.session_state.get("columnas_filtro", []),
            key="columnas_filtro"
        )
    else:
        columnas_url = st.query_params.get("columnas")

        if columnas_url:
            if isinstance(columnas_url, str):
                columnas_url = columnas_url.split(",")

            columnas_filtro = [
                c for c in columnas_url if c in columnas_disponibles
            ]
        else:
            columnas_filtro = []

    # Guardar en URL
    if columnas_filtro:
        st.query_params["columnas"] = ",".join(columnas_filtro)
    else:
        if "columnas" in st.query_params:
            del st.query_params["columnas"]

    if not modo_lectura:
        st.sidebar.divider()
        st.sidebar.subheader("🔍 Filtros")

    # --------------------------------------------------
    # UTILIDAD: seleccionar todos los valores del filtro
    # --------------------------------------------------
    def seleccionar_todos(col, valores):
        st.session_state[f"filtro_{col}"] = valores.copy()
    # --------------------------------------------------
    # FILTRO POR MES
    # --------------------------------------------------

    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    df["mes_num"] = df["fecha"].dt.month
    df["mes_nombre"] = df["mes_num"].map(meses_es)

    df_filtrado = df.copy()

    meses_disponibles = sorted(
        df["mes_nombre"].dropna().unique(),
        key=lambda x: list(meses_es.values()).index(x)
    )

    # Inicializar mes desde URL solo una vez
    if "mes_seleccionado" not in st.session_state:
        st.session_state["mes_seleccionado"] = st.query_params.get("mes", "Todos")

    if not modo_lectura:
        mes_seleccionado = st.sidebar.selectbox(
            "📅 Seleccionar mes",
            ["Todos"] + meses_disponibles,
            key="mes_seleccionado"
        )
    else:
        mes_seleccionado = st.session_state.get(
            "mes_seleccionado",
            st.query_params.get("mes", "Todos")
        )


    guardar_parametro("mes", mes_seleccionado)

    # --------------------------------------------------
    # CALCULAR RANGO BASE SEGÚN MES
    # --------------------------------------------------

    if mes_seleccionado != "Todos":

        df_mes = df[df["mes_nombre"] == mes_seleccionado]

        fecha_min = df_mes["fecha"].min()
        fecha_max = df_mes["fecha"].max()

    else:
        fecha_min = df["fecha"].min()
        fecha_max = df["fecha"].max()

    min_date = fecha_min.date()
    max_date = fecha_max.date()

    # --------------------------------------------------
    # RESETEAR RANGO SI CAMBIA MES
    # --------------------------------------------------

    if "mes_anterior" not in st.session_state:
        st.session_state["mes_anterior"] = mes_seleccionado

    if st.session_state["mes_anterior"] != mes_seleccionado:

        if "fecha_inicio" in st.query_params:
            del st.query_params["fecha_inicio"]

        if "fecha_fin" in st.query_params:
            del st.query_params["fecha_fin"]

        st.session_state["mes_anterior"] = mes_seleccionado
        
    ## FIN de FILTRO POR MES
    ################################
    for col in columnas_filtro:

        valores = (
            df_filtrado[col]
            .dropna()
            .astype(str)
            .sort_values()
            .unique()
            .tolist()
        )


        key = f"filtro_{col}"

        # LEER filtros desde URL
        valores_url = st.query_params.get(col)
        if valores_url:
            if isinstance(valores_url, str):
                valores_url = valores_url.split(",")  # 🔹 separar múltiples valores
            seleccion_actual = [v for v in valores_url if v in valores]
        else:
            seleccion_actual = []

        # -----------------------------
        # Botón seleccionar todos
        # -----------------------------
        if not modo_lectura:

            if st.sidebar.button("✔ Todos", key=f"btn_all_{col}"):
                st.session_state[key] = valores.copy()
                st.rerun()

            # Si el filtro no existe en session_state, reconstruir desde URL
            if key not in st.session_state:

                valores_url = st.query_params.get(col)

                if valores_url:
                    if isinstance(valores_url, str):
                        valores_url = [valores_url]

                    st.session_state[key] = [
                        v for v in valores_url if v in valores
                    ]
                else:
                    st.session_state[key] = []

            opciones_validas = sorted(
                df_filtrado[col].dropna().astype(str).unique()
            )

            # 🔥 Limpiar valores inválidos del session_state
            valores_guardados = st.session_state.get(key, [])

            valores_limpios = [
                v for v in valores_guardados
                if v in opciones_validas
            ]

            # Actualizar session_state si hubo limpieza
            st.session_state[key] = valores_limpios

            seleccion_actual = st.sidebar.multiselect(
                f"{col.replace('_', ' ').title()}",
                options=opciones_validas,
                default=valores_limpios,
                key=key
            )


        if modo_lectura:
            valores_url = st.query_params.get(col)
            if valores_url:
                if isinstance(valores_url, str):
                    valores_url = valores_url.split(",")  # 🔹 separar varios valores
                seleccion_actual = [v for v in valores_url if v in valores]
            else:
                seleccion_actual = []

            # Mostrar los filtros en la barra lateral (solo lectura)
            st.sidebar.markdown(f"**{col.replace('_',' ').title()}:** {', '.join(seleccion_actual) if seleccion_actual else 'Todos'}")

        # Guardar solo los valores seleccionados en URL
        if seleccion_actual:
            st.query_params[col] = ",".join(seleccion_actual)  # 🔹 join para multi-selección
        else:
            if col in st.query_params:
                del st.query_params[col]

        # Aplicar filtro
        if seleccion_actual:
            df_filtrado = df_filtrado[
                df_filtrado[col].isin(seleccion_actual)
            ]

    # --------------------------------------------------
    # RANGO DE FECHAS
    # --------------------------------------------------

    fecha_inicio_url = st.query_params.get("fecha_inicio")
    fecha_fin_url = st.query_params.get("fecha_fin")

    if fecha_inicio_url and fecha_fin_url and mes_seleccionado == "Todos":
        try:
            fecha_inicio = pd.to_datetime(fecha_inicio_url).date()
            fecha_fin = pd.to_datetime(fecha_fin_url).date()
            fechas_default = (fecha_inicio, fecha_fin)
        except:
            fechas_default = (min_date, max_date)
    else:
        fechas_default = (min_date, max_date)

    if not modo_lectura:
        fechas = st.sidebar.date_input(
            "Rango de fechas",
            value=fechas_default,
            min_value=min_date,
            max_value=max_date
        )
    else:
        fecha_inicio_url = st.query_params.get("fecha_inicio")
        fecha_fin_url = st.query_params.get("fecha_fin")

        if fecha_inicio_url and fecha_fin_url:
            fechas = (
                pd.to_datetime(fecha_inicio_url).date(),
                pd.to_datetime(fecha_fin_url).date()
            )
        else:
            fechas = fechas_default


    if len(fechas) == 2:

        guardar_parametro("fecha_inicio", str(fechas[0]))
        guardar_parametro("fecha_fin", str(fechas[1]))

        df_filtrado = df_filtrado[
            (df_filtrado["fecha"] >= pd.to_datetime(fechas[0])) &
            (df_filtrado["fecha"] <= pd.to_datetime(fechas[1]))
        ]
    # --------------------------------------------------
    # COMPARACIONES
    # --------------------------------------------------
    if not modo_lectura:
        modo = st.sidebar.radio(
            "📊 Comparar por",
            ["Sin comparación", "Por día", "Por mes"]
        )
    else:
        modo = st.query_params.get("modo", "Sin comparación")

    
    # --------------------------------------------------
    # INGRESOS / EGRESOS / SALDO
    # --------------------------------------------------
    st.markdown("""
        <hr style="
            border: none;
            height: 1px;
            background: linear-gradient(to right, transparent, #ccc, transparent);
        ">
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-default">', unsafe_allow_html=True)

    st.subheader("📌 Resumen General")
    st.caption("Vista general del comportamiento financiero")

    st.markdown('</div>', unsafe_allow_html=True)

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

        def card(titulo, valor, color, icono):
            st.markdown(f"""
            <div class="card-hover" style="
                background:white;
                padding:22px;
                border-radius:14px;
                box-shadow:0px 4px 12px rgba(0,0,0,0.08);
                border-left:6px solid {color};
            ">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <p style="margin:0; color:gray; font-size:14px;">{titulo}</p>
                        <h2 style="margin:0; color:{color};">S/ {valor:,.2f}</h2>
                    </div>
                    <div style="font-size:28px;">{icono}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        #col1, col2, col3 = st.columns(3)

        with col1:
            card("Ingresos", total_ingresos, "#5095B4", "📈")

        with col2:
            card("Egresos", total_egresos, "#dc2626", "📉") 

        with col3:
            card("Saldo", saldo, "#2563eb", "💰")
        
    st.divider()
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
            "Ingresos": "#5095B4",
            "Egresos": "#BE2323"
        }
    )

    # Hacer porcentajes más grandes y visibles
    fig_pie.update_traces(
        textinfo="percent",
        textfont_size=30,          # 🔹 tamaño más grande
        textposition="inside",     # dentro del gráfico
        insidetextorientation="radial"
    )

    fig_pie.update_layout(
        uniformtext_minsize=15,
        uniformtext_mode="hide"
    )
    fig_pie.update_layout(
        annotations=[
            dict(
                text=f"<b>S/ {saldo:,.0f}</b><br>Saldo",
                x=0.5, y=0.5,
                font_size=15,
                showarrow=False
            )
        ]
    )


    st.plotly_chart(fig_pie, use_container_width=True)

    # --------------------------------------------------
    # TABLA DINÁMICA
    # --------------------------------------------------
    st.markdown("## 📊 Resultado Financiero")
    st.caption("Análisis dinámico basado en filtros aplicados")

    columnas_grupo = columnas_filtro.copy()

    # ------------------------------------------
    # 🔹 AGREGAR MES SI:
    # 1) Se seleccionó un mes específico
    # 2) O el rango de fechas cubre más de un mes
    # ------------------------------------------

    fecha_inicio = pd.to_datetime(fechas[0])
    fecha_fin = pd.to_datetime(fechas[1])

    meses_en_rango = df_filtrado["mes_nombre"].nunique()

    if mes_seleccionado != "Todos" or meses_en_rango > 1:
        if "mes_nombre" not in columnas_grupo:
            columnas_grupo.append("mes_nombre")

    # ------------------------------------------

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
    # Formato especial para deuda_pendiente
    if "deuda_pendiente" in tabla.columns:
        tabla["deuda_pendiente"] = (
            pd.to_numeric(tabla["deuda_pendiente"], errors="coerce")
            .fillna(0)
            .map(lambda x: f"{x:,.2f}")
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
        .set_properties(subset=["TOTAL"], **{"font-weight": "bold"})
    )

    st.dataframe(tabla_estilizada, use_container_width=True)

        # --------------------------------------------------
        # DETALLE
        # --------------------------------------------------
    with st.expander("🔍 Ver detalle completo"):
            st.dataframe(df_filtrado, use_container_width=True)

    # --------------------------------------------------
    # 📈 Visualización de Gráfico por columna seleccionada
    # --------------------------------------------------
    st.subheader("📈 Visualización de Gráfico")

    # Colores profesionales financieros
    color_financiero = {
        "INGRESO": "#16a34a",
        "EGRESO": "#dc2626"
    }
    # Paleta ejecutiva para gráficos
    paleta_ejecutiva = [
        "#5B9BD5",  # azul corporativo 5B9BD5
        "#A5A5A5",  # azul claro
        "#70AD47",  # violeta elegante
        "#FFC000",  # teal
        "#ED7D31",  # ámbar
        "#4472C4",  # gris corporativo
        "#9E480E",  # púrpura
        "#636363", 
        "#997300",
        "#255E91",
        "#43682B",
        "#722E2E", # verde ejecutivo
    ]
    # --------------------------------------------------
    # AGRUPACIÓN PARA GRÁFICO (modo lectura o edición)
    # --------------------------------------------------

    columnas_posibles = [c for c in tabla.columns if c not in ["total_general_s", "total_general_s_fmt"]]

    # Leer agrupación desde URL si es lectura
    if modo_lectura:
        param_agrupacion = st.query_params.get("agrupacion", ["clasificacion_1"])
        if isinstance(param_agrupacion, str):
            param_agrupacion = param_agrupacion.split(",")
        ejes_x = [c for c in param_agrupacion if c in columnas_posibles][:2]  # máximo 2 columnas
        if not ejes_x:
            ejes_x = ["clasificacion_1"] if "clasificacion_1" in columnas_posibles else [columnas_posibles[0]]
    else:
        ejes_x = st.multiselect(
            "Agrupar gráfico por (máx. 2 columnas):",
            options=columnas_posibles,
            default=st.session_state.get("agrupacion_multi", ["clasificacion_1"]),
            max_selections=2,
            key="agrupacion_multi",
            disabled=modo_lectura
        )
        st.query_params["agrupacion"] = ",".join(ejes_x)

    # --------------------------------------------------
    # Preparación de datos para gráfico
    # --------------------------------------------------

    df_filtrado["total_general_s"] = pd.to_numeric(df_filtrado["total_general_s"], errors="coerce").fillna(0)

    graf_pivot = (
        df_filtrado
        .copy()
        .fillna("Sin categoría")
        .groupby(ejes_x + ["ingresoegreso"], as_index=False)["total_general_s"]
        .sum()
    )

    if graf_pivot.empty:
        st.info("No hay datos para mostrar con los filtros actuales.")
        st.stop()

    # Limitar categorías Top + Otros solo si es 1 columna
    MAX_CATEGORIAS = 15
    if len(ejes_x) == 1:
        col = ejes_x[0]
        totales = graf_pivot.groupby(col)["total_general_s"].sum().sort_values(ascending=False)
        if len(totales) > MAX_CATEGORIAS:
            top = totales.head(MAX_CATEGORIAS).index
            graf_pivot[col] = graf_pivot[col].apply(lambda x: x if x in top else "Otros")
            graf_pivot = graf_pivot.groupby([col, "ingresoegreso"], as_index=False)["total_general_s"].sum()
   # --------------------------------------------------
    # Ordenar categorías correctamente para Plotly
    # --------------------------------------------------

    category_orders = {}

    for col in ejes_x:
        if col == "mes_nombre":
            # Mantener orden de Enero a Diciembre
            category_orders[col] = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ]
        else:
            # Orden descendente por total_general_s
            orden = (
                graf_pivot.groupby(col)["total_general_s"]
                .sum()
                .sort_values(ascending=False)
                .index
                .tolist()
            )
            category_orders[col] = orden

    

    # --------------------------------------------------
    # Cálculo profesional de barras por grupo
    # --------------------------------------------------

    if len(ejes_x) == 1:
        barras_por_grupo = graf_pivot["ingresoegreso"].nunique()
    else:
        barras_por_grupo = graf_pivot[ejes_x[1]].nunique()

    # --------------------------------------------------
    # Cálculo de barras
    # --------------------------------------------------

    cantidad_barras = graf_pivot[ejes_x[0]].nunique()

    if cantidad_barras <= 10:
        text_pos = "outside"
        text_angle = -90
        text_size = 13

    elif cantidad_barras <= 18:
        text_pos = "outside"
        text_angle = -90
        text_size = 11

    elif cantidad_barras <= 28:
        text_pos = "inside"
        text_angle = 0
        text_size = 10

    else:
        text_pos = "outside"
        text_angle = -90
        text_size = 5
    # ancho máximo permitido por plotly es 1
    #ancho_barra = min(0.9 / barras_por_grupo, 0.35)
    barras_total = cantidad_barras*barras_por_grupo
    ancho_barra = min(0.9 / barras_total, 0.35)
    # --------------------------------------------------
    # Construcción del gráfico con category_orders
    # --------------------------------------------------
    if len(ejes_x) == 1:
        columna_x = ejes_x[0]

        fig_bar = px.bar(
            graf_pivot,
            x=columna_x,
            y="total_general_s",
            color="ingresoegreso",
            color_discrete_map=color_financiero,
            text=graf_pivot["total_general_s"].map(lambda x: f"S/ {x:,.0f}"),
            labels={"total_general_s": "Total S/"},
            barmode="group",
            title="Total por " + columna_x.replace("_", " ").title(),
            hover_data={columna_x: True, "ingresoegreso": True, "total_general_s": ":,.2f"},
            category_orders={columna_x: category_orders[columna_x]}  # 🔹 aplicar orden
        )

        for trace in fig_bar.data:
            trace.textfont = dict(color=trace.marker.color)
            trace.texttemplate = "<b>%{text}</b>"
    elif len(ejes_x) == 2:
        col1, col2 = ejes_x

        fig_bar = px.bar(
            graf_pivot,
            x=col1,
            y="total_general_s",
            color=col2,
            color_discrete_sequence=paleta_ejecutiva,
            text=graf_pivot["total_general_s"].map(lambda x: f"S/ {x:,.0f}"),
            labels={"total_general_s": "Total S/"},
            barmode="group",
            title="Total por " + " + ".join(ejes_x).replace("_", " ").title(),
            hover_data={col1: True, col2: True, "total_general_s": ":,.2f"},
            category_orders={
                col1: category_orders[col1],
                col2: category_orders[col2]
            }  # 🔹 aplicar orden a ambas columnas
        )
        for trace in fig_bar.data:
            trace.textfont = dict(color=trace.marker.color)
            trace.texttemplate = "<b>%{text}</b>"

    else:
        st.warning("Máximo 2 columnas permitidas.")
        st.stop()

    # --------------------------------------------------
    # Ajuste automático de textos para evitar colisiones
    # --------------------------------------------------
    
    
    fig_bar.update_traces(
        #width=ancho_barra,
        textposition=text_pos,
        textangle=text_angle,
        textfont=dict(size=text_size),
        cliponaxis=False
    )
    
    fig_bar.update_traces(
        hovertemplate="<b>%{x}</b><br>Total: S/ %{y:,.2f}<extra></extra>"
    )
    # --------------------------------------------------
    # ESCALA INTELIGENTE DEL EJE Y
    # --------------------------------------------------

    max_valor = graf_pivot["total_general_s"].max()
    min_valor = graf_pivot["total_general_s"].min()

    # Detectar diferencia entre valores
    if min_valor == 0:
        ratio = max_valor
    else:
        ratio = max_valor / min_valor

    # Espacio superior dinámico
    if ratio > 1000:
        espacio_superior = 1.9
    elif ratio > 200:
        espacio_superior = 1.7
    elif ratio > 50:
        espacio_superior = 1.55
    elif ratio > 10:
        espacio_superior = 1.45
    else:
        espacio_superior = 1.35

    fig_bar.update_yaxes(range=[0, max_valor * espacio_superior])
    fig_bar.update_yaxes(automargin=True)
    # --------------------------------------------------
    # Ajustes dinámicos
    # --------------------------------------------------

    num_conceptos = graf_pivot[ejes_x[-1]].nunique()

    margen_superior = 170 + (num_conceptos * 6)

    if margen_superior > 260:
        margen_superior = 260

    altura_grafico = 500 + (cantidad_barras * 35)

    if altura_grafico > 1100:
        altura_grafico = 1100
    # --------------------------------------------------
    # ESPACIO DINÁMICO ENTRE BARRAS
    # --------------------------------------------------

    if cantidad_barras <= 4:
        gap_barras = 0.55
    elif cantidad_barras <= 8:
        gap_barras = 0.45
    elif cantidad_barras <= 15:
        gap_barras = 0.35
    else:
        gap_barras = 0.25

    fig_bar.update_layout(
        xaxis_title=None,
        yaxis_title="Total S/",
        height=altura_grafico,

        title=dict(
            text="Total por " + " + ".join(ejes_x).replace("_", " ").title(),
            #y=0.95,           # 🔹 bajar un poco el título para dejar espacio a la leyenda arriba
            x=0,
            y=1,
            xanchor="left",
            yanchor="top"
        ),

        legend=dict(
            title="Conceptos",
            orientation="h",
            yanchor="bottom",  # el punto y= se refiere al fondo de la leyenda
            y=1.30,            # 🔹 colocar la leyenda por encima del título
            xanchor="center",
            x=0.5
        ),

        margin=dict(
            t=margen_superior + 40,  # 🔹 aumentar margen superior si es necesario
            b=80,
            l=60,
            r=40
        ),
        barmode="group",
        bargap=0.25,
        bargroupgap=0.05,
        uniformtext_minsize=12,
        uniformtext_mode="show",
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    #st.divider()
    # Grid suave
    fig_bar.update_yaxes(
        showgrid=True,
        gridcolor="rgba(200,200,200,0.25)"
    )

    # Formato monetario
    fig_bar.update_yaxes(
        tickprefix="S/ ",
        separatethousands=True
    )

    fig_bar.update_xaxes(tickangle=-45)

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
            zipf.writestr("control_caja_proyectado.xlsx", excel_buffer.read())

            # -----------------------------
            # Gráficos
            # -----------------------------
            zipf.writestr(
                "grafico_ingresos_egresos.png",
                fig_pie.to_image(format="png", engine="kaleido", scale=2)
            )

            zipf.writestr(
                "grafico_resultados.png",
                fig_bar.to_image(format="png", engine="kaleido",scale=2)
            )

        zip_buffer.seek(0)
        return zip_buffer

        #boton

    st.divider()
    # --------------------------------------------------
    # LINK COMPARTIBLE
    # --------------------------------------------------

    if not modo_lectura:

        st.sidebar.divider()

        filtros_compartir = {}

        for k, v in st.query_params.items():
            if isinstance(v, list):
                filtros_compartir[k] = v
            else:
                if "," in str(v):
                    filtros_compartir[k] = str(v).split(",")
                else:
                    filtros_compartir[k] = v


        # generar id de vista
        view_id = guardar_vista(filtros_compartir)

        components.html(f"""
        <div style="margin-top:10px">

        <button onclick="copyUrl()" style="
        background:#2E8B57;
        color:white;
        border:none;
        padding:10px 16px;
        border-radius:8px;
        cursor:pointer;
        font-size:14px;
        width:100%;
        ">
        🔗 Generar y copiar URL corta
        </button>

        </div>

        <script>

        function copyUrl() {{

        const base = window.parent.location.origin + window.parent.location.pathname;
        const url = base + "?v={view_id}";

        navigator.clipboard.writeText(url).then(function() {{
            alert("✅ URL copiada:\\n" + url);
        }});

        }}

        </script>
        """, height=80)

    st.divider()
    st.subheader("📤 Exportar Excel + Gráficos")

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
        file_name="Control_Caja_Excel_Proyectado.zip",
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
        ultima_fecha,
        fecha_inicio,
        fecha_fin
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
    # TÍTULO DEL PDF
    # -------------------------------
        story.append(Paragraph("<b>REPORTE EJECUTIVO – CONTROL DE CAJA</b>", styles["Title"]))
        story.append(Spacer(1, 12))

        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")

        fecha_inicio_fmt = pd.to_datetime(fecha_inicio).strftime("%d/%m/%Y")
        fecha_fin_fmt = pd.to_datetime(fecha_fin).strftime("%d/%m/%Y")

        story.append(
            Paragraph(
                f"<b>Fecha de generación:</b> {fecha_generacion}",
                styles["Normal"]
            )
        )

        story.append(Spacer(1, 6))

        story.append(
            Paragraph(
                f"<b>Rango de Análisis:</b> {fecha_inicio_fmt} al {fecha_fin_fmt}",
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
        pie_img = BytesIO(
        fig_pie.to_image(format="png", engine="kaleido", scale=2)
        )

        bar_img = BytesIO(
        fig_bar.to_image(format="png", engine="kaleido", scale=2)
        )

        story.append(Paragraph("<b>Distribución de Ingresos y Egresos</b>", styles["Heading2"]))
        story.append(Spacer(1, 8))
        story.append(Image(pie_img, width=14*cm, height=9*cm))
        story.append(Spacer(1, 16))

        story.append(Paragraph("<b>Resultados según filtros</b>", styles["Heading2"]))
        story.append(Spacer(1, 8))
        story.append(Image(bar_img, width=15*cm, height=9*cm))
        story.append(Spacer(1, 16))

    # -------------------------------
    # TABLA RESUMEN
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
                color = "#BE2323" if es_egreso else "#269161"
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

    st.subheader("📤 Exportar PDF")

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
        ultima_fecha=ultima_fecha,
        fecha_inicio=fechas[0],
        fecha_fin=fechas[1]
    )
    st.download_button(
        "📄 Descargar PDF",
        data=pdf_buffer,
        file_name="reporte_control_caja_proyectado.pdf",
        mime="application/pdf"
    )