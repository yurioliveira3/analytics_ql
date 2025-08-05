# Analytics QL

Sistema inteligente de consultas conversacionais para bancos de dados relacionais, utilizando IA generativa para democratizar o acesso aos dados através de linguagem natural.

## 📋 Visão Geral

O Analytics QL é uma solução completa que permite aos usuários realizarem consultas complexas em bancos de dados PostgreSQL usando linguagem natural. O sistema combina técnicas de RAG (Retrieval Augmented Generation), busca semântica e análise automática de dados para gerar insights acionáveis.

### 🎯 Principais Funcionalidades

- **Consultas em Linguagem Natural**: Converta perguntas em português para SQL automaticamente
- **Análise Inteligente de Schemas**: Mapeamento e documentação automática de bancos de dados
- **Visualizações Dinâmicas**: Gráficos interativos gerados automaticamente (Plotly)
- **Machine Learning Integrado**: Algoritmos automáticos aplicados aos resultados
- **Insights com IA**: Análise textual dos dados usando Google Gemini
- **Interface Conversacional**: Chat web intuitivo com histórico persistente
- **Segurança Avançada**: Validação de queries e proteção contra comandos maliciosos

## 🏗️ Arquitetura

O sistema é dividido em dois componentes principais:

### 🔧 Engine (Preparação Offline)
- **Extração**: Conecta ao PostgreSQL e extrai DDLs de todos os objetos
- **Análise**: Usa Gemini para gerar resumos inteligentes dos schemas
- **Indexação**: Converte metadados em embeddings e armazena no PGVector
- **Resultado**: Base de conhecimento semântica pronta para consultas

### 🚀 App (Interface Online)
- **Interface**: Web app Flask com chat conversacional
- **Busca**: Encontra contexto relevante no vector store
- **Geração**: Cria SQL otimizado usando IA
- **Execução**: Valida e executa queries com segurança
- **Análise**: Gera visualizações e insights automáticos

## 🛠️ Tecnologias Utilizadas

### Backend
- **Flask**: Framework web
- **SQLAlchemy**: ORM e gerenciamento de banco
- **Pandas**: Manipulação e análise de dados
- **Scikit-learn**: Algoritmos de machine learning

### IA e ML
- **Google Gemini**: Geração de SQL e insights
- **Sentence Transformers**: Cross-encoder para reranking
- **LangChain**: RAG e integração com vector stores
- **HuggingFace Embeddings**: Modelos de embedding

### Frontend e Visualização
- **Plotly**: Gráficos interativos e dashboards
- **Bootstrap**: Interface responsiva
- **JavaScript**: Interações dinâmicas

### Banco de Dados
- **PostgreSQL**: Banco de dados principal
- **PGVector**: Extensão para busca vetorial e embeddings
- **Psycopg2**: Driver PostgreSQL para Python

## 📦 Instalação

### Pré-requisitos
- Python 3.8+
- PostgreSQL 14+ com extensão PGVector
- Google Gemini API Key
- Dependências Python (ver requirements.txt)

### 1. Clone o repositório
```bash
git clone <repository-url>
cd analytics_ql
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure o banco de dados
```bash
# Execute os scripts de inicialização
cd Database/init-scripts
psql -U postgres -d analytics_db -f metadata.sql
psql -U postgres -d analytics_db -f app_user.sql
psql -U postgres -d analytics_db -f verify_metadata.sql
```

### 4. Configure as variáveis de ambiente

```bash
# Copie o template de configuração
cp .env.example .env

# Edite com suas configurações
nano .env  # ou use seu editor preferido

# Verifique a configuração
python check_env.py
```

**Configuração mínima necessária:**
```env
# Database (obrigatório)
DATABASE_URL=postgresql://seu_usuario:sua_senha@localhost:5482/analytics_db

# Google Gemini (obrigatório)  
GOOGLE_API_KEY=sua_chave_gemini_aqui

# Flask (recomendado para produção)
SECRET_KEY=sua_chave_secreta_256_bits
```

**Para Docker:**
```env
# Configurações do docker-compose
POSTGRES_DB=analytics_db
POSTGRES_USER=postgresql
POSTGRES_PASSWORD=sua_senha_segura
```

## 🚀 Uso

### 1. Execute o Engine (Preparação)
```bash
cd Engine
python engine.py
```

### 2. Execute a App (Interface)
```bash
cd App
python cli.py
```

### 3. Acesse a aplicação
Abra o navegador em `http://localhost:5000`

## 💡 Exemplos de Uso

### Consultas Suportadas
- "Quantos alunos estão matriculados em cada curso?"
- "Mostre a evolução das vendas por mês"
- "Quais produtos têm maior margem de lucro?"
- "Identifique padrões anômalos nos dados de acesso"

### Recursos Avançados
- **Algoritmos ML**: RandomForest, KMeans, PCA, IsolationForest
- **Tipos de Gráfico**: Barras, Linha, Pizza, Dispersão, Histograma, Mapa de Calor
- **Export**: Excel, CSV
- **Sessões**: Histórico persistente e múltiplas conversas

## 🔒 Segurança

- **Validação de SQL**: Bloqueio de comandos DDL/DML perigosos
- **Análise de Performance**: EXPLAIN automático antes da execução
- **Rate Limiting**: Controle de uso da IA
- **Isolamento**: Usuário com permissões limitadas (SELECT only)

## 📊 Monitoramento

O sistema registra métricas importantes:
- Tokens consumidos (Gemini)
- Tempo de resposta
- Queries executadas
- Erros e exceções

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🎓 Uso Acadêmico

Este projeto foi desenvolvido como parte de uma pesquisa acadêmica sobre **Inteligência Artificial Generativa aplicada a consultas conversacionais em bancos de dados relacionais**. 

### Citação
Se utilizar este trabalho em pesquisas acadêmicas, favor citar:
```bibtex
@misc{analytics_ql_2024,
  title={Analytics QL: Sistema de Consultas Conversacionais com IA Generativa},
  author={[Seu Nome]},
  year={2024},
  howpublished={\url{https://github.com/seu-usuario/analytics_ql}}
}
```

## 📞 Suporte

Para dúvidas e suporte:
- Abra uma [issue](../../issues)
- Entre em contato: [yuri.alves@ecomp.ufsm.br]

## 🔮 Roadmap

- [ ] Suporte a múltiplos SGBDs (MySQL, SQL Server)
- [ ] API REST completa
- [ ] Dashboard administrativo
- [ ] Integração com ferramentas de BI
- [ ] Suporte a múltiplos idiomas

---

**Analytics QL** - Democratizando o acesso aos dados através da IA conversacional 🤖📊