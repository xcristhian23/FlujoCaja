import streamlit as st
import plotly.express as px

def mostrar_resumen(df):

    total_ingresos = df[
        df["ingresoegreso"].str.upper() == "INGRESO"
    ]["total_general_s"].sum()

    total_egresos = df[
        df["ingresoegreso"].str.upper() == "EGRESO"
    ]["total_general_s"].sum()

    saldo = total_ingresos + total_egresos

    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Total Ingresos", f"S/ {total_ingresos:,.2f}")
    col2.metric("💸 Total Egresos", f"S/ {total_egresos:,.2f}")
    col3.metric("⚖️ Saldo", f"S/ {saldo:,.2f}")

    return total_ingresos, total_egresos, saldo


def grafico_pie(total_ingresos, total_egresos):

    df_ie = {
        "Tipo": ["Ingresos", "Egresos"],
        "Monto": [total_ingresos, abs(total_egresos)]
    }

    fig = px.pie(
        df_ie,
        names="Tipo",
        values="Monto",
        hole=0.5
    )

    st.plotly_chart(fig, use_container_width=True)

    return fig
