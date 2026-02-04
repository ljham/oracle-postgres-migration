# Preservación de Lógica en Procedures y Functions

<purpose>
Guía para mantener lógica de negocio intacta durante conversión Oracle→PostgreSQL.
</purpose>

---

<principles>

## Regla de Oro: **PRESERVAR > OPTIMIZAR**

Durante la migración:
1. **✅ SIEMPRE:** Preservar lógica exacta de negocio
2. **❌ NUNCA:** "Mejorar" código sin aprobación explícita
3. **✅ SIEMPRE:** Mantener estructura if/else/loop idéntica
4. **✅ SIEMPRE:** Respetar orden de operaciones
5. **❌ NUNCA:** Simplificar expresiones "redundantes" (pueden ser intencionales)

**Razón:** El código Oracle puede tener lógica de negocio no-obvia que parece redundante pero es crítica.

</principles>

---

<rules>

## 1. Branches Condicionales (IF/ELSIF/ELSE)

<rule name="preserve-exact-structure">
**Mantener estructura EXACTA de condicionales**, incluso si parece redundante.
</rule>

```sql
-- Oracle (PRESERVAR COMO ESTÁ)
IF condicion1 THEN
  valor := 1;
ELSIF condicion2 THEN
  valor := 2;
ELSE
  valor := 0;
END IF;

-- PostgreSQL (MISMA ESTRUCTURA)
IF condicion1 THEN
  valor := 1;
ELSIF condicion2 THEN
  valor := 2;
ELSE
  valor := 0;
END IF;
```

**❌ NO simplificar** con CASE o COALESCE sin aprobación.

---

## 2. Loops (FOR/WHILE/LOOP)

<rule name="preserve-loop-type">
Mantener el TIPO de loop original (FOR no debe volverse WHILE, etc.).
</rule>

```sql
-- Oracle: FOR loop numérico
FOR i IN 1..10 LOOP ... END LOOP;

-- PostgreSQL: MISMO tipo de loop
FOR i IN 1..10 LOOP ... END LOOP;
```

---

## 3. Orden de Operaciones

<rule name="preserve-execution-order">
Mantener orden EXACTO de statements, incluso si parece optimizable.
</rule>

```sql
-- Oracle (orden específico)
v_total := 0;
SELECT SUM(amount) INTO v_total FROM tabla1;
v_final := v_total * 1.1;

-- PostgreSQL (MISMO orden)
v_total := 0;
SELECT SUM(amount) INTO v_total FROM tabla1;
v_final := v_total * 1.1;
```

**❌ NO combinar** en single statement sin aprobación.

---

## 4. Manejo de Excepciones

<rule name="preserve-exception-blocks">
Mantener bloques EXCEPTION idénticos. No agregar/eliminar handlers.
</rule>

```sql
-- Oracle
BEGIN
  ... lógica ...
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    resultado := 0;
  WHEN OTHERS THEN
    RAISE;
END;

-- PostgreSQL (MISMA estructura)
BEGIN
  ... lógica ...
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    resultado := 0;
  WHEN OTHERS THEN
    RAISE;
END;
```

---

## 5. Inicialización de Variables

<rule name="preserve-initialization">
Mantener valores iniciales EXACTOS (NULL, 0, '', etc.).
</rule>

```sql
-- Oracle
v_count NUMBER := 0;    -- Inicializado explícitamente
v_name VARCHAR2(100);   -- NULL implícito

-- PostgreSQL (MISMA inicialización)
v_count NUMERIC := 0;   -- Inicializado explícitamente
v_name VARCHAR(100);    -- NULL implícito
```

---

## 6. Expresiones Complejas

<rule name="preserve-complex-expressions">
NO simplificar expresiones matemáticas/lógicas complejas.
</rule>

```sql
-- Oracle (expresión compleja)
v_result := (v_a + v_b) * v_c / (v_d - v_e + 1);

-- PostgreSQL (IDÉNTICA)
v_result := (v_a + v_b) * v_c / (v_d - v_e + 1);
```

**Razón:** Orden de operaciones y precisión numérica pueden ser críticos.

---

## 7. Valores Por Defecto en Parámetros

<rule name="preserve-defaults">
Mantener valores por defecto EXACTOS en parámetros.
</rule>

```sql
-- Oracle
PROCEDURE proc(p_flag VARCHAR2 DEFAULT 'N', p_valor NUMBER DEFAULT 0)

-- PostgreSQL (MISMOS defaults)
CREATE PROCEDURE proc(p_flag VARCHAR DEFAULT 'N', p_valor NUMERIC DEFAULT 0)
```

</rules>

---

<warnings>

## ⚠️ Trampas Comunes (EVITAR)

### ❌ Trampa 1: "Simplificar" lógica redundante
```sql
-- Oracle (parece redundante pero puede tener razón de negocio)
IF v_status = 'A' THEN
  v_result := 'ACTIVE';
ELSIF v_status = 'A' THEN  -- Parece duplicado
  v_result := 'APPROVED';   -- Pero podría ejecutarse en ciertos casos
END IF;
```
**Acción:** Mantener EXACTO, documentar en comentario si tienes duda.

### ❌ Trampa 2: Cambiar tipo de dato "equivalente"
```sql
-- Oracle: VARCHAR2(1) para flag
v_flag VARCHAR2(1);

-- ❌ NO cambiar a: BOOLEAN
-- ✅ MANTENER: VARCHAR(1)
```
**Razón:** Aplicación puede insertar 'S'/'N' directamente.

### ❌ Trampa 3: Optimizar queries
```sql
-- Oracle (query que parece ineficiente)
SELECT * INTO rec FROM tabla WHERE id = p_id;

-- ❌ NO optimizar a: SELECT id, name INTO ... (solo campos necesarios)
-- ✅ MANTENER: SELECT * INTO ...
```
**Razón:** Código posterior puede usar campos "no usados" en ciertos paths.

</warnings>

---

<checklist>

## ✅ Checklist de Preservación

Antes de completar conversión, verificar:

- [ ] Estructura de condicionales idéntica (IF/ELSIF/ELSE)
- [ ] Tipo de loops preservado (FOR/WHILE/LOOP)
- [ ] Orden de statements mantenido
- [ ] Bloques EXCEPTION idénticos
- [ ] Inicialización de variables exacta
- [ ] Expresiones complejas sin simplificar
- [ ] Valores por defecto en parámetros idénticos
- [ ] Tipos de datos equivalentes (no "mejorados")
- [ ] No se agregaron/eliminaron statements

</checklist>

---

**Versión:** 2.0 (optimizada con XML tags)
**Última Actualización:** 2026-02-03
**Principio:** PRESERVAR lógica de negocio > OPTIMIZAR código
