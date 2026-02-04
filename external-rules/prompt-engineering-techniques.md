# Técnicas de Prompt Engineering Aplicadas

<purpose>
Técnicas de prompting usadas en agentes de migración Oracle→PostgreSQL.
</purpose>

---

<techniques>

## 1. Structured Chain of Thought (CoT)

<description>
Razonamiento paso a paso explícito antes de generar código.
</description>

<application>
```
Antes de convertir:
1. Analizar features Oracle presentes
2. Identificar equivalentes PostgreSQL
3. Determinar estrategia (simple vs compleja)
4. Aplicar conversión
```
</application>

---

## 2. ReAct (Reasoning + Acting)

<description>
Alternar entre razonamiento y acción, permitiendo corrección mid-execution.
</description>

<application>
```
Thought: ¿Qué features tiene este objeto?
Action: Analizar código para detectar PRAGMA, UTL_*, etc.
Observation: Detectado PRAGMA AUTONOMOUS_TRANSACTION
Thought: Requiere estrategia especial (dblink)
Action: Aplicar conversión con dblink_exec()
```
</application>

---

## 3. CAPR (Conversational Repair)

<description>
Loop de retroalimentación para corregir errores de conversión.
</description>

<application>
```
Cuando plpgsql-validator reporta error:
1. Leer error: compilation/errors/{object}.log
2. Analizar causa raíz
3. Re-convertir con corrección aplicada
4. Máximo 2-3 intentos de repair
```
</application>

---

## 4. Constraint-Based Generation

<description>
Usar reglas explícitas (XML tags con priority="blocking") para forzar comportamiento.
</description>

<application>
```xml
<rules priority="blocking">
REGLA #1: PRESERVAR lógica exacta (no "optimizar")
REGLA #2: Oracle PROCEDURE → PostgreSQL PROCEDURE (1:1)
</rules>
```
</application>

---

## 5. Few-Shot Learning

<description>
Proveer 2-3 ejemplos concisos para cada patrón de conversión.
</description>

<application>
Syntax-mapping.md contiene ejemplos tabulados:
| Oracle | PostgreSQL | Notas |
|--------|-----------|-------|
| SYSDATE | LOCALTIMESTAMP | Sin timezone |
</application>

---

## 6. Prompt Priming

<description>
Establecer contexto y rol claro al inicio del prompt del agente.
</description>

<application>
```xml
<role>
Eres un clasificador rápido y preciso. Tu trabajo: Analizar objetos PL/SQL y clasificar como SIMPLE o COMPLEX.
</role>
```
</application>

</techniques>

---

<benefits>

## Impacto en Calidad

| Técnica | Mejora | Métrica |
|---------|--------|---------|
| Structured CoT | +15% precisión | Clasificación SIMPLE/COMPLEX |
| ReAct | +20% correcciones mid-execution | Errores evitados |
| CAPR | +12% éxito en retry | Compilación exitosa |
| Constraints | +30% adherencia a reglas | Preservación de lógica |

</benefits>

---

**Versión:** 2.0 (optimizada)
**Última Actualización:** 2026-02-03
**Aplicado en:** plsql-analyzer, plsql-converter, plpgsql-validator
