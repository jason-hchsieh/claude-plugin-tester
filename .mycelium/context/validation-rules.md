# Claude Code Plugin Validation Rules - Comprehensive Reference

**Research Date:** 2026-02-13
**Task:** Analyze plugin structure requirements from authoritative sources

---

## Overview

This document provides comprehensive validation rules for all Claude Code plugin component types, extracted from:
- plugin-dev official documentation
- The Complete Guide to Building Skills for Claude
- Real plugin examples (jasonhch-plugins, claude-plugins-official)
- plugin.json manifest schema from production plugins

**Coverage:** 6 component types with complete validation rules

---

## 1. SKILLS VALIDATION RULES

### YAML Frontmatter Schema

**Required fields:**
- `name` (string): kebab-case, 3-50 characters, lowercase, hyphens only
  - Examples: `my-skill` ✅, `My_Skill` ❌, `sk` ❌
- `description` (string): 10-1024 characters
  - MUST include what it does AND when to use it
  - MUST include specific trigger phrases
  - Third-person style preferred

**Optional fields:**
- `version` (string): Semantic version (e.g., "1.0.0")
- `license` (string): License identifier (MIT, Apache-2.0, etc.)
- `compatibility` (string): 1-500 characters, environment requirements
- `metadata` (object): Custom key-value pairs
- `allowed-tools` (string or array): Tool restrictions

**Security restrictions:**
- ❌ NO XML angle brackets (< >) in frontmatter
- ❌ NO "claude" or "anthropic" in skill name (reserved)

**Description requirements:**
```yaml
# ✅ Good
description: Analyzes Figma design files and generates developer handoff documentation. Use when user uploads .fig files, asks for "design specs", "component documentation", or "design-to-code handoff".

# ❌ Bad
description: Helps with design files.
```

### File Structure Requirements

**Mandatory:**
- `SKILL.md` - Exact case required (not skill.md or SKILL.MD)

**Optional subdirectories:**
- `scripts/` - Executable code (Python, Bash, etc.)
- `references/` - Documentation loaded as needed
- `examples/` - Working code examples
- `assets/` - Templates, fonts, icons

**Folder naming:**
- ✅ kebab-case: `notion-project-setup`
- ❌ Spaces: `Notion Project Setup`
- ❌ Underscores: `notion_project_setup`
- ❌ Capitals: `NotionProjectSetup`

**Forbidden:**
- ❌ NO README.md inside skill folder (use SKILL.md or references/)

### Progressive Disclosure Pattern

**Three-level hierarchy:**
1. **YAML frontmatter** - Always loaded (minimal triggering info)
2. **SKILL.md body** - Loaded when skill is relevant (core instructions)
3. **Linked files** - Additional files loaded as needed

**Best practices:**
- Keep SKILL.md body under 5,000 words (ideally 1,000-3,000)
- Move detailed docs to `references/`
- Link to references clearly

### Description Quality Standards

**Must include:**
- What the skill does (capability statement)
- When to use it (triggering conditions)
- Specific trigger phrases users might say
- Relevant file types (if applicable)

**Examples:**

```yaml
# ✅ Excellent
description: Manages Linear project workflows including sprint planning, task creation, and status tracking. Use when user mentions "sprint", "Linear tasks", "project planning", or asks to "create tickets".

# ✅ Good
description: Converts Markdown to PDF with custom styling. Use when user uploads .md files and asks to "generate PDF", "export to PDF", or "create document".

# 🟡 Okay (could be better)
description: Helps with PDF generation from Markdown files.

# ❌ Poor (too vague)
description: Helps with documents.
```

### Naming Conventions

**Skill folder and frontmatter name:**
- kebab-case required
- 3-50 characters
- Lowercase letters, numbers, hyphens only
- Must start/end with alphanumeric
- Folder name MUST match frontmatter `name` field

---

## 2. AGENTS VALIDATION RULES

### Frontmatter Schema

**Required fields:**
- `name` (string): Agent identifier
  - 3-50 chars, lowercase-hyphens only
  - Must start/end with alphanumeric
  - Examples: `code-reviewer` ✅, `ag` ❌ (too short), `_start` ❌
- `description` (string): 10-5,000 characters
  - MUST include triggering conditions
  - MUST include 2-6 `<example>` blocks
- `model` (string): "inherit", "sonnet", "opus", or "haiku"
- `color` (string): "blue", "cyan", "green", "yellow", "magenta", or "red"

**Optional fields:**
- `tools` (array): Allowed tools list

### Description Block Format (CRITICAL)

**Must include:**
1. Triggering statement ("Use this agent when...")
2. Multiple `<example>` blocks (2-4 recommended, max 6)
3. Each example with context, user request, assistant response
4. `<commentary>` explaining why agent triggers

**Complete example:**
```yaml
name: skill-reviewer
description: |
  Use this agent when the user has created or modified a skill and needs quality review, asks to "review my skill", "check skill quality", or "improve skill description".

  <example>
  Context: User just created a new skill
  user: "I've created a PDF processing skill"
  assistant: "Great! Let me review the skill quality."
  <commentary>
  Skill created, proactively trigger skill-reviewer to ensure it follows best practices.
  </commentary>
  assistant: "I'll use the skill-reviewer agent to review the skill."
  </example>

  <example>
  Context: User asks for skill improvement
  user: "Can you check if my skill description is good enough?"
  assistant: "I'll use the skill-reviewer agent to analyze your skill description."
  </example>
model: sonnet
color: cyan
tools: ["Read", "Grep", "Glob"]
```

### Tool Allowlist Validation

**Format:** Array of tool names
```yaml
tools: ["Read", "Write", "Grep", "Bash"]
```

**Common patterns:**
- Read-only: `["Read", "Grep", "Glob"]`
- Code generation: `["Read", "Write", "Grep", "Edit"]`
- Testing: `["Read", "Bash", "Grep"]`
- All tools: Omit field or use `["*"]`

**Best practice:** Limit to minimum needed (least privilege principle)

### Model Selection Rules

- `inherit` - Use parent's model (recommended default)
- `sonnet` - Balanced performance (standard)
- `opus` - Most capable, expensive (complex analysis)
- `haiku` - Fast, cheap (simple tasks)

### Color Guidelines

- **blue/cyan**: Analysis, review
- **green**: Success-oriented tasks
- **yellow**: Caution, validation
- **red**: Critical, security
- **magenta**: Creative, generation

Choose distinct colors for different agents in same plugin.

### System Prompt Quality Standards

**Structure requirements:**
- Written in second person ("You are...", "You will...")
- Define role and responsibilities
- Include step-by-step process
- Specify quality standards
- Define output format
- Address edge cases

**Length:**
- Minimum: 20 characters
- Recommended: 500-3,000 characters
- Maximum: 10,000 characters

**Example structure:**
```markdown
You are a [role] specializing in [domain].

**Your Core Responsibilities:**
1. [Primary responsibility]
2. [Secondary responsibility]

**Analysis Process:**
1. [Step one]
2. [Step two]

**Output Format:**
[What to provide and how to structure]

**Edge Cases:**
- [Case 1]: [How to handle]
```

---

## 3. COMMANDS VALIDATION RULES

### Frontmatter Schema

**All fields optional:**
- `description` (string): ~60 characters recommended, shown in `/help`
- `argument-hint` (string): Document expected arguments
  - Format: `[arg1] [arg2] [optional-arg]`
- `allowed-tools` (string or array): Tools command can use
- `model` (string): "sonnet", "opus", or "haiku"
- `disable-model-invocation` (boolean): Prevent programmatic invocation

**Description:**
- Keep under 60 characters for clean `/help` display
- Start with verb (Review, Deploy, Generate)
- Be specific about command purpose
- Default: First line of command prompt if not specified

**Argument-hint examples:**
- Simple: `[issue-number]`
- Multi-arg: `[pr-number] [priority] [assignee]`
- With options: `[test-pattern] [options]`

**Allowed-tools formats:**
- Single: `allowed-tools: Read`
- Comma-separated: `allowed-tools: Read, Write, Edit`
- Array: `allowed-tools: ["Read", "Write", "Bash(git:*)"]`
- Bash with filter: `Bash(git:*)`, `Bash(npm:*)`
- All: `"*"` (not recommended)

### Markdown Body Structure

**Command content = Instructions FOR Claude** (not messages TO user)

```markdown
# ✅ Correct (instructions for Claude)
Review this code for security vulnerabilities including:
- SQL injection
- XSS attacks
- Authentication issues

Provide specific line numbers and severity ratings.

# ❌ Incorrect (messages to user)
This command will review your code for security issues.
You'll receive a report with vulnerability details.
```

### File Reference Patterns

**Using @ syntax:**
```markdown
Review @$1 for:
- Code quality
- Best practices
```

**Multiple files:**
```markdown
Compare @src/old-version.js with @src/new-version.js
```

**Static references:**
```markdown
Review @package.json and @tsconfig.json for consistency
```

### CLAUDE_PLUGIN_ROOT Variable

**MUST use for portability:**
```markdown
# Execute script
!`bash ${CLAUDE_PLUGIN_ROOT}/scripts/analyze.sh $1`

# Load config
@${CLAUDE_PLUGIN_ROOT}/config/settings.json

# Use template
@${CLAUDE_PLUGIN_ROOT}/templates/report.md
```

**Why:** Ensures plugin works across all installations, no hardcoded paths

---

## 4. HOOKS VALIDATION RULES

### JSON Schema for hooks.json

**Plugin format (in `hooks/hooks.json`):**
```json
{
  "description": "Brief explanation of hooks (optional)",
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Stop": [...],
    "SubagentStop": [...],
    "SessionStart": [...],
    "SessionEnd": [...],
    "PreCompact": [...],
    "UserPromptSubmit": [...],
    "Notification": [...]
  }
}
```

**Key requirement:** `hooks` field is required wrapper containing event hooks

### Event Types

**Available events:**
- `PreToolUse` - Before tool execution (approve/deny/modify)
- `PostToolUse` - After tool execution (react to results)
- `Stop` - When main agent considers stopping
- `SubagentStop` - When subagent considers stopping
- `UserPromptSubmit` - When user submits prompt
- `SessionStart` - When session begins
- `SessionEnd` - When session ends
- `PreCompact` - Before context compaction
- `Notification` - When Claude sends notifications

### Hook Types

**Prompt-based hooks (recommended):**
```json
{
  "type": "prompt",
  "prompt": "Evaluate if this tool use is appropriate: $TOOL_INPUT",
  "timeout": 30
}
```
Supported events: Stop, SubagentStop, UserPromptSubmit, PreToolUse

**Command hooks:**
```json
{
  "type": "command",
  "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh",
  "timeout": 60
}
```
All events supported.

### Output Format Requirements

**Standard output (all hooks):**
```json
{
  "continue": true,
  "suppressOutput": false,
  "systemMessage": "Message for Claude"
}
```

**PreToolUse specific:**
```json
{
  "hookSpecificOutput": {
    "permissionDecision": "allow|deny|ask",
    "updatedInput": {"field": "modified_value"}
  },
  "systemMessage": "Explanation for Claude"
}
```

**Stop/SubagentStop specific:**
```json
{
  "decision": "approve|block",
  "reason": "Explanation",
  "systemMessage": "Additional context"
}
```

**Exit codes:**
- `0` - Success (stdout shown in transcript)
- `2` - Blocking error (stderr fed to Claude)
- Other - Non-blocking error

### Security Patterns

**Input validation:**
```bash
#!/bin/bash
set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name')

# Validate tool name format
if [[ ! "$tool_name" =~ ^[a-zA-Z0-9_]+$ ]]; then
  echo '{"decision": "deny", "reason": "Invalid tool name"}' >&2
  exit 2
fi
```

**Path safety:**
```bash
# Deny path traversal
if [[ "$file_path" == *".."* ]]; then
  echo '{"decision": "deny", "reason": "Path traversal detected"}' >&2
  exit 2
fi

# Deny sensitive files
if [[ "$file_path" == *".env"* ]] || [[ "$file_path" == *"secret"* ]]; then
  echo '{"decision": "deny", "reason": "Sensitive file"}' >&2
  exit 2
fi
```

**Quote all variables:**
```bash
# ✅ GOOD: Quoted
echo "$file_path"
cd "$CLAUDE_PROJECT_DIR"

# ❌ BAD: Unquoted (injection risk)
echo $file_path
cd $CLAUDE_PROJECT_DIR
```

### Matcher Patterns

**Exact match:**
```json
"matcher": "Write"
```

**Multiple tools (OR):**
```json
"matcher": "Read|Write|Edit"
```

**Wildcard:**
```json
"matcher": "*"
```

**Regex patterns:**
```json
"matcher": "mcp__.*__delete.*"
```

**Common patterns:**
- All MCP tools: `"mcp__.*"`
- Specific MCP plugin: `"mcp__plugin_asana_.*"`
- File operations: `"Read|Write|Edit"`
- Bash only: `"Bash"`

### Environment Variables

**Available in all command hooks:**
- `$CLAUDE_PROJECT_DIR` - Project root path
- `$CLAUDE_PLUGIN_ROOT` - Plugin directory (use for portable paths)
- `$CLAUDE_ENV_FILE` - SessionStart only: persist env vars here
- `$CLAUDE_CODE_REMOTE` - Set if running in remote context

**MUST use ${CLAUDE_PLUGIN_ROOT}:**
```json
{
  "type": "command",
  "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
}
```

### Timeout Standards

**Defaults:**
- Command hooks: 60 seconds
- Prompt hooks: 30 seconds

**Best practice:** Set explicit timeouts
```json
{
  "type": "command",
  "command": "bash script.sh",
  "timeout": 10
}
```

---

## 5. MCP CONFIGS VALIDATION RULES

### .mcp.json Schema

**Location:** Plugin root directory as `.mcp.json`

**Format:**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "executable-name",
      "args": ["-t", "stdio"],
      "env": {
        "ENV_VAR": "${ENV_VAR:-default_value}"
      }
    }
  }
}
```

**Real example:**
```json
{
  "mcpServers": {
    "gitea": {
      "command": "gitea-mcp",
      "args": ["-t", "stdio"],
      "env": {
        "GITEA_HOST": "${GITEA_HOST:-https://gitea.com}",
        "GITEA_TOKEN": "${GITEA_TOKEN}"
      }
    }
  }
}
```

### Server Types

**stdio (most common):**
```json
{
  "command": "server-binary",
  "args": ["-t", "stdio"]
}
```

**SSE/HTTP/WebSocket:**
```json
{
  "command": "server-binary",
  "args": ["-t", "sse", "--port", "3000"]
}
```

### Environment Variable Expansion

**Syntax:** `${VAR_NAME:-default_value}`

**Examples:**
- With default: `"${GITEA_HOST:-https://gitea.com}"`
- No default: `"${API_KEY}"`
- Required var: `"${REQUIRED_VAR}"`

**Best practice:** Always provide defaults when possible

### Authentication Config Patterns

**Token-based:**
```json
"env": {
  "API_TOKEN": "${SERVICE_API_TOKEN}"
}
```

**Multiple auth methods:**
```json
"env": {
  "API_KEY": "${SERVICE_API_KEY}",
  "API_SECRET": "${SERVICE_API_SECRET}",
  "BASE_URL": "${SERVICE_URL:-https://api.service.com}"
}
```

---

## 6. PLUGIN.JSON MANIFEST REQUIREMENTS

### Required Fields

**Minimal valid manifest:**
```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Brief description of plugin"
}
```

**Extended manifest:**
```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Brief description of plugin",
  "author": {
    "name": "Author Name",
    "email": "author@example.com"
  },
  "keywords": ["keyword1", "keyword2"],
  "license": "MIT",
  "hooks": {}
}
```

### Version Format

**Semantic versioning:** `MAJOR.MINOR.PATCH`
- Examples: `"1.0.0"`, `"0.3.0"`, `"2.1.5"`
- Must be string, not number
- Follow semver.org spec

### Auto-discovery Configuration

**Plugin structure auto-discovered:**
- `skills/` directory - All SKILL.md files discovered
- `agents/` directory - All .md files discovered
- `commands/` directory - All .md files discovered
- `hooks/hooks.json` - Hook configuration
- `.mcp.json` - MCP server configuration

**No explicit declaration needed** - Claude discovers automatically if present

### Dependencies Specification

**MCP server dependencies:**
```json
{
  "name": "plugin-name",
  "description": "Plugin that uses MCP",
  "metadata": {
    "mcp-server": "server-name",
    "requires": "server-binary"
  }
}
```

### Name Validation

**Rules:**
- kebab-case recommended
- Lowercase letters, numbers, hyphens
- No spaces, underscores, or capitals
- Must be unique

**Reserved names:**
- ❌ Cannot start with "claude-" or "anthropic-" (reserved)

### Author Field

**Simple:**
```json
"author": "Author Name"
```

**Extended:**
```json
"author": {
  "name": "Author Name",
  "email": "author@example.com",
  "url": "https://example.com"
}
```

### Keywords Field

**Format:** Array of strings
```json
"keywords": ["notifications", "ntfy", "remote", "alerts"]
```

**Best practices:**
- Use relevant, searchable terms
- Include use cases and technologies
- 3-10 keywords recommended
- Lowercase preferred

---

## CRITICAL VALIDATION PATTERNS

### Universal Naming Convention

**All component names (skills, agents, plugins):**
- ✅ kebab-case only: `my-component-name`
- ✅ Lowercase letters, numbers, hyphens
- ❌ NO spaces, underscores, capitals
- 3-50 characters
- Must start/end with alphanumeric

### File Naming Rules

- **Skills:** `SKILL.md` (exact case)
- **Agents:** `agent-name.md` (kebab-case)
- **Commands:** `command-name.md` (kebab-case)
- **Hooks:** `hooks.json` in `hooks/` directory
- **MCP:** `.mcp.json` in plugin root
- **Manifest:** `plugin.json` or in `.claude-plugin/` directory

### Progressive Disclosure Hierarchy

1. **Frontmatter** - Minimal, always loaded
2. **Main file body** - Loaded when relevant
3. **Reference files** - Loaded as needed

Apply primarily to skills, but also agents/commands for detailed docs.

### Security Rules Across All Components

- ❌ NO XML angle brackets in frontmatter
- ✅ Quote all bash variables
- ✅ Validate all inputs in hooks
- ✅ Use ${CLAUDE_PLUGIN_ROOT} for portability
- ✅ Set appropriate timeouts
- ✅ Follow principle of least privilege for tools

---

## PRE-PUBLICATION VALIDATION CHECKLIST

### Plugin Structure
- [ ] Plugin name is kebab-case
- [ ] Version follows semver (X.Y.Z)
- [ ] plugin.json has required fields (name, version, description)
- [ ] Author field properly formatted

### Skills
- [ ] SKILL.md exists (exact case)
- [ ] Frontmatter has name and description
- [ ] Description includes trigger phrases and when-to-use
- [ ] Folder name matches skill name in frontmatter
- [ ] No README.md in skill folder
- [ ] Name is kebab-case, 3-50 chars

### Agents
- [ ] Agent name is 3-50 chars, lowercase-hyphens
- [ ] Description includes 2-4 <example> blocks with <commentary>
- [ ] Model field is valid (inherit/sonnet/opus/haiku)
- [ ] Color field is valid (blue/cyan/green/yellow/magenta/red)
- [ ] System prompt is 500-3,000 chars (if used)
- [ ] Tools array properly formatted (if used)

### Commands
- [ ] Command body contains instructions FOR Claude (not TO user)
- [ ] argument-hint matches positional arguments ($1, $2, etc.)
- [ ] allowed-tools uses proper format (string or array)
- [ ] ${CLAUDE_PLUGIN_ROOT} used for all file references
- [ ] Description under 60 chars

### Hooks
- [ ] hooks.json has "hooks" wrapper object
- [ ] Hook types are "prompt" or "command"
- [ ] ${CLAUDE_PLUGIN_ROOT} used in all command paths
- [ ] Timeout values set appropriately (10-60s)
- [ ] Exit codes documented (0=success, 2=blocking)
- [ ] All variables quoted in scripts
- [ ] Input validation implemented

### MCP Configs
- [ ] .mcp.json in plugin root
- [ ] Environment variables use ${VAR:-default} syntax
- [ ] Command and args specified correctly
- [ ] Server name is descriptive

---

## VALIDATION RULE SUMMARY BY COMPONENT

| Component | File Name | Name Format | Required Fields | Key Validations |
|-----------|-----------|-------------|-----------------|-----------------|
| **Skill** | `SKILL.md` | kebab-case, 3-50 chars | name, description | Trigger phrases, progressive disclosure |
| **Agent** | `{name}.md` | kebab-case, 3-50 chars | name, description, model, color | <example> blocks, tool restrictions |
| **Command** | `{name}.md` | kebab-case | (all optional) | Instructions FOR Claude, ${CLAUDE_PLUGIN_ROOT} |
| **Hook** | `hooks.json` | N/A | hooks wrapper object | Security patterns, exit codes, timeouts |
| **MCP** | `.mcp.json` | N/A | mcpServers object | Env var expansion, server types |
| **Manifest** | `plugin.json` | kebab-case | name, version, description | Semver, auto-discovery |

---

**Document Version:** 1.0
**Last Updated:** 2026-02-13
**Sources:** plugin-dev, The Complete Guide, 14+ production plugins
**Coverage:** All 6 component types with production-tested validation rules
