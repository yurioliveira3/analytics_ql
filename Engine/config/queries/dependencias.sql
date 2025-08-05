-- QUERY DEPENDÊNCIAS (PostgreSQL)
SELECT DISTINCT
	d.schemaname AS schema_dependente,
	d.objname AS objeto_dependente,
	d.objtype AS tipo_objeto_dependente,
	d.ref_schemaname AS schema_referenciado,
	d.ref_objname AS objeto_referenciado,
	d.ref_objtype AS tipo_objeto_referenciado
FROM (
	SELECT
		n.nspname AS schemaname,
		c.relname AS objname,
		CASE c.relkind
			WHEN 'r' THEN 'TABLE'
			WHEN 'v' THEN 'VIEW'
			WHEN 'f' THEN 'FOREIGN TABLE'
			WHEN 'm' THEN 'MATERIALIZED VIEW'
			ELSE c.relkind::text
		END AS objtype,
		rn.nspname AS ref_schemaname,
		rc.relname AS ref_objname,
		CASE rc.relkind
			WHEN 'r' THEN 'TABLE'
			WHEN 'v' THEN 'VIEW'
			WHEN 'f' THEN 'FOREIGN TABLE'
			WHEN 'm' THEN 'MATERIALIZED VIEW'
			ELSE rc.relkind::text
		END AS ref_objtype
	FROM pg_depend pd
	JOIN pg_class c ON pd.objid = c.oid
	JOIN pg_namespace n ON c.relnamespace = n.oid
	JOIN pg_class rc ON pd.refobjid = rc.oid
	JOIN pg_namespace rn ON rc.relnamespace = rn.oid
	WHERE rn.nspname = :schema
	  AND rn.nspname <> n.nspname
	  AND c.relkind <> 'S' -- SYNONYM não existe, mas ignora tipo especial
	  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
) d
UNION
SELECT DISTINCT
	d.schemaname AS schema_dependente,
	d.objname AS objeto_dependente,
	d.objtype AS tipo_objeto_dependente,
	d.ref_schemaname AS schema_referenciado,
	d.ref_objname AS objeto_referenciado,
	d.ref_objtype AS tipo_objeto_referenciado
FROM (
	SELECT
		n.nspname AS schemaname,
		c.relname AS objname,
		CASE c.relkind
			WHEN 'r' THEN 'TABLE'
			WHEN 'v' THEN 'VIEW'
			WHEN 'f' THEN 'FOREIGN TABLE'
			WHEN 'm' THEN 'MATERIALIZED VIEW'
			ELSE c.relkind::text
		END AS objtype,
		rn.nspname AS ref_schemaname,
		rc.relname AS ref_objname,
		CASE rc.relkind
			WHEN 'r' THEN 'TABLE'
			WHEN 'v' THEN 'VIEW'
			WHEN 'f' THEN 'FOREIGN TABLE'
			WHEN 'm' THEN 'MATERIALIZED VIEW'
			ELSE rc.relkind::text
		END AS ref_objtype
	FROM pg_depend pd
	JOIN pg_class c ON pd.objid = c.oid
	JOIN pg_namespace n ON c.relnamespace = n.oid
	JOIN pg_class rc ON pd.refobjid = rc.oid
	JOIN pg_namespace rn ON rc.relnamespace = rn.oid
	WHERE rn.nspname NOT IN ('pg_catalog', 'information_schema')
	  AND rn.nspname <> n.nspname
	  AND c.relkind <> 'S'
	  AND n.nspname = :schema
) d
ORDER BY
	schema_dependente
;