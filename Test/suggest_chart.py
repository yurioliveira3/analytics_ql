import plotly.io as pio
import plotly.express as px
import pandas as pd

def suggest_chart(df: pd.DataFrame) -> str | None:
    """
    Recebe um DataFrame e devolve um snippet HTML (Plotly) 
    com um gráfico “adequado” aos tipos de coluna encontrados.
    Retorna None se não conseguir sugerir nada.
    """
    try:
        # 1) Detecta colunas
        num_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()
        dt_cols  = df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns.tolist()

        # 2) Heurística bem simples
        if len(num_cols) == 1 and not cat_cols:
            fig = px.histogram(df, x=num_cols[0])
        elif len(num_cols) >= 1 and cat_cols:
            fig = px.bar(df, x=cat_cols[0], y=num_cols[0])
        elif len(num_cols) >= 2:
            fig = px.scatter(df, x=num_cols[0], y=num_cols[1])
        elif dt_cols and num_cols:
            fig = px.line(df, x=dt_cols[0], y=num_cols[0])
        else:
            return None  # não achou combinação decente

        # 3) Converte para HTML autônomo
        return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

    except Exception as e:
        print(f"Erro na sugestão de gráfico: {e}")
        return None
