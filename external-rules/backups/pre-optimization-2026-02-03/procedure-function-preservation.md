# Regla Crítica: Preservación Exacta de PROCEDURE vs FUNCTION

**Fecha:** 2026-02-01
**Versión:** 1.0
**Prioridad:** CRÍTICA - NUNCA VIOLAR

---

## 🎯 Objetivo

Preservar la estructura **EXACTA** de Oracle en PostgreSQL:
- Oracle PROCEDURE → PostgreSQL PROCEDURE
- Oracle FUNCTION → PostgreSQL FUNCTION
- **1:1 mapping sin crear objetos adicionales**

---

## ❌ ERROR COMÚN (PROHIBIDO)

```sql
-- Oracle: PROCEDURE con OUT parameter
CREATE OR REPLACE PROCEDURE p_test(
  p_in IN NUMBER,
  p_out OUT VARCHAR2
) IS
BEGIN
  p_out := 'resultado';
END;

-- ❌ CONVERSIÓN INCORRECTA (PROHIBIDA)
CREATE OR REPLACE FUNCTION p_test(
  p_in NUMERIC,
  OUT p_out VARCHAR
) RETURNS VARCHAR AS $$
...
```

**Por qué está mal:**
- Cambia PROCEDURE → FUNCTION
- Altera la arquitectura original
- Confunde la semántica del código

---

## ✅ CONVERSIÓN CORRECTA (OBLIGATORIA)

### Oracle PROCEDURE → PostgreSQL PROCEDURE

```sql
-- Oracle: PROCEDURE con parámetros IN/OUT
CREATE OR REPLACE PROCEDURE p_test(
  p_in IN NUMBER,
  p_out OUT VARCHAR2
) IS
BEGIN
  p_out := 'resultado';
END;

-- ✅ CONVERSIÓN CORRECTA
CREATE OR REPLACE PROCEDURE dafx_k_replica_usuarios_pha.p_test(
  p_in NUMERIC,
  INOUT p_out VARCHAR  -- OUT → INOUT en PostgreSQL
) LANGUAGE plpgsql AS $$
BEGIN
  p_out := 'resultado';
END;
$$;
```

**Cambios aplicados:**
1. ✅ Mantiene PROCEDURE
2. ✅ OUT → INOUT (requirement de PostgreSQL)
3. ✅ Preserva semántica original

---

### Oracle FUNCTION → PostgreSQL FUNCTION

```sql
-- Oracle: FUNCTION con RETURN
CREATE OR REPLACE FUNCTION calcular_total(p_id NUMBER)
RETURN NUMBER IS
  v_total NUMBER;
BEGIN
  SELECT SUM(monto) INTO v_total FROM ventas WHERE id = p_id;
  RETURN v_total;
END;

-- ✅ CONVERSIÓN CORRECTA
CREATE OR REPLACE FUNCTION dafx_k_replica_usuarios_pha.calcular_total(
  p_id NUMERIC
) RETURNS NUMERIC AS $$
DECLARE
  v_total NUMERIC;
BEGIN
  SELECT SUM(monto) INTO v_total FROM ventas WHERE id = p_id;
  RETURN v_total;
END;
$$ LANGUAGE plpgsql;
```

**Cambios aplicados:**
1. ✅ Mantiene FUNCTION
2. ✅ RETURN → RETURNS
3. ✅ Preserva semántica original

---

## 📋 Reglas de Conversión

### 1. Identificación del Tipo Original

**SIEMPRE leer del manifest.json:**
```json
{
  "object_type": "PROCEDURE"  // o "FUNCTION"
}
```

### 2. Parámetros IN/OUT/IN OUT

| Oracle | PostgreSQL PROCEDURE | PostgreSQL FUNCTION |
|--------|---------------------|---------------------|
| IN | IN | IN |
| OUT | INOUT | OUT (retorna) |
| IN OUT | INOUT | INOUT |

### 3. RETURN vs OUT Parameters

**PROCEDURE (sin RETURN):**
- Oracle: Usa OUT/IN OUT parameters
- PostgreSQL: Usa INOUT parameters + CALL

**FUNCTION (con RETURN):**
- Oracle: Usa RETURN + opcionalmente OUT
- PostgreSQL: Usa RETURNS + opcionalmente OUT

---

## 🔧 Sintaxis PostgreSQL PROCEDURE

### Básico (sin parámetros OUT)

```sql
CREATE OR REPLACE PROCEDURE schema.procedure_name(
  p_param1 NUMERIC,
  p_param2 VARCHAR
) LANGUAGE plpgsql AS $$
BEGIN
  -- Lógica...
END;
$$;

-- Llamada
CALL schema.procedure_name(123, 'valor');
```

### Con Parámetros INOUT

```sql
CREATE OR REPLACE PROCEDURE schema.procedure_name(
  p_in NUMERIC,
  INOUT p_out VARCHAR DEFAULT NULL  -- INOUT con valor inicial
) LANGUAGE plpgsql AS $$
BEGIN
  p_out := 'resultado: ' || p_in::TEXT;
END;
$$;

-- Llamada con variable
DO $$
DECLARE
  v_result VARCHAR;
BEGIN
  CALL schema.procedure_name(123, v_result);
  RAISE NOTICE 'Resultado: %', v_result;
END;
$$;
```

### Con Múltiples INOUT

```sql
CREATE OR REPLACE PROCEDURE schema.procedure_name(
  p_in NUMERIC,
  INOUT p_out1 VARCHAR DEFAULT NULL,
  INOUT p_out2 NUMERIC DEFAULT NULL,
  INOUT p_out3 TIMESTAMP DEFAULT NULL
) LANGUAGE plpgsql AS $$
BEGIN
  p_out1 := 'mensaje';
  p_out2 := 100;
  p_out3 := CURRENT_TIMESTAMP;
END;
$$;
```

---

## ⚠️ Diferencias Oracle vs PostgreSQL PROCEDURE

### 1. OUT vs INOUT

**Oracle:**
```sql
PROCEDURE p_test(p_out OUT VARCHAR2) IS
BEGIN
  p_out := 'valor';
END;
```

**PostgreSQL:**
```sql
-- OUT solo funciona en FUNCTION, no en PROCEDURE
-- Debe usar INOUT
CREATE OR REPLACE PROCEDURE p_test(
  INOUT p_out VARCHAR DEFAULT NULL  -- INOUT, no OUT
) LANGUAGE plpgsql AS $$
BEGIN
  p_out := 'valor';
END;
$$;
```

### 2. Llamada: EXECUTE vs CALL

**Oracle:**
```sql
DECLARE
  v_result VARCHAR2(100);
BEGIN
  p_test(v_result);  -- Llamada directa
END;
```

**PostgreSQL:**
```sql
DO $$
DECLARE
  v_result VARCHAR;
BEGIN
  CALL p_test(v_result);  -- CALL obligatorio
  RAISE NOTICE 'Resultado: %', v_result;
END;
$$;
```

### 3. RETURN en PROCEDURE

**Oracle:**
```sql
PROCEDURE p_test(p_out OUT VARCHAR2) IS
BEGIN
  IF error THEN
    RETURN;  -- Salir temprano
  END IF;
  p_out := 'ok';
END;
```

**PostgreSQL:**
```sql
CREATE OR REPLACE PROCEDURE p_test(
  INOUT p_out VARCHAR DEFAULT NULL
) LANGUAGE plpgsql AS $$
BEGIN
  IF error THEN
    RETURN;  -- OK, sale del procedure sin retornar valor
  END IF;
  p_out := 'ok';
END;
$$;
```

---

## 📊 Checklist de Validación

Antes de escribir el archivo convertido, verificar:

**A) Tipo de Objeto:**
- [ ] ¿Leíste `object_type` del manifest.json?
- [ ] ¿PROCEDURE Oracle → PROCEDURE PostgreSQL?
- [ ] ¿FUNCTION Oracle → FUNCTION PostgreSQL?

**B) Parámetros:**
- [ ] ¿OUT parameters → INOUT en PROCEDURE?
- [ ] ¿OUT parameters → OUT en FUNCTION?
- [ ] ¿IN parameters → IN en ambos?

**C) Sintaxis:**
- [ ] ¿PROCEDURE usa `LANGUAGE plpgsql AS $$`?
- [ ] ¿FUNCTION usa `RETURNS tipo AS $$`?
- [ ] ¿Parámetros INOUT tienen DEFAULT NULL?

**D) Estructura:**
- [ ] ¿1:1 mapping (mismo número de objetos)?
- [ ] ¿Sin objetos adicionales creados?
- [ ] ¿Nombres preservados?

---

## 🚫 Objetos Adicionales: Cuándo Crear y Notificar

### Regla: Solo Crear si Absolutamente Necesario

**Casos PERMITIDOS (con notificación):**

1. **Función Helper para Package:**
   ```sql
   -- Oracle usa $$PLSQL_UNIT → PostgreSQL necesita función
   CREATE OR REPLACE FUNCTION schema.get_package_name()
   RETURNS VARCHAR AS $$
   BEGIN
     RETURN 'schema';
   END;
   $$ LANGUAGE plpgsql IMMUTABLE;
   ```

   **NOTIFICACIÓN OBLIGATORIA:**
   ```markdown
   ⚠️ OBJETO ADICIONAL CREADO:
   - Nombre: get_package_name()
   - Razón: Reemplaza $$PLSQL_UNIT de Oracle (no existe en PostgreSQL)
   - Tipo: FUNCTION helper
   - Uso: Logging de errores en EXCEPTION blocks
   ```

2. **Secuencia para AUTO_INCREMENT:**
   ```sql
   -- Si Oracle usa SEQUENCE.NEXTVAL pero secuencia no existe
   CREATE SEQUENCE IF NOT EXISTS schema.seq_name START WITH 1;
   ```

   **NOTIFICACIÓN OBLIGATORIA:**
   ```markdown
   ⚠️ OBJETO ADICIONAL CREADO:
   - Nombre: seq_name
   - Razón: Secuencia referenciada pero no encontrada en manifest
   - Tipo: SEQUENCE
   - Uso: Generación de IDs
   ```

3. **Type Compuesto para OUT Multiple:**
   ```sql
   -- Si PROCEDURE tiene muchos OUT (>5) y mejora claridad
   CREATE TYPE schema.type_name AS (
     field1 VARCHAR,
     field2 NUMERIC,
     field3 TIMESTAMP
   );
   ```

   **NOTIFICACIÓN OBLIGATORIA:**
   ```markdown
   ⚠️ OBJETO ADICIONAL CREADO:
   - Nombre: type_name
   - Razón: Simplifica PROCEDURE con 6+ parámetros INOUT
   - Tipo: COMPOSITE TYPE
   - Uso: Agrupa valores de retorno
   ```

### Casos PROHIBIDOS (nunca crear):

- ❌ Convertir PROCEDURE → FUNCTION "porque es más fácil"
- ❌ Wrapper functions innecesarias
- ❌ Views intermedias sin justificación
- ❌ Schemas adicionales no solicitados

---

## 📝 Formato de Notificación

Cuando crees un objeto adicional, incluir en el log de conversión:

```markdown
## ⚠️ Objetos Adicionales Creados

### 1. get_package_name() - FUNCTION helper

**Razón:** PostgreSQL no tiene equivalente a $$PLSQL_UNIT de Oracle.

**Propósito:** Retorna el nombre del schema (package) para logging de errores.

**Ubicación:** sql/migrated/.../package_name/_helper_functions.sql

**Uso en código:**
```sql
-- Oracle
v_unit := $$PLSQL_UNIT;

-- PostgreSQL
v_unit := dafx_k_replica_usuarios_pha.get_package_name();
```

**Alternativa considerada:** Hardcodear el nombre del package en cada EXCEPTION.
**Por qué descartada:** Menos mantenible, propenso a errores.

**Aprobación:** ⏳ PENDIENTE (notificado al usuario)
```

---

## 🎯 Resumen Ejecutivo

**Regla de Oro:**
```
Oracle PROCEDURE → PostgreSQL PROCEDURE (INOUT parameters)
Oracle FUNCTION  → PostgreSQL FUNCTION (RETURNS + OUT)
1 Package Oracle = 1 Schema PostgreSQL (mismo # objetos)
```

**Excepciones permitidas:**
- Función helper (get_package_name) - CON NOTIFICACIÓN
- Secuencia faltante - CON NOTIFICACIÓN
- Type compuesto (>5 INOUT) - CON NOTIFICACIÓN

**Excepciones prohibidas:**
- Cambiar PROCEDURE → FUNCTION
- Crear wrappers innecesarios
- Alterar arquitectura original

**Validación:**
- SIEMPRE leer object_type del manifest.json
- NUNCA asumir que OUT parameter = FUNCTION
- SIEMPRE preservar 1:1 mapping

---

**Última actualización:** 2026-02-01
**Autor:** Sistema de Migración Oracle→PostgreSQL v2.0
**Status:** REGLA CRÍTICA - NUNCA VIOLAR
