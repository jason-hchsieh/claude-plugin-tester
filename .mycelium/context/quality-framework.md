# Quality Scoring Framework for Claude Code Plugins

**Framework Version:** 1.0
**Created:** 2026-02-13
**Task:** Define quality dimensions & metrics for plugin testing framework

---

## Overview

This framework provides a comprehensive, objective quality scoring system for Claude Code plugins, producing actionable scores on a 0-100 scale across multiple dimensions. It supports both framework-provided validators and user-authored tests.

**Design Principles:**
1. **Comprehensive**: Covers all quality aspects
2. **Actionable**: Scores indicate specific improvements needed
3. **Fair**: Plugins of different complexity scored appropriately
4. **Measurable**: All metrics objectively calculated
5. **Weighted**: Important factors have greater impact

---

## 1. QUALITY DIMENSIONS WITH SUB-METRICS

### 1A. Structural Correctness (Weight: 30% of overall score)

Measures whether plugin conforms to required file structure, naming conventions, schema, and formatting rules. Entirely objective.

**Sub-metrics and weights:**

| Sub-metric | Weight | What it measures | Calculation |
|---|---|---|---|
| YAML/JSON Validity | 20% | Frontmatter parses without errors; hooks.json/plugin.json/mcp.json parse correctly | `valid_files / total_files` ratio |
| Required Fields Present | 25% | All required fields exist (skill: name+description; agent: name+description+model+color; manifest: name+version+description) | `present_fields / required_fields` averaged |
| Naming Conventions | 20% | kebab-case names, 3-50 chars, start/end alphanumeric, folder matches frontmatter | Binary pass/fail per component, ratio across plugin |
| File Organization | 20% | Correct file names (SKILL.md case), directory structure, ${CLAUDE_PLUGIN_ROOT} usage | `max(0, 100 - (violations * 15))` |
| Schema Compliance | 15% | Field value constraints met: description length, semver, valid enums, no XML brackets | `compliant_fields / total_checked_fields` ratio |

**Formula:**
```
structural_score = (
    yaml_json_validity_ratio * 20 +
    required_fields_ratio * 25 +
    naming_convention_ratio * 20 +
    file_organization_score * 20 +
    schema_compliance_ratio * 15
)
```

**Score examples:**
- **100**: All YAML/JSON valid, all required fields present, all naming correct, perfect directory layout, all schema constraints met
- **75**: One skill missing description trigger phrases, one agent missing color field
- **50**: hooks.json parse error, two naming violations, one skill has README.md in folder
- **25**: Multiple parse errors, several missing required fields
- **0**: plugin.json invalid, no valid YAML frontmatter, pervasive naming violations

---

### 1B. Functional Effectiveness (Weight: 30% of overall score)

Measures how well plugin will actually work when loaded -- triggering, description quality, error handling, user test results.

**Sub-metrics and weights:**

| Sub-metric | Weight | What it measures | Calculation |
|---|---|---|---|
| Description Quality | 25% | Descriptions include "what" and "when", contain trigger phrases, appropriate length, avoid vagueness | Composite heuristic checks (see below) |
| Trigger Pattern Coverage | 20% | Skills have trigger phrases; agents have example blocks; commands have clear descriptions | Count-based checks per component type |
| Error Handling Completeness | 15% | Skills include troubleshooting; hooks handle exit codes; commands handle errors | Presence checks for error-handling patterns |
| User Test Pass Rate | 30% | Results from user-authored tests (YAML, Python, Bash) | `(passed_tests / total_tests) * 100`, or baseline if none |
| Component Execution Readiness | 10% | Hook scripts syntactically valid, referenced scripts exist, MCP binaries checkable | Binary checks per referenced resource |

**Description Quality Sub-scoring (0-100):**
```python
desc_score = 0

# Length check (0-20 points)
if len(description) >= 100: desc_score += 20
elif len(description) >= 50: desc_score += 10
elif len(description) >= 10: desc_score += 5

# Contains "what it does" statement (0-20 points)
if has_action_statement(description): desc_score += 20

# Contains "when to use" / trigger conditions (0-30 points)
trigger_keywords = ["use when", "trigger", "use this", "ask to",
                     "asks for", "mentions", "says", "requests"]
matches = count_keyword_matches(description, trigger_keywords)
desc_score += min(30, matches * 10)

# Contains specific trigger phrases in quotes (0-20 points)
quoted_phrases = count_quoted_phrases(description)
desc_score += min(20, quoted_phrases * 5)

# Penalty for vagueness (0-10 point deduction)
vague_patterns = ["helps with", "does things", "general purpose"]
if any_match(description, vague_patterns): desc_score -= 10

desc_score = clamp(desc_score, 0, 100)
```

**User Test Pass Rate Integration:**
```python
if total_user_tests > 0:
    test_score = (passed_tests / total_tests) * 100
else:
    test_score = 50  # Neutral baseline
    # Apply "no tests" penalty separately (-5 points)
```

**Formula:**
```
functional_score = (
    avg_description_quality * 25 +
    trigger_pattern_coverage * 20 +
    error_handling_completeness * 15 +
    user_test_score * 30 +
    execution_readiness * 10
)
```

**Score examples:**
- **100**: Excellent descriptions with trigger phrases, agents have 3+ examples, error handling present, all user tests pass, all scripts exist
- **75**: Good descriptions, one agent has only 1 example, 90% user tests pass
- **50**: Moderate descriptions, no user tests (baseline 50), some missing error handling
- **25**: Vague descriptions, no example blocks, user tests mostly failing
- **0**: "Does stuff" descriptions, no trigger patterns, all user tests failing

---

### 1C. Code Quality (Weight: 20% of overall score)

Measures quality of executable code within plugin -- hook scripts, utilities, configuration practices. Plugins without scripts receive baseline score (70) to avoid penalizing simple plugins.

**Sub-metrics and weights:**

| Sub-metric | Weight | What it measures | Calculation |
|---|---|---|---|
| Script Syntax Validity | 25% | Shell scripts pass shellcheck; Python syntax valid; JSON configs parse | `valid_scripts / total_scripts` ratio |
| Security Practices | 30% | Variables quoted in bash, set -euo pipefail, input validation, no hardcoded credentials, HTTPS for MCP, path traversal checks | Security checklist compliance ratio |
| Portability Practices | 20% | ${CLAUDE_PLUGIN_ROOT} used consistently, no hardcoded paths, env var expansion with defaults | Count portable vs non-portable references |
| Best Practices Adherence | 15% | Explicit timeouts in hooks, tool restrictions follow least privilege, appropriate model selection | Checklist compliance ratio |
| Error Handling in Scripts | 10% | Exit codes used correctly, stderr for errors, jq parsing with error handling | Pattern detection in script files |

**Security Checklist (scored as ratio):**
```python
security_checks = [
    "all_bash_variables_quoted",           # grep for unquoted $VAR
    "set_euo_pipefail_present",            # in each bash script
    "no_hardcoded_credentials",            # scan for api_key=, token=, password=
    "no_xml_in_frontmatter",              # scan for < > in YAML
    "https_for_mcp_servers",              # check .mcp.json URLs
    "input_validation_in_hooks",          # look for jq parsing, validation logic
    "no_path_traversal_vulnerability",    # check for ".." handling
    "no_sensitive_file_operations",       # check for .env, secrets patterns
    "claude_plugin_root_used",            # vs hardcoded paths
    "appropriate_file_permissions"         # chmod 600 for sensitive files
]

security_score = (checks_passed / len(security_checks)) * 100
```

**Handling plugins without scripts:**
```python
if total_scripts == 0 and total_hook_commands == 0:
    code_quality_score = 70  # Baseline: not penalized, not rewarded
else:
    code_quality_score = weighted_sub_metrics()
```

**Formula:**
```python
code_quality_score = (
    script_syntax_ratio * 25 +
    security_score * 30 +
    portability_score * 20 +
    best_practices_score * 15 +
    error_handling_score * 10
)
```

**Score examples:**
- **100**: All scripts pass shellcheck, set -euo pipefail everywhere, all variables quoted, input validation everywhere, ${CLAUDE_PLUGIN_ROOT} used consistently
- **75**: Scripts pass shellcheck, most variables quoted, one hook missing validation
- **50**: Some shellcheck warnings, several unquoted variables, some hardcoded paths
- **25**: Shellcheck errors, hardcoded credentials, no set -e, unquoted variables
- **0**: Syntax errors, credentials in plaintext, path traversal vulnerabilities

---

### 1D. Documentation Completeness (Weight: 20% of overall score)

Measures how well plugin is documented for both Claude and human users.

**Sub-metrics and weights:**

| Sub-metric | Weight | What it measures | Calculation |
|---|---|---|---|
| Description Quality | 25% | SKILL.md body quality, agent system prompt quality, command instruction clarity | Word count, structure presence, actionability |
| Examples Presence | 25% | Skill examples section, agent example blocks, command usage examples | `components_with_examples / total_components` ratio |
| Reference Documentation | 20% | Presence of references/ directory in skills, linked reference files | `skills_with_references / total_skills` + link validity |
| Troubleshooting Coverage | 15% | Troubleshooting sections in skills, error handling guidance, common issues documented | Pattern detection for troubleshooting headers |
| Instructions Clarity | 15% | Step-by-step instructions, markdown formatting, code blocks, tables | Structural analysis of markdown |

**Instructions Clarity Sub-scoring (0-100):**
```python
clarity_score = 0

# Heading structure (0-20)
if count_headings(content) >= 3: clarity_score += 20
elif count_headings(content) >= 1: clarity_score += 10

# Code blocks (0-20)
if count_code_blocks(content) >= 2: clarity_score += 20
elif count_code_blocks(content) >= 1: clarity_score += 10

# Numbered steps (0-20)
if has_numbered_lists(content): clarity_score += 20

# Tables or structured data (0-15)
if has_tables(content): clarity_score += 15

# Appropriate length (0-15)
word_count = count_words(content)
if 500 <= word_count <= 5000: clarity_score += 15
elif 200 <= word_count <= 500: clarity_score += 10
elif word_count > 5000: clarity_score += 5
elif word_count < 200: clarity_score += 5

# Penalty for no actionable content
if word_count < 50: clarity_score = max(0, clarity_score - 20)

clarity_score = clamp(clarity_score, 0, 100)
```

**Formula:**
```python
documentation_score = (
    description_body_quality * 25 +
    examples_presence_ratio * 25 +
    reference_docs_score * 20 +
    troubleshooting_coverage * 15 +
    instructions_clarity * 15
)
```

**Score examples:**
- **100**: Rich SKILL.md bodies with steps/examples/troubleshooting, detailed agent system prompts, populated references/, clear markdown
- **75**: Good docs but one skill missing examples, agents have prompts but no edge cases, one dead link in references
- **50**: Basic documentation, minimal SKILL.md bodies, no troubleshooting sections
- **25**: Minimal SKILL.md bodies (just titles), no examples, no references
- **0**: Empty SKILL.md bodies beyond frontmatter, no documentation

---

## 2. COMPONENT-TYPE-SPECIFIC SCORING

Different component types have different priorities. Sub-metric weights shift based on component type.

### Skills Scoring Profile
```python
functional_emphasis = {
    "description_quality": 35,  # ELEVATED: trigger phrases critical
    "trigger_coverage": 25,     # ELEVATED: must trigger reliably
    "error_handling": 10,
    "user_tests": 25,
    "execution_readiness": 5
}

documentation_emphasis = {
    "description_body": 20,
    "examples": 25,             # ELEVATED: need usage examples
    "references": 20,           # Progressive disclosure matters
    "troubleshooting": 20,      # ELEVATED: users need troubleshooting
    "clarity": 15
}
```

**Skill-specific checks:**
- Description includes both "what" and "when" (mandatory; 0 score if missing "when")
- Folder name matches frontmatter `name` field
- No README.md in skill folder (5-point deduction)
- SKILL.md body under 5,000 words
- References/ directory used (progressive disclosure bonus)

### Agents Scoring Profile
```python
structural_emphasis = {
    "required_fields": 30,     # ELEVATED: 4 required fields
    "schema_compliance": 20    # ELEVATED: enum validation for model, color
}

functional_emphasis = {
    "trigger_coverage": 30,     # ELEVATED: example blocks critical
    "execution_readiness": 15   # Tool restrictions matter
}

documentation_emphasis = {
    "description_body": 30,     # ELEVATED: system prompt quality core
    "examples": 30,             # ELEVATED: example blocks are main doc
}
```

**Agent-specific checks:**
- Description contains 2-6 `<example>` blocks (0 examples = 0, 1 = 40, 2 = 70, 3 = 85, 4+ = 100)
- Each example has `<commentary>` tag (5 points per example with commentary)
- System prompt length: minimum 20 chars, recommended 500-3000 chars
- Model/color are valid enums
- Tool restrictions follow least privilege

### Commands Scoring Profile
```python
structural_emphasis = {
    "required_fields": 10,      # REDUCED: all fields optional
    "file_organization": 25,    # ${CLAUDE_PLUGIN_ROOT} usage critical
    "schema_compliance": 30     # ELEVATED: description < 60 chars, argument-hint format
}

functional_emphasis = {
    "description_quality": 30,  # ELEVATED: shown in /help
    "error_handling": 20,       # ELEVATED: must handle bad input
}
```

**Command-specific checks:**
- Body contains instructions FOR Claude (not TO user)
- argument-hint matches $1/$2 references
- allowed-tools properly formatted
- Description under 60 characters
- ${CLAUDE_PLUGIN_ROOT} for all file references

### Hooks Scoring Profile
```python
code_quality_emphasis = {       # ELEVATED dimension weight for hooks
    "script_syntax": 30,        # ELEVATED: scripts are core
    "security": 35,             # ELEVATED: security surface
}
```

**Hook-specific checks:**
- hooks.json has "hooks" wrapper object
- Event names valid
- Hook type is "command" or "prompt"
- ${CLAUDE_PLUGIN_ROOT} in all command paths
- Timeout values set (10-60s)
- Exit code handling (0=success, 2=blocking)
- set -euo pipefail in bash scripts
- All variables quoted

### MCP Configs Scoring Profile
```python
functional_emphasis = {
    "execution_readiness": 40   # ELEVATED: command must exist, server reachable
}
```

**MCP-specific checks:**
- .mcp.json in plugin root
- "mcpServers" top-level key
- Each server has "command" field
- Environment variables use ${VAR:-default} syntax
- No plaintext secrets

---

## 3. OVERALL PLUGIN SCORE CALCULATION

### Dimension Weights (Default)
```python
overall_score = (
    structural_score * 0.30 +
    functional_score * 0.30 +
    code_quality_score * 0.20 +
    documentation_score * 0.20
)
```

### Complexity-Adjusted Dimension Weights

Simple plugins shouldn't be penalized for missing complexity:

```python
def get_dimension_weights(plugin):
    has_scripts = plugin.script_count > 0
    has_hooks = plugin.hook_count > 0

    if not has_scripts and not has_hooks:
        # Simple plugin: reduce code quality weight
        return {
            "structural": 0.35,
            "functional": 0.30,
            "code_quality": 0.10,  # Reduced (baseline 70 applies)
            "documentation": 0.25
        }
    elif has_hooks:
        # Hook-heavy plugin: boost code quality weight
        return {
            "structural": 0.25,
            "functional": 0.25,
            "code_quality": 0.30,  # Elevated
            "documentation": 0.20
        }
    else:
        # Standard plugin
        return {
            "structural": 0.30,
            "functional": 0.30,
            "code_quality": 0.20,
            "documentation": 0.20
        }
```

### Component Aggregation

Individual component scores aggregate using weighted average:

```python
component_weights = {
    "skill": 1.0,
    "agent": 1.0,
    "command": 0.8,
    "hook": 1.0,
    "mcp_config": 0.7,
    "manifest": 0.5  # Always present, lower relative weight
}

weighted_sum = sum(component.score * component_weights[component.type]
                   for component in components)
weight_total = sum(component_weights[c.type] for c in components)

dimension_score = weighted_sum / weight_total
```

### Score Bands

| Band | Range | Label | Meaning |
|------|-------|-------|---------|
| A+ | 95-100 | Exceptional | Exemplary plugin, publishable as reference |
| A | 90-94 | Excellent | Production-ready, well-crafted |
| B+ | 85-89 | Very Good | Minor improvements possible |
| B | 80-84 | Good | Solid plugin with some gaps |
| C+ | 75-79 | Above Average | Functional but with noticeable issues |
| C | 70-74 | Average | Meets minimum standards |
| D | 60-69 | Below Average | Needs improvement in several areas |
| F+ | 50-59 | Poor | Significant issues need addressing |
| F | 0-49 | Failing | Major structural or functional problems |

---

## 4. PASS/FAIL THRESHOLDS

### Passing Criteria

A plugin **passes** when ALL of the following are met:
1. Overall score >= 60
2. No critical failures (see below)
3. Structural score >= 50 (minimum structural integrity)
4. No blocking user test failures at "critical" severity

### Critical Failures (Always Fail)

These conditions cause automatic FAIL regardless of score:
```python
critical_failures = [
    "plugin_json_unparseable",           # Manifest cannot be read
    "no_valid_components_found",         # Plugin has nothing usable
    "xml_injection_in_frontmatter",      # Security: < > in YAML
    "hardcoded_credentials_detected",    # Security: plaintext secrets
    "reserved_name_used",               # "claude-*" or "anthropic-*"
    "skill_md_case_wrong",             # skill.md instead of SKILL.md
    "critical_user_test_failure"        # User test marked "critical" failed
]
```

### Issue Severity Classification

| Severity | Score Impact | Blocks Publication | Example |
|----------|-------------|-------------------|---------|
| **Critical** | Automatic FAIL | Yes, always | XML injection, hardcoded credentials, unparseable manifest |
| **Error** | -15 to -25 points | Yes, if overall < 60 | Missing required fields, invalid JSON, shellcheck errors |
| **Warning** | -5 to -10 points | No | Description too short, missing examples, unquoted variable |
| **Info** | -0 to -2 points | No | Missing optional fields, could improve trigger phrases |

### Publication Blocking Criteria

Plugin is **blocked from publication** when:
1. Overall score < 60 (D grade or below), OR
2. Any critical failure exists, OR
3. Structural score < 40, OR
4. Any user test at "critical" severity fails, OR
5. Security practices score < 30

---

## 5. SCORING FORMULAS (IMPLEMENTATION REFERENCE)

### Structural Score
```python
structural_score = (
    (valid_files / total_files) * 100 * 0.20 +
    (present_fields / required_fields) * 100 * 0.25 +
    (naming_pass / naming_total) * 100 * 0.20 +
    max(0, 100 - (violations * 15)) * 0.20 +
    (compliant / checked) * 100 * 0.15
)
```

### Functional Score
```python
functional_score = (
    avg(description_scores) * 0.25 +
    trigger_coverage_score * 0.20 +
    error_handling_score * 0.15 +
    user_test_score * 0.30 +
    (ready_count / total_checks) * 100 * 0.10
)
```

### Code Quality Score
```python
if no_scripts:
    code_quality_score = 70  # Baseline
else:
    code_quality_score = (
        (valid / total) * 100 * 0.25 +
        (security_checks_passed / security_checks_total) * 100 * 0.30 +
        (portable / total_refs) * 100 * 0.20 +
        (bp_score / bp_total) * 100 * 0.15 +
        (eh_score / eh_total) * 100 * 0.10
    )
```

### Documentation Score
```python
documentation_score = (
    avg(body_scores) * 0.25 +
    (with_examples / total) * 100 * 0.25 +
    ref_score * 0.20 +
    (ts_count / ts_total) * 100 * 0.15 +
    avg(clarity_scores) * 0.15
)
```

### Overall Score
```python
weights = get_dimension_weights(plugin)
overall = (
    structural * weights["structural"] +
    functional * weights["functional"] +
    code_quality * weights["code_quality"] +
    documentation * weights["documentation"]
)
overall = apply_test_adjustments(overall, user_test_results)
overall = round(overall, 1)
```

---

## 6. USER TEST INTEGRATION

### How User Test Results Affect Scoring

User test results directly impact **Functional Effectiveness** dimension through "User Test Pass Rate" sub-metric (30% of functional score).

**Score calculation:**
```python
if total_tests > 0:
    test_score = (passed_tests / total_tests) * 100
    coverage = tested_components / total_components

    # Coverage bonus
    coverage_bonus = 0
    if coverage >= 0.80: coverage_bonus = 5
    elif coverage >= 0.50: coverage_bonus = 3
    elif coverage >= 0.25: coverage_bonus = 1

    # Severity penalties
    severity_penalty = sum(
        30 for t in failed_tests if t.severity == "critical" +
        15 for t in failed_tests if t.severity == "blocking" +
        5 for t in failed_tests if t.severity == "warning"
    )
    severity_penalty = min(severity_penalty, 50)

    effective_score = max(0, test_score + coverage_bonus - severity_penalty)
else:
    effective_score = 50  # Neutral baseline
    # Apply -5 penalty to functional score (no tests)
```

### Test Severity Levels

| Level | Score Impact per Failure | Blocks Publication | Use For |
|-------|------------------------|-------------------|---------|
| **advisory** | 0 points | No | Performance benchmarks, nice-to-have features |
| **warning** | -5 points | No | Non-critical functionality, edge cases |
| **blocking** | -15 points | Only if overall < 60 | Core functionality, expected behavior |
| **critical** | -30 points | Yes, always | Security, data integrity, essential features |

### Missing Tests Penalty

Plugins with no user tests:
- User test score baseline: 50 (neutral)
- Additional penalty: -5 points to functional score
- Maximum functional score without tests: ~86/100

### Test Coverage Bonuses

Applied as additive bonus to overall score:
```
if test_coverage >= 80%:   overall += 5
elif test_coverage >= 50%: overall += 3
elif test_coverage >= 25%: overall += 1
```

---

## 7. RECOMMENDATION ENGINE

### Recommendation Generation

Based on dimension/sub-metric scores, generate specific, actionable recommendations.

**Priority levels:**
- **critical**: Security issues, parse errors, critical test failures
- **high**: Structural errors, missing required fields, functional failures
- **medium**: Naming violations, missing examples, unquoted variables
- **low**: Optional improvements, best practices, nice-to-haves

**Recommendation format:**
```python
Recommendation(
    priority="high",
    dimension="structural",
    message="Fix YAML/JSON parse errors in configuration files",
    details=[
        "hooks/hooks.json:15 - Unclosed bracket",
        "skills/my-skill/SKILL.md - Invalid YAML frontmatter"
    ]
)
```

### Common Recommendations

**Structural < 60:**
- "Fix structural validation errors to reach minimum passing threshold"

**YAML/JSON Validity < 100:**
- "Fix YAML/JSON parse errors in [file]"
- Details: Specific parse error messages

**Required Fields < 80:**
- "Add missing required field '[field]' to [component]"
- Details: List of required fields for component type

**Naming < 80:**
- "Fix naming convention: '[name]' should be kebab-case (e.g., '[suggestion]')"

**Description Quality < 70:**
- "Improve description quality for [component]"
- Details:
  - "Add trigger phrases: include 'Use when...' with specific user phrases"
  - "Add action statement: describe what it does (start with a verb)"
  - "Expand description: aim for 100+ characters"
  - "Remove vague language: replace 'helps with' with specific actions"

**User Tests < 60:**
- If no tests: "Add user-authored tests to validate plugin behavior"
- If failing: "Fix failing test: '[test name]' ([severity])"

**Security < 60:**
- "Fix security issue: [description]"
- Details: File, line number, fix suggestion

**Examples < 60:**
- "Add examples to [component]"
- Details: "Include at least one usage example showing input and expected output"

### Example Report

```
Quality Score Report - plugin-name v1.0.0
==========================================

Overall Score: 82/100 (B - Good)           PASSED

Dimension Scores:
  Structural Correctness:     91/100  [A]
  Functional Effectiveness:   78/100  [C+]
  Code Quality:               85/100  [B+]
  Documentation:              72/100  [C]

Component Breakdown:
  Skills:
    my-skill (SKILL.md):       85/100
  Agents:
    my-agent (my-agent.md):    76/100

User Tests: 15 total, 15 passed (100%)
  Impact: +5 bonus (100% pass rate, 80%+ coverage)

Recommendations (3):
  [HIGH] Improve description quality for skill 'my-skill'
    - Add trigger phrases: include 'Use when...'
    - Expand description: aim for 100+ characters

  [MEDIUM] Add examples to agent 'my-agent'
    - Include usage example with input/output

  [LOW] Add troubleshooting section to skill
    - Add '## Troubleshooting' with common issues
```

---

## IMPLEMENTATION NOTES

### Tools to Leverage

From `.mycelium/context/existing-tools.md`:
- **cclint**: Structural validation, schema compliance
- **cc-plugin-eval**: Triggering validation
- **shellcheck**: Script syntax validation
- **plugin-dev scripts**: validate-agent.sh, validate-hook-schema.sh

### Validation Rules Reference

All component-specific validation rules are documented in:
`.mycelium/context/validation-rules.md`

### User Test Format Reference

User test manifest format and severity levels are documented in:
`.mycelium/context/user-test-examples.md`

---

**Framework Version:** 1.0
**Status:** Production-ready
**Coverage:** All 6 component types, 4 quality dimensions, complete scoring formulas
