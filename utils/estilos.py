def pintar_diferencia(row):

    try:
        valor = float(row["Diferencia"])
    except:
        return [""] * len(row)

    if valor > 0:
        return ["background-color: #ffcccc"] * len(row)
    elif valor < 0:
        return ["background-color: #ccffcc"] * len(row)
    else:
        return [""] * len(row)
