WITH object_list AS (
    -- TABELAS / VIEWS / MATERIALIZED VIEWS
    SELECT
        c.oid,
        'pg_class'::regclass AS classid,
        c.relname AS object_name,
        CASE
            c.relkind
                WHEN 'r' THEN 'TABLE'
            WHEN 'v' THEN 'VIEW'
            WHEN 'm' THEN 'MATERIALIZED_VIEW'
            ELSE 'OTHER'
        END AS object_type,
        n.nspname AS object_schema
    FROM
        pg_catalog.pg_class c
    JOIN pg_catalog.pg_namespace n ON
        n.oid = c.relnamespace
    WHERE
        c.relkind IN ('r', 'v', 'm')
    UNION ALL
    -- FUNCTIONS / PROCEDURES
    SELECT
        p.oid,
        'pg_proc'::regclass,
        p.proname,
        CASE
            p.prokind
                WHEN 'f' THEN 'FUNCTION'
            WHEN 'p' THEN 'PROCEDURE'
            ELSE 'ROUTINE'
        END,
        n.nspname
    FROM
        pg_catalog.pg_proc p
    JOIN pg_catalog.pg_namespace n ON
        n.oid = p.pronamespace
    UNION ALL
    -- TRIGGERS
    SELECT
        t.oid,
        'pg_trigger'::regclass,
        t.tgname,
        'TRIGGER',
        n.nspname
    FROM
        pg_catalog.pg_trigger t
    JOIN pg_catalog.pg_class c ON
        c.oid = t.tgrelid
    JOIN pg_catalog.pg_namespace n ON
        n.oid = c.relnamespace
    WHERE
        NOT t.tgisinternal
    UNION ALL
    -- TYPES compostos
    SELECT
        ty.oid,
        'pg_type'::regclass,
        ty.typname,
        'TYPE',
        n.nspname
    FROM
        pg_catalog.pg_type ty
    JOIN pg_catalog.pg_namespace n ON
        n.oid = ty.typnamespace
    WHERE
        ty.typtype = 'c'
        AND n.nspname NOT IN ('pg_catalog', 'information_schema')
),
/* --------------------- RESOLVE NOME HUMANO --------------------- */
-- Helper para resolver objid/classid/objsubid => schema.tabela(.coluna)
resolve_name AS (
    SELECT
        d.classid,
        d.objid,
        d.objsubid,
        CASE
            WHEN d.classid = 'pg_class'::regclass THEN
                    ns.nspname || '.' || c.relname ||
                    CASE
                WHEN d.objsubid > 0 THEN '.' || a.attname
                ELSE ''
            END
            WHEN d.classid = 'pg_proc'::regclass THEN
                    np.nspname || '.' || p.proname
            WHEN d.classid = 'pg_type'::regclass THEN
                    nt.nspname || '.' || t.typname
            WHEN d.classid = 'pg_trigger'::regclass THEN
                    ntr.nspname || '.' || trg.tgname
            ELSE pg_identify_object(d.classid, d.objid, d.objsubid)::text
        END AS human_name
    FROM
        pg_depend d
    LEFT JOIN pg_class c ON
        d.classid = 'pg_class'::regclass
        AND c.oid = d.objid
    LEFT JOIN pg_namespace ns ON
        ns.oid = c.relnamespace
    LEFT JOIN pg_attribute a ON
        a.attrelid = c.oid
        AND a.attnum = d.objsubid
    LEFT JOIN pg_proc p ON
        d.classid = 'pg_proc'::regclass
        AND p.oid = d.objid
    LEFT JOIN pg_namespace np ON
        np.oid = p.pronamespace
    LEFT JOIN pg_type t ON
        d.classid = 'pg_type'::regclass
        AND t.oid = d.objid
    LEFT JOIN pg_namespace nt ON
        nt.oid = t.typnamespace
    LEFT JOIN pg_trigger trg ON
        d.classid = 'pg_trigger'::regclass
        AND trg.oid = d.objid
    LEFT JOIN pg_class ctr ON
        trg.tgrelid = ctr.oid
    LEFT JOIN pg_namespace ntr ON
        ntr.oid = ctr.relnamespace
),
resolve_name_ref AS (
    SELECT
        d.refclassid AS classid,
        d.refobjid AS objid,
        0 AS objsubid,
        -- pg_depend não guarda refobjsubid
            CASE
            WHEN d.refclassid = 'pg_class'::regclass THEN
                    ns.nspname || '.' || c.relname
            WHEN d.refclassid = 'pg_proc'::regclass THEN
                    np.nspname || '.' || p.proname
            WHEN d.refclassid = 'pg_type'::regclass THEN
                    nt.nspname || '.' || t.typname
            WHEN d.refclassid = 'pg_trigger'::regclass THEN
                    ntr.nspname || '.' || trg.tgname
            ELSE pg_identify_object(d.refclassid, d.refobjid, 0)::text
        END AS human_name
    FROM
        pg_depend d
    LEFT JOIN pg_class c ON
        d.refclassid = 'pg_class'::regclass
        AND c.oid = d.refobjid
    LEFT JOIN pg_namespace ns ON
        ns.oid = c.relnamespace
    LEFT JOIN pg_proc p ON
        d.refclassid = 'pg_proc'::regclass
        AND p.oid = d.refobjid
    LEFT JOIN pg_namespace np ON
        np.oid = p.pronamespace
    LEFT JOIN pg_type t ON
        d.refclassid = 'pg_type'::regclass
        AND t.oid = d.refobjid
    LEFT JOIN pg_namespace nt ON
        nt.oid = t.typnamespace
    LEFT JOIN pg_trigger trg ON
        d.refclassid = 'pg_trigger'::regclass
        AND trg.oid = d.refobjid
    LEFT JOIN pg_class ctr ON
        trg.tgrelid = ctr.oid
    LEFT JOIN pg_namespace ntr ON
        ntr.oid = ctr.relnamespace
),
/* --------------------- INBOUND / OUTBOUND --------------------- */
deps_in AS (
    SELECT
        o.oid,
        COUNT(*) AS cnt,
        string_agg(DISTINCT rn.human_name, ', ' ORDER BY rn.human_name) AS names
    FROM
        object_list o
    LEFT JOIN pg_depend d
            ON
        d.refobjid = o.oid
        AND d.deptype NOT IN ('i')
    LEFT JOIN resolve_name rn
            ON
        rn.classid = d.classid
            AND rn.objid = d.objid
            AND rn.objsubid = d.objsubid
        GROUP BY
            o.oid
),
deps_out AS (
    SELECT
        o.oid,
        COUNT(*) AS cnt,
        string_agg(DISTINCT rr.human_name, ', ' ORDER BY rr.human_name) AS names
    FROM
        object_list o
    LEFT JOIN pg_depend d
            ON
        d.objid = o.oid
        AND d.deptype NOT IN ('i')
    LEFT JOIN resolve_name_ref rr
            ON
        rr.classid = d.refclassid
            AND rr.objid = d.refobjid
        GROUP BY
            o.oid
)
SELECT
	o.object_name,
	o.object_type,
	COALESCE(di.cnt, 0) AS depend,
	COALESCE(dt.cnt, 0) AS dependencies,
	COALESCE(REPLACE(REPLACE(di.names, '"default value",,', ''), '(,', '('), '') AS depend_list,
	COALESCE(REPLACE(dt.names, ',,', ','), '') AS dependencies_list,
	-- FKs
    COALESCE((
        SELECT COUNT(*)
        FROM information_schema.table_constraints tc
        WHERE tc.table_schema = o.object_schema
          AND tc.table_name = o.object_name
          AND tc.constraint_type = 'FOREIGN KEY'
    ), 0) AS fks,
	COALESCE((
        SELECT COUNT(*)
        FROM information_schema.referential_constraints rc
        JOIN information_schema.table_constraints kcu
          ON kcu.constraint_name = rc.unique_constraint_name
         AND kcu.constraint_schema = rc.unique_constraint_schema
        WHERE kcu.table_schema = o.object_schema
          AND kcu.table_name = o.object_name
          AND rc.constraint_schema <> kcu.table_schema
    ), 0) AS fks_externas,
	-- Linhas
	ABS(COALESCE((
        SELECT reltuples::bigint
        FROM pg_class c
        WHERE c.oid = o.oid
          AND o.object_type IN ('TABLE', 'MATERIALIZED_VIEW', 'VIEW')
    ), 0)) AS linhas,
	-- Tamanho MB
    COALESCE((
        CASE WHEN o.object_type IN ('TABLE', 'MATERIALIZED_VIEW', 'VIEW')
             THEN ROUND(pg_total_relation_size(o.oid) / (1024.0 * 1024.0), 2)
             ELSE 0 END
    ), 0) AS tamanho_mb,
	-- Indexes
    COALESCE((
        SELECT COUNT(*)
        FROM pg_indexes i
        WHERE i.schemaname = o.object_schema
          AND i.tablename = o.object_name
    ), 0) AS INDEXES,
	-- Triggers
    COALESCE((
        SELECT COUNT(*)
        FROM pg_catalog.pg_trigger t
        JOIN pg_catalog.pg_class c2 ON c2.oid = t.tgrelid
        JOIN pg_catalog.pg_namespace n2 ON n2.oid = c2.relnamespace
        WHERE NOT t.tgisinternal
          AND n2.nspname = o.object_schema
          AND c2.relname = o.object_name
    ), 0) AS triggers,
	'VALID' AS status,
	COALESCE(lf.last_ddl_time, NOW()) AS created,
	COALESCE(lf.last_ddl_time, NOW()) AS last_ddl_time
FROM
	object_list o
LEFT JOIN deps_in di ON
	di.oid = o.oid
LEFT JOIN deps_out dt ON
	dt.oid = o.oid
LEFT JOIN LATERAL (
	SELECT
		(pg_stat_file(pg_relation_filepath(o.oid))).modification::timestamp AS last_ddl_time
) lf ON
	o.object_type IN ('TABLE', 'VIEW', 'MATERIALIZED_VIEW')
WHERE
        o.object_schema = %s
    AND o.object_type IN ('PROCEDURE','FUNCTION','TABLE','VIEW','MATERIALIZED_VIEW','TRIGGER')
ORDER BY
	o.object_type,
	o.object_name;
