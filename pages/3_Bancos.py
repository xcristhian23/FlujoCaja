import streamlit as st
import pandas as pd

st.set_page_config(page_title="Resumen por Hojas", layout="wide")

st.title("📊 Análisis de Excel por Hojas")

# --------------------------------------------------
# 📂 Cargar archivo Excel
# --------------------------------------------------
archivo = st.file_uploader("Cargar archivo Excel", type=["xlsx"])

if archivo:

    # Leer todas las hojas
    hojas_dict = pd.read_excel(archivo, sheet_name=None)

    nombres_hojas = list(hojas_dict.keys())

    # --------------------------------------------------
    # 🔎 Sidebar - Filtros
    # --------------------------------------------------
    st.sidebar.header("🔎 Filtros")

    hoja_seleccionada = st.sidebar.multiselect(
        "Seleccionar hoja(s):",
        options=nombres_hojas,
        default=nombres_hojas
    )

    if not hoja_seleccionada:
        st.warning("Selecciona al menos una hoja.")
        st.stop()

    # --------------------------------------------------
    # 📊 Procesar hojas seleccionadas
    # --------------------------------------------------
    resultados = []

    for hoja in hoja_seleccionada:

        df = hojas_dict[hoja].copy()

        # Normalizar nombres de columnas
        df.columns = df.columns.str.strip().str.lower()

        # Validar columnas necesarias
        if "tipo" not in df.columns or "monto" not in df.columns:
            st.error(f"La hoja '{hoja}' no contiene columnas 'tipo' y 'monto'.")
            continue

        ingresos = df[df["tipo"].str.upper() == "INGRESO"]["monto"].sum()
        egresos = df[df["tipo"].str.upper() == "EGRESO"]["monto"].sum()
        saldo = ingresos - egresos

        resultados.append({
            "Hoja": hoja,
            "Ingresos": ingresos,
            "Egresos": egresos,
            "Saldo": saldo
        })

    if resultados:

        st.subheader("📌 Resumen por Hoja")

        # Mostrar tarjetas dinámicas
        cols = st.columns(len(resultados))

        for col, data in zip(cols, resultados):

            with col:
                st.markdown(f"""
                <div style="
                    padding:20px;
                    border-radius:15px;
                    background-color:#f0f2f6;
                    box-shadow:2px 2px 10px rgba(0,0,0,0.1);
                ">
                    <h4>{data['Hoja']}</h4>
                    <p><b>Ingresos:</b> S/ {data['Ingresos']:,.2f}</p>
                    <p><b>Egresos:</b> S/ {data['Egresos']:,.2f}</p>
                    <p><b>Saldo:</b> S/ {data['Saldo']:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)

        # --------------------------------------------------
        # 📋 Tabla consolidada opcional
        # --------------------------------------------------
        st.subheader("📋 Tabla Consolidada")

        df_resultado = pd.DataFrame(resultados)
        st.dataframe(df_resultado, use_container_width=True)

else:
    st.info("Carga un archivo Excel para comenzar.")