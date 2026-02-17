import streamlit as st
import pandas as pd

def aplicar_filtros(df):

    st.sidebar.header("🎛️ Configuración de filtros")

    columnas_disponibles = [
        c for c in df.columns
        if c not in ["total_general_s", "anio_mes"]
    ]

    columnas_filtro = st.sidebar.multiselect(
        "Selecciona columnas para filtrar",
        columnas_disponibles
    )

    st.sidebar.divider()
    st.sidebar.subheader("🔍 Filtros")

    df_filtrado = df.copy()

    for col in columnas_filtro:

        valores = sorted(df_filtrado[col].dropna().unique())
        key = f"filtro_{col}"

        opciones = ["Todos"] + valores

        if key not in st.session_state:
            st.session_state[key] = []

        def on_change_callback(col=col, valores=valores, key=key):
            seleccion = st.session_state[key]
            if "Todos" in seleccion:
                st.session_state[key] = valores.copy()

        st.sidebar.multiselect(
            col.replace("_", " ").title(),
            options=opciones,
            key=key,
            on_change=on_change_callback
        )

        if st.session_state[key]:
            df_filtrado = df_filtrado[
                df_filtrado[col].isin(st.session_state[key])
            ]

    # Filtro fecha
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

    return df_filtrado, columnas_filtro
