import pandas as pd
import sys
import os

# Adiciona o diretório App ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'App'))

from utils.ml_algorithms import apply_ml_algorithm

# Teste 1: DataFrame pequeno que causava o erro original
print("🔍 Teste 1: DataFrame com 3 amostras (problema original)")
df_small = pd.DataFrame({
    'nome': ['Isadora Farias', 'Alice Ribeiro', 'Aline Prado'],
    'nota': [9.31, 9.18, 8.97]
})

print("DataFrame:")
print(df_small)
print()

# Testando KMeans
result = apply_ml_algorithm(df_small, "KMeans")
if result:
    print(f"✅ KMeans funcionou! Clusters: {result}")
    print(f"   Número de clusters únicos: {len(set(result))}")
else:
    print("❌ KMeans falhou")

print("\n" + "="*60)

# Teste 2: DataFrame ainda menor (2 amostras)
print("🔍 Teste 2: DataFrame com 2 amostras (caso extremo)")
df_tiny = pd.DataFrame({
    'nome': ['João Silva', 'Maria Santos'],
    'valor': [100, 200]
})

print("DataFrame:")
print(df_tiny)
print()

result = apply_ml_algorithm(df_tiny, "KMeans")
if result:
    print(f"✅ KMeans funcionou com 2 amostras! Clusters: {result}")
else:
    print("❌ KMeans falhou com 2 amostras")

print("\n" + "="*60)

# Teste 3: DataFrame maior para verificar comportamento normal
print("🔍 Teste 3: DataFrame maior (comportamento normal)")
df_large = pd.DataFrame({
    'nome': [f'Pessoa {i}' for i in range(1, 11)],
    'idade': [20, 25, 30, 35, 40, 45, 50, 55, 60, 65],
    'salario': [3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500]
})

print(f"DataFrame com {len(df_large)} amostras:")
print(df_large.head())
print()

result = apply_ml_algorithm(df_large, "KMeans")
if result:
    print(f"✅ KMeans funcionou com dados maiores! Primeiros clusters: {result[:5]}...")
    print(f"   Número de clusters únicos: {len(set(result))}")
else:
    print("❌ KMeans falhou com dados maiores")

print("\n" + "="*60)

# Teste 4: Testando PCA
print("🔍 Teste 4: Testando PCA com dados pequenos")
result_pca = apply_ml_algorithm(df_small, "PCA")
if result_pca:
    print(f"✅ PCA funcionou! Primeiros componentes: {result_pca}")
else:
    print("❌ PCA falhou")

print("\n" + "="*60)

# Teste 5: DataFrame sem colunas numéricas
print("🔍 Teste 5: DataFrame sem colunas numéricas")
df_no_numeric = pd.DataFrame({
    'nome': ['Ana', 'João', 'Maria'],
    'cidade': ['SP', 'RJ', 'MG']
})

print("DataFrame:")
print(df_no_numeric)
print()

result = apply_ml_algorithm(df_no_numeric, "KMeans")
if result:
    print(f"✅ Resultado inesperado: {result}")
else:
    print("✅ Corretamente retornou None para dados não-numéricos")

print("\n🎯 Testes concluídos!")
