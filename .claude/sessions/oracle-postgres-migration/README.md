# Guía de Navegación - Documentación del Proyecto

**Proyecto:** Migración Oracle 19c → PostgreSQL 17.4 (Amazon Aurora)
**Objetos a migrar:** 8,122 objetos PL/SQL
**Timeline:** 3 meses
**Estado:** validated | ready-for-planning

---

## 🎯 Para Sub-agentes: Cómo Leer Esta Documentación

### Paso 1: Lectura Obligatoria Inicial

**SIEMPRE lee primero:** [`00_index.md`](./00_index.md)

Este archivo contiene:
- ✅ Resumen ejecutivo completo (257 líneas)
- ✅ Arquitectura en 5 fases
- ✅ Contexto crítico del proyecto
- ✅ Números clave y métricas
- ✅ Estado actual y próximos pasos
- ✅ Decisiones técnicas más importantes

**Este archivo es suficiente para entender el proyecto completo.** Lee los otros módulos solo si necesitas detalles específicos.

---

### Paso 2: Lectura Selectiva según tu Tarea

Según tu rol/tarea, lee los módulos adicionales que necesites:

| Tu Tarea | Módulos Recomendados | Orden Sugerido |
|----------|---------------------|----------------|
| **Planificación general** | Todos | 00 → 01 → 02 → 03 → 04 |
| **Análisis de código (Code Comprehension)** | 01, 02, 03, 04 | 00 → 01 → 02 → 04 |
| **Decisión de migración (Migration Strategist)** | 01, 02, 04 | 00 → 04 → 02 |
| **Implementación backend** | 02, 03, 04 | 00 → 03 → 04 → 02 |
| **Testing/Validación (QA)** | 02, 03 | 00 → 02 → 03 |
| **Investigación técnica** | 04, 03 | 00 → 04 → 03 |
| **Revisión de decisiones** | 04, 05 | 00 → 04 → 05 |
| **Debugging/troubleshooting** | 05, 04 | 00 → 05 → 04 |

---

## 📁 Estructura de Módulos

### [`00_index.md`](./00_index.md) - Resumen Ejecutivo (START HERE)
**Líneas:** 257 | **Tipo:** Resumen denso

**Contiene:**
- Problema y alcance del proyecto
- Arquitectura completa en 5 fases
- Decisiones técnicas críticas (7 decisiones)
- Números clave (8,122 objetos, 3 meses, etc.)
- Estado actual y próximos pasos
- Estructura de archivos del proyecto

**Cuándo leer:** SIEMPRE (obligatorio para todos los sub-agentes)

---

### [`01_problem_statement.md`](./01_problem_statement.md) - Problema y Objetivos
**Líneas:** 264 | **Tipo:** Análisis 5W1H

**Contiene:**
- Problem Statement completo (5W1H: Why, What, Who, When, Where, How)
- Jobs-to-be-Done (JTBD)
- Scope Definition (In/Out of scope)
- Assumptions y Constraints (⚠️ CRÍTICO: Aurora PostgreSQL managed service)
- Success Metrics (cuantitativas y cualitativas)
- Dependencies y Risks

**Cuándo leer:**
- ✅ Necesitas entender el "por qué" del proyecto
- ✅ Quieres ver criterios de éxito medibles
- ✅ Necesitas conocer constraints de Aurora PostgreSQL
- ✅ Vas a evaluar riesgos o dependencies

---

### [`02_user_stories.md`](./02_user_stories.md) - Épicas y User Stories
**Líneas:** 536 | **Tipo:** Requisitos funcionales

**Contiene:**
- 7 Épicas del proyecto (Epic 0-4)
- 25+ User Stories con criterios de aceptación
- Épicas: Infraestructura, Comprensión Semántica, Decisión Estratégica, Validación, Backend

**Cuándo leer:**
- ✅ Necesitas detalles específicos de funcionalidad
- ✅ Quieres ver criterios de aceptación para una feature
- ✅ Estás implementando una User Story específica
- ✅ Necesitas entender qué hace cada sub-agente

---

### [`03_architecture.md`](./03_architecture.md) - Diseño Técnico
**Líneas:** 353 | **Tipo:** Arquitectura del sistema

**Contiene:**
- Arquitectura completa del sistema (5 fases detalladas)
- Estructura de archivos del proyecto
- Flujo de ejecución detallado
- Integración con ora2pg
- Estrategia Claude Code Web vs CLI

**Cuándo leer:**
- ✅ Necesitas entender cómo funciona el sistema completo
- ✅ Quieres saber qué archivos se generan en cada fase
- ✅ Estás implementando parte de la arquitectura
- ✅ Necesitas entender flujos de datos

---

### [`04_decisions.md`](./04_decisions.md) - Decisiones Técnicas
**Líneas:** 464 | **Tipo:** Decisiones y conversiones

**Contiene:**
- 7 Decisiones técnicas críticas (con justificación)
- Mapeo de conversiones Oracle → PostgreSQL
- Tipos de datos, funciones, sintaxis SQL, PL/SQL → PL/pgSQL
- Decisiones sobre: Variables de estado, AUTONOMOUS_TRANSACTION, Vector DB, DIRECTORY→S3, UTL_HTTP→Lambda

**Cuándo leer:**
- ✅ Necesitas saber cómo convertir código Oracle a PostgreSQL
- ✅ Quieres entender por qué se tomó una decisión técnica
- ✅ Estás migrando código y necesitas referencia de conversión
- ✅ Necesitas mapeo de funciones Oracle → PostgreSQL

---

### [`05_changelog.md`](./05_changelog.md) - Historial de Cambios
**Líneas:** 333 | **Tipo:** Registro de evolución

**Contiene:**
- Historial completo de versiones (v1.1 a v2.1)
- Cambios críticos por versión
- Impacto de cada cambio
- Evolución de decisiones

**Cuándo leer:**
- ✅ Quieres entender cómo evolucionó el proyecto
- ✅ Necesitas ver el contexto de una decisión
- ✅ Estás debuggeando y quieres ver cambios recientes
- ✅ Necesitas trazabilidad de actualizaciones

---

## 🚀 Quick Start para Sub-agentes

### Escenario 1: Primera vez en el proyecto
```
1. Lee 00_index.md completo (obligatorio)
2. Identifica tu tarea específica
3. Consulta la tabla "Lectura Selectiva según tu Tarea"
4. Lee solo los módulos relevantes para tu tarea
```

### Escenario 2: Tarea específica ya asignada
```
1. Lee 00_index.md (sección relevante a tu tarea)
2. Lee el módulo específico que necesitas
3. Usa referencias cruzadas si necesitas contexto adicional
```

### Escenario 3: Debugging o investigación
```
1. Lee 00_index.md (contexto general)
2. Lee 05_changelog.md (cambios recientes)
3. Lee módulo específico relacionado con el issue
```

---

## ⚙️ Convenciones de Idioma

- **Documentación:** Español (este proyecto está en español)
- **Código:** Inglés (nombres de variables, funciones, clases)
- **Términos técnicos:** Sin traducir (endpoint, hook, middleware, etc.)

---

## 📊 Métricas de Contexto

| Módulo | Líneas | Tiempo Lectura Estimado |
|--------|--------|------------------------|
| 00_index.md | 257 | ~3 min |
| 01_problem_statement.md | 264 | ~3 min |
| 02_user_stories.md | 536 | ~6 min |
| 03_architecture.md | 353 | ~4 min |
| 04_decisions.md | 464 | ~5 min |
| 05_changelog.md | 333 | ~4 min |
| **Total si lees todo** | **2,207** | **~25 min** |

**Recomendación:** NO leas todo. Lee solo lo que necesitas según tu tarea (ahorra ~60-80% de tiempo).

---

## 🔗 Referencias Rápidas

- **Archivo principal:** [`../context_oracle-postgres-migration.md`](../context_oracle-postgres-migration.md)
- **Código Oracle extraído:** `../../sql/extracted/*.sql`
- **DDL PostgreSQL:** `../../sql/exported/*.sql`
- **Inventario de objetos:** `../../sql/extracted/inventory.md`

---

**Última actualización:** 2025-12-30
**Versión de documentación:** 2.1
**Framework:** Context Flow Optimization
