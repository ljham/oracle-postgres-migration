# Discovery Session: Oracle to PostgreSQL Migration Tool

## 1. Initial Request

El usuario necesita una herramienta basada en agentes de IA para migrar:
1. Codigo PL/SQL (Oracle 19c) a PL/pgSQL (PostgreSQL 17.4)
2. Codigo backend (Java, JavaScript, TypeScript, Python) que usa conexiones/ORMs de Oracle

> **📌 IMPORTANTE:** Este documento ha sido modularizado para optimizar el acceso de sub-agentes. Ver versión modular en:
> **[oracle-postgres-migration/](./oracle-postgres-migration/)** (6 módulos especializados)
>
> - **[00_index.md](./oracle-postgres-migration/00_index.md)** - Resumen ejecutivo DENSO + TOC (contexto completo)
> - **[01_problem_statement.md](./oracle-postgres-migration/01_problem_statement.md)** - 5W1H + JTBD + Scope
> - **[02_user_stories.md](./oracle-postgres-migration/02_user_stories.md)** - Épicas + User Stories
> - **[03_architecture.md](./oracle-postgres-migration/03_architecture.md)** - Diseño técnico
> - **[04_decisions.md](./oracle-postgres-migration/04_decisions.md)** - Decisiones clave
> - **[05_changelog.md](./oracle-postgres-migration/05_changelog.md)** - Historial de cambios
>
> **Para sub-agentes:**
> 1. **SIEMPRE lee primero:** `00_index.md` (contexto completo en ~257 líneas)
> 2. **Luego lee selectivamente:** Módulos específicos según tu tarea
> 3. **Consulta:** `README.md` para guía detallada de navegación por tarea
>
> **Nota:** La documentación completa está distribuida en los 6 módulos especializados (total: 2,207 líneas). Este archivo es solo el punto de entrada.

**Fecha:** 2025-12-23
**Estado:** validated | ready-for-planning
**Stakeholders:** Equipo de migracion dedicado, Desarrolladores senior, Arquitectos

---

**Documento creado por:** requirements-engineer (sub-agente)
**Fecha de creacion:** 2025-12-23
**Ultima actualizacion:** 2025-12-29
**Version:** 1.9
**Revision critica:** Claude Opus 4.5
**Estado:** ✅ Ready for Planning (Email Strategy Defined - AWS SES + Lambda)
