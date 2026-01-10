# Archivos Archivados

**Propósito:** Este directorio contiene archivos obsoletos, demos incompletas y documentación antigua que ya no se usa.

---

## Scripts Archivados

### scripts/prepare_migration_v3_improved.py
- **Estado:** Demo incompleta
- **Descripción:** Versión 3 con mejoras quirúrgicas al regex (nunca terminada)
- **Razón de archivo:** Las mejoras se integraron en v2.1
- **NO USAR:** Usar `scripts/prepare_migration_v2.py` (v2.1) en su lugar

### scripts/test_parsing_v2.py
- **Estado:** Test obsoleto
- **Descripción:** Script de pruebas para v2
- **Razón de archivo:** Ya no es necesario (validate_parsing.py lo reemplaza)
- **NO USAR:** Usar `scripts/validate_parsing.py` en su lugar

---

## Documentación Archivada

### docs/PARSING_ANALYSIS.md
- **Estado:** Obsoleto
- **Descripción:** Análisis inicial del parsing (2026-01-10)
- **Razón de archivo:** Consolidado en `docs/DESARROLLO.md` (sección Sistema de Parsing)
- **Referencia:** Ver `docs/DESARROLLO.md` para info actualizada

### docs/VALIDATION_REPORT.md
- **Estado:** Obsoleto
- **Descripción:** Reporte de validación inicial (2026-01-10)
- **Razón de archivo:** Consolidado en `docs/DESARROLLO.md` (sección Sistema de Parsing)
- **Referencia:** Ver `docs/DESARROLLO.md` para info actualizada

### docs/COMANDOS_GUIA.md
- **Estado:** Obsoleto
- **Descripción:** Guía de comandos slash (nunca implementados)
- **Razón de archivo:** Comandos slash no se implementaron
- **Referencia:** N/A

### docs/ARQUITECTURA.md
- **Estado:** Consolidado
- **Descripción:** Arquitectura del plugin, decisiones de diseño
- **Razón de archivo:** Consolidado en `docs/DESARROLLO.md` (sección Arquitectura)
- **Referencia:** Ver `docs/DESARROLLO.md`

### docs/ESTRATEGIA.md
- **Estado:** Consolidado
- **Descripción:** 4 fases de migración, timeline, experimentos
- **Razón de archivo:** Consolidado en `docs/GUIA_MIGRACION.md`
- **Referencia:** Ver `docs/GUIA_MIGRACION.md`

### docs/OBJETOS_CONTEXTO.md
- **Estado:** Consolidado
- **Descripción:** REFERENCE vs EXECUTABLE, estrategia de contexto
- **Razón de archivo:** Parte usuario → `docs/GUIA_MIGRACION.md`, parte técnica → `docs/DESARROLLO.md`
- **Referencia:** Ver ambos documentos consolidados

### docs/TRACKING_SYSTEM.md
- **Estado:** Consolidado
- **Descripción:** Sistema de progreso y reanudación
- **Razón de archivo:** Consolidado en `docs/GUIA_MIGRACION.md` (sección Sistema de Progreso)
- **Referencia:** Ver `docs/GUIA_MIGRACION.md`

### QUICKSTART.md
- **Estado:** Consolidado
- **Descripción:** Guía de inicio rápido (7 minutos)
- **Razón de archivo:** Contenido duplicado con `README.md` (sección Inicio Rápido) y `docs/GUIA_MIGRACION.md`
- **Referencia:** Ver `README.md` (sección "🚀 Inicio Rápido") para instalación rápida, `docs/GUIA_MIGRACION.md` para proceso completo

---

## Directorio Completo

```
archived/
├── README.md                                    ← Este archivo
├── QUICKSTART.md                                ← Consolidado (duplicado con README)
├── scripts/
│   ├── prepare_migration_v3_improved.py         ← Demo incompleta
│   └── test_parsing_v2.py                       ← Test obsoleto
└── docs/
    ├── ARQUITECTURA.md                          ← Consolidado
    ├── ESTRATEGIA.md                            ← Consolidado
    ├── OBJETOS_CONTEXTO.md                      ← Consolidado
    ├── TRACKING_SYSTEM.md                       ← Consolidado
    ├── PARSING_ANALYSIS.md                      ← Consolidado
    ├── VALIDATION_REPORT.md                     ← Consolidado
    └── COMANDOS_GUIA.md                         ← Obsoleto
```

---

## Política de Archivo

Archivos que van aquí:
- ✅ Demos incompletas
- ✅ Tests obsoletos
- ✅ Documentación consolidada/reemplazada
- ✅ Versiones antiguas de scripts

Archivos que NO van aquí:
- ❌ Scripts funcionales en producción
- ❌ Documentación actualizada
- ❌ Configuración del plugin

---

**Última Actualización:** 2026-01-10
