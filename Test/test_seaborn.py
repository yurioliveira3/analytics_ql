import seaborn as sns
import matplotlib.pyplot as plt

# Carrega um dataset de exemplo do seaborn
df = sns.load_dataset("iris")

# Gráfico 1: Scatterplot
sns.scatterplot(data=df, x="sepal_length", y="sepal_width", hue="species")
plt.title("Scatterplot - Iris")
plt.show()

# Gráfico 2: Histograma
sns.histplot(data=df, x="petal_length", bins=20, kde=True)
plt.title("Histograma - Petal Length")
plt.show()

# Gráfico 3: Boxplot
sns.boxplot(data=df, x="species", y="sepal_length")
plt.title("Boxplot - Sepal Length por Espécie")
plt.show()

# Gráfico 4: Heatmap de correlação
corr = df.corr(numeric_only=True)
sns.heatmap(corr, annot=True, cmap="coolwarm")
plt.title("Heatmap - Correlação")
plt.show()

print("Pronto! Você viu 4 gráficos básicos com Seaborn")
