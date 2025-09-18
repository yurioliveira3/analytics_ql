"""
Módulo para criação inteligente de algoritmos de ML com ajustes automáticos.
"""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
from utils.logger import get_logger

logger = get_logger(__name__)


class SmartKMeans:
    """
    Wrapper inteligente para KMeans que ajusta automaticamente o número de clusters
    baseado no tamanho dos dados para evitar o erro "n_samples should be >= n_clusters".
    """
    
    def __init__(self):
        self.kmeans = None
        self.n_clusters_used = None
        
    def _calculate_optimal_clusters(self, n_samples: int) -> int:
        """
        Calcula o número ótimo de clusters baseado no tamanho dos dados.
        
        Args:
            n_samples: Número de amostras nos dados
            
        Returns:
            Número inteligente de clusters a usar
        """
        if n_samples <= 1:
            raise ValueError("Não é possível aplicar clustering com menos de 2 amostras")
        elif n_samples == 2:
            return 2
        elif n_samples <= 4:
            return 2  # Para poucos dados, usar apenas 2 clusters
        elif n_samples <= 10:
            return min(3, n_samples - 1)  # Para dados pequenos, ser conservador
        else:
            # Para dados maiores, usar até 8 clusters, mas nunca mais que n_samples-1
            return min(8, n_samples - 1)
    
    def fit_predict(self, X):
        """
        Treina o modelo e retorna as predições de cluster.
        
        Args:
            X: Dados para clustering (DataFrame ou array)
            
        Returns:
            Array com os labels dos clusters
        """
        n_samples = len(X)
        self.n_clusters_used = self._calculate_optimal_clusters(n_samples)
        
        logger.debug(f"Aplicando KMeans com {self.n_clusters_used} clusters para {n_samples} amostras")
        
        self.kmeans = KMeans(
            n_clusters=self.n_clusters_used, 
            random_state=42,
            n_init=10  # Número de inicializações para estabilidade
        )
        
        return self.kmeans.fit_predict(X)
        
    def fit(self, X):
        """
        Treina o modelo KMeans.
        
        Args:
            X: Dados para treinamento
            
        Returns:
            Self para chaining
        """
        n_samples = len(X)
        self.n_clusters_used = self._calculate_optimal_clusters(n_samples)
        
        logger.debug(f"Treinando KMeans com {self.n_clusters_used} clusters para {n_samples} amostras")
        
        self.kmeans = KMeans(
            n_clusters=self.n_clusters_used, 
            random_state=42,
            n_init=10
        )
        
        return self.kmeans.fit(X)
        
    def predict(self, X):
        """
        Prediz os clusters para novos dados.
        
        Args:
            X: Dados para predição
            
        Returns:
            Array com os labels dos clusters
        """
        if self.kmeans is None:
            self.fit(X)
        return self.kmeans.predict(X)


class SmartPCA:
    """
    Wrapper inteligente para PCA que ajusta automaticamente o número de componentes.
    """
    
    def __init__(self):
        self.pca = None
        self.n_components_used = None
        
    def _calculate_optimal_components(self, n_samples: int, n_features: int) -> int:
        """
        Calcula o número ótimo de componentes PCA.
        
        Args:
            n_samples: Número de amostras
            n_features: Número de features
            
        Returns:
            Número de componentes a usar
        """
        # PCA não pode ter mais componentes que min(n_samples, n_features)
        max_components = min(n_samples, n_features)
        
        if max_components <= 1:
            return 1
        elif max_components == 2:
            return 2
        else:
            # Usar 2 componentes por padrão para visualização, mas respeitar limites
            return min(2, max_components)
    
    def fit_transform(self, X):
        """
        Treina o PCA e transforma os dados.
        
        Args:
            X: Dados para transformação
            
        Returns:
            Dados transformados
        """
        if isinstance(X, pd.DataFrame):
            n_samples, n_features = X.shape
        else:
            n_samples, n_features = X.shape
            
        self.n_components_used = self._calculate_optimal_components(n_samples, n_features)
        
        logger.debug(f"Aplicando PCA com {self.n_components_used} componentes para dados {n_samples}x{n_features}")
        
        self.pca = PCA(n_components=self.n_components_used, random_state=42)
        return self.pca.fit_transform(X)
    
    def fit(self, X):
        """Treina o PCA."""
        if isinstance(X, pd.DataFrame):
            n_samples, n_features = X.shape
        else:
            n_samples, n_features = X.shape
            
        self.n_components_used = self._calculate_optimal_components(n_samples, n_features)
        self.pca = PCA(n_components=self.n_components_used, random_state=42)
        return self.pca.fit(X)
    
    def transform(self, X):
        """Transforma os dados usando PCA treinado."""
        if self.pca is None:
            self.fit(X)
        return self.pca.transform(X)


def create_smart_algorithm(algorithm_name: str):
    """
    Factory function para criar algoritmos de ML inteligentes com ajustes automáticos.
    
    Args:
        algorithm_name: Nome do algoritmo (KMeans, PCA, etc.)
        
    Returns:
        Instância do algoritmo inteligente
    """
    if algorithm_name == "KMeans":
        return SmartKMeans()
    elif algorithm_name == "PCA":
        return SmartPCA()
    elif algorithm_name == "RandomForestRegressor":
        return RandomForestRegressor(random_state=42)
    elif algorithm_name == "RandomForestClassifier":
        return RandomForestClassifier(random_state=42)
    elif algorithm_name == "IsolationForest":
        return IsolationForest(random_state=42)
    else:
        raise ValueError(f"Algoritmo '{algorithm_name}' não suportado")


def apply_ml_algorithm(df: pd.DataFrame, algorithm_name: str) -> list | None:
    """
    Aplica um algoritmo de ML de forma inteligente a um DataFrame.
    
    Args:
        df: DataFrame com dados numéricos
        algorithm_name: Nome do algoritmo a aplicar
        
    Returns:
        Lista com os resultados do algoritmo, ou None se houver erro
    """
    try:
        # Extrair apenas colunas numéricas
        numeric_df = df.select_dtypes(include=["number"]).dropna()
        
        if numeric_df.empty:
            logger.warning("Nenhuma coluna numérica encontrada para aplicar ML")
            return None
            
        if len(numeric_df) < 2:
            logger.warning("Menos de 2 amostras disponíveis para ML")
            return None
        
        # Limpar nome do algoritmo (remover parâmetros se houver)
        clean_algorithm_name = algorithm_name.split("(")[0].strip()
        
        # Criar algoritmo inteligente
        algorithm = create_smart_algorithm(clean_algorithm_name)
        
        # Aplicar algoritmo
        if hasattr(algorithm, "fit_predict"):
            result = algorithm.fit_predict(numeric_df)
        elif hasattr(algorithm, "fit_transform"):
            result = algorithm.fit_transform(numeric_df)
            # Se PCA retornou array 2D, pegar apenas a primeira componente
            if len(result.shape) > 1 and result.shape[1] > 1:
                result = result[:, 0]  # Primeira componente principal
        elif hasattr(algorithm, "predict"):
            algorithm.fit(numeric_df)
            result = algorithm.predict(numeric_df)
        else:
            logger.error(f"Algoritmo {clean_algorithm_name} não tem método de predição conhecido")
            return None
            
        logger.info(f"Algoritmo {clean_algorithm_name} aplicado com sucesso em {len(numeric_df)} amostras")
        return result.tolist() if hasattr(result, 'tolist') else list(result)
        
    except Exception as e:
        logger.error(f"Erro ao aplicar algoritmo {algorithm_name}: {e}")
        return None
