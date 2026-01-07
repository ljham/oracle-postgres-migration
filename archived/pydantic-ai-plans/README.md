# Planes Archivados - Pydantic AI

**Fecha de archivo:** 2025-01-05

## ¿Por qué estos planes fueron archivados?

Estos planes fueron creados entre el 2024-12-30 y 2025-01-03 para una estrategia de migración Oracle → PostgreSQL usando **Pydantic AI agents con API de Anthropic**.

## Razón del Cambio de Estrategia

**Descubrimiento del 2025-01-05:**
- El proyecto cuenta con suscripción **Claude Code Pro ($20/mes)**
- NO hay presupuesto para API de Anthropic (~$30-150 USD adicionales)
- Claude Code CLI/Web con sub-agentes nativos es suficiente y NO requiere API

**Tecnología Original (Pydantic AI):**
- Requiere API de Anthropic (pago por tokens)
- Aplicaciones Python autónomas con Pydantic AI
- Agentes ejecutándose 24/7 de forma independiente
- Checkpoints programáticos automáticos
- Infraestructura AWS para agentes autónomos

**Tecnología Actual (Claude Code CLI/Web):**
- Suscripción Claude Code Pro (ya pagada)
- Sub-agentes nativos de Claude Code
- Ejecución interactiva (no 24/7)
- Sin necesidad de infraestructura AWS adicional
- ~50 mensajes cada 5 horas
- 20+ sub-agentes en paralelo (confirmado experimentalmente)

## Contenido Archivado

### 1. `00_PLAN_CONSOLIDADO.md`
Plan maestro para implementación con Pydantic AI agents:
- Agentes autónomos para análisis, conversión, validación
- Uso de API de Anthropic
- Checkpoints programáticos
- Workflow de 4 fases con agentes independientes

### 2. `plan_pydantic_ai_agents.md`
Diseño detallado de agentes Pydantic AI:
- Arquitectura de agentes autónomos
- System prompts para cada tipo de agente
- Herramientas personalizadas (tools)
- Inyección de dependencias
- Patrones de retry y error handling

### 3. `plan_backend_logic.md`
Infraestructura AWS para agentes autónomos:
- Lambda functions para agentes
- S3 para almacenamiento de estado
- DynamoDB para checkpoints
- EventBridge para scheduling
- Step Functions para orquestación

### 4. `plan_testing_strategy.md`
Framework de testing para agentes:
- Shadow testing automático
- Unit tests para agentes Pydantic AI
- Integration tests con mocks de API
- Estrategia de testing continuo

## Conocimiento Preservado

El conocimiento valioso NO se perdió. Está preservado en:

### 📁 `.claude/sessions/oracle-postgres-migration/`
- `00_index.md` - Resumen ejecutivo, números clave, estado actual
- `01_problem_statement.md` - 5W1H, JTBD, Scope, Assumptions, Constraints
- `02_user_stories.md` - 7 Épicas + 25+ User Stories + Criterios de Aceptación
- `04_decisions.md` - 10 Decisiones técnicas críticas (AUTONOMOUS_TRANSACTION, UTL_HTTP, etc.)
- `05_changelog.md` - Historial de versiones
- `README.md` - Guía de navegación

### 📄 `.claude/ESTRATEGIA_MIGRACION.md`
Estrategia actual usando Claude Code CLI/Web:
- Workflow en 4 fases
- Timeline: 25.5 horas sobre 5-6 sesiones
- Uso de ora2pg para objetos SIMPLES (gratis)
- Sub-agentes Claude para objetos COMPLEX
- Integración con pgvector para embeddings
- Resultados experimentales (20 sub-agentes en paralelo)

## ¿Estos planes son totalmente inútiles?

**NO.** Aunque están archivados, contienen:

✅ **Conceptos aprovechables:**
- Framework de shadow testing (aplicable a cualquier estrategia)
- Criterios de clasificación SIMPLE vs COMPLEX
- Estrategias de conversión de features Oracle
- Patrones de validación de compilación

✅ **Investigación valiosa:**
- Análisis profundo de features Oracle problemáticas
- Decisiones arquitectónicas documentadas
- Esfuerzo de investigación considerable

✅ **Referencia histórica:**
- Entender evolución de decisiones del proyecto
- Aprender de enfoques descartados
- Recuperar conceptos si cambia la estrategia futura

## Estrategia Actual

Ver documentos maestros:
- **`.claude/ESTRATEGIA_MIGRACION.md`** - Estrategia completa actual
- **`.claude/PLAN_REORGANIZACION.md`** - Este plan de reorganización
- **`.claude/CLAUDE.md`** - Configuración actualizada del proyecto

---

**Archivado por:** Claude Sonnet 4.5
**Fecha:** 2025-01-05
**Razón:** Cambio de Pydantic AI (API) a Claude Code CLI/Web (suscripción)
