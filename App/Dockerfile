# App Dockerfile - Interface web Flask
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia o requirements.txt do projeto
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia os arquivos da aplicação
COPY App/ ./App/
COPY Database/ ./Database/
COPY logs/ ./logs/

# Cria diretórios necessários
RUN mkdir -p ./logs && \
    mkdir -p ./App/flask_session

# Define variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=App/cli.py
ENV FLASK_ENV=production

# Expõe a porta da aplicação
EXPOSE 5001

# Comando para executar a aplicação Flask
CMD ["python", "App/cli.py"]
