"""
Constantes e mapeamentos utilizados no sistema de análise de dados.
"""

from sentence_transformers import CrossEncoder
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from typing import Final, Callable

# Dicionário de tradução para análises estatísticas
TRAD_ESTATISTICAS = {
    "count": "contagem",
    "mean": "média",
    "std": "dv"
}

# Mapeamento de algoritmos de ML essenciais
ALGORITHM_MAPPING: dict[str, Callable] = {
    # Regressão: Previsão de valores contínos. Robusto e versátil.
    "RandomForestRegressor": RandomForestRegressor,
    # Classificação: Previsão de categorias. Ótimo para dados tabulares.
    "RandomForestClassifier": RandomForestClassifier,
    # Clusterização: Agrupamento de dados por similaridade. Padrão da indústria.
    "KMeans": KMeans,
    # Detecção de Anomalias: Identificação de outliers.
    "IsolationForest": IsolationForest,
    # Redução de Dimensionalidade: Projeção de dados para visualização.
    "PCA": lambda: PCA(n_components=2)
}

# Modelo para rankear a melhor query
reranker_model: Final = CrossEncoder("BAAI/bge-reranker-v2-m3", trust_remote_code=True)
