# Agent Coordination Best Practices

This document outlines best practices for coordinating parallel code-implementer agents in complex implementation projects.

## Table of Contents

1. [Core Challenges](#core-challenges)
2. [File Writing Guarantees](#file-writing-guarantees)
3. [Status Monitoring](#status-monitoring)
4. [Verification Strategy](#verification-strategy)
5. [Phase Architecture](#phase-architecture)
6. [Prompt Engineering](#prompt-engineering)
7. [Real-world Example](#real-world-example)

---

## Core Challenges

### Challenge 1: Silent File Creation Failures

**Problem:** Agents report "task complete" but files aren't actually written to disk.

**Root Cause:** Agents can lose context about file writes, especially when using background execution.

**Solution:** Mandate explicit verification in agent prompts.

```
✅ GOOD: Agent writes file, then verifies with Bash
WRITE: app/core/redis.py (200 lines)
VERIFY: $ ls -lah app/core/redis.py
OUTPUT: -rw-r--r-- 200 app/core/redis.py
✅ CONFIRMED: File exists with content

❌ BAD: Agent reports complete without verification
WRITE: app/core/redis.py
STATUS: Task complete
(File never gets written)
```

### Challenge 2: Notification Gaps

**Problem:** No clear indication when agents finish, especially with background execution.

**Root Cause:** System sends notifications, but they may not reach user in real-time.

**Solution:** Use TaskOutput polling + structured completion reports.

```
// Instead of waiting for notification:
TaskOutput(agent_id, block: false)
→ Returns immediately with status

// When ready to proceed:
TaskOutput(agent_id, block: true, timeout: 30min)
→ Waits for completion, then returns result
```

### Challenge 3: Integration Dependencies

**Problem:** Phase 2 agent needs Phase 1 outputs but files don't exist.

**Root Cause:** Sequential execution without verification gate between phases.

**Solution:** Insert verification phase between Phase 1 and Phase 2.

```
Phase 1: Launch 5 agents in parallel
         ↓
Phase 1.5: Verify all files exist (Explore agent)
           ↓
Phase 2: Launch integration agent
```

---

## File Writing Guarantees

### Best Practice: Explicit Verification

Every agent prompt should include this section:

```markdown
## File Writing Requirements

CRITICAL: You MUST verify files exist after writing.

### Process

1. **Write File**
   ```
   Use the Write tool:
   - File path: [FULL_PATH]
   - Content: [FULL_IMPLEMENTATION]
   ```

2. **Verify Immediately**
   ```bash
   # Check file exists
   ls -lah [FILE_PATH]

   # Check file size (should be > 0)
   wc -l [FILE_PATH]

   # Check readability
   head -5 [FILE_PATH]
   ```

3. **Report Completion**
   ```
   ✅ [FILE_PATH] created successfully
   - Size: [X] bytes
   - Lines: [Y]
   - Status: Ready for integration
   ```

4. **STOP**: Do NOT report task complete until steps 1-3 verified.
```

### Verification Checklist Template

```markdown
## Verification Checklist

- [ ] File written with Write tool
- [ ] File exists: `ls -lah` returns file
- [ ] File size > 0 bytes: `[ -s FILE ]` passes
- [ ] File readable: `head -5` shows content
- [ ] File path correct: Full path matches spec
- [ ] Ready for next phase: All checks pass ✅
```

---

## Status Monitoring

### Pattern 1: Non-blocking Status Check

Use when you need current status without waiting:

```javascript
// Launch agent
agent = Task(..., run_in_background: true)
// Returns: { agentId: "a4a00b9", ... }

// Check status immediately (doesn't wait)
status = TaskOutput(agent.agentId, block: false, timeout: 5000)
// Returns: { status: "running", ... } or { status: "completed", ... }

// Log status
console.log(`Agent ${agent.agentId}: ${status.status}`)
// Output: Agent a4a00b9: running
```

### Pattern 2: Blocking Wait for Completion

Use when you need to proceed after agent finishes:

```javascript
// Launch agent
agent = Task(..., run_in_background: true)

// Wait for completion (blocks)
result = TaskOutput(agent.agentId, block: true, timeout: 600000)
// Returns: { status: "completed", output: "..." }

// Proceed with next phase
if (result.status === "completed") {
  launchPhase2Agent()
}
```

### Pattern 3: Parallel Agent Monitoring

Monitor multiple agents in parallel:

```javascript
// Launch all Phase 1 agents
agents = [
  Task(..., run_in_background: true),  // Agent 1
  Task(..., run_in_background: true),  // Agent 2
  Task(..., run_in_background: true),  // Agent 3
]

// Check status of all agents
statuses = agents.map(agent =>
  TaskOutput(agent.id, block: false, timeout: 5000)
)

// Log all statuses
statuses.forEach((status, i) => {
  console.log(`Agent ${i+1}: ${status.status}`)
})

// Wait for all to complete
Promise.all(
  agents.map(agent =>
    TaskOutput(agent.id, block: true, timeout: 600000)
  )
)
```

---

## Verification Strategy

### Three-Layer Verification

**Layer 1: Agent Self-Verification**
- Agent verifies each file after writing
- Agent reports file paths and sizes
- Agent includes in task summary

**Layer 2: Automated Verification**
- Use Explore agent to check Phase 1 completeness
- Verify all expected files exist
- Verify file sizes are reasonable
- Run verification between phases

**Layer 3: Integration Testing**
- Phase 2 agent tries to import Phase 1 modules
- Catches import errors immediately
- Reports specific missing files

### Verification Command Template

```bash
# Check multiple files in one command
find app -type f \( \
  -name "json_parser.py" -o \
  -name "nginx_parser.py" -o \
  -name "redis.py" -o \
  -name "upload.py" -o \
  -name "search.py" \
) | xargs wc -l | tail -1

# Expected output:
#   145 app/parsers/json_parser.py
#   120 app/parsers/nginx_parser.py
#   180 app/core/redis.py
#   ...
#  1200 total
```

### Exploration Agent Prompt

```markdown
## Verification Task: Phase 1 Completeness Check

Verify that ALL Phase 1 component files exist and have content.

### Files to Verify

1. app/parsers/__init__.py
   - Must exist
   - Should export parse_json_file, parse_nginx_file

2. app/parsers/json_parser.py
   - Must exist
   - Should be > 100 lines
   - Should contain parse_json_file function

3. app/parsers/nginx_parser.py
   - Must exist
   - Should be > 80 lines
   - Should contain parse_nginx_file function

4. app/core/redis.py
   - Must exist
   - Should be > 100 lines
   - Should contain RedisManager class

5. app/models/upload.py
   - Must exist
   - Should be > 40 lines
   - Should contain UploadInitRequest model

6. app/api/upload.py
   - Must exist
   - Should be > 150 lines
   - Should contain upload router

7. app/models/search.py
   - Must exist
   - Should be > 40 lines
   - Should contain SearchRequest model

8. app/api/search.py
   - Must exist
   - Should be > 100 lines
   - Should contain search router

### Verification Steps

1. Use Glob to find all Python files in app/
2. Check that each file above exists
3. Use Read to check file sizes and content
4. Verify imports work: check __init__.py exports
5. Report: PASS/FAIL for each file with details

### Success Criteria

✅ All 8 files exist
✅ All files > expected line count
✅ No syntax errors in imports
✅ Functions/classes exist as specified

Report any MISSING or INCOMPLETE files immediately.
```

---

## Phase Architecture

### Recommended Three-Phase Pattern

```
┌─────────────────────────────────────────────────────┐
│ PHASE 1: Parallel Implementation (30 min)           │
├─────────────────────────────────────────────────────┤
│ Launch 5 agents in parallel:                        │
│ - Agent #1: Upload API                             │
│ - Agent #2: JSON Parser                            │
│ - Agent #3: Nginx Parser                           │
│ - Agent #4: Redis Integration                      │
│ - Agent #5: Search Endpoint                        │
│                                                     │
│ Each agent:                                        │
│ 1. Implements component                            │
│ 2. Writes files with Write tool                    │
│ 3. Verifies with Bash (ls, wc, head)              │
│ 4. Reports completion with file paths              │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ PHASE 1.5: Verification (5 min)                     │
├─────────────────────────────────────────────────────┤
│ Launch Explore agent to verify:                     │
│ - All Phase 1 files exist                          │
│ - File sizes are reasonable                        │
│ - No syntax errors                                 │
│ - All imports work                                 │
│                                                     │
│ Block until verification passes                    │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ PHASE 2: Integration (20 min)                       │
├─────────────────────────────────────────────────────┤
│ Launch Agent #6 (Integration):                      │
│ - Wire routers into main.py                        │
│ - Create background worker                         │
│ - Add Redis lifecycle management                   │
│ - Test imports                                     │
│                                                     │
│ Agent can safely assume Phase 1 complete           │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ PHASE 3: Integration Testing (10 min)               │
├─────────────────────────────────────────────────────┤
│ Run verification checklist:                         │
│ - Upload 50MB file in chunks                       │
│ - Parse 10K JSON logs                              │
│ - Parse 10K Nginx logs                             │
│ - Cache logs to Redis                              │
│ - Search with filters                              │
│ - Verify RLS isolation                             │
└─────────────────────────────────────────────────────┘
```

### Phase Gates

Each phase should have a completion gate:

```
Phase 1 → ✅ All 5 agents report complete
         → ✅ Files verified to exist
         → ✅ No syntax errors detected
         → PROCEED to Phase 2

Phase 2 → ✅ Integration agent reports complete
         → ✅ main.py updated successfully
         → ✅ All imports work
         → PROCEED to Phase 3

Phase 3 → ✅ All verification tests pass
         → ✅ No errors in logs
         → ✅ RLS working correctly
         → PROJECT COMPLETE
```

---

## Prompt Engineering

### Essential Elements for Agent Prompts

Every agent prompt should include:

#### 1. Clear File Specifications

```markdown
## Files to Create/Update

### app/core/redis.py (NEW)
- Path: /Users/beatrice.../punkt-backend/app/core/redis.py
- Type: Python module
- Dependencies: asyncio, redis, json, logging
- Exports: RedisManager class, redis_manager instance

### app/main.py (UPDATE)
- Path: /Users/beatrice.../punkt-backend/app/main.py
- Existing file - add Redis integration
- Add: redis_manager import
- Modify: startup and shutdown events
- Add: Redis connect/disconnect
```

#### 2. Verification Checklist

```markdown
## Verification (REQUIRED BEFORE COMPLETION)

After writing each file:

[ ] File exists: `ls -lah [path]`
[ ] File size > 0: `[ -s [path] ]` succeeds
[ ] Imports work: Try importing in Python
[ ] No syntax errors: `python -m py_compile [path]`
[ ] Complete implementation (not partial)
[ ] All functions/classes present as spec'd
```

#### 3. Completion Report Template

```markdown
## Completion Report

List all files created/modified:

**Created:**
- [ ] app/core/redis.py (256 lines, 8.2KB)
- [ ] app/workers/__init__.py (5 lines, 150B)

**Modified:**
- [ ] app/main.py (+30 lines: Redis integration)

**Verification:**
- [x] All files exist and readable
- [x] No syntax errors
- [x] All imports successful
- [x] Ready for Phase 2 integration

**Status:** ✅ COMPLETE
```

#### 4. Error Handling

```markdown
## Error Handling (CRITICAL)

If you encounter errors:

1. **File Write Error**
   - Don't skip the file
   - Report the error message
   - Retry the Write tool call
   - Verify file exists after retry

2. **Import Error**
   - Check file path is correct
   - Verify file is in correct directory
   - Check imports statement syntax
   - Report specific import failure

3. **Syntax Error**
   - Don't partially implement
   - Report line number
   - Fix the syntax error
   - Verify with python -m py_compile

DO NOT mark task complete if any file is missing.
```

---

## Real-world Example

### Day 2 Implementation (5 Parallel Agents)

#### Agent Launch

```javascript
// Phase 1: Launch all 5 agents
const phase1Agents = [
  {
    id: "agent-upload",
    agent: Task({
      subagent_type: "code-implementer",
      description: "Chunked upload endpoints",
      prompt: `
        [FULL PROMPT with verification checklist]
        ...
        ## Verification

        After writing app/api/upload.py and app/models/upload.py:

        1. Verify both files exist:
           $ ls -lah app/api/upload.py app/models/upload.py

        2. Check line counts:
           $ wc -l app/api/upload.py
           $ wc -l app/models/upload.py

        3. Report completion with file paths and sizes.
      `,
      run_in_background: true
    })
  },
  // ... 4 more agents
]
```

#### Status Monitoring

```javascript
// Check status while other work continues
const checkStatus = async () => {
  const statuses = await Promise.all(
    phase1Agents.map(agent =>
      TaskOutput(agent.agent.id, block: false, timeout: 5000)
    )
  )

  statuses.forEach((status, i) => {
    console.log(`Agent ${i+1}: ${status.status}`)
  })
}

// Check every 10 seconds
setInterval(checkStatus, 10000)
```

#### Phase 1.5: Verification

```javascript
// After all Phase 1 agents complete
const verifyPhase1 = await Task({
  subagent_type: "Explore",
  description: "Verify Phase 1 completeness",
  prompt: `
    Verify all Phase 1 files exist:
    - app/parsers/json_parser.py (> 100 lines)
    - app/parsers/nginx_parser.py (> 80 lines)
    - app/core/redis.py (> 100 lines)
    - app/api/upload.py (> 150 lines)
    - app/api/search.py (> 100 lines)

    Use Glob and Read to verify.
  `
})

// Check verification passed
if (!verifyPhase1.success) {
  console.error("Phase 1 verification failed!")
  console.error(verifyPhase1.error)
  process.exit(1)
}
```

#### Phase 2: Integration

```javascript
// After Phase 1 verified
const phase2Agent = await Task({
  subagent_type: "code-implementer",
  description: "Integration - wire all components",
  prompt: `
    PREREQUISITE: Phase 1 is complete and verified.
    All these files exist and are ready:
    - app/parsers/json_parser.py
    - app/core/redis.py
    - app/api/upload.py
    - app/api/search.py

    Now wire everything into main.py...
    [FULL INTEGRATION PROMPT]
  `
})
```

---

## Key Takeaways

1. **Always verify files after writing** - Don't trust agent completion without confirmation
2. **Use TaskOutput(block: false)** - Check status without blocking
3. **Insert verification gates** - Between major phases
4. **Include explicit checklists** - In agent prompts
5. **Report file paths and sizes** - In completion summaries
6. **Block until verified** - Before launching dependent agents
7. **Monitor status during execution** - Check agent progress periodically

---

## Template Checklist

When launching parallel agents:

- [ ] Each agent has verification section in prompt
- [ ] Each agent has completion report template
- [ ] Phase gates defined between phases
- [ ] Verification agent ready for Phase 1.5
- [ ] Integration agent ready for Phase 2
- [ ] All prompts include error handling guidance
- [ ] Status monitoring plan in place
- [ ] Rollback plan if verification fails

---

## Questions?

Refer to ROADMAP.md for the Day 2 implementation example that used these practices.
