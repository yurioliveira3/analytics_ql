"""
Teste de integração para verificar se as funcionalidades de regressão foram integradas corretamente.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'App'))

import pandas as pd
import numpy as np
from App.utils.chart_generator import suggest_chart
from App.utils.llm_utils import generate_insights_payload

def test_regression_integration():
    """Testa a integração da análise de regressão com os insights."""
    
    # Criar dados de teste com correlação linear
    np.random.seed(42)
    x = np.linspace(0, 10, 100)
    y = 2 * x + 1 + np.random.normal(0, 1, 100)  # y = 2x + 1 + ruído
    
    df = pd.DataFrame({
        'tempo_estudo': x,
        'nota_final': y
    })
    
    print("=== Teste de Integração - Análise de Regressão ===\n")
    
    # Testar função suggest_chart
    print("1. Testando suggest_chart...")
    chart_html, chart_type, regression_info = suggest_chart(df)
    
    print(f"   Chart Type: {chart_type}")
    print(f"   Regression Info: {regression_info}")
    
    if regression_info:
        print(f"   R²: {regression_info['r_squared']:.4f}")
        print(f"   Slope: {regression_info['slope']:.4f}")
        print(f"   Equação: {regression_info['equation']}")
    
    # Testar função generate_insights_payload
    print("\n2. Testando generate_insights_payload...")
    
    # Mock de last_entry
    last_entry = {
        "nl_query": "Qual é a relação entre tempo de estudo e nota final?",
        "executed_query": "SELECT tempo_estudo, nota_final FROM estudantes",
        "used_tables": ["estudantes"]
    }
    
    # Análise descritiva mock
    dataframe_analysis_df = df.describe()
    
    payload = generate_insights_payload(
        last_entry=last_entry,
        result=df,
        dataframe_analysis_df=dataframe_analysis_df,
        ml_algorithm=None,
        chart_type=chart_type,
        regression_info=regression_info
    )
    
    print(f"   Payload contém regression_analysis: {'regression_analysis' in payload}")
    print(f"   Tipo de regression_analysis: {type(payload.get('regression_analysis'))}")
    
    if isinstance(payload.get('regression_analysis'), dict):
        print(f"   Chaves da regression_analysis: {list(payload['regression_analysis'].keys())}")
    
    print("\n=== Teste Concluído ===")
    
    return payload, regression_info

if __name__ == "__main__":
    test_regression_integration()
