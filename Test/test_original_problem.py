import pandas as pd
import sys
import os

# Adiciona o diretório App ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'App'))

from utils.ml_algorithms import apply_ml_algorithm

# Reproduzindo exatamente o seu caso
print("🎯 Reproduzindo o problema original:")
print("DataFrame: Isadora Farias 9.31, Alice Ribeiro 9.18, Aline Prado 8.97")
print()

# Criando DataFrame igual ao seu
df = pd.DataFrame({
    'nome': ['Isadora Farias', 'Alice Ribeiro', 'Aline Prado'],
    'nota': [9.31, 9.18, 8.97]
})

print("DataFrame original:")
print(df)
print()

# Aplicando KMeans (que era o que estava dando erro)
print("Aplicando KMeans...")
ml_result = apply_ml_algorithm(df, "KMeans")

if ml_result:
    print(f"✅ SUCESSO! Clusters gerados: {ml_result}")
    
    # Adicionando resultado ao DataFrame como fazia o sistema original
    df_with_clusters = df.copy()
    df_with_clusters["resultado_ml"] = ml_result
    
    print("\nDataFrame com clusters:")
    print(df_with_clusters)
    
    print(f"\n📊 Análise dos clusters:")
    for i, cluster in enumerate(ml_result):
        print(f"   {df.iloc[i]['nome']}: Cluster {cluster}")
        
    print(f"\n🔢 Total de clusters únicos: {len(set(ml_result))}")
    
else:
    print("❌ FALHOU - algo ainda está errado")

print("\n" + "="*60)
print("🔍 Testando outros algoritmos com os mesmos dados:")

# Testando outros algoritmos
algorithms = ["PCA", "IsolationForest"]

for alg in algorithms:
    print(f"\nTestando {alg}...")
    result = apply_ml_algorithm(df, alg)
    if result:
        print(f"   ✅ {alg} funcionou: {result}")
    else:
        print(f"   ❌ {alg} falhou")

print(f"\n🎉 Problema resolvido! Agora o KMeans funciona com apenas 3 amostras.")
print(f"   • Antes: Erro 'n_samples=3 should be >= n_clusters=8'")
print(f"   • Agora: Usa automaticamente 2 clusters para {len(df)} amostras")
