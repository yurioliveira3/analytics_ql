
-- ####################################################################################
-- ################################# DADOS PARA ALUNOS ################################
-- ####################################################################################

-- Inserir Departamentos
INSERT INTO alunos.departamentos (nome) VALUES
('Ciência da Computação'),
('Engenharia de Software'),
('Administração de Empresas');

-- Inserir Professores
INSERT INTO alunos.professores (nome, email) VALUES
('Dr. João Silva', 'joao.silva@universidade.com'),
('Dra. Maria Oliveira', 'maria.oliveira@universidade.com'),
('Dr. Carlos Pereira', 'carlos.pereira@universidade.com');

-- Inserir Cursos
INSERT INTO alunos.cursos (nome, descricao) VALUES
('Sistemas de Informação', 'Curso focado em desenvolvimento e gestão de sistemas.'),
('Engenharia de Dados', 'Curso para formar especialistas em infraestrutura e análise de dados.'),
('Marketing Digital', 'Curso sobre estratégias de marketing no ambiente online.');

-- Inserir Disciplinas
INSERT INTO alunos.disciplinas (nome, id_curso, id_professor) VALUES
('Banco de Dados', 1, 1),
('Programação Orientada a Objetos', 1, 2),
('Big Data', 2, 1),
('Gestão de Mídias Sociais', 3, 3);

-- Inserir Alunos
INSERT INTO alunos.alunos (nome, data_nascimento, cpf, email) VALUES
('Ana Clara', '2002-05-10', '11122233344', 'ana.clara@email.com'),
('Bruno Costa', '2001-08-22', '22233344455', 'bruno.costa@email.com'),
('Carla Dias', '2003-01-15', '33344455566', 'carla.dias@email.com');

-- Inserir Turmas
INSERT INTO alunos.turmas (id_disciplina, semestre, ano) VALUES
(1, '2024.1', 2024),
(2, '2024.1', 2024),
(3, '2024.2', 2024);

-- Inserir Matrículas
INSERT INTO alunos.matriculas (id_aluno, id_curso, data_matricula, status) VALUES
(1, 1, '2024-01-10', 'Ativa'),
(2, 1, '2024-01-11', 'Ativa'),
(3, 2, '2024-07-20', 'Ativa');

-- Inserir Notas
INSERT INTO alunos.notas (id_matricula, id_disciplina, nota) VALUES
(1, 1, 8.5),
(1, 2, 9.0),
(2, 1, 7.0);

-- Inserir Endereços
INSERT INTO alunos.enderecos (id_aluno, logradouro, numero, cidade, estado, cep) VALUES
(1, 'Rua das Flores', '123', 'São Paulo', 'SP', '01001000'),
(2, 'Avenida Principal', '456', 'Rio de Janeiro', 'RJ', '20040030');

-- Inserir Presença
INSERT INTO alunos.presenca (id_matricula, id_turma, data_aula, presente) VALUES
(1, 1, '2024-03-15', true),
(1, 1, '2024-03-22', true),
(2, 1, '2024-03-15', false);


-- ####################################################################################
-- ################################ DADOS PARA PRODUTOS ###############################
-- ####################################################################################

-- Inserir Categorias
INSERT INTO produtos.categorias (nome) VALUES
('Eletrônicos'),
('Livros'),
('Roupas');

-- Inserir Fornecedores
INSERT INTO produtos.fornecedores (nome_fantasia, razao_social, cnpj) VALUES
('Tech Distribuidora', 'Tech Soluções LTDA', '11222333000144'),
('Livraria Saber', 'Saber & Cia LTDA', '44555666000177');

-- Inserir Produtos
INSERT INTO produtos.produtos (nome, descricao, preco_custo, preco_venda, id_categoria, id_fornecedor) VALUES
('Smartphone X', 'Smartphone de última geração', 1500.00, 2500.00, 1, 1),
('A Arte da Guerra', 'Livro clássico sobre estratégia', 20.00, 45.00, 2, 2),
('Camiseta Básica', 'Camiseta de algodão', 15.00, 35.00, 3, 1);

-- Inserir Estoque
INSERT INTO produtos.estoque (id_produto, quantidade) VALUES
(1, 100),
(2, 250),
(3, 500);

-- Inserir Clientes
INSERT INTO produtos.clientes (nome, email) VALUES
('Fernanda Lima', 'fernanda.lima@cliente.com'),
('Ricardo Souza', 'ricardo.souza@cliente.com');

-- Inserir Pedidos
INSERT INTO produtos.pedidos (id_cliente, data_pedido, status) VALUES
(1, '2024-07-10 10:00:00', 'Enviado'),
(2, '2024-07-11 14:30:00', 'Processando');

-- Inserir Itens de Pedido
INSERT INTO produtos.itens_pedido (id_pedido, id_produto, quantidade, preco_unitario) VALUES
(1, 1, 1, 2500.00),
(1, 2, 2, 45.00),
(2, 3, 5, 35.00);

-- Inserir Transportadoras
INSERT INTO produtos.transportadoras (nome) VALUES
('Correios'),
('Transp Rápido');

-- Inserir Envios
INSERT INTO produtos.envios (id_pedido, id_transportadora, codigo_rastreio, data_envio) VALUES
(1, 1, 'BR123456789', '2024-07-11');

-- Inserir Pagamentos
INSERT INTO produtos.pagamentos (id_pedido, metodo_pagamento, valor, data_pagamento) VALUES
(1, 'Cartão de Crédito', 2590.00, '2024-07-10 10:05:00'),
(2, 'Boleto', 175.00, NULL);

-- Inserir Avaliações
INSERT INTO produtos.avaliacoes (id_produto, id_cliente, nota, comentario) VALUES
(1, 1, 5, 'Excelente produto, entrega rápida!');
