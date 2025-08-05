SELECT
    t.relname AS tabela,
    t.n_live_tup AS linhas,
    round((pg_total_relation_size(t.relid) / 1024.0 / 1024.0), 2) AS tamanho_mb,
    round((pg_total_relation_size(t.relid) / 1024.0 / 1024.0 / 1024.0), 2) AS tamanho_gb,
    '' AS dado_mais_novo,
    '' AS salvar
FROM
    pg_stat_user_tables t
WHERE
    t.schemaname = $1
ORDER BY
    tamanho_mb DESC;