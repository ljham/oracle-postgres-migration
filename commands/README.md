# Comandos del Plugin Oracle → PostgreSQL Migration

Este directorio contiene los **slash commands** del plugin que facilitan el uso de los 4 agentes especializados.

## 📋 Comandos Disponibles

### 🔧 Comando de Utilidad

| Comando | Descripción | Uso Típico |
|---------|-------------|------------|
| `/init` | Inicializa proyecto (manifest, progress, directorios) | **Primera vez** antes de iniciar migración |
| `/status` | Muestra progreso general de todas las fases | **Cualquier momento** para ver estado |

### 🚀 Comandos de Fases (Orden de Ejecución)

| Fase | Comando | Descripción | Agente Invocado |
|------|---------|-------------|-----------------|
| **1** | `/analyze` | Analiza y clasifica objetos PL/SQL en SIMPLE/COMPLEX | `plsql-analyzer` |
| **2B** | `/convert` | Convierte objetos COMPLEX con estrategias arquitectónicas | `plsql-converter` |
| **3** | `/validate` | Valida compilación en PostgreSQL 17.4 | `compilation-validator` |
| **4** | `/test` | Ejecuta shadow testing Oracle vs PostgreSQL | `shadow-tester` |

**Nota:** Fase 2A (conversión SIMPLE) se ejecuta localmente con ora2pg, no usa comandos.

---

## 🎯 Flujo de Trabajo Completo

```bash
# 1. Inicializar proyecto (solo primera vez)
/init

# 2. Verificar estado inicial
/status

# 3. FASE 1: Análisis (5 horas)
/analyze next           # Procesar siguiente batch de 200 objetos
/analyze next           # Repetir hasta completar 8,122 objetos
/status 1               # Verificar progreso Fase 1

# 4. FASE 2A: Conversión Simple (30 min - LOCAL)
# Ejecutar manualmente:
bash scripts/convert_simple_objects.sh

# 5. FASE 2B: Conversión Compleja (5 horas)
/convert next           # Procesar siguiente batch de 200 objetos complejos
/convert next           # Repetir hasta completar ~3,122 objetos
/status 2               # Verificar progreso Fase 2

# 6. FASE 3: Validación (5 horas)
/validate next          # Validar siguiente batch de 200 objetos
/validate next          # Repetir hasta completar 8,122 objetos
/status 3               # Verificar progreso Fase 3

# 7. FASE 4: Shadow Testing (10 horas)
/test next              # Testear siguiente batch de 50 objetos
/test next              # Repetir hasta completar 8,122 objetos
/status 4               # Verificar progreso Fase 4

# 8. Verificar éxito completo
/status                 # Debe mostrar 100% en todas las fases
```

---

## 🔍 Anatomía de un Comando

Cada comando está definido en un archivo markdown con esta estructura:

```markdown
---
name: comando-nombre
description: Descripción corta del comando
arguments:
  - name: arg1
    description: Descripción del argumento
    required: false
    default: "valor-default"
---

# Comando: /comando-nombre

Descripción larga del comando...

## Uso
Ejemplos de uso...

## Lo que hace
Explicación detallada...

---

**PROMPT DE EJECUCIÓN:**

Este prompt es lo que Claude ejecuta cuando se invoca el comando.
Aquí se incluyen:
1. Verificaciones de pre-requisitos
2. Lógica de invocación del agente
3. Post-procesamiento de resultados
```

---

## 🤖 Cómo los Comandos Invocan Agentes

### Estructura del Prompt de Ejecución

Los comandos usan el **Tool `Task`** para invocar agentes. Ejemplo:

```markdown
**PROMPT DE EJECUCIÓN:**

Voy a ejecutar la **Fase 1: Análisis** usando el agente `plsql-analyzer`.

**Pasos:**

1. Verificar archivos fuente
2. Leer progress.json
3. **Invocar agente:**

   Usaré el Tool `Task` con:
   - `subagent_type`: "plsql-analyzer"
   - `prompt`: "Analizar batch {{batch}} objetos {{range}}"
   - `description`: "Analizar batch {{batch}}"

4. Actualizar progreso
5. Mostrar resumen
```

### Variables Dinámicas

Los comandos soportan variables que se reemplazan dinámicamente:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `{{batch}}` | Número de batch | `001`, `002`, `next` |
| `{{count}}` | Cantidad de objetos | `200`, `100`, `50` |
| `{{type}}` | Tipo de objetos | `simple`, `complex`, `all` |
| `{{strategy}}` | Estrategia de conversión | `UTL_HTTP`, `AUTONOMOUS_TRANSACTION` |
| `{{phase}}` | Fase específica | `1`, `2`, `3`, `4`, `all` |
| `{{mode}}` | Modo de operación | `unit`, `integration`, `both` |

---

## 📊 Directrices para Claude Code

Cuando Claude Code ejecuta un comando:

1. **Lee el frontmatter YAML** para entender argumentos y defaults
2. **Reemplaza variables** `{{arg}}` con valores proporcionados o defaults
3. **Ejecuta el prompt de ejecución** completo
4. **Invoca el agente correspondiente** usando Tool `Task`
5. **Procesa el resultado** del agente
6. **Muestra resumen** al usuario

### Ejemplo de Invocación Interna

```javascript
// Cuando el usuario ejecuta: /analyze 001
// Claude Code hace internamente:

const command = readCommand("commands/analyze.md");
const args = {
  batch: "001",           // Proporcionado por usuario
  count: "200"            // Default del comando
};

const prompt = replaceVariables(command.prompt, args);
// Resultado: "... batch 001 ... count 200 ..."

// Ejecutar prompt que contiene:
Task({
  subagent_type: "plsql-analyzer",
  prompt: "Analizar batch 001, objetos 1-200 desde sql/extracted/",
  description: "Analizar batch 001"
});
```

---

## 🎨 Beneficios de los Comandos

### ✅ Para el Usuario

- **Interfaz simple:** `/analyze` vs `Task plsql-analyzer "..."`
- **Argumentos con defaults:** No necesita recordar parámetros complejos
- **Validaciones automáticas:** El comando verifica pre-requisitos
- **Progreso automático:** Actualiza progress.json sin intervención

### ✅ Para Claude Code

- **Prompt estructurado:** El comando proporciona contexto completo
- **Invocación correcta:** Garantiza parámetros correctos al agente
- **Flujo guiado:** Sabe exactamente qué hacer en cada paso
- **Reutilizable:** Mismo comando funciona en todos los proyectos

### ✅ Para el Agente

- **Contexto completo:** Recibe toda la información necesaria
- **Archivos específicos:** Sabe exactamente qué archivos leer
- **Output estructurado:** Sabe dónde guardar resultados
- **Estado persistente:** Puede leer/actualizar progress.json

---

## 🔧 Creando Nuevos Comandos

### Plantilla Básica

```markdown
---
name: mi-comando
description: Descripción del comando
arguments:
  - name: arg1
    description: Descripción del argumento
    required: false
    default: "default-value"
---

# Comando: /mi-comando

Descripción larga...

## Uso
```bash
/mi-comando
/mi-comando arg1
```

---

**PROMPT DE EJECUCIÓN:**

Voy a ejecutar {{arg1}}...

**Pasos:**

1. Verificar pre-requisitos
2. Invocar agente si es necesario:
   ```
   Task({
     subagent_type: "nombre-agente",
     prompt: "...",
     description: "..."
   })
   ```
3. Post-procesar resultados
4. Mostrar resumen
```

### Registrar en plugin.json

```json
{
  "commands": [
    "commands/init.md",
    "commands/mi-comando.md",  ← Agregar aquí
    "..."
  ]
}
```

---

## 📚 Referencias

- [Claude Code Plugin Development](https://code.claude.com/docs/en/plugins)
- [Task Tool Documentation](https://code.claude.com/docs/en/tools/task)
- [YAML Frontmatter Specification](https://yaml.org/)

---

## 🆘 Troubleshooting

### Comando no reconocido

```bash
# Verificar que el comando está registrado
grep "mi-comando" .claude-plugin/plugin.json

# Reiniciar Claude Code para recargar plugin
```

### Variables no reemplazan

```bash
# Verificar sintaxis en el comando:
# ✅ Correcto: {{variable}}
# ❌ Incorrecto: {variable}, $variable, ${variable}
```

### Agente no se invoca

```bash
# Verificar que el agente está registrado
grep "nombre-agente" .claude-plugin/plugin.json

# Verificar sintaxis de invocación en el comando
```

---

**Última Actualización:** 2025-01-07
**Versión:** 1.0.0
