# Mapeo de Sintaxis Oracle → PostgreSQL

**Propósito:** Referencia rápida de conversiones sintácticas Oracle→PostgreSQL.
**Uso:** Consultar cuando el agente converter necesite transformar sintaxis específica.

---

## Funciones de Manejo de Errores

| Oracle | PostgreSQL | Notas |
|--------|-----------|-------|
| `RAISE_APPLICATION_ERROR(-20001, 'msg')` | `RAISE EXCEPTION 'msg'` | Sin código numérico en PostgreSQL |
| `$$plsql_unit` | `'nombre_del_objeto'` | ⚠️ **Reemplazar directamente con literal** - NO crear variable constante |
| `dbms_utility.format_error_backtrace` | `GET STACKED DIAGNOSTICS v_context = PG_EXCEPTION_CONTEXT` | Declarar `v_context TEXT` en DECLARE |
| `SQLERRM` | `SQLERRM` | Compatible, mismo nombre |

**⚠️ IMPORTANTE - `$$plsql_unit`:**

PostgreSQL NO tiene equivalente directo a `$$plsql_unit`. La solución es simple: reemplazar directamente con el nombre del objeto donde se usa.

**❌ INCORRECTO - No crear variable constante:**
```sql
-- Oracle
BEGIN
  RAISE_APPLICATION_ERROR(-20001, 'Error en ' || $$plsql_unit || ': ' || SQLERRM);
END;

-- PostgreSQL INCORRECTO (NO hacer esto)
DECLARE
  v_object_name CONSTANT TEXT := 'schema_name.procedure_name';  -- ❌ Variable innecesaria
BEGIN
  RAISE EXCEPTION 'Error en %: %', v_object_name, SQLERRM;
END;
```

**✅ CORRECTO - Reemplazo directo:**
```sql
-- Oracle
BEGIN
  RAISE_APPLICATION_ERROR(-20001, 'Error en ' || $$plsql_unit || ': ' || SQLERRM);
END;

-- PostgreSQL CORRECTO (hacer esto)
BEGIN
  RAISE EXCEPTION 'Error en schema_name.procedure_name: %', SQLERRM;  -- ✅ Directo, sin variable
END;
```

**Razones:**
- PostgreSQL no tiene `$$plsql_unit` nativo
- Crear variable constante agrega complejidad innecesaria
- El nombre del objeto es conocido en tiempo de conversión
- Mantiene el código simple y directo

---

## Funciones de Fecha/Hora

| Oracle | PostgreSQL | Notas |
|--------|-----------|-------|
| `SYSDATE` | `LOCALTIMESTAMP` | Fecha y hora actual SIN timezone (equivalente exacto Oracle) |
| `SYSTIMESTAMP` | `CURRENT_TIMESTAMP` | Fecha y hora CON timezone |
| `TRUNC(date)` | `DATE_TRUNC('day', date)` | Truncar a día |
| `ADD_MONTHS(date, n)` | `date + INTERVAL 'n months'` | Sumar meses |
| `MONTHS_BETWEEN(d1, d2)` | `EXTRACT(YEAR FROM AGE(d1, d2)) * 12 + EXTRACT(MONTH FROM AGE(d1, d2))` | Diferencia en meses |

---

## Funciones de Manipulación de Datos

| Oracle | PostgreSQL | Notas |
|--------|-----------|-------|
| `NVL(a, b)` | `COALESCE(a, b)` | Primer valor no nulo |
| `NVL2(a, b, c)` | `CASE WHEN a IS NOT NULL THEN b ELSE c END` | Condicional nulo |
| `DECODE(expr, val1, res1, val2, res2, default)` | `CASE expr WHEN val1 THEN res1 WHEN val2 THEN res2 ELSE default END` | Switch |

---

## Secuencias

| Oracle | PostgreSQL | Notas |
|--------|-----------|-------|
| `sequence_name.NEXTVAL` | `nextval('sequence_name'::regclass)` | Obtener siguiente valor |
| `sequence_name.CURRVAL` | `currval('sequence_name'::regclass)` | Obtener valor actual |

---

## Sintaxis Eliminada (Sin Equivalente)

| Oracle | PostgreSQL | Acción |
|--------|-----------|--------|
| `FROM DUAL` | *(eliminar)* | No necesario en PostgreSQL |
| `WITH READ ONLY` | *(eliminar)* | De vistas, no necesario |
| `FORCE` | *(eliminar)* | De CREATE VIEW, no soportado |

---

## Cursores y Loops

| Oracle | PostgreSQL | Notas |
|--------|-----------|-------|
| `CURSOR c IS SELECT ...` | `FOR var IN (SELECT ...) LOOP` | No declarar cursor, usar query inline |
| Variable de FOR loop *(implícita)* | Variable de FOR loop: `var RECORD` *(explícita en DECLARE)* | **CRÍTICO:** PostgreSQL requiere declaración explícita |

**Ejemplo FOR loop (CRÍTICO):**

```sql
-- Oracle (variable implícita)
BEGIN
  FOR reg IN (SELECT * FROM t) LOOP
    -- usar reg
  END LOOP;
END;

-- PostgreSQL (variable explícita - OBLIGATORIA)
DECLARE
  reg RECORD;  -- ✅ SIEMPRE declarar
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
| `CREATE OR REPLACE PROCEDURE proc(p IN VARCHAR2)` | `CREATE OR REPLACE PROCEDURE proc(p VARCHAR)` | Sin `IN`, sin `2` en VARCHAR |
| `CREATE OR REPLACE FUNCTION func RETURN NUMBER` | `CREATE OR REPLACE FUNCTION func() RETURNS NUMERIC` | `RETURNS` con `S`, `()` obligatorio |
| Llamada a procedure: `pkg.proc(...)` | `CALL schema.proc(...)` | Usar `CALL`, schema explícito |

### ⚠️ CRÍTICO - Constantes Literales de Texto en Llamadas

**Problema:** PostgreSQL no puede inferir el tipo de constantes literales de texto en named parameters. Tipo `unknown` causa errores.

```sql
-- ❌ INCORRECTO - tipo "unknown"
CALL schema.procedure(
  param_varchar => '2rR9A9NbRXI=',  -- tipo: unknown ❌
  param_flag    => 'S'              -- tipo: unknown ❌
);

-- ✅ CORRECTO - CAST explícito
CALL schema.procedure(
  param_varchar => CAST('2rR9A9NbRXI=' AS VARCHAR),  ✅
  param_flag    => CAST('S' AS VARCHAR)              ✅
);
```

**Regla:** Cuando uses constantes literales de texto (`'...'`) como argumentos en `CALL`, siempre hacer `CAST('valor' AS VARCHAR)`.

**Aplica a:**
- Constantes de texto: `'valor'`, `'S'`, `'N'`, etc.
- Fechas hardcoded: `CAST('2024-01-01' AS DATE)`
- Números NO lo requieren: `123`, `45.67` (tipo inferido correctamente)

---

## Packages → Schemas

| Oracle | PostgreSQL | Estrategia |
|--------|-----------|-----------|
| `CREATE PACKAGE pkg IS ... END;` | `CREATE SCHEMA pkg;` | Package → Schema |
| Variable pública: `g_var VARCHAR2(100)` | Setter: `pkg.set_var()` + Getter: `pkg.get_var()` | Usar `set_config()` / `current_setting()` |
| Constante pública: `C_VAL CONSTANT NUMBER := 10` | Replicar en cada función que la usa | PostgreSQL no tiene package-level constants |
| Tipo público: `TYPE t IS RECORD(...)` | `CREATE TYPE pkg.t AS (...)` | Tipo compuesto en schema |

---

## PRAGMA AUTONOMOUS_TRANSACTION

| Oracle | PostgreSQL | Estrategia |
|--------|-----------|-----------|
| `PRAGMA AUTONOMOUS_TRANSACTION` | **Opción A:** `dblink_exec()` | Transacción separada via dblink |
| | **Opción B:** Tabla staging + pg_cron | Rediseño arquitectónico |
| | **Opción C:** AWS Lambda | Cloud-native async |

**Recomendación:** Opción A (dblink) por defecto.

---

## Tipos de Colección

| Oracle | PostgreSQL | Estrategia |
|--------|-----------|-----------|
| `TYPE t_arr IS TABLE OF VARCHAR2(100) INDEX BY PLS_INTEGER` | `CREATE TYPE t_arr AS (elems VARCHAR[])` | Array PostgreSQL |
| `TYPE t_arr IS VARRAY(10) OF NUMBER` | `CREATE TYPE t_arr AS (elems NUMERIC[])` | Array con límite lógico (no forzado) |
| `BULK COLLECT INTO v_arr` | `v_arr := ARRAY(SELECT ...)` | Coleccionar resultados en array |
| `FORALL i IN v_arr.FIRST..v_arr.LAST` | `FOREACH elem IN ARRAY v_arr LOOP ... END LOOP` | Iterar array |

---

## Referencias

**Cuando necesites sintaxis NO listada aquí:**

1. **Consultar Context7 PRIMERO:**
   ```python
   mcp__context7__query_docs(
       libraryId="/websites/postgresql_17",
       query="PostgreSQL 17 syntax for <feature>"
   )
   ```

2. **Revisar ejemplos prácticos** de Context7 (no solo teoría)

3. **Aplicar la sintaxis oficial** validada por Context7

---

**Última Actualización:** 2026-01-26
**Versión:** 1.0
**Compatibilidad:** Oracle 19c → PostgreSQL 17.4
