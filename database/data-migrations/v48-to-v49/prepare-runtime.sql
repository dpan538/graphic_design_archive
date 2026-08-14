-- Ephemeral helpers, created by the disposable-cluster administrator before
-- SET ROLE.  They are scoped to the importer session and vanish at disconnect.
\set ON_ERROR_STOP on

CREATE FUNCTION pg_temp.gda_b64_json_scalar(p_value text)
RETURNS text
LANGUAGE sql
IMMUTABLE
SET search_path = pg_catalog
AS $$
  SELECT convert_from(decode(p_value, 'base64'), 'UTF8')::jsonb #>> '{}'
$$;

CREATE FUNCTION pg_temp.gda_inject(p_checkpoint text)
RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
  IF current_setting('gda.phase2b.inject', true) = p_checkpoint THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'PHASE2B_INJECTED_FAILURE:' || p_checkpoint;
  END IF;
END
$$;

GRANT EXECUTE ON FUNCTION pg_temp.gda_b64_json_scalar(text),
  pg_temp.gda_inject(text) TO gda_v49_phase2a_schema_owner;
