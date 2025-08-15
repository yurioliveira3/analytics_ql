# Engine Dockerfile - Responsável pelo mapeamento de metadados
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia o requirements.txt do projeto
COPY ../requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia os arquivos da Engine
COPY . ./Engine/
COPY ../logs ./logs/

# Cria diretório de logs se não existir
RUN mkdir -p ./logs

# Define variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expõe a porta (caso seja necessário para logs ou monitoramento)
EXPOSE 8080

# Comando para executar a Engine
CMD ["python", "Engine/engine.py"]
