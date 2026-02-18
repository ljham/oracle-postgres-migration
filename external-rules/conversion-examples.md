# Ejemplos de Conversión Oracle → PostgreSQL

<purpose>
Ejemplos end-to-end de patrones comunes de conversion Oracle→PostgreSQL.
Archivo de REFERENCIA HUMANA — NO cargado automaticamente por el agente plsql-converter.
Consultar para validar que el agente aplique correctamente los patrones.
</purpose>

---

<examples>

## Ejemplo 1: PROCEDURE con parámetros OUT → INOUT

**Oracle:**
```sql
PROCEDURE get_patient_data(
  p_id    IN  NUMBER,
  p_name  OUT VARCHAR2,
  p_age   OUT NUMBER,
  p_error OUT VARCHAR2
) IS
BEGIN
  SELECT nombre, edad
    INTO p_name, p_age
    FROM pacientes
   WHERE id = p_id;
  p_error := NULL;
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    p_name  := NULL;
    p_age   := NULL;
    p_error := 'Paciente no encontrado';
  WHEN OTHERS THEN
    p_error := SQLERRM;
END;
```

**PostgreSQL:**
```sql
-- Migrated from Oracle 19c to PostgreSQL 17.4
-- Original: PROCEDURE PKG_PACIENTES.GET_PATIENT_DATA
SET search_path TO latino_owner, pkg_pacientes, public;

CREATE OR REPLACE PROCEDURE pkg_pacientes.get_patient_data(
  p_id    NUMERIC,
  INOUT p_name  VARCHAR DEFAULT NULL,   -- OUT → INOUT
  INOUT p_age   NUMERIC DEFAULT NULL,   -- OUT → INOUT
  INOUT p_error VARCHAR DEFAULT NULL    -- OUT → INOUT
) LANGUAGE plpgsql AS $$
BEGIN
  SELECT nombre, edad
    INTO STRICT p_name, p_age    -- STRICT: lanza NO_DATA_FOUND como Oracle
    FROM pacientes
   WHERE id = p_id;
  p_error := NULL;
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    p_name  := NULL;
    p_age   := NULL;
    p_error := 'Paciente no encontrado';
  WHEN OTHERS THEN
    p_error := SQLERRM;
END; $$;
```

**Cambios aplicados:**
- `OUT → INOUT` (REGLA #2)
- `SELECT INTO` → `SELECT INTO STRICT` (equivalencia con Oracle NO_DATA_FOUND)
- `NUMBER → NUMERIC`, `VARCHAR2 → VARCHAR`
- Header SQL con `SET search_path`
- Schema prefix `pkg_pacientes.`

---

## Ejemplo 2: FOR Loop con cursor implícito → RECORD explícito

**Oracle:**
```sql
PROCEDURE process_orders(p_date DATE) IS
BEGIN
  FOR reg IN (SELECT id, monto, estado FROM ordenes WHERE fecha = p_date) LOOP
    IF reg.estado = 'P' THEN
      UPDATE ordenes SET estado = 'A' WHERE id = reg.id;
    END IF;
  END LOOP;
END;
```

**PostgreSQL:**
```sql
CREATE OR REPLACE PROCEDURE schema_name.process_orders(
  p_date TIMESTAMP  -- DATE → TIMESTAMP
) LANGUAGE plpgsql AS $$
DECLARE
  reg RECORD;  -- ✅ OBLIGATORIO: declarar variable del FOR loop
BEGIN
  FOR reg IN (SELECT id, monto, estado FROM ordenes WHERE fecha = p_date) LOOP
    IF reg.estado = 'P' THEN
      UPDATE ordenes SET estado = 'A' WHERE id = reg.id;
    END IF;
  END LOOP;
END; $$;
```

**Cambios aplicados:**
- `DECLARE reg RECORD` — CRÍTICO, error #1 en migraciones (REGLA #5)
- `DATE → TIMESTAMP`

---

## Ejemplo 3: PRAGMA AUTONOMOUS_TRANSACTION + COMMIT → aws_lambda

**Oracle:**
```sql
PROCEDURE registrar_auditoria(
  p_objeto VARCHAR2,
  p_accion VARCHAR2,
  p_usuario VARCHAR2
) IS
  PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN
  INSERT INTO app_auditoria(fecha, objeto, accion, usuario)
  VALUES(SYSDATE, p_objeto, p_accion, p_usuario);
  COMMIT;  -- Commit en transacción autónoma
END;
```

**PostgreSQL (con aws_lambda — Aurora 17.4):**
```sql
CREATE OR REPLACE PROCEDURE schema_name.registrar_auditoria(
  p_objeto  VARCHAR,
  p_accion  VARCHAR,
  p_usuario VARCHAR
) LANGUAGE plpgsql AS $$
DECLARE
  v_payload JSONB;
  v_response TEXT;
BEGIN
  -- PRAGMA AUTONOMOUS_TRANSACTION → aws_lambda (NUNCA dblink)
  v_payload := jsonb_build_object(
    'table_name', 'app_auditoria',
    'fecha', LOCALTIMESTAMP,
    'objeto', p_objeto,
    'accion', p_accion,
    'usuario', p_usuario
  );
  BEGIN
    SELECT aws_lambda.invoke(
      'arn:aws:lambda:<region>:<account>:function:autonomous_log_writer',
      v_payload::TEXT
    ) INTO v_response;
  EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Fallo invocación Lambda autonomous_log_writer: %', SQLERRM;
  END;
  -- COMMIT eliminado: Lambda maneja su propia transacción independiente
END; $$;
```

**Cambios aplicados:**
- `PRAGMA AUTONOMOUS_TRANSACTION` → `aws_lambda.invoke()` (feature-strategies.md #1, NUNCA dblink)
- `SYSDATE → LOCALTIMESTAMP`
- `COMMIT → eliminado` (Lambda maneja su propia tx)
- `VARCHAR2 → VARCHAR`

---

## Ejemplo 4: Variable global de package → Getter/Setter en _create_schema.sql

**Oracle (package spec + body):**
```sql
-- Spec
CREATE PACKAGE mgm_k_config IS
  Gv_Schema    VARCHAR2(50) := 'latino_owner';
  Gi_MaxItems  NUMBER := 100;
  C_VERSION    CONSTANT NUMBER := 3;
END;

-- Body (uso en procedure)
PROCEDURE get_config_value(p_key VARCHAR2, p_value OUT VARCHAR2) IS
BEGIN
  p_value := Gv_Schema || '.' || p_key;  -- Uso de variable global
END;
```

**PostgreSQL — _create_schema.sql:**
```sql
CREATE SCHEMA IF NOT EXISTS mgm_k_config;
SET search_path TO latino_owner, mgm_k_config, public;

-- Getter/Setter para Gv_Schema
CREATE OR REPLACE FUNCTION mgm_k_config.get_gv_schema()
RETURNS VARCHAR LANGUAGE plpgsql AS $$
BEGIN
  RETURN COALESCE(current_setting('mgm_k_config.gv_schema', TRUE), 'latino_owner');
END; $$;

CREATE OR REPLACE FUNCTION mgm_k_config.set_gv_schema(p_value VARCHAR)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
  PERFORM set_config('mgm_k_config.gv_schema', p_value, FALSE);
END; $$;

-- Getter/Setter para Gi_MaxItems
CREATE OR REPLACE FUNCTION mgm_k_config.get_gi_maxitems()
RETURNS NUMERIC LANGUAGE plpgsql AS $$
BEGIN
  RETURN COALESCE(current_setting('mgm_k_config.gi_maxitems', TRUE)::NUMERIC, 100);
END; $$;

CREATE OR REPLACE FUNCTION mgm_k_config.set_gi_maxitems(p_value NUMERIC)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
  PERFORM set_config('mgm_k_config.gi_maxitems', p_value::TEXT, FALSE);
END; $$;
```

**PostgreSQL — get_config_value.sql:**
```sql
SET search_path TO latino_owner, mgm_k_config, public;

CREATE OR REPLACE PROCEDURE mgm_k_config.get_config_value(
  p_key   VARCHAR,
  INOUT p_value VARCHAR DEFAULT NULL  -- OUT → INOUT
) LANGUAGE plpgsql AS $$
DECLARE
  v_version NUMERIC := 3;  -- C_VERSION replicado como literal
BEGIN
  -- Gv_Schema → getter function
  p_value := mgm_k_config.get_gv_schema() || '.' || p_key;
END; $$;
```

**Cambios aplicados:**
- Variables globales `Gv_*`, `Gi_*` → Getters/Setters en `_create_schema.sql`
- Constante `C_VERSION` → literal en cada función que la usa
- `Gv_Schema` → `mgm_k_config.get_gv_schema()`
- `OUT → INOUT`

---

## Ejemplo 5: EXECUTE IMMEDIATE / DBMS_SQL → EXECUTE nativo

**Oracle:**
```sql
FUNCTION get_next_sequence(p_seq_name VARCHAR2) RETURN NUMBER IS
  v_result NUMBER;
  v_sql VARCHAR2(200);
BEGIN
  v_sql := 'SELECT ' || p_seq_name || '.NEXTVAL FROM DUAL';
  EXECUTE IMMEDIATE v_sql INTO v_result;
  RETURN v_result;
END;
```

**PostgreSQL:**
```sql
CREATE OR REPLACE FUNCTION schema_name.get_next_sequence(
  p_seq_name VARCHAR
) RETURNS NUMERIC LANGUAGE plpgsql AS $$
DECLARE
  v_result NUMERIC;
BEGIN
  -- EXECUTE IMMEDIATE → EXECUTE nativo de PostgreSQL
  -- seq.NEXTVAL FROM DUAL → nextval('seq'::regclass)
  EXECUTE format('SELECT nextval(%L::regclass)', p_seq_name)
    INTO v_result;
  RETURN v_result;
END; $$;
```

**Cambios aplicados:**
- `DBMS_SQL` / `EXECUTE IMMEDIATE` → `EXECUTE format(...)` (feature-strategies.md #4)
- `seq.NEXTVAL FROM DUAL` → `nextval('seq'::regclass)`
- `FROM DUAL → eliminado`
- `NUMBER → NUMERIC`, `VARCHAR2 → VARCHAR`
- `FUNCTION ... RETURN NUMBER → RETURNS NUMERIC`

</examples>

---

**Version:** 1.2
**Ultima Actualizacion:** 2026-02-17
**Cambios v1.2:** Agregado STRICT a SELECT INTO (Ejemplo 1), clarificado como archivo de referencia humana (no cargado por agente)
