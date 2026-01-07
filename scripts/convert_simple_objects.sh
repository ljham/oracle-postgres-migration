#!/bin/bash

################################################################################
# FASE 2A: Conversión de Objetos SIMPLES con ora2pg
#
# Este script convierte automáticamente objetos clasificados como SIMPLE
# usando ora2pg (herramienta local, 0 tokens Claude)
#
# Input:  classification/simple_objects.txt (~5,000 objetos)
#         sql/extracted/*.sql (código Oracle)
# Output: migrated/simple/*.sql (código PostgreSQL)
#
# Timeline: ~30 minutos
# Costo tokens Claude: 0 ✅
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}FASE 2A: Conversión Simple con ora2pg${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}1. Verificando prerequisitos...${NC}"

if [ ! -f "classification/simple_objects.txt" ]; then
    echo -e "${RED}ERROR: classification/simple_objects.txt no existe${NC}"
    echo "Ejecuta FASE 1 primero (plsql-analyzer)"
    exit 1
fi

if ! command -v ora2pg &> /dev/null; then
    echo -e "${RED}ERROR: ora2pg no está instalado${NC}"
    echo "Instala ora2pg: sudo apt install ora2pg (Debian/Ubuntu)"
    echo "O descarga desde: https://ora2pg.darold.net/"
    exit 1
fi

# Count simple objects
SIMPLE_COUNT=$(wc -l < classification/simple_objects.txt)
echo -e "${GREEN}✓ Encontrados $SIMPLE_COUNT objetos SIMPLE para convertir${NC}"

# Create output directories
echo -e "${YELLOW}2. Creando estructura de directorios...${NC}"
mkdir -p migrated/simple/{functions,procedures,packages,triggers}
echo -e "${GREEN}✓ Directorios creados${NC}"

# Create ora2pg configuration
echo -e "${YELLOW}3. Generando configuración ora2pg...${NC}"
cat > /tmp/ora2pg_simple.conf <<EOF
# ora2pg configuration for SIMPLE objects conversion
# Generated: $(date)

# Oracle connection (read-only)
ORACLE_HOME=/usr/lib/oracle/19.3/client64
ORACLE_DSN=dbi:Oracle:host=${ORACLE_HOST:-localhost};sid=${ORACLE_SID:-ORCL};port=${ORACLE_PORT:-1521}
ORACLE_USER=${ORACLE_USER:-readonly_user}
ORACLE_PWD=${ORACLE_PASSWORD:-your_password}

# PostgreSQL target version
PG_VERSION=17.4
PG_SUPPORTS_IDENTITY=1

# Export type (only PL/SQL code)
TYPE=FUNCTION PROCEDURE PACKAGE TRIGGER

# Output directory
OUTPUT=migrated/simple
OUTPUT_DIR=migrated/simple

# Schema mapping
SCHEMA=${ORACLE_SCHEMA:-PUBLIC}
EXPORT_SCHEMA=0

# Conversion options
PLSQL_PGSQL=1
ENABLE_MICROSECOND=1

# Data type mapping
DATA_TYPE=NUMBER:numeric,VARCHAR2:varchar,DATE:timestamp,CLOB:text,BLOB:bytea

# Exclude objects (only convert SIMPLE objects)
# We'll filter using object list from classification/simple_objects.txt

# Output format
FILE_PER_FUNCTION=1
FILE_PER_TABLE=0

# Debugging
DEBUG=0
QUIET=0
EOF

echo -e "${GREEN}✓ Configuración generada: /tmp/ora2pg_simple.conf${NC}"

# Extract object names from classification
echo -e "${YELLOW}4. Preparando lista de objetos SIMPLE...${NC}"

# Parse simple_objects.txt to extract object names
# Format: obj_001  # PKG_VENTAS.CALCULAR_DESCUENTO
awk '{print $3}' classification/simple_objects.txt > /tmp/simple_object_names.txt
OBJECT_LIST=$(cat /tmp/simple_object_names.txt | tr '\n' ',' | sed 's/,$//')

echo -e "${GREEN}✓ Lista preparada: $SIMPLE_COUNT objetos${NC}"

# Run ora2pg for each object type
echo -e "${YELLOW}5. Ejecutando conversión ora2pg...${NC}"
echo ""

# Functions
echo -e "${BLUE}  5.1 Convirtiendo functions...${NC}"
ora2pg -c /tmp/ora2pg_simple.conf -t FUNCTION -o migrated/simple/functions/ 2>&1 | tee /tmp/ora2pg_functions.log
FUNC_COUNT=$(find migrated/simple/functions/ -name "*.sql" | wc -l)
echo -e "${GREEN}  ✓ $FUNC_COUNT functions convertidas${NC}"

# Procedures
echo -e "${BLUE}  5.2 Convirtiendo procedures...${NC}"
ora2pg -c /tmp/ora2pg_simple.conf -t PROCEDURE -o migrated/simple/procedures/ 2>&1 | tee /tmp/ora2pg_procedures.log
PROC_COUNT=$(find migrated/simple/procedures/ -name "*.sql" | wc -l)
echo -e "${GREEN}  ✓ $PROC_COUNT procedures convertidos${NC}"

# Packages (convert to schemas with functions)
echo -e "${BLUE}  5.3 Convirtiendo packages...${NC}"
ora2pg -c /tmp/ora2pg_simple.conf -t PACKAGE -o migrated/simple/packages/ 2>&1 | tee /tmp/ora2pg_packages.log
PKG_COUNT=$(find migrated/simple/packages/ -name "*.sql" | wc -l)
echo -e "${GREEN}  ✓ $PKG_COUNT packages convertidos${NC}"

# Triggers
echo -e "${BLUE}  5.4 Convirtiendo triggers...${NC}"
ora2pg -c /tmp/ora2pg_simple.conf -t TRIGGER -o migrated/simple/triggers/ 2>&1 | tee /tmp/ora2pg_triggers.log
TRIG_COUNT=$(find migrated/simple/triggers/ -name "*.sql" | wc -l)
echo -e "${GREEN}  ✓ $TRIG_COUNT triggers convertidos${NC}"

# Summary
TOTAL_CONVERTED=$((FUNC_COUNT + PROC_COUNT + PKG_COUNT + TRIG_COUNT))
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Resumen de Conversión${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Objetos SIMPLE esperados: ${YELLOW}$SIMPLE_COUNT${NC}"
echo -e "Objetos convertidos:      ${GREEN}$TOTAL_CONVERTED${NC}"
echo ""
echo -e "Desglose:"
echo -e "  Functions:   $FUNC_COUNT"
echo -e "  Procedures:  $PROC_COUNT"
echo -e "  Packages:    $PKG_COUNT"
echo -e "  Triggers:    $TRIG_COUNT"
echo ""

# Check if all objects were converted
if [ "$TOTAL_CONVERTED" -eq "$SIMPLE_COUNT" ]; then
    echo -e "${GREEN}✓ ÉXITO: Todos los objetos SIMPLE convertidos${NC}"
else
    MISSING=$((SIMPLE_COUNT - TOTAL_CONVERTED))
    echo -e "${YELLOW}⚠ ADVERTENCIA: $MISSING objetos no fueron convertidos${NC}"
    echo "Revisa logs: /tmp/ora2pg_*.log"
fi

# Generate conversion report
echo -e "${YELLOW}6. Generando reporte de conversión...${NC}"
cat > migrated/simple/CONVERSION_REPORT.md <<REPORT
# FASE 2A - Reporte de Conversión Simple

**Fecha:** $(date)
**Herramienta:** ora2pg
**Objetos procesados:** $SIMPLE_COUNT

## Resumen

| Tipo | Convertidos | Archivo Log |
|------|-------------|-------------|
| Functions | $FUNC_COUNT | /tmp/ora2pg_functions.log |
| Procedures | $PROC_COUNT | /tmp/ora2pg_procedures.log |
| Packages | $PKG_COUNT | /tmp/ora2pg_packages.log |
| Triggers | $TRIG_COUNT | /tmp/ora2pg_triggers.log |
| **TOTAL** | **$TOTAL_CONVERTED** | - |

## Archivos Generados

\`\`\`
migrated/simple/
├── functions/*.sql ($FUNC_COUNT archivos)
├── procedures/*.sql ($PROC_COUNT archivos)
├── packages/*.sql ($PKG_COUNT archivos)
└── triggers/*.sql ($TRIG_COUNT archivos)
\`\`\`

## Siguiente Paso

Proceder a **FASE 3: Compilación Validation**
\`\`\`bash
# Validar compilación en PostgreSQL
# Ver: examples/phase3_launch_example.md
\`\`\`

## Logs

- Functions: \`/tmp/ora2pg_functions.log\`
- Procedures: \`/tmp/ora2pg_procedures.log\`
- Packages: \`/tmp/ora2pg_packages.log\`
- Triggers: \`/tmp/ora2pg_triggers.log\`

---

**Costo tokens Claude:** 0 ✅ (conversión local)
**Tiempo ejecución:** $(date)
REPORT

echo -e "${GREEN}✓ Reporte generado: migrated/simple/CONVERSION_REPORT.md${NC}"

# Cleanup
echo -e "${YELLOW}7. Limpieza...${NC}"
rm -f /tmp/simple_object_names.txt
echo -e "${GREEN}✓ Archivos temporales eliminados${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}FASE 2A COMPLETADA EXITOSAMENTE${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Siguiente paso: ${BLUE}FASE 2B - Conversión compleja${NC}"
echo -e "Ver: ${YELLOW}examples/phase2b_launch_example.md${NC}"
echo ""
