import plotly.express as px

def grafico_comparacion(df):

    fig = px.bar(
        df,
        x="Categoría",
        y=["Ejecutado", "Proyecto"],
        barmode="group",
        title="Ejecutado vs Proyecto"
    )

    return fig
