# Mapeo de Sintaxis Oracle → PostgreSQL

<purpose>
Referencia rápida de conversiones sintácticas Oracle→PostgreSQL para agente plsql-converter.
</purpose>

---

<mappings>

## Manejo de Errores

| Oracle | PostgreSQL | Notas |
|--------|-----------|-------|
| `RAISE_APPLICATION_ERROR(-20001, 'msg')` | `RAISE EXCEPTION 'msg'` | Sin código numérico |
| `$$plsql_unit` | `'nombre_literal'` | Reemplazo directo con nombre del objeto |
| `dbms_utility.format_error_backtrace` | `GET STACKED DIAGNOSTICS v_context = PG_EXCEPTION_CONTEXT` | Declarar `v_context TEXT` |
| `SQLERRM` | `SQLERRM` | Compatible |

**⚠️ CRÍTICO `$$plsql_unit`:** Reemplazar con literal directo, NO crear variable constante.

```sql
-- ✅ CORRECTO
BEGIN
  RAISE EXCEPTION 'Error en schema.proc_name: %', SQLERRM;
END;
```

---

## Fecha/Hora

| Oracle | PostgreSQL | Notas |
|--------|-----------|-------|
| `SYSDATE` | `LOCALTIMESTAMP` | Sin timezone (equivalente exacto) |
| `SYSTIMESTAMP` | `CURRENT_TIMESTAMP` | Con timezone |
| `TRUNC(date)` | `DATE_TRUNC('day', date)` | Truncar |
| `ADD_MONTHS(date, n)` | `date + INTERVAL 'n months'` | Sumar meses |
| `MONTHS_BETWEEN(d1, d2)` | `EXTRACT(YEAR FROM AGE(d1, d2)) * 12 + EXTRACT(MONTH FROM AGE(d1, d2))` | Diferencia |

---

## Manipulación de Datos

| Oracle | PostgreSQL |
|--------|-----------|
| `NVL(a, b)` | `COALESCE(a, b)` |
| `NVL2(a, b, c)` | `CASE WHEN a IS NOT NULL THEN b ELSE c END` |
| `DECODE(expr, v1, r1, default)` | `CASE expr WHEN v1 THEN r1 ELSE default END` |

---

## Secuencias

| Oracle | PostgreSQL |
|--------|-----------|
| `seq.NEXTVAL` | `nextval('seq'::regclass)` |
| `seq.CURRVAL` | `currval('seq'::regclass)` |

---

## Sintaxis Eliminada

| Oracle | PostgreSQL | Acción |
|--------|-----------|--------|
| `FROM DUAL` | — | Eliminar |
| `WITH READ ONLY` | — | Eliminar (vistas) |
| `FORCE` | — | Eliminar (CREATE VIEW) |

---

## Cursores y Loops

| Oracle | PostgreSQL | Notas |
|--------|-----------|-------|
| `CURSOR c IS SELECT ...` | `FOR var IN (SELECT ...) LOOP` | Query inline |
| Variable FOR loop *(implícita)* | `var RECORD` *(explícita DECLARE)* | **CRÍTICO** |

**Ejemplo FOR loop:**
```sql
-- PostgreSQL (variable OBLIGATORIA)
DECLARE
  reg RECORD;  -- ✅ Declarar siempre
BEGIN
  FOR reg IN (SELECT * FROM t) LOOP
    -- usar reg
  END LOOP;
END;
```

---

## Procedures y Functions

| Oracle | PostgreSQL | Notas |
|--------|-----------|-------|
| `PROCEDURE proc(p IN VARCHAR2)` | `PROCEDURE proc(p VARCHAR)` | Sin `IN`, sin `2` |
| `FUNCTION func RETURN NUMBER` | `FUNCTION func() RETURNS NUMERIC` | `()` obligatorio |
| `pkg.proc(...)` | `CALL schema.proc(...)` | `CALL` + schema |

**⚠️ CRÍTICO - CAST en CALL con literales:**
```sql
-- ✅ CORRECTO
CALL schema.proc(
  param => CAST('valor' AS VARCHAR),  -- Tipo explícito
  flag  => CAST('S' AS VARCHAR)
);
```
**Razón:** PostgreSQL no infiere tipo de literales de texto en named parameters.

---

## Packages → Schemas

| Oracle | PostgreSQL |
|--------|-----------|
| `CREATE PACKAGE pkg` | `CREATE SCHEMA pkg` |
| Variable pública `g_var` | Setter/Getter + `set_config()` / `current_setting()` |
| Constante pública `C_VAL` | Replicar en cada función |
| `TYPE t IS RECORD` | `CREATE TYPE pkg.t AS (...)` |

---

## PRAGMA AUTONOMOUS_TRANSACTION

| Estrategia | Uso |
|-----------|-----|
| **A: dblink** | Default (transacción separada) |
| **B: Staging + pg_cron** | Rediseño arquitectónico |
| **C: AWS Lambda** | Cloud-native async |

---

## Tipos de Colección

| Oracle | PostgreSQL |
|--------|-----------|
| `TABLE OF VARCHAR2 INDEX BY PLS_INTEGER` | `VARCHAR[]` (array) |
| `VARRAY(10) OF NUMBER` | `NUMERIC[]` (array) |
| `BULK COLLECT INTO v_arr` | `v_arr := ARRAY(SELECT ...)` |
| `FORALL i IN v_arr.FIRST..LAST` | `FOREACH elem IN ARRAY v_arr LOOP` |

</mappings>

---

<references>

**Para sintaxis NO listada:**
1. Consultar Context7: `/websites/postgresql_17`
2. Aplicar sintaxis oficial validada

</references>

---

**Versión:** 2.0 (optimizada con XML tags)
**Última Actualización:** 2026-02-03
**Compatibilidad:** Oracle 19c → PostgreSQL 17.4
