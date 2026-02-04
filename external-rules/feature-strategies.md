# Estrategias de Conversión por Feature Oracle

<purpose>
Estrategias arquitectónicas para convertir features complejas Oracle→PostgreSQL.
Consultar cuando plsql-converter encuentre objetos COMPLEX con features específicas.
</purpose>

---

<strategies>

## 1. PRAGMA AUTONOMOUS_TRANSACTION

<feature>
Transacciones autónomas (commits independientes del caller). ~40 objetos estimados.
</feature>

<options>
| Opción | Cuándo usar | Implementación |
|--------|-------------|----------------|
| **A: dblink** ✅ | Default | `dblink_exec()` con conexión separada |
| **B: Staging + pg_cron** | Logging no crítico | Tabla temporal + job asíncrono |
| **C: AWS Lambda** | Auditoría distribuida | Invocar Lambda para commit independiente |
</options>

<implementation strategy="A">
```sql
-- PostgreSQL (dblink)
CREATE OR REPLACE PROCEDURE log_audit(p_action VARCHAR) LANGUAGE plpgsql AS $$
BEGIN
  PERFORM dblink_exec('dbname=<db>',
    format('INSERT INTO audit_log VALUES (CURRENT_TIMESTAMP, %L)', p_action));
END; $$;
```
**Requiere:** Extensión `dblink`
</implementation>

---

## 2. UTL_HTTP (Llamadas HTTP)

<feature>
Cliente HTTP para consumir APIs externas. ~15 objetos estimados.
</feature>

<strategy>
**AWS Lambda** (cloud-native)
```
PostgreSQL → aws_lambda.invoke() → Lambda Function → HTTP API
```
</strategy>

<implementation>
```sql
-- PostgreSQL
CREATE FUNCTION http_get(p_url VARCHAR) RETURNS TEXT LANGUAGE plpgsql AS $$
DECLARE v_payload JSONB; v_response TEXT;
BEGIN
  v_payload := jsonb_build_object('url', p_url, 'method', 'GET');
  SELECT aws_lambda.invoke('arn:aws:lambda:...:http-client', v_payload::TEXT) INTO v_response;
  RETURN v_response;
END; $$;
```
**Requiere:** Lambda function + extensión `aws_lambda`
</implementation>

---

## 3. UTL_FILE (Operaciones de Archivos)

<feature>
Lectura/escritura de archivos. ~20 objetos estimados.
</feature>

<strategy>
**AWS S3** (cloud-native)
```
PostgreSQL ↔ aws_s3 ↔ S3 Bucket
```
</strategy>

<implementation>
```sql
-- Escribir a S3
SELECT aws_s3.query_export_to_s3('SELECT * FROM tabla',
  aws_commons.create_s3_uri('bucket', 'path/file.txt', 'us-east-1'));

-- Leer desde S3
SELECT aws_s3.table_import_from_s3('tmp_table', '', '(FORMAT CSV)',
  aws_commons.create_s3_uri('bucket', 'path/file.txt', 'us-east-1'));
```
**Requiere:** S3 bucket + extensión `aws_s3` + IAM role
</implementation>

---

## 4. DBMS_SQL (SQL Dinámico)

<feature>
Construcción y ejecución dinámica de SQL. ~30 objetos estimados.
</feature>

<strategy>
**EXECUTE** nativo de PostgreSQL (más simple que DBMS_SQL)
</strategy>

<implementation>
```sql
-- Oracle
v_cursor := DBMS_SQL.OPEN_CURSOR;
DBMS_SQL.PARSE(v_cursor, v_sql, DBMS_SQL.NATIVE);
DBMS_SQL.EXECUTE(v_cursor);

-- PostgreSQL (simplificado)
EXECUTE v_sql;
-- O con parámetros:
EXECUTE format('SELECT * FROM %I WHERE id = %L', table_name, id_value);
```
**Ventaja:** Sintaxis más simple, nativa de PostgreSQL.
</implementation>

---

## 5. OBJECT TYPES y Collections

<feature>
Tipos de objetos personalizados y colecciones. ~25 objetos estimados.
</feature>

<strategy>
**Composite Types + Arrays**
- OBJECT TYPE → Composite Type (`CREATE TYPE ... AS (...)`)
- TABLE OF → Array (`type[]`)
</strategy>

<implementation>
```sql
-- Oracle
TYPE t_employee IS OBJECT (id NUMBER, name VARCHAR2(100));
TYPE t_employees IS TABLE OF t_employee;

-- PostgreSQL
CREATE TYPE t_employee AS (id NUMERIC, name VARCHAR(100));
-- Usar como: t_employee[] para array
```
</implementation>

---

## 6. BULK COLLECT y FORALL

<feature>
Operaciones masivas optimizadas. ~35 objetos estimados.
</feature>

<strategy>
**Arrays + FOREACH**
- BULK COLLECT → `ARRAY(SELECT ...)`
- FORALL → `FOREACH ... IN ARRAY`
</strategy>

<implementation>
```sql
-- Oracle
BULK COLLECT INTO v_ids;
FORALL i IN v_ids.FIRST..v_ids.LAST
  UPDATE ...;

-- PostgreSQL
v_ids := ARRAY(SELECT id FROM tabla);
FOREACH v_id IN ARRAY v_ids LOOP
  UPDATE ...;
END LOOP;
```
</implementation>

---

## 7. PIPELINED FUNCTIONS

<feature>
Funciones que retornan filas incrementalmente. ~10 objetos estimados.
</feature>

<strategy>
**RETURNS SETOF + RETURN NEXT**
</strategy>

<implementation>
```sql
-- Oracle
FUNCTION get_data RETURN t_table PIPELINED IS ...

-- PostgreSQL
CREATE FUNCTION get_data() RETURNS SETOF t_row LANGUAGE plpgsql AS $$
BEGIN
  FOR rec IN SELECT * FROM tabla LOOP
    RETURN NEXT rec;
  END LOOP;
  RETURN;
END; $$;
```
</implementation>

---

## 8. CONNECT BY (Queries Jerárquicas)

<feature>
Consultas de relaciones padre-hijo. ~12 objetos estimados.
</feature>

<strategy>
**WITH RECURSIVE** (Common Table Expressions recursivas)
</strategy>

<implementation>
```sql
-- Oracle
SELECT * FROM tabla START WITH parent_id IS NULL CONNECT BY PRIOR id = parent_id;

-- PostgreSQL
WITH RECURSIVE jerarquia AS (
  SELECT * FROM tabla WHERE parent_id IS NULL  -- Base
  UNION ALL
  SELECT t.* FROM tabla t JOIN jerarquia j ON t.parent_id = j.id  -- Recursión
)
SELECT * FROM jerarquia;
```
</implementation>

---

## 9. PACKAGES → SCHEMAS

<feature>
Conversión completa de packages. ~50 packages estimados.
</feature>

<strategy>
**Schema + Functions/Procedures**
- Package → Schema
- Variables públicas → `set_config()` / `current_setting()`
- Constantes públicas → Replicar en cada función
- Tipos públicos → `CREATE TYPE schema.type`
</strategy>

<implementation>
```sql
-- Oracle
CREATE PACKAGE pkg IS
  C_VAL CONSTANT NUMBER := 100;
  PROCEDURE proc1;
END pkg;

-- PostgreSQL
CREATE SCHEMA pkg;
-- Constante: replicar en cada función que la usa
CREATE PROCEDURE pkg.proc1() ...;
```
**Nota:** Variables globales requieren sesión-level config con `set_config()`.
</implementation>

</strategies>

---

<decision-tree>

## Guía de Selección Rápida

**¿Qué feature tiene el objeto COMPLEX?**

1. **PRAGMA AUTONOMOUS_TRANSACTION** → Usar dblink
2. **UTL_HTTP** → Usar AWS Lambda
3. **UTL_FILE** → Usar AWS S3
4. **DBMS_SQL** → Usar EXECUTE nativo
5. **OBJECT TYPE** → Composite Type
6. **BULK/FORALL** → Arrays + FOREACH
7. **PIPELINED** → RETURNS SETOF
8. **CONNECT BY** → WITH RECURSIVE
9. **PACKAGE** → Schema + replicar constantes

</decision-tree>

---

**Versión:** 2.0 (optimizada con XML tags)
**Última Actualización:** 2026-02-03
**Cobertura:** 9 features complejas, ~237 objetos estimados
