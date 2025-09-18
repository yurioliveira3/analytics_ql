import pandas as pd
import sys
import os

# Adiciona o diretório App ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'App'))

from utils.constants import ALGORITHM_MAPPING

# Criando o DataFrame exatamente como você mencionou
df = pd.DataFrame({
    'nome': ['Isadora Farias', 'Alice Ribeiro', 'Aline Prado'],
    'nota': [9.31, 9.18, 8.97]
})

print("DataFrame original:")
print(df)

# Extraindo apenas as colunas numéricas
numeric_df = df.select_dtypes(include=["number"]).dropna()
print(f"\nDataFrame numérico: {numeric_df.shape}")
print(numeric_df)

# Testando o KMeans inteligente
print("\n🔍 Testando KMeans inteligente...")
try:
    creator = ALGORITHM_MAPPING.get("KMeans")
    alg = creator()
    
    print(f"Aplicando KMeans em {len(numeric_df)} amostras...")
    ml_result = alg.fit_predict(numeric_df)
    
    print(f"✅ Sucesso! Resultado: {ml_result}")
    print(f"Clusters encontrados: {len(set(ml_result))}")
    
    # Adicionando resultado ao DataFrame original
    df_with_ml = df.copy()
    df_with_ml["cluster"] = ml_result
    print(f"\nDataFrame com clusters:")
    print(df_with_ml)
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

# Testando com DataFrame ainda menor (2 amostras)
print("\n" + "="*50)
print("🔍 Testando com apenas 2 amostras...")

df_small = pd.DataFrame({
    'nome': ['João Silva', 'Maria Santos'],
    'nota': [8.5, 9.2]
})

numeric_df_small = df_small.select_dtypes(include=["number"]).dropna()
print(f"DataFrame pequeno: {numeric_df_small.shape}")

try:
    creator = ALGORITHM_MAPPING.get("KMeans")
    alg = creator()
    
    ml_result_small = alg.fit_predict(numeric_df_small)
    print(f"✅ Sucesso com 2 amostras! Resultado: {ml_result_small}")
    print(f"Clusters: {len(set(ml_result_small))}")
    
except Exception as e:
    print(f"❌ Erro com 2 amostras: {e}")
