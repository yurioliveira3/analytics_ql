/* 
  Regras considerads para classificar a dificuldade das queries:
  Alta: usa CTE múltiplas, WINDOW/ROW_NUMBER(), LATERAL ou sub-CTEs em cascata
  Média: até 3 joins, subqueries simples (HAVING, filtros), agregações básicas com GROUP BY
  Baixa: SELECT simples, 0–2 joins, poucas agregações, sem subqueries

  Totais finais
    - Baixa: 36/65 (55%)
    - Média: 20/65 (31%)
    - Alta : 9/65 (14%)
*/ 
-- ####################################################################################
-- ############################### QUERIES PARA ALUNOS ################################
-- ####################################################################################

-- Query 1: Selecionar todos os alunos cadastrados.
-- Nível de dificuldade: Baixa
SELECT * FROM alunos.alunos;

-- Query 2: Listar todos os cursos e suas descrições.
-- Nível de dificuldade: Baixa
SELECT nome, descricao FROM alunos.cursos;

-- Query 3: Listar alunos e os cursos em que estão matriculados (JOIN simples).
-- Nível de dificuldade: Média
SELECT
    a.nome AS nome_aluno,
    c.nome AS nome_curso,
    m.status
FROM
    alunos.matriculas m
JOIN
    alunos.alunos a ON m.id_aluno = a.id
JOIN
    alunos.cursos c ON m.id_curso = c.id;

-- Query 4: Exibir as disciplinas e os professores que as lecionam (JOIN simples).
-- Nível de dificuldade: Média
SELECT
    d.nome AS disciplina,
    p.nome AS professor
FROM
    alunos.disciplinas d
LEFT JOIN
    alunos.professores p ON d.id_professor = p.id;

-- Query 5: Consultar as notas de um aluno específico em suas disciplinas (JOIN duplo).
-- Nível de dificuldade: Média
SELECT
    a.nome AS aluno,
    d.nome AS disciplina,
    n.nota
FROM
    alunos.notas n
JOIN
    alunos.matriculas m ON n.id_matricula = m.id
JOIN
    alunos.alunos a ON m.id_aluno = a.id
JOIN
    alunos.disciplinas d ON n.id_disciplina = d.id
WHERE
    a.email = 'ana.clara@email.com';

-- Query 6: Listar todos os professores e os departamentos existentes.
-- Nível de dificuldade: Média
SELECT
    p.nome AS professor,
    d.nome AS departamento
FROM
    alunos.professores p
CROSS JOIN
    alunos.departamentos d;

-- Query 7: Exibir alunos que não possuem endereço cadastrado.
-- Nível de dificuldade: Média
SELECT
    a.nome AS aluno_sem_endereco
FROM
    alunos.alunos a
LEFT JOIN
    alunos.enderecos e ON a.id = e.id_aluno
WHERE
    e.id IS NULL;

-- Query 8: Contar o número de disciplinas por curso.
-- Nível de dificuldade: Média
SELECT
    c.nome AS curso,
    COUNT(d.id) AS total_disciplinas
FROM
    alunos.cursos c
LEFT JOIN
    alunos.disciplinas d ON c.id = d.id_curso
GROUP BY
    c.nome;

-- Query 9: Listar turmas e o nome da disciplina associada.
-- Nível de dificuldade: Média
SELECT
    t.id AS id_turma,
    t.semestre,
    t.ano,
    d.nome AS disciplina
FROM
    alunos.turmas t
JOIN
    alunos.disciplinas d ON t.id_disciplina = d.id;

-- Query 10: Exibir alunos com presença registrada em uma data específica.
-- Nível de dificuldade: Média
SELECT
    a.nome AS aluno,
    pr.data_aula,
    pr.presente
FROM
    alunos.presenca pr
JOIN
    alunos.matriculas m ON pr.id_matricula = m.id
JOIN
    alunos.alunos a ON m.id_aluno = a.id
WHERE
    pr.data_aula = '2024-03-15';

-- Query 11: Média, mediana e desvio padrão das notas por disciplina (somente com >= 10 notas).
-- Nível de dificuldade: Alta
WITH stats AS (
  SELECT
    d.id                AS id_disciplina,
    d.nome              AS disciplina,
    AVG(n.nota)         AS media,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY n.nota) AS mediana,
    STDDEV_POP(n.nota)  AS desvio_padrao,
    COUNT(*)            AS qtd_notas
  FROM alunos.notas n
  JOIN alunos.disciplinas d ON d.id = n.id_disciplina
  GROUP BY d.id, d.nome
)
SELECT * FROM stats
WHERE qtd_notas >= 10;

-- Query 12: Ranking dos alunos por média geral (DENSE_RANK por curso).
-- Nível de dificuldade: Alta
WITH medias AS (
  SELECT
    m.id_curso,
    m.id_aluno,
    AVG(n.nota) AS media_aluno
  FROM alunos.matriculas m
  JOIN alunos.notas n ON n.id_matricula = m.id
  GROUP BY m.id_curso, m.id_aluno
)
SELECT
  a.nome,
  c.nome AS curso,
  media_aluno,
  DENSE_RANK() OVER (PARTITION BY c.id ORDER BY media_aluno DESC) AS posicao_no_curso
FROM medias me
JOIN alunos.alunos a ON a.id = me.id_aluno
JOIN alunos.cursos c ON c.id = me.id_curso
ORDER BY c.nome, posicao_no_curso;

-- Query 13: Top 5 alunos por curso (mesma lógica da 12, limitado).
-- Nível de dificuldade: Alta
WITH medias AS (
  SELECT
    m.id_curso,
    m.id_aluno,
    AVG(n.nota) AS media_aluno
  FROM alunos.matriculas m
  JOIN alunos.notas n ON n.id_matricula = m.id
  GROUP BY m.id_curso, m.id_aluno
), ranked AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY id_curso ORDER BY media_aluno DESC) AS rn
  FROM medias
)
SELECT
  a.nome,
  c.nome AS curso,
  media_aluno
FROM ranked r
JOIN alunos.alunos a ON a.id = r.id_aluno
JOIN alunos.cursos c ON c.id = r.id_curso
WHERE rn <= 5
ORDER BY c.nome, media_aluno DESC;

-- Query 14: Taxa de presença por aluno em cada turma (>= 75%).
-- Nível de dificuldade: Alta
SELECT
  a.nome AS aluno,
  t.id   AS id_turma,
  d.nome AS disciplina,
  ROUND(100.0 * AVG(CASE WHEN pr.presente THEN 1 ELSE 0 END), 2) AS taxa_presenca_pct
FROM alunos.presenca pr
JOIN alunos.matriculas m   ON m.id = pr.id_matricula
JOIN alunos.alunos a       ON a.id = m.id_aluno
JOIN alunos.turmas t       ON t.id = pr.id_turma
JOIN alunos.disciplinas d  ON d.id = t.id_disciplina
GROUP BY a.nome, t.id, d.nome
HAVING AVG(CASE WHEN pr.presente THEN 1 ELSE 0 END) >= 0.75
ORDER BY taxa_presenca_pct DESC;

-- Query 15: Alunos reprovados (nota < 6) em 2 ou mais disciplinas.
-- Nível de dificuldade: Alta
WITH reprov AS (
  SELECT
    m.id_aluno,
    COUNT(*) AS qtd_reprovacoes
  FROM alunos.notas n
  JOIN alunos.matriculas m ON m.id = n.id_matricula
  WHERE n.nota < 6
  GROUP BY m.id_aluno
)
SELECT a.nome, qtd_reprovacoes
FROM reprov r
JOIN alunos.alunos a ON a.id = r.id_aluno
WHERE qtd_reprovacoes >= 2
ORDER BY qtd_reprovacoes DESC;

-- Query 16: Distribuição de notas por faixas (0-5, 5-7, 7-9, 9-10) por disciplina.
-- Nível de dificuldade: Média
SELECT
  d.nome AS disciplina,
  SUM(CASE WHEN n.nota < 5   THEN 1 ELSE 0 END) AS faixa_0_5,
  SUM(CASE WHEN n.nota >=5 AND n.nota <7 THEN 1 ELSE 0 END) AS faixa_5_7,
  SUM(CASE WHEN n.nota >=7 AND n.nota <9 THEN 1 ELSE 0 END) AS faixa_7_9,
  SUM(CASE WHEN n.nota >=9 THEN 1 ELSE 0 END) AS faixa_9_10
FROM alunos.notas n
JOIN alunos.disciplinas d ON d.id = n.id_disciplina
GROUP BY d.nome
ORDER BY d.nome;

-- Query 17: Evolução do número de matrículas por semestre (gera série de semestres dinamicamente).
-- Nível de dificuldade: Baixa
WITH semestres AS (
  SELECT DISTINCT semestre, ano
  FROM alunos.turmas
),
mat_por_sem AS (
  SELECT
    t.semestre,
    t.ano,
    COUNT(DISTINCT m.id_aluno) AS alunos_no_semestre
  FROM alunos.turmas t
  JOIN alunos.presenca pr ON pr.id_turma = t.id
  JOIN alunos.matriculas m ON m.id = pr.id_matricula
  GROUP BY t.semestre, t.ano
)
SELECT s.semestre, s.ano, COALESCE(mps.alunos_no_semestre,0) AS alunos_no_semestre
FROM semestres s
LEFT JOIN mat_por_sem mps
  ON mps.semestre = s.semestre AND mps.ano = s.ano
ORDER BY s.ano, s.semestre;

-- Query 18: Lista de alunos sem matrícula ativa.
-- Nível de dificuldade: Baixa
SELECT
  a.id,
  a.nome
FROM alunos.alunos a
LEFT JOIN alunos.matriculas m ON m.id_aluno = a.id AND m.status = 'Ativa'
WHERE m.id IS NULL;

-- Query 19: Disciplinas com mais de X turmas (exemplo: > 2).
-- Nível de dificuldade: Baixa
SELECT
  d.nome AS disciplina,
  COUNT(t.id) AS qtd_turmas
FROM alunos.disciplinas d
JOIN alunos.turmas t ON t.id_disciplina = d.id
GROUP BY d.nome
HAVING COUNT(t.id) > 2
ORDER BY qtd_turmas DESC;

-- Query 20: Nota média de cada aluno por disciplina (pivot simples com FILTER).
-- Nível de dificuldade: Baixa
SELECT
  a.nome AS aluno,
  AVG(n.nota) FILTER (WHERE d.nome = 'Banco de Dados') AS media_bd,
  AVG(n.nota) FILTER (WHERE d.nome = 'Programação Orientada a Objetos') AS media_poo,
  AVG(n.nota) FILTER (WHERE d.nome = 'Big Data') AS media_bigdata
FROM alunos.notas n
JOIN alunos.matriculas m ON m.id = n.id_matricula
JOIN alunos.alunos a     ON a.id = m.id_aluno
JOIN alunos.disciplinas d ON d.id = n.id_disciplina
GROUP BY a.nome;

-- Query 21: Dias letivos (aulas) por disciplina e percentual de presença (usando WINDOW).
-- Nível de dificuldade: Alta
WITH base AS (
  SELECT
    d.id AS id_disciplina,
    d.nome AS disciplina,
    pr.id_matricula,
    pr.data_aula,
    pr.presente::int AS pres,
    COUNT(*) OVER (PARTITION BY d.id, pr.data_aula) AS qtaulas_no_dia
  FROM alunos.presenca pr
  JOIN alunos.turmas t ON t.id = pr.id_turma
  JOIN alunos.disciplinas d ON d.id = t.id_disciplina
)
SELECT
  disciplina,
  ROUND(100.0 * SUM(pres)::numeric / COUNT(*), 2) AS presenca_geral_pct,
  COUNT(DISTINCT data_aula)                          AS dias_letivos
FROM base
GROUP BY disciplina
ORDER BY presenca_geral_pct DESC;

-- Query 22: Alunos com média acima da média do curso (subquery correlacionada).
-- Nível de dificuldade: Média
SELECT
  a.nome,
  c.nome AS curso,
  AVG(n.nota) AS media_aluno
FROM alunos.matriculas m
JOIN alunos.alunos a ON a.id = m.id_aluno
JOIN alunos.cursos c ON c.id = m.id_curso
JOIN alunos.notas n  ON n.id_matricula = m.id
GROUP BY a.nome, c.id, c.nome
HAVING AVG(n.nota) >
       (SELECT AVG(n2.nota)
        FROM alunos.matriculas m2
        JOIN alunos.notas n2 ON n2.id_matricula = m2.id
        WHERE m2.id_curso = c.id);

-- Query 23: Quantidade de alunos por estado (endereços).
-- Nível de dificuldade: Média
SELECT
  e.estado,
  COUNT(DISTINCT a.id) AS total_alunos
FROM alunos.alunos a
JOIN alunos.enderecos e ON e.id_aluno = a.id
GROUP BY e.estado
ORDER BY total_alunos DESC;

-- Query 24: Quantidade de disciplinas por professor (inclui 0).
-- Nível de dificuldade: Média
SELECT
  p.nome AS professor,
  COUNT(d.id) AS total_disciplinas
FROM alunos.professores p
LEFT JOIN alunos.disciplinas d ON d.id_professor = p.id
GROUP BY p.nome
ORDER BY total_disciplinas DESC;

-- Query 25: Última aula frequentada por cada aluno (MAX por data_aula).
-- Nível de dificuldade: Baixa
SELECT
  a.nome,
  MAX(pr.data_aula) AS ultima_presenca
FROM alunos.presenca pr
JOIN alunos.matriculas m ON m.id = pr.id_matricula
JOIN alunos.alunos a ON a.id = m.id_aluno
GROUP BY a.nome
ORDER BY ultima_presenca DESC;

-- Query 26: % de alunos com endereço por cidade (GROUPING SETS exemplo simples).
-- Nível de dificuldade: Baixa
SELECT
  cidade,
  ROUND(100.0 * COUNT(DISTINCT id_aluno)::numeric /
        NULLIF((SELECT COUNT(*) FROM alunos.alunos),0), 2) AS pct_alunos_com_endereco
FROM alunos.enderecos
GROUP BY cidade
ORDER BY pct_alunos_com_endereco DESC;

-- Query 27: Turmas superlotadas (mais de 40 matrículas/ presença).
-- Nível de dificuldade: Baixa
SELECT
  t.id AS turma,
  d.nome AS disciplina,
  COUNT(DISTINCT m.id_aluno) AS alunos_presentes
FROM alunos.presenca pr
JOIN alunos.matriculas m ON m.id = pr.id_matricula
JOIN alunos.turmas t ON t.id = pr.id_turma
JOIN alunos.disciplinas d ON d.id = t.id_disciplina
GROUP BY t.id, d.nome
HAVING COUNT(DISTINCT m.id_aluno) > 40;

-- Query 28: Média de notas por curso e semestre (JOIN turmas/disciplinas).
-- Nível de dificuldade: Baixa
SELECT
  c.nome  AS curso,
  t.semestre,
  ROUND(AVG(n.nota),2) AS media
FROM alunos.notas n
JOIN alunos.matriculas m ON m.id = n.id_matricula
JOIN alunos.cursos c ON c.id = m.id_curso
JOIN alunos.turmas t ON t.id = (SELECT pr.id_turma FROM alunos.presenca pr WHERE pr.id_matricula = m.id LIMIT 1)
GROUP BY c.nome, t.semestre
ORDER BY c.nome, t.semestre;

-- Query 29: Alunos com mais de uma matrícula em cursos diferentes.
-- Nível de dificuldade: Baixa
SELECT
  a.nome,
  COUNT(DISTINCT m.id_curso) AS qtd_cursos
FROM alunos.matriculas m
JOIN alunos.alunos a ON a.id = m.id_aluno
GROUP BY a.nome
HAVING COUNT(DISTINCT m.id_curso) > 1;

-- Query 30: Percentual de disciplinas com professor definido vs. sem professor.
-- Nível de dificuldade: Baixa
SELECT
  ROUND(100.0 * SUM(CASE WHEN id_professor IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_com_professor,
  ROUND(100.0 * SUM(CASE WHEN id_professor IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)     AS pct_sem_professor
FROM alunos.disciplinas;

-- ####################################################################################
-- ############################## QUERIES PARA PRODUTOS ###############################
-- ####################################################################################

-- Query 1: Selecionar todos os produtos disponíveis.
-- Nível de dificuldade: Baixa
SELECT * FROM produtos.produtos;

-- Query 2: Listar todos os clientes.
-- Nível de dificuldade: Baixa
SELECT nome, email FROM produtos.clientes;

-- Query 3: Visualizar todos os pedidos realizados.
-- Nível de dificuldade: Baixa
SELECT id, id_cliente, status, data_pedido FROM produtos.pedidos;

-- Query 4: Listar produtos e suas respectivas categorias (JOIN simples).
-- Nível de dificuldade: Média
SELECT
    p.nome AS produto,
    c.nome AS categoria
FROM
    produtos.produtos p
JOIN
    produtos.categorias c ON p.id_categoria = c.id;

-- Query 5: Verificar a quantidade de cada produto em estoque (JOIN simples).
-- Nível de dificuldade: Baixa
SELECT
    p.nome AS produto,
    e.quantidade
FROM
    produtos.estoque e
JOIN
    produtos.produtos p ON e.id_produto = p.id;

-- Query 6: Exibir os pedidos junto com o nome do cliente que os realizou (JOIN simples).
-- Nível de dificuldade: Média
SELECT
    p.id AS id_pedido,
    c.nome AS cliente,
    p.status,
    p.data_pedido
FROM
    produtos.pedidos p
JOIN
    produtos.clientes c ON p.id_cliente = c.id;

-- Query 7: Detalhar os itens de um pedido específico (JOIN duplo).
-- Nível de dificuldade: Média
SELECT
    ped.id AS id_pedido,
    prod.nome AS produto,
    ip.quantidade,
    ip.preco_unitario
FROM
    produtos.itens_pedido ip
JOIN
    produtos.pedidos ped ON ip.id_pedido = ped.id
JOIN
    produtos.produtos prod ON ip.id_produto = prod.id
WHERE
    ped.id = 1;

-- Query 8: Listar produtos e seus fornecedores (JOIN simples).
-- Nível de dificuldade: Média
SELECT
    p.nome AS produto,
    f.nome_fantasia AS fornecedor
FROM
    produtos.produtos p
JOIN
    produtos.fornecedores f ON p.id_fornecedor = f.id;

-- Query 9: Mostrar as avaliações dos produtos, incluindo nome do cliente e do produto (JOIN duplo).
-- Nível de dificuldade: Média
SELECT
    p.nome AS produto,
    c.nome AS cliente,
    a.nota,
    a.comentario
FROM
    produtos.avaliacoes a
JOIN
    produtos.produtos p ON a.id_produto = p.id
JOIN
    produtos.clientes c ON a.id_cliente = c.id;

-- Query 10: Consultar informações de envio de um pedido (JOIN duplo).
-- Nível de dificuldade: Média
SELECT
    p.id AS id_pedido,
    t.nome AS transportadora,
    e.codigo_rastreio,
    e.data_envio
FROM
    produtos.envios e
JOIN
    produtos.pedidos p ON e.id_pedido = p.id
JOIN
    produtos.transportadoras t ON e.id_transportadora = t.id;

-- Query 11: Listar produtos que nunca receberam avaliação.
-- Nível de dificuldade: Baixa
SELECT
    p.nome AS produto_sem_avaliacao
FROM
    produtos.produtos p
LEFT JOIN
    produtos.avaliacoes a ON p.id = a.id_produto
WHERE
    a.id IS NULL;

-- Query 12: Exibir clientes que nunca realizaram pedidos.
-- Nível de dificuldade: Baixa
SELECT
    c.nome AS cliente_sem_pedido
FROM
    produtos.clientes c
LEFT JOIN
    produtos.pedidos p ON c.id = p.id_cliente
WHERE
    p.id IS NULL;

-- Query 13: Listar pedidos que ainda não possuem pagamento registrado.
-- Nível de dificuldade: Baixa
SELECT
    p.id AS pedido_sem_pagamento,
    p.status
FROM
    produtos.pedidos p
LEFT JOIN
    produtos.pagamentos pg ON p.id = pg.id_pedido
WHERE
    pg.id IS NULL;

-- Query 14: Exibir produtos que estão em promoção atualmente.
-- Nível de dificuldade: Média
SELECT
    pr.nome AS produto,
    pm.nome AS promocao,
    pm.desconto_percentual
FROM
    produtos.produtos_promocao pp
JOIN
    produtos.produtos pr ON pp.id_produto = pr.id
JOIN
    produtos.promocoes pm ON pp.id_promocao = pm.id
WHERE
    CURRENT_DATE BETWEEN pm.data_inicio AND pm.data_fim;

-- Query 15: Consultar o histórico de alteração de preços de um produto específico.
-- Nível de dificuldade: Baixa
SELECT
    lp.preco_antigo,
    lp.preco_novo,
    lp.data_alteracao
FROM
    produtos.log_precos lp
JOIN
    produtos.produtos p ON lp.id_produto = p.id;

-- Query 16: Receita total por mês (somando itens de pedido).
-- Nível de dificuldade: Média
SELECT
  DATE_TRUNC('month', p.data_pedido) AS mes,
  SUM(ip.quantidade * ip.preco_unitario) AS receita
FROM produtos.pedidos p
JOIN produtos.itens_pedido ip ON ip.id_pedido = p.id
GROUP BY 1
ORDER BY 1;

-- Query 17: Ticket médio por cliente.
-- Nível de dificuldade: Alta
WITH total_cliente AS (
  SELECT
    p.id_cliente,
    SUM(ip.quantidade * ip.preco_unitario) AS total_gasto,
    COUNT(DISTINCT p.id) AS pedidos
  FROM produtos.pedidos p
  JOIN produtos.itens_pedido ip ON ip.id_pedido = p.id
  GROUP BY p.id_cliente
)
SELECT
  c.nome,
  total_gasto,
  pedidos,
  ROUND(total_gasto / NULLIF(pedidos,0), 2) AS ticket_medio
FROM total_cliente tc
JOIN produtos.clientes c ON c.id = tc.id_cliente
ORDER BY total_gasto DESC;

-- Query 18: Top 10 produtos mais vendidos (por valor).
-- Nível de dificuldade: Baixa
SELECT
  pr.nome,
  SUM(ip.quantidade * ip.preco_unitario) AS valor_total
FROM produtos.itens_pedido ip
JOIN produtos.produtos pr ON pr.id = ip.id_produto
GROUP BY pr.nome
ORDER BY valor_total DESC
LIMIT 10;

-- Query 19: Margem (%) por produto.
-- Nível de dificuldade: Baixa
SELECT
  p.nome,
  ROUND(100.0 * (p.preco_venda - p.preco_custo) / p.preco_venda, 2) AS margem_pct
FROM produtos.produtos p
ORDER BY margem_pct DESC;

-- Query 20: Produtos sem estoque ou com estoque abaixo de X (ex.: < 20).
-- Nível de dificuldade: Baixa
SELECT
  p.nome,
  e.quantidade
FROM produtos.produtos p
LEFT JOIN produtos.estoque e ON e.id_produto = p.id
WHERE COALESCE(e.quantidade,0) < 20
ORDER BY e.quantidade NULLS FIRST;

-- Query 21: Pedidos sem envio após 3 dias da data_pedido.
-- Nível de dificuldade: Baixa
SELECT
  p.id,
  p.data_pedido,
  CURRENT_DATE - p.data_pedido::date AS dias_sem_envio
FROM produtos.pedidos p
LEFT JOIN produtos.envios e ON e.id_pedido = p.id
WHERE e.id IS NULL
  AND CURRENT_DATE - p.data_pedido::date > 3;

-- Query 22: Clientes com mais de N pedidos (ex.: > 5).
-- Nível de dificuldade: Baixa
SELECT
  c.nome,
  COUNT(p.id) AS total_pedidos
FROM produtos.clientes c
JOIN produtos.pedidos p ON p.id_cliente = c.id
GROUP BY c.nome
HAVING COUNT(p.id) > 5
ORDER BY total_pedidos DESC;

-- Query 23: Faturamento por categoria (agrupado).
-- Nível de dificuldade: Baixa
SELECT
  cat.nome AS categoria,
  SUM(ip.quantidade * ip.preco_unitario) AS faturamento
FROM produtos.itens_pedido ip
JOIN produtos.produtos pr ON pr.id = ip.id_produto
JOIN produtos.categorias cat ON cat.id = pr.id_categoria
GROUP BY cat.nome
ORDER BY faturamento DESC;

-- Query 24: LTV (lifetime value) por cliente (soma de todos pedidos).
-- Nível de dificuldade: Baixa
SELECT
  c.nome,
  SUM(ip.quantidade * ip.preco_unitario) AS ltv
FROM produtos.clientes c
LEFT JOIN produtos.pedidos p ON p.id_cliente = c.id
LEFT JOIN produtos.itens_pedido ip ON ip.id_pedido = p.id
GROUP BY c.nome
ORDER BY ltv DESC NULLS LAST;

-- Query 25: Primeira compra de cada cliente.
-- Nível de dificuldade: Baixa
SELECT
  c.nome,
  MIN(p.data_pedido) AS primeira_compra
FROM produtos.clientes c
JOIN produtos.pedidos p ON p.id_cliente = c.id
GROUP BY c.nome
ORDER BY primeira_compra;

-- Query 26: Variação percentual de preço por produto (log_precos).
-- Nível de dificuldade: Baixa
SELECT
  pr.nome,
  lp.preco_antigo,
  lp.preco_novo,
  ROUND(100.0 * (lp.preco_novo - lp.preco_antigo) / lp.preco_antigo, 2) AS variacao_pct,
  lp.data_alteracao
FROM produtos.log_precos lp
JOIN produtos.produtos pr ON pr.id = lp.id_produto
ORDER BY lp.data_alteracao DESC;

-- Query 27: Preço final de produtos em promoção (preco_venda - desconto%).
-- Nível de dificuldade: Baixa
SELECT
  pr.nome,
  pr.preco_venda,
  pm.desconto_percentual,
  ROUND(pr.preco_venda * (1 - pm.desconto_percentual/100), 2) AS preco_final
FROM produtos.produtos_promocao pp
JOIN produtos.produtos pr ON pr.id = pp.id_produto
JOIN produtos.promocoes pm ON pm.id = pp.id_promocao
WHERE CURRENT_DATE BETWEEN pm.data_inicio AND pm.data_fim;

-- Query 28: Taxa de devolução por produto (% itens devolvidos / vendidos).
-- Nível de dificuldade: Alta
WITH vendidos AS (
  SELECT id_produto, SUM(quantidade) AS qtd_vendida
  FROM produtos.itens_pedido
  GROUP BY id_produto
),
devolvidos AS (
  SELECT id_item_pedido_produto AS id_produto, COUNT(*) AS qtd_devolvida
  FROM produtos.devolucoes
  GROUP BY id_item_pedido_produto
)
SELECT
  pr.nome,
  COALESCE(d.qtd_devolvida,0) AS qtd_devolvida,
  v.qtd_vendida,
  ROUND(100.0 * COALESCE(d.qtd_devolvida,0) / NULLIF(v.qtd_vendida,0), 2) AS taxa_devolucao_pct
FROM vendidos v
JOIN produtos.produtos pr ON pr.id = v.id_produto
LEFT JOIN devolvidos d ON d.id_produto = v.id_produto
ORDER BY taxa_devolucao_pct DESC NULLS LAST;

-- Query 29: Pedidos com atraso de pagamento (data_pagamento NULL ou > 2 dias após pedido).
-- Nível de dificuldade: Média
SELECT
  p.id AS pedido,
  p.data_pedido,
  pg.data_pagamento,
  COALESCE(pg.data_pagamento::date - p.data_pedido::date, CURRENT_DATE - p.data_pedido::date) AS dias_ate_pagamento
FROM produtos.pedidos p
LEFT JOIN produtos.pagamentos pg ON pg.id_pedido = p.id
WHERE pg.data_pagamento IS NULL
   OR pg.data_pagamento::date - p.data_pedido::date > 2
ORDER BY dias_ate_pagamento DESC;

-- Query 30: Produtos com mais alterações de preço (log_precos count).
-- Nível de dificuldade: Baixa
SELECT
  pr.nome,
  COUNT(lp.id) AS alteracoes
FROM produtos.log_precos lp
JOIN produtos.produtos pr ON pr.id = lp.id_produto
GROUP BY pr.nome
ORDER BY alteracoes DESC;

-- Query 31: Clientes que avaliaram e compraram o mesmo produto (join tri-relacional).
-- Nível de dificuldade: Média
SELECT DISTINCT
  c.nome AS cliente,
  p.nome AS produto
FROM produtos.avaliacoes a
JOIN produtos.clientes c ON c.id = a.id_cliente
JOIN produtos.produtos p ON p.id = a.id_produto
JOIN produtos.itens_pedido ip ON ip.id_produto = p.id
JOIN produtos.pedidos pd ON pd.id = ip.id_pedido AND pd.id_cliente = c.id;

-- Query 32: Receita acumulada (running total) por dia.
-- Nível de dificuldade: Alta
WITH diario AS (
  SELECT
    p.data_pedido::date AS dia,
    SUM(ip.quantidade * ip.preco_unitario) AS receita_dia
  FROM produtos.pedidos p
  JOIN produtos.itens_pedido ip ON ip.id_pedido = p.id
  GROUP BY p.data_pedido::date
)
SELECT
  dia,
  receita_dia,
  SUM(receita_dia) OVER (ORDER BY dia) AS receita_acumulada
FROM diario
ORDER BY dia;

-- Query 33: Número de produtos por fornecedor e categoria (GROUPING SETS).
-- Nível de dificuldade: Baixa
SELECT
  f.nome_fantasia   AS fornecedor,
  c.nome            AS categoria,
  COUNT(p.id)       AS qtd_produtos
FROM produtos.produtos p
JOIN produtos.fornecedores f ON f.id = p.id_fornecedor
JOIN produtos.categorias    c ON c.id = p.id_categoria
GROUP BY GROUPING SETS ((f.nome_fantasia, c.nome), (f.nome_fantasia), (c.nome));

-- Query 34: Pedidos com valor total calculado via LATERAL.
-- Nível de dificuldade: Alta
SELECT
  p.id,
  c.nome AS cliente,
  tot.valor_total
FROM produtos.pedidos p
JOIN produtos.clientes c ON c.id = p.id_cliente
JOIN LATERAL (
  SELECT SUM(ip.quantidade * ip.preco_unitario) AS valor_total
  FROM produtos.itens_pedido ip
  WHERE ip.id_pedido = p.id
) tot ON TRUE
ORDER BY tot.valor_total DESC NULLS LAST;

-- Query 35: Produtos com estoque zerado que ainda estão em promoção (consistência/erro de negócio).
-- Nível de dificuldade: Baixa
SELECT
  pr.nome,
  e.quantidade,
  pm.nome AS promocao
FROM produtos.produtos_promocao pp
JOIN produtos.produtos pr ON pr.id = pp.id_produto
JOIN produtos.promocoes pm ON pm.id = pp.id_promocao
LEFT JOIN produtos.estoque e ON e.id_produto = pr.id
WHERE COALESCE(e.quantidade,0) = 0
  AND CURRENT_DATE BETWEEN pm.data_inicio AND pm.data_fim;
