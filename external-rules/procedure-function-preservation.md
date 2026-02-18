# Preservacion de Logica en Procedures y Functions

<purpose>
Guia para mantener logica de negocio intacta durante conversion Oracle→PostgreSQL.
</purpose>

---

<principles>

## Regla de Oro: **PRESERVAR > OPTIMIZAR**

El codigo Oracle puede tener logica de negocio no-obvia que parece redundante pero es critica.

**SIEMPRE preservar:**
- Estructura de condicionales (IF/ELSIF/ELSE) — NO simplificar con CASE/COALESCE
- Tipo de loop (FOR/WHILE/LOOP) — NO cambiar un tipo por otro
- Orden exacto de statements — NO combinar o reordenar
- Bloques EXCEPTION identicos — NO agregar/eliminar handlers
- Inicializacion de variables (NULL, 0, '') — NO cambiar valores iniciales
- Expresiones matematicas/logicas — NO simplificar (precision numerica critica)
- Valores por defecto en parametros — NO modificar

**NUNCA "mejorar" codigo** sin aprobacion explicita del usuario.

</principles>

---

<warnings>

## Trampas Comunes (EVITAR)

### Trampa 1: Simplificar logica "redundante"
```sql
-- Oracle (parece ineficiente pero puede tener razon de negocio)
IF v_status = 'A' THEN
  v_result := 'ACTIVE';
ELSIF v_status = 'I' THEN
  v_result := 'INACTIVE';
ELSE
  v_result := 'UNKNOWN';  -- Parece innecesario pero puede ser intencional
END IF;
```
**Accion:** Mantener EXACTO. NO simplificar con CASE o eliminar branches.

### Trampa 2: Cambiar tipo de dato "equivalente"
```sql
-- Oracle: VARCHAR2(1) para flag
v_flag VARCHAR2(1);

-- NO cambiar a: BOOLEAN
-- MANTENER: VARCHAR(1)
```
**Razon:** Aplicacion puede insertar 'S'/'N' directamente.

### Trampa 3: Optimizar queries
```sql
-- Oracle (query que parece ineficiente)
SELECT * INTO rec FROM tabla WHERE id = p_id;

-- NO optimizar a: SELECT id, name INTO ... (solo campos necesarios)
-- MANTENER: SELECT * INTO ...
```
**Razon:** Codigo posterior puede usar campos "no usados" en ciertos paths.

</warnings>

---

<checklist>

## Checklist de Preservacion

Antes de completar conversion, verificar:

- [ ] Estructura de condicionales identica (IF/ELSIF/ELSE)
- [ ] Tipo de loops preservado (FOR/WHILE/LOOP)
- [ ] Orden de statements mantenido
- [ ] Bloques EXCEPTION identicos
- [ ] Inicializacion de variables exacta
- [ ] Expresiones complejas sin simplificar
- [ ] Valores por defecto en parametros identicos
- [ ] Tipos de datos equivalentes (no "mejorados")
- [ ] No se agregaron/eliminaron statements
- [ ] Comentarios preservados intactos

</checklist>

---

**Version:** 3.0
**Ultima Actualizacion:** 2026-02-17
**Principio:** PRESERVAR logica de negocio > OPTIMIZAR codigo
**Cambios v3.0:** Condensado de 241 a ~90 lineas. Eliminados 7 ejemplos de codigo identico Oracle=PostgreSQL. Corregido ejemplo Trampa 1 (logicamente imposible). Agregado "Comentarios preservados" a checklist.
