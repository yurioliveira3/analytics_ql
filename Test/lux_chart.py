import lux  # habilita recomendações Lux para DataFrame
import altair as alt
import pandas as pd

alt.data_transformers.disable_max_rows() 

def suggest_lux_chart(df: pd.DataFrame) -> tuple[str | None, str | None]:
    """
    Retorna (html_snippet, chart_type) ou (None, None) se não houver sugestão.
    chart_type: 'correlation', 'distribution', …
    """
    try:
        ldf = lux.LuxDataFrame(df.copy())
        _ = ldf.recommendation                # força cálculo dos painéis

        for cat in ["Correlation", "Distribution", "Occurrence",
                    "Temporal", "Geographical"]:
            vis_list = ldf.recommendation.get(cat, [])
            if not vis_list:
                continue

            vis = vis_list[0]

            # 1ª tentativa: Altair pronto
            try:
                chart = vis.to_altair()                   # HEAD do Lux → alt.Chart
            except Exception:
                # fallback raro: gera spec Vega-Lite e recria o Chart
                spec = vis.to_vegalite(prettyOutput=False)
                chart = alt.Chart.from_dict(spec, validate=False)

            html = chart.to_html(full_html=False,
                                  embed_options={"mode": "vega-lite"})
            return html, cat.lower()

        return None, None

    except Exception as e:
        print(f"[Lux] erro geral: {e}")
        return None, None