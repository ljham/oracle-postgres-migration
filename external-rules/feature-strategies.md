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
Uso principal en Oracle: registrar logs/auditoría que persistan incluso si la tx principal hace ROLLBACK.
</feature>

<options>
| Opción | Cuándo usar | Implementación |
|--------|-------------|----------------|
| **A: AWS Lambda** ✅ | **Default (SIEMPRE)** | `aws_lambda.invoke()` → Lambda → INSERT en tabla de log |

**⚠️ PROHIBIDO usar dblink** — afecta gestión de sesiones y genera problemas sistémicos en Aurora.
</options>

<implementation strategy="A">
```sql
-- Oracle (AUTONOMOUS_TRANSACTION)
CREATE OR REPLACE PROCEDURE p_registrar_log(p_accion VARCHAR2, p_error VARCHAR2) IS
  PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN
  INSERT INTO tabla_log (fecha, accion, error, usuario)
  VALUES (SYSDATE, p_accion, p_error, USER);
  COMMIT;
END;

-- PostgreSQL (aws_lambda — Aurora 17.4)
CREATE OR REPLACE PROCEDURE p_registrar_log(p_accion VARCHAR, p_error VARCHAR) LANGUAGE plpgsql AS $$
DECLARE
  v_payload JSONB;
  v_response TEXT;
BEGIN
  v_payload := jsonb_build_object(
    'table_name', 'tabla_log',
    'fecha', LOCALTIMESTAMP,
    'accion', p_accion,
    'error', p_error,
    'usuario', CURRENT_USER
  );
  BEGIN
    SELECT aws_lambda.invoke(
      'arn:aws:lambda:<region>:<account>:function:autonomous_log_writer',
      v_payload::TEXT
    ) INTO v_response;
  EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Fallo invocación Lambda autonomous_log_writer: %', SQLERRM;
  END;
END; $$;
```
**Requiere:** Extensión `aws_lambda` + Lambda function `autonomous_log_writer`
**Comportamiento:** La Lambda inserta en la misma tabla de log. Si la tx principal hace ROLLBACK, el log persiste (mismo comportamiento que AUTONOMOUS_TRANSACTION en Oracle).
**Si Lambda falla:** RAISE EXCEPTION notifica el error — NUNCA usar dblink como fallback.
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

## 6. PIPELINED FUNCTIONS

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

## 7. CONNECT BY (Queries Jerárquicas)

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

## 8. PACKAGES → SCHEMAS

<feature>
Conversión completa de packages. ~50 packages estimados.
</feature>

<strategy>
**Schema + Functions/Procedures + Getters/Setters para variables globales**
- Package → Schema (`CREATE SCHEMA`)
- Variables públicas (`Gv_*`, `Gi_*`) → Getter + Setter con `set_config()` / `current_setting()`
- Variables privadas (`Lv_*`) → Getter + Setter con prefijo `_` (`_get_lv_*`/`_set_lv_*`)
- Constantes públicas (`C_*`) → Replicar como literal en cada función que las usa
- Tipos públicos → `CREATE TYPE schema.type AS (...)`
- COMMIT/ROLLBACK dentro del package → **Preservar tal cual** (si tiene AUTONOMOUS_TRANSACTION → aws_lambda, ver sección #1)
</strategy>

<implementation>
```sql
-- Oracle package
CREATE PACKAGE pkg IS
  Gv_Schema   VARCHAR2(50) := 'latino_owner';
  Gi_MaxItems NUMBER := 100;
  C_VERSION   CONSTANT NUMBER := 2;
  TYPE t_row IS RECORD (id NUMBER, name VARCHAR2(100));
  PROCEDURE proc1;
END pkg;

-- PostgreSQL _create_schema.sql
CREATE SCHEMA IF NOT EXISTS pkg;
SET search_path TO latino_owner, pkg, public;

-- Tipos públicos
CREATE TYPE pkg.t_row AS (id NUMERIC, name VARCHAR(100));

-- Variables globales: Getter + Setter
CREATE OR REPLACE FUNCTION pkg.get_gv_schema() RETURNS VARCHAR LANGUAGE plpgsql AS $$
BEGIN RETURN COALESCE(current_setting('pkg.gv_schema', TRUE), 'latino_owner'); END; $$;

CREATE OR REPLACE FUNCTION pkg.set_gv_schema(p_value VARCHAR) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN PERFORM set_config('pkg.gv_schema', p_value, FALSE); END; $$;

CREATE OR REPLACE FUNCTION pkg.get_gi_maxitems() RETURNS NUMERIC LANGUAGE plpgsql AS $$
BEGIN RETURN COALESCE(current_setting('pkg.gi_maxitems', TRUE)::NUMERIC, 100); END; $$;

CREATE OR REPLACE FUNCTION pkg.set_gi_maxitems(p_value NUMERIC) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN PERFORM set_config('pkg.gi_maxitems', p_value::TEXT, FALSE); END; $$;

-- Procedimiento (constante replicada como literal)
CREATE OR REPLACE PROCEDURE pkg.proc1() LANGUAGE plpgsql AS $$
DECLARE
  v_version NUMERIC := 2;  -- C_VERSION replicado como literal
  v_schema  VARCHAR;
BEGIN
  v_schema := pkg.get_gv_schema();  -- Acceso a variable global via getter
  -- ...
END; $$;
```

**Reglas de naming para getters/setters:**
- `Gv_NombreVar` → `get_gv_nombrevars()` / `set_gv_nombrevar(p_value VARCHAR)`
- `Gi_Contador` → `get_gi_contador()` / `set_gi_contador(p_value NUMERIC)`
- Config key: `'{schema}.{variable_lowercase}'`
</implementation>

</strategies>

---

<decision-tree>

## Guía de Selección Rápida

**¿Qué feature tiene el objeto COMPLEX?**

1. **PRAGMA AUTONOMOUS_TRANSACTION** → Usar AWS Lambda (NUNCA dblink)
2. **UTL_HTTP** → Usar AWS Lambda
3. **UTL_FILE** → Usar AWS S3
4. **DBMS_SQL** → Usar EXECUTE nativo
5. **OBJECT TYPE** → Composite Type
6. **PIPELINED** → RETURNS SETOF
7. **CONNECT BY** → WITH RECURSIVE
8. **PACKAGE** → Schema + getters/setters (públicos + privados)

</decision-tree>

---

**Versión:** 2.1
**Última Actualización:** 2026-02-17
**Cobertura:** 8 features complejas, ~202 objetos estimados (BULK/FORALL movido a syntax-mapping.md)
