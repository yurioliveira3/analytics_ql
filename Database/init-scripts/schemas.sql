-- Schema: alunos
CREATE SCHEMA IF NOT EXISTS alunos;

-- Tabela de Alunos
CREATE TABLE IF NOT EXISTS alunos.alunos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    data_nascimento DATE NOT NULL,
    cpf VARCHAR(11) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE
);

-- Tabela de Cursos
CREATE TABLE IF NOT EXISTS alunos.cursos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT
);

-- Tabela de Professores
CREATE TABLE IF NOT EXISTS alunos.professores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE
);

-- Tabela de Disciplinas
CREATE TABLE IF NOT EXISTS alunos.disciplinas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    id_curso INT NOT NULL,
    id_professor INT,
    FOREIGN KEY (id_curso) REFERENCES alunos.cursos(id),
    FOREIGN KEY (id_professor) REFERENCES alunos.professores(id)
);

-- Tabela de Matrículas
CREATE TABLE IF NOT EXISTS alunos.matriculas (
    id SERIAL PRIMARY KEY,
    id_aluno INT NOT NULL,
    id_curso INT NOT NULL,
    data_matricula DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) NOT NULL,
    FOREIGN KEY (id_aluno) REFERENCES alunos.alunos(id),
    FOREIGN KEY (id_curso) REFERENCES alunos.cursos(id)
);

-- Tabela de Notas
CREATE TABLE IF NOT EXISTS alunos.notas (
    id SERIAL PRIMARY KEY,
    id_matricula INT NOT NULL,
    id_disciplina INT NOT NULL,
    nota DECIMAL(4, 2) NOT NULL,
    CHECK (nota >= 0 AND nota <= 10),
    FOREIGN KEY (id_matricula) REFERENCES alunos.matriculas(id),
    FOREIGN KEY (id_disciplina) REFERENCES alunos.disciplinas(id)
);

-- Tabela de Endereços
CREATE TABLE IF NOT EXISTS alunos.enderecos (
    id SERIAL PRIMARY KEY,
    id_aluno INT NOT NULL,
    logradouro VARCHAR(255) NOT NULL,
    numero VARCHAR(20),
    cidade VARCHAR(100) NOT NULL,
    estado VARCHAR(2) NOT NULL,
    cep VARCHAR(8) NOT NULL,
    FOREIGN KEY (id_aluno) REFERENCES alunos.alunos(id)
);

-- Tabela de Departamentos
CREATE TABLE IF NOT EXISTS alunos.departamentos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL
);

-- Tabela de Turmas
CREATE TABLE IF NOT EXISTS alunos.turmas (
    id SERIAL PRIMARY KEY,
    id_disciplina INT NOT NULL,
    semestre VARCHAR(6) NOT NULL,
    ano INT NOT NULL,
    FOREIGN KEY (id_disciplina) REFERENCES alunos.disciplinas(id)
);

-- Tabela de Presença
CREATE TABLE IF NOT EXISTS alunos.presenca (
    id SERIAL PRIMARY KEY,
    id_matricula INT NOT NULL,
    id_turma INT NOT NULL,
    data_aula DATE NOT NULL,
    presente BOOLEAN NOT NULL,
    FOREIGN KEY (id_matricula) REFERENCES alunos.matriculas(id),
    FOREIGN KEY (id_turma) REFERENCES alunos.turmas(id)
);


-- Schema: produtos
CREATE SCHEMA IF NOT EXISTS produtos;

-- Tabela de Categorias de Produtos
CREATE TABLE IF NOT EXISTS produtos.categorias (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE
);

-- Tabela de Fornecedores
CREATE TABLE IF NOT EXISTS produtos.fornecedores (
    id SERIAL PRIMARY KEY,
    nome_fantasia VARCHAR(100) NOT NULL,
    razao_social VARCHAR(100) UNIQUE NOT NULL,
    cnpj VARCHAR(14) UNIQUE NOT NULL
);

-- Tabela de Produtos
CREATE TABLE IF NOT EXISTS produtos.produtos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    preco_custo DECIMAL(10, 2) NOT NULL,
    preco_venda DECIMAL(10, 2) NOT NULL,
    id_categoria INT NOT NULL,
    id_fornecedor INT NOT NULL,
    FOREIGN KEY (id_categoria) REFERENCES produtos.categorias(id),
    FOREIGN KEY (id_fornecedor) REFERENCES produtos.fornecedores(id)
);

-- Tabela de Estoque
CREATE TABLE IF NOT EXISTS produtos.estoque (
    id SERIAL PRIMARY KEY,
    id_produto INT UNIQUE NOT NULL,
    quantidade INT NOT NULL DEFAULT 0,
    FOREIGN KEY (id_produto) REFERENCES produtos.produtos(id)
);

-- Tabela de Clientes
CREATE TABLE IF NOT EXISTS produtos.clientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE
);

-- Tabela de Pedidos
CREATE TABLE IF NOT EXISTS produtos.pedidos (
    id SERIAL PRIMARY KEY,
    id_cliente INT NOT NULL,
    data_pedido TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    FOREIGN KEY (id_cliente) REFERENCES produtos.clientes(id)
);

-- Tabela de Itens de Pedido
CREATE TABLE IF NOT EXISTS produtos.itens_pedido (
    id_pedido INT NOT NULL,
    id_produto INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (id_pedido, id_produto),
    FOREIGN KEY (id_pedido) REFERENCES produtos.pedidos(id),
    FOREIGN KEY (id_produto) REFERENCES produtos.produtos(id)
);

-- Tabela de Transportadoras
CREATE TABLE IF NOT EXISTS produtos.transportadoras (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL
);

-- Tabela de Envios
CREATE TABLE IF NOT EXISTS produtos.envios (
    id SERIAL PRIMARY KEY,
    id_pedido INT NOT NULL,
    id_transportadora INT NOT NULL,
    codigo_rastreio VARCHAR(50),
    data_envio DATE,
    FOREIGN KEY (id_pedido) REFERENCES produtos.pedidos(id),
    FOREIGN KEY (id_transportadora) REFERENCES produtos.transportadoras(id)
);

-- Tabela de Pagamentos
CREATE TABLE IF NOT EXISTS produtos.pagamentos (
    id SERIAL PRIMARY KEY,
    id_pedido INT NOT NULL,
    metodo_pagamento VARCHAR(50) NOT NULL,
    valor DECIMAL(10, 2) NOT NULL,
    data_pagamento TIMESTAMP,
    FOREIGN KEY (id_pedido) REFERENCES produtos.pedidos(id)
);

-- Tabela de Devoluções
CREATE TABLE IF NOT EXISTS produtos.devolucoes (
    id SERIAL PRIMARY KEY,
    id_item_pedido_pedido INT NOT NULL,
    id_item_pedido_produto INT NOT NULL,
    motivo TEXT,
    data_devolucao DATE NOT NULL,
    FOREIGN KEY (id_item_pedido_pedido, id_item_pedido_produto) REFERENCES produtos.itens_pedido(id_pedido, id_produto)
);

-- Tabela de Avaliações de Produtos
CREATE TABLE IF NOT EXISTS produtos.avaliacoes (
    id SERIAL PRIMARY KEY,
    id_produto INT NOT NULL,
    id_cliente INT NOT NULL,
    nota INT NOT NULL CHECK (nota >= 1 AND nota <= 5),
    comentario TEXT,
    FOREIGN KEY (id_produto) REFERENCES produtos.produtos(id),
    FOREIGN KEY (id_cliente) REFERENCES produtos.clientes(id)
);

-- Tabela de Promoções
CREATE TABLE IF NOT EXISTS produtos.promocoes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    desconto_percentual DECIMAL(5, 2) NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL
);

-- Tabela de Produtos em Promoção
CREATE TABLE IF NOT EXISTS produtos.produtos_promocao (
    id_produto INT NOT NULL,
    id_promocao INT NOT NULL,
    PRIMARY KEY (id_produto, id_promocao),
    FOREIGN KEY (id_produto) REFERENCES produtos.produtos(id),
    FOREIGN KEY (id_promocao) REFERENCES produtos.promocoes(id)
);

-- Tabela de Log de Alterações de Preços
CREATE TABLE IF NOT EXISTS produtos.log_precos (
    id SERIAL PRIMARY KEY,
    id_produto INT NOT NULL,
    preco_antigo DECIMAL(10, 2) NOT NULL,
    preco_novo DECIMAL(10, 2) NOT NULL,
    data_alteracao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_produto) REFERENCES produtos.produtos(id)
);
