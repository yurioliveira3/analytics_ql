"""
Módulo para geração de gráficos e visualizações de dados.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import uuid
from utils.logger import get_logger

# Logger para este módulo
logger = get_logger(__name__)


def is_identifier(series: pd.Series) -> bool:
    """
    Identifica se uma série é um identificador (ID, código, etc.).
    
    Args:
        series: Série do pandas a ser analisada
        
    Returns:
        True se for identificador, False caso contrário
    """
    name = series.name.lower()
    # 1) Nome suspeito
    if any(key in name for key in ["id", "cod", "code", "cpf", "rg", "registro"]):
        return True
    # 2) Cardinalidade alta e inteira
    if pd.api.types.is_integer_dtype(series):
        unique_ratio = series.nunique(dropna=True) / len(series)
        if unique_ratio >= 0.8:           # >= 80 % valores únicos
            return True
    if "data_nascimento" in name:
        return False 
    
    return False


def suggest_chart(df: pd.DataFrame) -> tuple[str | None, str | None]:
    """
    Analisa o DataFrame e devolve (html_snippet, chart_type).

    Retorna (None, None) se nenhuma regra encontrar gráfico adequado.
    
    Args:
        df: DataFrame a ser analisado
        
    Returns:
        Tupla com (HTML do gráfico, tipo do gráfico) ou (None, None)
    """
    try:
        # 1 ─ Classificação de colunas
        num_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()
        dt_cols  = df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns.tolist()

        id_like  = [col for col in num_cols if is_identifier(df[col])]
        num_cols = [col for col in num_cols if col not in id_like]

        # ── Detecção de categorias de "baixa cardinalidade" ──────────────────
        CAT_SMALL_MAX = 8
        small_cat_cols = [c for c in cat_cols if df[c].nunique() <= CAT_SMALL_MAX]
        
        # ── Nova função: escolher categórica "melhor" (menor cardinalidade > 1) ──
        def get_best_categorical(cols: list[str]) -> str | None:
            """Retorna a categórica com menor cardinalidade > 1."""
            if not cols:
                return None
            valid_cols = [(c, df[c].nunique()) for c in cols if df[c].nunique() > 1]
            if not valid_cols:
                return None
            return min(valid_cols, key=lambda x: x[1])[0]

        # ── Filtro "all-unique" reativado ────────────────────────────────────────
        def has_all_unique_values(cols: list[str]) -> bool:
            """Verifica se todas as colunas categóricas têm apenas valores únicos."""
            return all(df[col].nunique() == len(df) for col in cols)

        if cat_cols and has_all_unique_values(cat_cols) and not num_cols:
            return None, None  # Pula gráfico se tudo for único

        # 2 ─ Regras específicas (mais restritas → mais genéricas)

        # 2A0. Pie para único registro com duas colunas numéricas (percentuais)
        if df.shape[0] == 1 and len(num_cols) == 2:
            values = df.iloc[0][num_cols].tolist()
            labels = num_cols
            fig = px.pie(
                values=values,
                names=labels,
                hole=0.3,
                labels={labels[0]: labels[0], labels[1]: labels[1]}
            )
            chart_type = "pizza"

        # 2A. Heatmap: 2 categóricas de baixa cardinalidade, 0 numéricas
        elif len(small_cat_cols) >= 2 and not num_cols:
            row, col = small_cat_cols[:2]
            pivot = pd.crosstab(df[row], df[col])
            fig = px.imshow(
                pivot,
                labels=dict(x=col, y=row, color="Contagem"),
                text_auto=True,
                aspect="auto"
            )
            chart_type = "mapa_de_calor"

        # 2B. Multi-line temporal: datetime + ≥2 numéricas
        elif dt_cols and len(num_cols) >= 2:
            time_col = dt_cols[0]
            plot_df = df[[time_col] + num_cols].sort_values(time_col)
            fig = px.line(plot_df, x=time_col, y=num_cols, markers=False)
            chart_type = "multilinha"

        # 2C. Linha temporal simples: datetime + 1 numérica
        elif dt_cols and len(num_cols) == 1:
            time_col = dt_cols[0]
            num_col = num_cols[0]
            plot_df = df[[time_col, num_col]].sort_values(time_col)
            fig = px.line(plot_df, x=time_col, y=num_col, markers=False)
            chart_type = "linha"

        # 2D. Bloco pie/bar unificado: 1 categórica + ≤1 numérica
        elif cat_cols and len(num_cols) <= 1:
            cat = get_best_categorical(cat_cols)
            if cat is None:
                return None, None  # Todas categóricas têm cardinalidade 1

            if num_cols:
                values_col = num_cols[0]
                counts = df[[cat, values_col]].dropna()
            else:
                values_col = "count"
                counts = df[cat].value_counts().reset_index()
                counts.columns = [cat, values_col]

            if len(counts) <= 4:
                fig = px.pie(counts, names=cat, values=values_col, hole=0.3)
                chart_type = "pizza"
            else:
                fig = px.bar(
                    counts.sort_values(values_col, ascending=False),
                    x=cat, y=values_col, text=values_col
                )
                chart_type = "barras"

        # 2E. Histograma: 1 numérica, 0 categóricas
        elif len(num_cols) == 1 and not cat_cols:
            fig = px.histogram(df, x=num_cols[0])
            chart_type = "histograma"

        # 2F. Scatter com performance otimizada: ≥2 numéricas
        elif len(num_cols) >= 2:
            WEBGL_THRESHOLD = 1000  # Acima de 1000 pontos usa WebGL
            render_mode = "webgl" if len(df) > WEBGL_THRESHOLD else "auto"
            
            fig = px.scatter(
                df, 
                x=num_cols[0], 
                y=num_cols[1],
                render_mode=render_mode
            )
            chart_type = "dispersao"

        # 2G. Fallback para categóricas restantes
        elif cat_cols:
            cat = get_best_categorical(cat_cols)
            if cat is None:
                return None, None
            
            counts = df[cat].value_counts().reset_index()
            counts.columns = [cat, "count"]
            fig = px.bar(counts, x=cat, y="count")
            chart_type = "barras-contagem"

        # 2H. Fallback para datetime sem numéricas
        elif dt_cols:
            dt = dt_cols[0]
            fig = px.histogram(df, x=dt)
            chart_type = "histograma-data"

        else:
            return None, None

        # 3 ─ Layout padrão e exportação
        fig.update_layout(width=1000, height=400, margin=dict(l=20, r=20, t=40, b=20))

        # Adiciona linha de tendência OLS quando aplicável
        add_trendline_if_applicable(fig, df, chart_type, num_cols, dt_cols)

        html = pio.to_html(
            fig,
            full_html=False,
            include_plotlyjs="cdn",
            div_id=f"plotly-{uuid.uuid4().hex}",
            config={
                "displaylogo": False,
                "modeBarButtonsToRemove": ["pan2d", "select2d", "lasso2d"]
            }
        )

        return html, chart_type

    except Exception as e:
        logger.error(f"Erro em suggest_chart: {e}")
        return None, None


def add_trendline_if_applicable(fig, df: pd.DataFrame, chart_type: str, num_cols: list[str], dt_cols: list[str]) -> None:
    """
    Acrescenta uma linha de tendência OLS quando:
      • chart_type == "dispersao"  -> usa as duas colunas numéricas
      • chart_type == "multilinha" -> usa o 1ª coluna numérica vs datetime
    A linha só é adicionada se R² >= R2_THRESHOLD.
    
    Args:
        fig: Figura do Plotly
        df: DataFrame com os dados
        chart_type: Tipo do gráfico
        num_cols: Colunas numéricas
        dt_cols: Colunas de data/tempo
    """
    R2_THRESHOLD = 0.20               # ajuste de sensibilidade

    try:
        # Caso 1 ─ Scatter: duas colunas numéricas
        if chart_type == "dispersao" and len(num_cols) >= 2:
            x_col, y_col = num_cols[:2]
            data = df[[x_col, y_col]].dropna()
            if len(data) < 2:
                return  # sem dados suficientes

            x = data[x_col].to_numpy()
            y = data[y_col].to_numpy()

        # Caso 2 ─ Multi-line temporal: datetime + numérico
        elif chart_type == "multilinha" and dt_cols and num_cols:
            time_col = dt_cols[0]
            y_col    = num_cols[0]     # tendência da 1ª série
            data = df[[time_col, y_col]].dropna()
            if len(data) < 2:
                return

            # Datetime → int64 (nanos) para regressão
            x = data[time_col].astype("int64") / 1e9     # segundos
            y = data[y_col].to_numpy()
        else:
            return  # não aplicável

        # Regressão OLS simples y = a*x + b
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept
        denom = ((y - y.mean()) ** 2).sum()
        if denom == 0:
            return  # evita divisão por zero
        r2 = 1 - ((y - y_pred) ** 2).sum() / denom
        if np.isnan(r2) or r2 < R2_THRESHOLD:
            return  # tendência fraca

        # Adiciona linha de tendência
        x_min, x_max = x.min(), x.max()
        if chart_type == "dispersao":
            fig.add_scatter(
                x=[x_min, x_max],
                y=[intercept + slope*x_min, intercept + slope*x_max],
                mode="lines",
                line=dict(color="red", dash="dash"),
                name=f"Tendência (R²={r2:.2f})",
                hovertemplate=f"y = {slope:.2f}x + {intercept:.2f}<br>R² = {r2:.2f}<extra></extra>"
            )
        else:
            fig.add_scatter(
                x=pd.to_datetime([x_min*1e9, x_max*1e9]),
                y=[intercept + slope*x_min, intercept + slope*x_max],
                mode="lines",
                line=dict(color="red", dash="dash"),
                name=f"Tendência (R²={r2:.2f})",
                hovertemplate=f"y = {slope:.2f}x + {intercept:.2f}<br>R² = {r2:.2f}<extra></extra>"
            )
    except Exception as e:
        logger.error(f"Erro em add_trendline_if_applicable: {e}")
