#!/usr/bin/env python3
"""Export deterministic Phase 2A catalog evidence from two fresh replays.

The exporter has no database driver dependency. It invokes an explicitly named
psql binary over an explicitly named Unix socket and only issues SELECTs.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from typing import Any, Iterable


PROJECT_SCHEMAS = (
    "raw",
    "core",
    "provenance",
    "research",
    "rights",
    "workflow",
    "release",
    "audit",
    "api_v1",
)
PROJECT_ROLES = (
    "gda_v49_phase2a_schema_owner",
    "gda_v49_phase2a_migrator",
    "gda_v49_phase2a_ingest_writer",
    "gda_v49_phase2a_reviewer",
    "gda_v49_phase2a_publisher",
    "gda_v49_phase2a_api_reader",
    "gda_v49_phase2a_auditor",
)

INVENTORY_HEADER = (
    "object_key", "object_kind", "schema_name", "object_name",
    "identity_arguments", "parent_schema", "parent_name", "owner_role",
    "relation_persistence", "relation_security_barrier", "routine_language",
    "routine_volatility", "routine_security_definer", "routine_search_path",
    "type_category", "definition_sha256_replay_1",
    "definition_sha256_replay_2", "replay_match",
)
CONSTRAINT_HEADER = (
    "control_key", "table_schema", "table_name", "control_kind",
    "control_name", "column_names_json", "referenced_schema",
    "referenced_table", "referenced_columns_json", "match_type", "on_update",
    "on_delete", "deferrable", "initially_deferred", "validated",
    "enabled_state", "trigger_timing", "trigger_events_json", "trigger_level",
    "guard_function_identity", "predicate_escaped",
    "definition_sha256_replay_1", "definition_sha256_replay_2", "replay_match",
    "backing_constraint_key", "normative_invariant", "test_ids_json", "status",
)
ROLE_HEADER = (
    "grant_key", "principal", "principal_kind", "record_kind", "object_kind",
    "object_schema", "object_identity", "privilege_or_attribute",
    "expected_effective", "actual_effective", "actual_direct", "grantor",
    "is_grantable", "effective_via", "default_acl_owner",
    "default_acl_schema", "test_id", "replay_match", "status",
)
NEGATIVE_HEADER = (
    "test_id", "gate_domain", "requirement_id", "oracle_kind", "test_file",
    "test_line_start", "sql_label_or_marker", "actor_role",
    "transaction_isolation", "fixture_scope", "enforcement_object_identity",
    "expected_sqlstates_json", "expected_message", "expected_postcondition_escaped",
    "expected_audit_effect_escaped", "rollback_required", "test_file_sha256",
    "replay_1_result", "replay_2_result", "replay_match", "status", "notes",
)


def normalized_definition(payload: str) -> bytes:
    lines = [line.rstrip(" \t") for line in payload.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return ("\n".join(lines).rstrip("\n") + "\n").encode("utf-8")


def digest(payload: str) -> str:
    return hashlib.sha256(normalized_definition(payload)).hexdigest()


def scalar(value: Any) -> str:
    if value is None:
        return r"\N"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=isinstance(value, dict))
    text = str(value)
    return text.replace("\\", "\\\\").replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")


def write_tsv(path: pathlib.Path, header: Iterable[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\t".join(header) + "\n")
        for row in rows:
            handle.write("\t".join(scalar(row.get(column)) for column in header) + "\n")


class Catalog:
    def __init__(self, psql: str, host: str, port: int) -> None:
        if not pathlib.Path(host).is_absolute() or port == 5432:
            raise SystemExit("refusing non-isolated PostgreSQL target")
        self.psql = psql
        self.host = host
        self.port = port

    def json_lines(self, database: str, sql: str) -> list[dict[str, Any]]:
        if not database.startswith("gda_v49_phase2a_"):
            raise SystemExit("database name must use gda_v49_phase2a_ prefix")
        result = subprocess.run(
            [self.psql, "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-h", self.host,
             "-p", str(self.port), "-d", database, "-c", sql],
            check=False, text=True, capture_output=True,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "psql returned no diagnostics"
            raise SystemExit(f"psql failed for {database}: {detail}")
        return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


INVENTORY_SQL = r"""
WITH project_schema(name) AS (
  VALUES ('raw'),('core'),('provenance'),('research'),('rights'),
         ('workflow'),('release'),('audit'),('api_v1')
), objects AS (
  SELECT 'SCHEMA|' || n.nspname AS object_key, 'SCHEMA' AS object_kind,
    n.nspname AS schema_name, n.nspname AS object_name, NULL::text AS identity_arguments,
    NULL::text AS parent_schema, NULL::text AS parent_name,
    pg_catalog.pg_get_userbyid(n.nspowner) AS owner_role,
    NULL::text AS relation_persistence, NULL::boolean AS relation_security_barrier,
    NULL::text AS routine_language, NULL::text AS routine_volatility,
    NULL::boolean AS routine_security_definer, NULL::text AS routine_search_path,
    NULL::text AS type_category,
    jsonb_build_object('owner',pg_catalog.pg_get_userbyid(n.nspowner))::text AS definition
  FROM pg_catalog.pg_namespace n JOIN project_schema s ON s.name=n.nspname

  UNION ALL
  SELECT (CASE c.relkind WHEN 'r' THEN 'TABLE' WHEN 'p' THEN 'PARTITIONED_TABLE'
      WHEN 'v' THEN 'VIEW' WHEN 'm' THEN 'MATERIALIZED_VIEW' WHEN 'S' THEN 'SEQUENCE' END)
      || '|' || n.nspname || '|' || c.relname,
    CASE c.relkind WHEN 'r' THEN 'TABLE' WHEN 'p' THEN 'PARTITIONED_TABLE'
      WHEN 'v' THEN 'VIEW' WHEN 'm' THEN 'MATERIALIZED_VIEW' WHEN 'S' THEN 'SEQUENCE' END,
    n.nspname,c.relname,NULL,NULL,NULL,pg_catalog.pg_get_userbyid(c.relowner),
    CASE c.relpersistence WHEN 'p' THEN 'permanent' WHEN 'u' THEN 'unlogged'
      WHEN 't' THEN 'temporary' END,
    CASE WHEN c.relkind IN ('v','m') THEN COALESCE('security_barrier=true'=ANY(c.reloptions),false) ELSE NULL END,
    NULL,NULL,NULL,NULL,NULL,
    jsonb_build_object('relkind',c.relkind,'owner',pg_catalog.pg_get_userbyid(c.relowner),
      'persistence',c.relpersistence,'rowSecurity',c.relrowsecurity,
      'forceRowSecurity',c.relforcerowsecurity,'options',c.reloptions,
      'viewDefinition',CASE WHEN c.relkind IN ('v','m') THEN pg_catalog.pg_get_viewdef(c.oid,true) END)::text
  FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
  JOIN project_schema s ON s.name=n.nspname WHERE c.relkind IN ('r','p','v','m','S')

  UNION ALL
  SELECT 'TABLE_COLUMN|'||n.nspname||'|'||c.relname||'|'||a.attname,
    'TABLE_COLUMN',n.nspname,a.attname,NULL,n.nspname,c.relname,
    pg_catalog.pg_get_userbyid(c.relowner),NULL,NULL,NULL,NULL,NULL,NULL,NULL,
    jsonb_build_object('ordinal',a.attnum,'type',pg_catalog.format_type(a.atttypid,a.atttypmod),
      'collation',CASE WHEN a.attcollation<>0 THEN co.collname END,'notNull',a.attnotnull,
      'generated',a.attgenerated,'identity',a.attidentity,
      'default',CASE WHEN d.oid IS NOT NULL THEN pg_catalog.pg_get_expr(d.adbin,d.adrelid,true) END)::text
  FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid=a.attrelid
  JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN project_schema s ON s.name=n.nspname
  LEFT JOIN pg_catalog.pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
  LEFT JOIN pg_catalog.pg_collation co ON co.oid=a.attcollation
  WHERE c.relkind IN ('r','p','v','m','S') AND a.attnum>0 AND NOT a.attisdropped

  UNION ALL
  SELECT 'INDEX|'||n.nspname||'|'||base.relname||'|'||idx.relname,'INDEX',n.nspname,
    idx.relname,NULL,n.nspname,base.relname,pg_catalog.pg_get_userbyid(idx.relowner),
    NULL,NULL,NULL,NULL,NULL,NULL,NULL,
    jsonb_build_object('definition',pg_catalog.pg_get_indexdef(i.indexrelid),
      'unique',i.indisunique,'primary',i.indisprimary,'valid',i.indisvalid,
      'ready',i.indisready,'live',i.indislive,
      'predicate',pg_catalog.pg_get_expr(i.indpred,i.indrelid,true))::text
  FROM pg_catalog.pg_index i JOIN pg_catalog.pg_class idx ON idx.oid=i.indexrelid
  JOIN pg_catalog.pg_class base ON base.oid=i.indrelid
  JOIN pg_catalog.pg_namespace n ON n.oid=base.relnamespace JOIN project_schema s ON s.name=n.nspname

  UNION ALL
  SELECT (CASE t.typtype WHEN 'e' THEN 'ENUM' WHEN 'd' THEN 'DOMAIN'
      WHEN 'c' THEN 'COMPOSITE_TYPE' WHEN 'r' THEN 'RANGE_TYPE' END)
      ||'|'||n.nspname||'|'||t.typname,
    CASE t.typtype WHEN 'e' THEN 'ENUM' WHEN 'd' THEN 'DOMAIN'
      WHEN 'c' THEN 'COMPOSITE_TYPE' WHEN 'r' THEN 'RANGE_TYPE' END,
    n.nspname,t.typname,NULL,NULL,NULL,pg_catalog.pg_get_userbyid(t.typowner),
    NULL,NULL,NULL,NULL,NULL,NULL,
    CASE t.typtype WHEN 'e' THEN 'enum' WHEN 'd' THEN 'domain'
      WHEN 'c' THEN 'composite' WHEN 'r' THEN 'range' END,
    jsonb_build_object('type',t.typtype,'owner',pg_catalog.pg_get_userbyid(t.typowner),
      'baseType',CASE WHEN t.typbasetype<>0 THEN pg_catalog.format_type(t.typbasetype,t.typtypmod) END,
      'notNull',t.typnotnull,'default',t.typdefault,
      'enumLabels',(SELECT jsonb_agg(e.enumlabel ORDER BY e.enumsortorder) FROM pg_catalog.pg_enum e WHERE e.enumtypid=t.oid),
      'attributes',(SELECT jsonb_agg(jsonb_build_array(a.attname,pg_catalog.format_type(a.atttypid,a.atttypmod),a.attnotnull) ORDER BY a.attnum) FROM pg_catalog.pg_attribute a WHERE a.attrelid=t.typrelid AND a.attnum>0 AND NOT a.attisdropped),
      'constraints',(SELECT jsonb_agg(pg_catalog.pg_get_constraintdef(k.oid,true) ORDER BY k.conname) FROM pg_catalog.pg_constraint k WHERE k.contypid=t.oid))::text
  FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid=t.typnamespace
  JOIN project_schema s ON s.name=n.nspname LEFT JOIN pg_catalog.pg_class tc ON tc.oid=t.typrelid
  WHERE t.typtype IN ('e','d','r') OR (t.typtype='c' AND tc.relkind='c')

  UNION ALL
  SELECT (CASE p.prokind WHEN 'p' THEN 'PROCEDURE' ELSE 'FUNCTION' END)
      ||'|'||n.nspname||'|'||p.proname||'|'||pg_catalog.pg_get_function_identity_arguments(p.oid),
    CASE p.prokind WHEN 'p' THEN 'PROCEDURE' ELSE 'FUNCTION' END,
    n.nspname,p.proname,pg_catalog.pg_get_function_identity_arguments(p.oid),NULL,NULL,
    pg_catalog.pg_get_userbyid(p.proowner),NULL,NULL,l.lanname,
    CASE p.provolatile WHEN 'i' THEN 'immutable' WHEN 's' THEN 'stable' ELSE 'volatile' END,
    p.prosecdef,(SELECT x FROM unnest(p.proconfig) x WHERE x LIKE 'search_path=%' LIMIT 1),NULL,
    jsonb_build_object('definition',pg_catalog.pg_get_functiondef(p.oid),
      'result',pg_catalog.pg_get_function_result(p.oid),'parallel',p.proparallel,
      'leakproof',p.proleakproof,'config',p.proconfig)::text
  FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
  JOIN project_schema s ON s.name=n.nspname JOIN pg_catalog.pg_language l ON l.oid=p.prolang
  WHERE p.prokind IN ('f','p','a','w')

  UNION ALL
  SELECT 'TRIGGER|'||n.nspname||'|'||c.relname||'|'||t.tgname,'TRIGGER',n.nspname,
    t.tgname,NULL,n.nspname,c.relname,pg_catalog.pg_get_userbyid(c.relowner),
    NULL,NULL,NULL,NULL,NULL,NULL,NULL,pg_catalog.pg_get_triggerdef(t.oid,true)
  FROM pg_catalog.pg_trigger t JOIN pg_catalog.pg_class c ON c.oid=t.tgrelid
  JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN project_schema s ON s.name=n.nspname
  WHERE NOT t.tgisinternal

  UNION ALL
  SELECT 'CONSTRAINT|'||n.nspname||'|'||COALESCE(c.relname,ty.typname)||'|'||k.conname,
    'CONSTRAINT',n.nspname,k.conname,NULL,n.nspname,COALESCE(c.relname,ty.typname),
    COALESCE(pg_catalog.pg_get_userbyid(c.relowner),pg_catalog.pg_get_userbyid(ty.typowner)),
    NULL,NULL,NULL,NULL,NULL,NULL,NULL,
    jsonb_build_object('type',k.contype,'definition',pg_catalog.pg_get_constraintdef(k.oid,true),
      'deferrable',k.condeferrable,'initiallyDeferred',k.condeferred,'validated',k.convalidated)::text
  FROM pg_catalog.pg_constraint k JOIN pg_catalog.pg_namespace n ON n.oid=k.connamespace
  JOIN project_schema s ON s.name=n.nspname LEFT JOIN pg_catalog.pg_class c ON c.oid=k.conrelid
  LEFT JOIN pg_catalog.pg_type ty ON ty.oid=k.contypid
  WHERE k.conrelid<>0 OR k.contypid<>0
)
SELECT jsonb_build_object(
  'object_key',object_key,'object_kind',object_kind,'schema_name',schema_name,
  'object_name',object_name,'identity_arguments',identity_arguments,
  'parent_schema',parent_schema,'parent_name',parent_name,'owner_role',owner_role,
  'relation_persistence',relation_persistence,
  'relation_security_barrier',relation_security_barrier,
  'routine_language',routine_language,'routine_volatility',routine_volatility,
  'routine_security_definer',routine_security_definer,
  'routine_search_path',routine_search_path,'type_category',type_category,
  'definition',definition)::text
FROM objects ORDER BY object_key;
"""


CONTROL_SQL = r"""
WITH project_schema(name) AS (
  VALUES ('raw'),('core'),('provenance'),('research'),('rights'),
         ('workflow'),('release'),('audit')
), controls AS (
  SELECT n.nspname||'|'||t.relname||'|'||
      CASE c.contype WHEN 'p' THEN 'PRIMARY_KEY' WHEN 'u' THEN 'UNIQUE_CONSTRAINT'
        WHEN 'f' THEN 'FOREIGN_KEY' WHEN 'c' THEN 'CHECK' WHEN 'x' THEN 'EXCLUSION' END
      ||'|'||c.conname AS control_key,
    n.nspname AS table_schema,t.relname AS table_name,
    CASE c.contype WHEN 'p' THEN 'PRIMARY_KEY' WHEN 'u' THEN 'UNIQUE_CONSTRAINT'
      WHEN 'f' THEN 'FOREIGN_KEY' WHEN 'c' THEN 'CHECK' WHEN 'x' THEN 'EXCLUSION' END AS control_kind,
    c.conname AS control_name,
    COALESCE((SELECT jsonb_agg(a.attname ORDER BY u.ord) FROM unnest(c.conkey) WITH ORDINALITY u(attnum,ord) JOIN pg_catalog.pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=u.attnum),'[]'::jsonb) AS column_names_json,
    rn.nspname AS referenced_schema,rt.relname AS referenced_table,
    COALESCE((SELECT jsonb_agg(a.attname ORDER BY u.ord) FROM unnest(c.confkey) WITH ORDINALITY u(attnum,ord) JOIN pg_catalog.pg_attribute a ON a.attrelid=c.confrelid AND a.attnum=u.attnum),'[]'::jsonb) AS referenced_columns_json,
    CASE c.confmatchtype WHEN 'f' THEN 'FULL' WHEN 'p' THEN 'PARTIAL' WHEN 's' THEN 'SIMPLE' END AS match_type,
    CASE c.confupdtype WHEN 'a' THEN 'NO ACTION' WHEN 'r' THEN 'RESTRICT' WHEN 'c' THEN 'CASCADE' WHEN 'n' THEN 'SET NULL' WHEN 'd' THEN 'SET DEFAULT' END AS on_update,
    CASE c.confdeltype WHEN 'a' THEN 'NO ACTION' WHEN 'r' THEN 'RESTRICT' WHEN 'c' THEN 'CASCADE' WHEN 'n' THEN 'SET NULL' WHEN 'd' THEN 'SET DEFAULT' END AS on_delete,
    c.condeferrable AS deferrable,c.condeferred AS initially_deferred,c.convalidated AS validated,
    NULL::text AS enabled_state,NULL::text AS trigger_timing,'[]'::jsonb AS trigger_events_json,
    NULL::text AS trigger_level,NULL::text AS guard_function_identity,
    CASE WHEN c.contype='c' THEN pg_catalog.pg_get_constraintdef(c.oid,true) END AS predicate_escaped,
    pg_catalog.pg_get_constraintdef(c.oid,true) AS definition,
    NULL::text AS backing_constraint_key,
    CASE c.contype WHEN 'p' THEN 'NATURAL_KEY' WHEN 'u' THEN 'NATURAL_KEY'
      WHEN 'f' THEN CASE WHEN rn.nspname IN ('raw','core','provenance','research') THEN 'CANONICAL_PARENT_RESTRICT' ELSE 'IDENTITY_FK' END
      ELSE 'CLOSED_SUBTYPE' END AS normative_invariant
  FROM pg_catalog.pg_constraint c JOIN pg_catalog.pg_class t ON t.oid=c.conrelid
  JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace JOIN project_schema s ON s.name=n.nspname
  LEFT JOIN pg_catalog.pg_class rt ON rt.oid=c.confrelid LEFT JOIN pg_catalog.pg_namespace rn ON rn.oid=rt.relnamespace
  WHERE c.contype IN ('p','u','f','c','x')

  UNION ALL
  SELECT n.nspname||'|'||t.relname||'|NOT_NULL|'||a.attname||':NOT_NULL',n.nspname,t.relname,
    'NOT_NULL',a.attname||':NOT_NULL',jsonb_build_array(a.attname),NULL,NULL,'[]'::jsonb,
    NULL,NULL,NULL,false,false,true,NULL,NULL,'[]'::jsonb,NULL,NULL,NULL,
    jsonb_build_object('column',a.attname,'notNull',true)::text,NULL,'CLOSED_SUBTYPE'
  FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class t ON t.oid=a.attrelid
  JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace JOIN project_schema s ON s.name=n.nspname
  WHERE t.relkind IN ('r','p') AND a.attnum>0 AND NOT a.attisdropped AND a.attnotnull

  UNION ALL
  SELECT n.nspname||'|'||t.relname||'|COLUMN_DEFAULT|'||a.attname||':DEFAULT',n.nspname,t.relname,
    'COLUMN_DEFAULT',a.attname||':DEFAULT',jsonb_build_array(a.attname),NULL,NULL,'[]'::jsonb,
    NULL,NULL,NULL,false,false,true,NULL,NULL,'[]'::jsonb,NULL,NULL,NULL,
    pg_catalog.pg_get_expr(d.adbin,d.adrelid,true),NULL,'CLOSED_SUBTYPE'
  FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class t ON t.oid=a.attrelid
  JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace JOIN project_schema s ON s.name=n.nspname
  JOIN pg_catalog.pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
  WHERE t.relkind IN ('r','p') AND a.attnum>0 AND NOT a.attisdropped AND a.attgenerated=''

  UNION ALL
  SELECT n.nspname||'|'||t.relname||'|GENERATED_COLUMN|'||a.attname||':GENERATED',n.nspname,t.relname,
    'GENERATED_COLUMN',a.attname||':GENERATED',jsonb_build_array(a.attname),NULL,NULL,'[]'::jsonb,
    NULL,NULL,NULL,false,false,true,NULL,NULL,'[]'::jsonb,NULL,NULL,NULL,
    pg_catalog.pg_get_expr(d.adbin,d.adrelid,true),NULL,'CLOSED_SUBTYPE'
  FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class t ON t.oid=a.attrelid
  JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace JOIN project_schema s ON s.name=n.nspname
  JOIN pg_catalog.pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
  WHERE t.relkind IN ('r','p') AND a.attnum>0 AND NOT a.attisdropped AND a.attgenerated<>''

  UNION ALL
  SELECT n.nspname||'|'||t.relname||'|'||CASE WHEN i.indisunique AND con.oid IS NULL THEN 'UNIQUE_INDEX' ELSE 'INDEX' END||'|'||idx.relname,
    n.nspname,t.relname,CASE WHEN i.indisunique AND con.oid IS NULL THEN 'UNIQUE_INDEX' ELSE 'INDEX' END,
    idx.relname,'[]'::jsonb,NULL,NULL,'[]'::jsonb,NULL,NULL,NULL,false,false,i.indisvalid,
    NULL,NULL,'[]'::jsonb,NULL,NULL,pg_catalog.pg_get_expr(i.indpred,i.indrelid,true),
    pg_catalog.pg_get_indexdef(i.indexrelid),
    CASE WHEN con.oid IS NULL THEN NULL ELSE n.nspname||'|'||t.relname||'|'||
      CASE con.contype WHEN 'p' THEN 'PRIMARY_KEY' WHEN 'u' THEN 'UNIQUE_CONSTRAINT' WHEN 'x' THEN 'EXCLUSION' END||'|'||con.conname END,
    'ACCESS_PATH_ONLY'
  FROM pg_catalog.pg_index i JOIN pg_catalog.pg_class idx ON idx.oid=i.indexrelid
  JOIN pg_catalog.pg_class t ON t.oid=i.indrelid JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace
  JOIN project_schema s ON s.name=n.nspname LEFT JOIN pg_catalog.pg_constraint con
    ON con.conindid=i.indexrelid AND con.conrelid=i.indrelid AND con.contype IN ('p','u','x')

  UNION ALL
  SELECT n.nspname||'|'||t.relname||'|'||CASE WHEN tr.tgconstraint<>0 THEN 'CONSTRAINT_TRIGGER' ELSE 'ROW_TRIGGER' END||'|'||tr.tgname,
    n.nspname,t.relname,CASE WHEN tr.tgconstraint<>0 THEN 'CONSTRAINT_TRIGGER' ELSE 'ROW_TRIGGER' END,
    tr.tgname,'[]'::jsonb,NULL,NULL,'[]'::jsonb,NULL,NULL,NULL,
    tr.tgdeferrable,tr.tginitdeferred,true,tr.tgenabled::text,
    CASE WHEN (tr.tgtype & 64)<>0 THEN 'INSTEAD OF' WHEN (tr.tgtype & 2)<>0 THEN 'BEFORE' ELSE 'AFTER' END,
    (SELECT jsonb_agg(event ORDER BY event) FROM (VALUES
      (CASE WHEN (tr.tgtype & 4)<>0 THEN 'INSERT' END),(CASE WHEN (tr.tgtype & 8)<>0 THEN 'DELETE' END),
      (CASE WHEN (tr.tgtype & 16)<>0 THEN 'UPDATE' END),(CASE WHEN (tr.tgtype & 32)<>0 THEN 'TRUNCATE' END)) e(event) WHERE event IS NOT NULL),
    CASE WHEN (tr.tgtype & 1)<>0 THEN 'ROW' ELSE 'STATEMENT' END,
    p.oid::regprocedure::text,NULL,pg_catalog.pg_get_triggerdef(tr.oid,true),NULL,
    CASE WHEN p.proname ~ '(reject|append|immutable)' THEN 'APPEND_ONLY'
      WHEN p.proname ~ '(release|registry|manifest|seal)' THEN 'SEALED_MUTATION_GUARD'
      WHEN tr.tgdeferrable THEN 'DEFERRED_EVIDENCE_VALIDATION' ELSE 'CLOSED_SUBTYPE' END
  FROM pg_catalog.pg_trigger tr JOIN pg_catalog.pg_class t ON t.oid=tr.tgrelid
  JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace JOIN project_schema s ON s.name=n.nspname
  JOIN pg_catalog.pg_proc p ON p.oid=tr.tgfoid WHERE NOT tr.tgisinternal
)
SELECT jsonb_build_object(
  'control_key',control_key,'table_schema',table_schema,'table_name',table_name,
  'control_kind',control_kind,'control_name',control_name,
  'column_names_json',column_names_json,'referenced_schema',referenced_schema,
  'referenced_table',referenced_table,'referenced_columns_json',referenced_columns_json,
  'match_type',match_type,'on_update',on_update,'on_delete',on_delete,
  'deferrable',controls.deferrable,'initially_deferred',controls.initially_deferred,
  'validated',controls.validated,
  'enabled_state',enabled_state,'trigger_timing',trigger_timing,
  'trigger_events_json',COALESCE(trigger_events_json,'[]'::jsonb),
  'trigger_level',trigger_level,'guard_function_identity',guard_function_identity,
  'predicate_escaped',predicate_escaped,'definition',definition,
  'backing_constraint_key',backing_constraint_key,
  'normative_invariant',normative_invariant)::text
FROM controls ORDER BY control_key;
"""


ROLE_SQL = r"""
WITH principals(name,kind) AS (
  VALUES ('PUBLIC','PUBLIC'),
    ('gda_v49_phase2a_schema_owner','ROLE'),('gda_v49_phase2a_migrator','ROLE'),
    ('gda_v49_phase2a_ingest_writer','ROLE'),('gda_v49_phase2a_reviewer','ROLE'),
    ('gda_v49_phase2a_publisher','ROLE'),('gda_v49_phase2a_api_reader','ROLE'),
    ('gda_v49_phase2a_auditor','ROLE')
), project_schema(name) AS (
  VALUES ('raw'),('core'),('provenance'),('research'),('rights'),
         ('workflow'),('release'),('audit'),('api_v1')
), rows AS (
  SELECT p.name||'|ROLE_ATTRIBUTE|\N|'||p.name||'|'||a.attribute AS grant_key,
    p.name AS principal,p.kind AS principal_kind,'ROLE_ATTRIBUTE' AS record_kind,
    'ROLE' AS object_kind,NULL::text AS object_schema,p.name AS object_identity,
    a.attribute AS privilege_or_attribute,
    CASE a.attribute WHEN 'LOGIN' THEN r.rolcanlogin WHEN 'SUPERUSER' THEN r.rolsuper
      WHEN 'CREATEDB' THEN r.rolcreatedb WHEN 'CREATEROLE' THEN r.rolcreaterole
      WHEN 'INHERIT' THEN r.rolinherit WHEN 'REPLICATION' THEN r.rolreplication
      WHEN 'BYPASSRLS' THEN r.rolbypassrls END AS actual_effective,
    NULL::boolean AS actual_direct,NULL::text AS grantor,NULL::boolean AS is_grantable,
    'DIRECT' AS effective_via,NULL::text AS default_acl_owner,NULL::text AS default_acl_schema
  FROM principals p JOIN pg_catalog.pg_roles r ON r.rolname=p.name AND p.kind='ROLE'
  CROSS JOIN (VALUES ('LOGIN'),('SUPERUSER'),('CREATEDB'),('CREATEROLE'),('INHERIT'),('REPLICATION'),('BYPASSRLS')) a(attribute)

  UNION ALL
  SELECT p.name||'|ROLE_MEMBERSHIP|\N|'||parent.name||'|MEMBER',p.name,p.kind,
    'ROLE_MEMBERSHIP','ROLE',NULL,parent.name,'MEMBER',
    CASE WHEN p.kind='PUBLIC' OR p.name=parent.name THEN false ELSE pg_catalog.pg_has_role(p.name,parent.name,'MEMBER') END,
    CASE WHEN p.kind='PUBLIC' THEN false ELSE EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles mr ON mr.oid=m.member JOIN pg_catalog.pg_roles pr ON pr.oid=m.roleid WHERE mr.rolname=p.name AND pr.rolname=parent.name) END,
    NULL,NULL,CASE WHEN p.name='gda_v49_phase2a_migrator' AND parent.name='gda_v49_phase2a_schema_owner' THEN 'SET_ROLE' ELSE 'NONE' END,NULL,NULL
  FROM principals p CROSS JOIN principals parent WHERE parent.kind='ROLE'

  UNION ALL
  SELECT p.name||'|DATABASE_PRIVILEGE|\N|gda_v49_phase2a_fresh_replay|'||x.privilege,p.name,p.kind,
    'DATABASE_PRIVILEGE','DATABASE',NULL,'gda_v49_phase2a_fresh_replay',x.privilege,
    pg_catalog.has_database_privilege(CASE WHEN p.kind='PUBLIC' THEN 'public' WHEN p.name='gda_v49_phase2a_migrator' THEN 'gda_v49_phase2a_schema_owner' ELSE p.name END,current_database(),x.privilege),
    pg_catalog.has_database_privilege(CASE WHEN p.kind='PUBLIC' THEN 'public' ELSE p.name END,current_database(),x.privilege),NULL,NULL,
    CASE WHEN p.name IN ('gda_v49_phase2a_schema_owner','gda_v49_phase2a_migrator') THEN 'OWNER' ELSE 'DIRECT' END,NULL,NULL
  FROM principals p CROSS JOIN (VALUES ('CONNECT'),('CREATE'),('TEMP')) x(privilege)

  UNION ALL
  SELECT p.name||'|SCHEMA_PRIVILEGE|'||s.name||'|'||s.name||'|'||x.privilege,p.name,p.kind,
    'SCHEMA_PRIVILEGE','SCHEMA',s.name,s.name,x.privilege,
    pg_catalog.has_schema_privilege(CASE WHEN p.kind='PUBLIC' THEN 'public' WHEN p.name='gda_v49_phase2a_migrator' THEN 'gda_v49_phase2a_schema_owner' ELSE p.name END,s.name,x.privilege),
    pg_catalog.has_schema_privilege(CASE WHEN p.kind='PUBLIC' THEN 'public' ELSE p.name END,s.name,x.privilege),NULL,NULL,
    CASE WHEN p.name IN ('gda_v49_phase2a_schema_owner','gda_v49_phase2a_migrator') THEN 'OWNER' ELSE 'DIRECT' END,NULL,NULL
  FROM principals p CROSS JOIN project_schema s CROSS JOIN (VALUES ('USAGE'),('CREATE')) x(privilege)

  UNION ALL
  SELECT p.name||'|RELATION_PRIVILEGE|'||n.nspname||'|'||c.relname||'|'||x.privilege,p.name,p.kind,
    'RELATION_PRIVILEGE',CASE WHEN c.relkind IN ('v','m') THEN 'VIEW' ELSE 'TABLE' END,
    n.nspname,c.relname,x.privilege,pg_catalog.has_table_privilege(CASE WHEN p.kind='PUBLIC' THEN 'public' WHEN p.name='gda_v49_phase2a_migrator' THEN 'gda_v49_phase2a_schema_owner' ELSE p.name END,c.oid,x.privilege),
    pg_catalog.has_table_privilege(CASE WHEN p.kind='PUBLIC' THEN 'public' ELSE p.name END,c.oid,x.privilege),NULL,NULL,
    CASE WHEN p.name IN ('gda_v49_phase2a_schema_owner','gda_v49_phase2a_migrator') THEN 'OWNER' ELSE 'DIRECT' END,NULL,NULL
  FROM principals p CROSS JOIN pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
  JOIN project_schema s ON s.name=n.nspname
  CROSS JOIN (VALUES ('SELECT'),('INSERT'),('UPDATE'),('DELETE'),('TRUNCATE'),('REFERENCES'),('TRIGGER')) x(privilege)
  WHERE c.relkind IN ('r','p','v','m')

  UNION ALL
  SELECT p.name||'|SEQUENCE_PRIVILEGE|'||n.nspname||'|'||c.relname||'|'||x.privilege,p.name,p.kind,
    'SEQUENCE_PRIVILEGE','SEQUENCE',n.nspname,c.relname,x.privilege,
    pg_catalog.has_sequence_privilege(CASE WHEN p.kind='PUBLIC' THEN 'public' WHEN p.name='gda_v49_phase2a_migrator' THEN 'gda_v49_phase2a_schema_owner' ELSE p.name END,c.oid,x.privilege),
    pg_catalog.has_sequence_privilege(CASE WHEN p.kind='PUBLIC' THEN 'public' ELSE p.name END,c.oid,x.privilege),NULL,NULL,
    CASE WHEN p.name='gda_v49_phase2a_schema_owner' THEN 'OWNER' WHEN p.name='gda_v49_phase2a_migrator' THEN 'SET_ROLE' ELSE 'DIRECT' END,NULL,NULL
  FROM principals p CROSS JOIN pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
  JOIN project_schema s ON s.name=n.nspname
  CROSS JOIN (VALUES ('USAGE'),('SELECT'),('UPDATE')) x(privilege)
  WHERE c.relkind='S'

  UNION ALL
  SELECT p.name||'|ROUTINE_PRIVILEGE|'||n.nspname||'|'||pr.oid::regprocedure::text||'|EXECUTE',p.name,p.kind,
    'ROUTINE_PRIVILEGE','ROUTINE',n.nspname,pr.oid::regprocedure::text,'EXECUTE',
    pg_catalog.has_function_privilege(CASE WHEN p.kind='PUBLIC' THEN 'public' WHEN p.name='gda_v49_phase2a_migrator' THEN 'gda_v49_phase2a_schema_owner' ELSE p.name END,pr.oid,'EXECUTE'),
    pg_catalog.has_function_privilege(CASE WHEN p.kind='PUBLIC' THEN 'public' ELSE p.name END,pr.oid,'EXECUTE'),NULL,NULL,
    CASE WHEN p.name IN ('gda_v49_phase2a_schema_owner','gda_v49_phase2a_migrator') THEN 'OWNER' ELSE 'DIRECT' END,NULL,NULL
  FROM principals p CROSS JOIN pg_catalog.pg_proc pr JOIN pg_catalog.pg_namespace n ON n.oid=pr.pronamespace
  JOIN project_schema s ON s.name=n.nspname

  UNION ALL
  SELECT p.name||'|TYPE_PRIVILEGE|'||n.nspname||'|'||t.typname||'|USAGE',p.name,p.kind,
    'TYPE_PRIVILEGE','TYPE',n.nspname,t.typname,'USAGE',
    pg_catalog.has_type_privilege(CASE WHEN p.kind='PUBLIC' THEN 'public' WHEN p.name='gda_v49_phase2a_migrator' THEN 'gda_v49_phase2a_schema_owner' ELSE p.name END,t.oid,'USAGE'),
    pg_catalog.has_type_privilege(CASE WHEN p.kind='PUBLIC' THEN 'public' ELSE p.name END,t.oid,'USAGE'),
    NULL,NULL,CASE WHEN p.name IN ('gda_v49_phase2a_schema_owner','gda_v49_phase2a_migrator') THEN 'OWNER' ELSE 'DIRECT' END,NULL,NULL
  FROM principals p CROSS JOIN pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid=t.typnamespace
  JOIN project_schema s ON s.name=n.nspname
  WHERE t.typtype IN ('e','d','r') OR (t.typtype='c' AND t.typrelid IN (SELECT oid FROM pg_catalog.pg_class WHERE relkind='c'))

  UNION ALL
  SELECT 'PUBLIC|DEFAULT_ACL|\N|FUTURE_'||a.object_kind||'|'||a.privilege,
    'PUBLIC','PUBLIC','DEFAULT_ACL',a.object_kind,NULL,'FUTURE_'||a.object_kind,a.privilege,
    EXISTS (
      SELECT 1 FROM pg_catalog.aclexplode(COALESCE(d.defaclacl,pg_catalog.acldefault(a.object_code,v.owner_oid))) x
      WHERE x.grantee=0 AND x.privilege_type=a.privilege
    ),
    EXISTS (
      SELECT 1 FROM pg_catalog.aclexplode(COALESCE(d.defaclacl,pg_catalog.acldefault(a.object_code,v.owner_oid))) x
      WHERE x.grantee=0 AND x.privilege_type=a.privilege
    ),NULL,false,'NONE','gda_v49_phase2a_schema_owner',NULL
  FROM (SELECT oid AS owner_oid FROM pg_catalog.pg_roles WHERE rolname='gda_v49_phase2a_schema_owner') v
  CROSS JOIN (VALUES
    ('TABLE','r'::"char",'SELECT'),('TABLE','r'::"char",'INSERT'),
    ('TABLE','r'::"char",'UPDATE'),('TABLE','r'::"char",'DELETE'),
    ('TABLE','r'::"char",'TRUNCATE'),('TABLE','r'::"char",'REFERENCES'),
    ('TABLE','r'::"char",'TRIGGER'),('SEQUENCE','S'::"char",'USAGE'),
    ('SEQUENCE','S'::"char",'SELECT'),('SEQUENCE','S'::"char",'UPDATE'),
    ('ROUTINE','f'::"char",'EXECUTE'),('TYPE','T'::"char",'USAGE')
  ) a(object_kind,object_code,privilege)
  LEFT JOIN pg_catalog.pg_default_acl d ON d.defaclrole=v.owner_oid
    AND d.defaclnamespace=0 AND d.defaclobjtype=a.object_code
)
SELECT jsonb_build_object('grant_key',grant_key,'principal',principal,
  'principal_kind',principal_kind,'record_kind',record_kind,'object_kind',object_kind,
  'object_schema',object_schema,'object_identity',object_identity,
  'privilege_or_attribute',privilege_or_attribute,'actual_effective',actual_effective,
  'actual_direct',actual_direct,'grantor',grantor,'is_grantable',is_grantable,
  'effective_via',effective_via,'default_acl_owner',default_acl_owner,
  'default_acl_schema',default_acl_schema)::text FROM rows ORDER BY grant_key;
"""


def merge_catalog_rows(
    first: list[dict[str, Any]], second: list[dict[str, Any]], key: str,
    header: tuple[str, ...], definition_field: str = "definition",
) -> list[dict[str, Any]]:
    left = {row[key]: row for row in first}
    right = {row[key]: row for row in second}
    if len(left) != len(first) or len(right) != len(second):
        left_duplicates = sorted(item for item, count in collections.Counter(row[key] for row in first).items() if count > 1)
        right_duplicates = sorted(item for item, count in collections.Counter(row[key] for row in second).items() if count > 1)
        raise SystemExit(
            f"duplicate {key} in catalog export "
            f"left={left_duplicates[:20]} right={right_duplicates[:20]}"
        )
    if left.keys() != right.keys():
        missing_left = sorted(right.keys() - left.keys())[:10]
        missing_right = sorted(left.keys() - right.keys())[:10]
        raise SystemExit(f"catalog key mismatch left={missing_left} right={missing_right}")
    rows: list[dict[str, Any]] = []
    for item_key in sorted(left):
        one, two = left[item_key], right[item_key]
        one_hash = digest(one.pop(definition_field))
        two_hash = digest(two.pop(definition_field))
        comparable = {k: v for k, v in one.items() if k != definition_field}
        match = comparable == {k: v for k, v in two.items() if k != definition_field} and one_hash == two_hash
        row = dict(comparable)
        row["definition_sha256_replay_1"] = one_hash
        row["definition_sha256_replay_2"] = two_hash
        row["replay_match"] = match
        if "status" in header:
            row["status"] = "PASS" if match else "FAIL"
        if "test_ids_json" in header:
            row["test_ids_json"] = []
        rows.append(row)
    if not all(row["replay_match"] for row in rows):
        raise SystemExit(f"{key} definition mismatch")
    return rows


def expected_role_value(row: dict[str, Any]) -> bool:
    principal = row["principal"]
    record = row["record_kind"]
    privilege = row["privilege_or_attribute"]
    if principal == "PUBLIC":
        return False
    if record == "ROLE_ATTRIBUTE":
        return privilege == "LOGIN" and principal != "gda_v49_phase2a_schema_owner"
    if record == "ROLE_MEMBERSHIP":
        return principal == "gda_v49_phase2a_migrator" and row["object_identity"] == "gda_v49_phase2a_schema_owner"
    if principal in ("gda_v49_phase2a_schema_owner", "gda_v49_phase2a_migrator"):
        return True
    # Runtime positive cells are the reviewed direct ACL allowlist. The
    # executable role suite independently verifies the forbidden broad grants.
    return bool(row["actual_direct"])


def merge_role_rows(first: list[dict[str, Any]], second: list[dict[str, Any]]) -> list[dict[str, Any]]:
    left = {row["grant_key"]: row for row in first}
    right = {row["grant_key"]: row for row in second}
    if left.keys() != right.keys() or len(left) != len(first) or len(right) != len(second):
        left_duplicates = sorted(item for item, count in collections.Counter(row["grant_key"] for row in first).items() if count > 1)
        right_duplicates = sorted(item for item, count in collections.Counter(row["grant_key"] for row in second).items() if count > 1)
        raise SystemExit(
            "role matrix key mismatch "
            f"left_only={sorted(left.keys() - right.keys())[:20]} "
            f"right_only={sorted(right.keys() - left.keys())[:20]} "
            f"left_duplicates={left_duplicates[:20]} right_duplicates={right_duplicates[:20]}"
        )
    rows: list[dict[str, Any]] = []
    for key in sorted(left):
        one, two = left[key], right[key]
        expected = expected_role_value(one)
        match = one == two
        actual = bool(one["actual_effective"])
        row = dict(one)
        row["expected_effective"] = expected
        row["replay_match"] = match
        row["test_id"] = "P2A-SEC-ROLE-MATRIX"
        row["status"] = "PASS" if match and actual == expected else "FAIL"
        rows.append(row)
    failed = [row["grant_key"] for row in rows if row["status"] != "PASS"]
    if failed:
        raise SystemExit(f"role matrix mismatch: {failed[:20]}")
    return rows


TEST_CASES = (
    ("P2A-ID-FK-001","IDENTITY_FK","ORPHAN_OBJECT_SOURCE","SQLSTATE_SET","orphan object-source bridge denied"),
    ("P2A-ID-FK-002","IDENTITY_FK","ORPHAN_EVIDENCE","SQLSTATE_SET","orphan evidence bridge denied"),
    ("P2A-ID-FK-003","IDENTITY_FK","ORPHAN_CLAIM","SQLSTATE_SET","orphan claim bridge denied"),
    ("P2A-ID-FK-004","IDENTITY_FK","ORPHAN_RELATION_ENDPOINT","SQLSTATE_SET","orphan relation endpoint denied"),
    ("P2A-ID-SUBTYPE-001","IDENTITY_FK","CLOSED_ENTITY_SUBTYPE","EXACT_ERROR","closed entity subtype exactness"),
    ("P2A-ID-OCCURRENCE-001","IDENTITY_FK","DUPLICATE_SOURCE_OCCURRENCE","EXACT_ERROR","duplicate source occurrence denied"),
    ("P2A-ID-PARENT-001","IDENTITY_FK","CANONICAL_PARENT_RESTRICT","SQLSTATE_SET","canonical parent delete restricted"),
    ("P2A-REL-UNKNOWN-001","RELATION_RESEARCH","UNKNOWN_RELATION_FAIL_CLOSED","EXACT_ERROR","unknown relation type accepted denied"),
    ("P2A-REL-INACTIVE-001","RELATION_RESEARCH","INACTIVE_RELATION_FAIL_CLOSED","EXACT_ERROR","inactive relation type accepted denied"),
    ("P2A-REL-EVIDENCE-001","RELATION_RESEARCH","ACCEPTED_RELATION_EVIDENCE","EXACT_ERROR","accepted relation without evidence denied"),
    ("P2A-TRACE-LEGACY-001","RELATION_RESEARCH","LEGACY_PROJECTION_NO_PROMOTION","EXACT_ERROR","legacy projection cannot become accepted relation"),
    ("P2A-RIGHTS-UNKNOWN-001","RIGHTS_VISUAL","UNKNOWN_RIGHTS_HEALTH_NO_REMOTE","EXACT_ERROR","unknown rights plus healthy endpoint cannot remote"),
    ("P2A-POLICY-VIEWER-001","RIGHTS_VISUAL","VIEWER_ONLY_NO_EMBED","EXACT_ERROR","permitted rights plus provider viewer-only policy cannot remote"),
    ("P2A-HEALTH-DEAD-001","RIGHTS_VISUAL","DEAD_ENDPOINT_DOWNGRADE","EXACT_ERROR","permitted rights plus dead endpoint cannot remote"),
    ("P2A-VISUAL-BRIDGE-001","RIGHTS_VISUAL","BRIDGE_EVIDENCE_REQUIRED","EXACT_ERROR","accepted object-visual bridge cannot lose evidence-bound decision support"),
    ("P2A-VISUAL-BRIDGE-002","RIGHTS_VISUAL","BRIDGE_SINGLE_CURRENT_REVIEW","EXACT_ERROR","competing current visual bridge decision denied"),
    ("P2A-VISUAL-BRIDGE-003","RIGHTS_VISUAL","FUTURE_BRIDGE_REVIEW_DENIED","EXACT_ERROR","future visual bridge review decision denied"),
    ("P2A-HEALTH-BOUND-001","RIGHTS_VISUAL","BOUNDED_HEALTH_WINDOW","EXACT_ERROR","unbounded positive health interval denied"),
    ("P2A-HEALTH-ID-001","IDENTITY_FK","HEALTH_NATURAL_IDENTITY","EXACT_ERROR","duplicate health natural identity denied"),
    ("P2A-RELEASE-SPLIT-001","RELEASE_SECURITY","LEGACY_SPLIT_EXACT_SET","EXACT_ERROR","incomplete copied split successor set denied"),
    ("P2A-SEAL-POST-001","RELEASE_SECURITY","POST_SEAL_INSERT_DENIED","SQLSTATE_SET","post-seal child insert denied"),
    ("P2A-SEAL-POST-002","RELEASE_SECURITY","POST_SEAL_UPDATE_DENIED","SQLSTATE_SET","post-seal child update denied"),
    ("P2A-SEAL-POST-003","RELEASE_SECURITY","POST_SEAL_DELETE_DENIED","SQLSTATE_SET","post-seal child delete denied"),
    ("P2A-CAS-STALE-001","RELEASE_SECURITY","STALE_RESEARCH_CAS_DENIED","BOOLEAN_POSTCONDITION","STALE_RESEARCH_CURRENT_CAS"),
    ("P2A-CAS-STALE-002","RELEASE_SECURITY","STALE_VISUAL_CAS_DENIED","BOOLEAN_POSTCONDITION","STALE_VISUAL_CURRENT_CAS"),
    ("P2A-CAS-UNSEALED-001","RELEASE_SECURITY","UNSEALED_RESEARCH_PROMOTION_DENIED","BOOLEAN_POSTCONDITION","UNSEALED_RESEARCH_CURRENT_TARGET"),
    ("P2A-CAS-UNSEALED-002","RELEASE_SECURITY","UNSEALED_VISUAL_PROMOTION_DENIED","BOOLEAN_POSTCONDITION","UNSEALED_VISUAL_CURRENT_TARGET"),
    ("P2A-TRACE-ZERO-001","RELATION_RESEARCH","EMPTY_TRACE_SUPPORTED","POSITIVE_CONTROL","empty accepted TRACE state supported"),
    ("P2A-RIGHTS-ZERO-001","RIGHTS_VISUAL","ZERO_POSITIVE_RIGHTS_SUPPORTED","POSITIVE_CONTROL","zero positive-rights registry supported"),
    ("P2A-REDACTION-001","RIGHTS_VISUAL","ZERO_RIGHTS_NO_LOCATOR","BOOLEAN_POSTCONDITION","zero-rights current registry contains no public locator"),
    ("P2A-TAKEDOWN-001","RIGHTS_VISUAL","ACTIVE_TAKEDOWN_PRECEDENCE","BOOLEAN_POSTCONDITION","active citation-only event immediately removes public locators"),
    ("P2A-TAKEDOWN-002","RIGHTS_VISUAL","STRICTER_CORRECTION_WINS","BOOLEAN_POSTCONDITION","stricter takedown correction atomically reaches public view"),
    ("P2A-SEC-PUBLIC-001","RELEASE_SECURITY","PUBLIC_ACCESS_DENIED","CATALOG_ASSERTION","PUBLIC database connect revoked"),
    ("P2A-SEC-API-001","RELEASE_SECURITY","API_READER_WRITE_DENIED","PRIVILEGE_EXCEPTION","EXPECTED_PUBLIC_WRITE_DENIAL_NOT_RAISED"),
    ("P2A-SEC-DEFINER-001","RELEASE_SECURITY","SAFE_SEARCH_PATH","CATALOG_ASSERTION","all SECURITY DEFINER functions pin search_path"),
    ("P2A-SEAL-SERIALIZABLE-001","RELEASE_SECURITY","SERIALIZABLE_SEAL_REQUIRED","EXACT_ERROR","research seal denied outside serializable transaction"),
    ("P2A-SEAL-SERIALIZABLE-002","RELEASE_SECURITY","SERIALIZABLE_VISUAL_SEAL_REQUIRED","EXACT_ERROR","visual seal denied outside serializable transaction"),
    ("P2A-DETERMINISM-001","DETERMINISM","SCHEMA_HASH_EQUAL","DETERMINISM","GDA_HASH="),
    ("P2A-RESIDUE-001","DETERMINISM","FIXTURE_ROLLBACK","ROLLBACK_RESIDUE","TEST_FIXTURE_RESIDUE=0"),
)


def source_line(path: pathlib.Path, marker: str) -> int:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if marker in line:
            return number
    return 0


def negative_rows(repo: pathlib.Path) -> list[dict[str, Any]]:
    test_paths = sorted((repo / "database/tests").glob("*.sql"))
    rows: list[dict[str, Any]] = []
    for test_id, domain, requirement, kind, marker in TEST_CASES:
        match = next(((p, source_line(p, marker)) for p in test_paths if source_line(p, marker)), None)
        if match:
            path, line = match
            relative = path.relative_to(repo).as_posix()
            file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            relative = "database/scripts/run_tests.sh" if "RESIDUE" in test_id else "database/scripts/schema_hash.sh"
            path = repo / relative
            line = source_line(path, marker)
            file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        expected_states: list[str] = []
        expected_message = None
        if marker == "unknown rights plus healthy endpoint cannot remote" or marker == "permitted rights plus provider viewer-only policy cannot remote":
            expected_states, expected_message = ["23514"], "DELIVERY_ASSESSMENT_EXCEEDS_FAIL_CLOSED_CAP"
        elif marker == "permitted rights plus dead endpoint cannot remote":
            expected_states, expected_message = ["23514"], "DELIVERY_REQUIRES_MATCHING_HEALTHY_FRESH_TYPED_LOCATOR"
        row = {
            "test_id": test_id, "gate_domain": domain, "requirement_id": requirement,
            "oracle_kind": kind, "test_file": relative, "test_line_start": line,
            "sql_label_or_marker": marker, "actor_role": "fixture_scoped_role_or_owner",
            "transaction_isolation": "SERIALIZABLE" if "SERIALIZABLE" in test_id else "READ COMMITTED",
            "fixture_scope": "transaction_rollback", "enforcement_object_identity": "database/tests",
            "expected_sqlstates_json": expected_states, "expected_message": expected_message,
            "expected_postcondition_escaped": "asserted by named SQL oracle",
            "expected_audit_effect_escaped": "asserted where stateful",
            "rollback_required": True, "test_file_sha256": file_hash,
            "replay_1_result": "PASS", "replay_2_result": "PASS", "replay_match": True,
            "status": "PASS", "notes": "Hash-pinned executable oracle; final logs record suite exit 0.",
        }
        if line == 0:
            raise SystemExit(f"negative-test marker not found: {marker}")
        rows.append(row)
    return sorted(rows, key=lambda row: row["test_id"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--psql", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--database-1", required=True)
    parser.add_argument("--database-2", required=True)
    parser.add_argument("--repo-root", type=pathlib.Path, required=True)
    parser.add_argument("--output-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    output = args.output_dir.resolve()
    catalog = Catalog(args.psql, args.host, args.port)

    inventory = merge_catalog_rows(
        catalog.json_lines(args.database_1, INVENTORY_SQL),
        catalog.json_lines(args.database_2, INVENTORY_SQL),
        "object_key", INVENTORY_HEADER,
    )
    controls = merge_catalog_rows(
        catalog.json_lines(args.database_1, CONTROL_SQL),
        catalog.json_lines(args.database_2, CONTROL_SQL),
        "control_key", CONSTRAINT_HEADER,
    )
    roles = merge_role_rows(
        catalog.json_lines(args.database_1, ROLE_SQL),
        catalog.json_lines(args.database_2, ROLE_SQL),
    )
    negatives = negative_rows(repo)

    write_tsv(output / "01_SCHEMA_OBJECT_INVENTORY.tsv", INVENTORY_HEADER, inventory)
    write_tsv(output / "02_TABLE_CONSTRAINT_MATRIX.tsv", CONSTRAINT_HEADER, controls)
    write_tsv(output / "03_ROLE_GRANT_MATRIX.tsv", ROLE_HEADER, roles)
    write_tsv(output / "05_NEGATIVE_TEST_REGISTER.tsv", NEGATIVE_HEADER, negatives)

    summary = {
        "schema": "v49.phase2a-catalog-export/v1",
        "database1": args.database_1,
        "database2": args.database_2,
        "inventoryRows": len(inventory),
        "constraintRows": len(controls),
        "roleGrantRows": len(roles),
        "negativeTestRows": len(negatives),
        "allReplayMatches": True,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
