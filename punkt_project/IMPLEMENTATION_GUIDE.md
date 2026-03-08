# Implementation Guide: Running Parallel Agent Tasks

Quick reference for executing multi-agent implementation tasks with proper coordination and verification.

## Quick Start

### Basic Pattern

```
1. Prepare → 2. Launch → 3. Monitor → 4. Verify → 5. Integrate → 6. Test
```

## Step-by-Step Execution

### Step 1: Prepare Agent Prompts

Create prompts for each agent with:

```markdown
## Template for Each Agent

### [Component Name]

**Files:**
- [ ] app/path/to/file.py (NEW) - [brief description]
- [ ] app/another/file.py (UPDATE) - [brief description]

**Implementation:**
[Full implementation spec from ROADMAP.md]

**Verification Checklist:**
After writing each file:
- [ ] File exists: `ls -lah [path]`
- [ ] Readable: `head -20 [path]` shows content
- [ ] Size > 0: `[ -s [path] ]` passes
- [ ] No syntax errors: Valid Python

**Completion Report:**
List all files with:
- Full path
- Line count
- Status (Created/Updated)

✅ Do NOT report complete until all files verified.
```

### Step 2: Launch All Parallel Agents

```bash
# Launch all agents at once
# Each returns an agent ID immediately

Agent #1 ID: a4a00b9
Agent #2 ID: acb731e
Agent #3 ID: a62e73c
Agent #4 ID: aac6c80
Agent #5 ID: aaf3be6

# Record all IDs for monitoring
```

### Step 3: Monitor Agent Progress

```bash
# Option A: Non-blocking status checks (recommended)
TaskOutput(agent_id, block: false, timeout: 5000)

# Check every agent's status:
Agent #1 (a4a00b9): running (16 tools used, 24628 tokens)
Agent #2 (acb731e): running (13 tools used, 21011 tokens)
Agent #3 (a62e73c): running (8 tools used, 18563 tokens)
Agent #4 (aac6c80): running (5 tools used, 14686 tokens)
Agent #5 (aaf3be6): running (12 tools used, 19234 tokens)

# Option B: Blocking wait (use when ready to proceed)
TaskOutput(agent_id, block: true, timeout: 600000)
# Waits until agent completes
```

### Step 4: Verify Phase 1 Completeness

After all agents report "complete":

```bash
# Run verification command
find app -type f \( \
  -path "*parsers*" -o \
  -name "redis.py" -o \
  -name "upload.py" -o \
  -name "search.py" \
) -type f | xargs wc -l

# Expected output shows all files with line counts
# Should NOT show "No such file or directory"

# If any file missing:
# - Re-launch that agent
# - Provide full prompt again
# - Ensure verification is in the prompt
```

### Step 5: Launch Integration Agent

After verification passes:

```bash
# Now safe to launch Agent #6 (Integration)
# Include in prompt:

"
PREREQUISITE: Phase 1 complete and verified.

Phase 1 files confirmed to exist:
- app/parsers/__init__.py
- app/parsers/json_parser.py
- app/parsers/nginx_parser.py
- app/core/redis.py
- app/models/upload.py
- app/api/upload.py
- app/models/search.py
- app/api/search.py

Now proceed with integration...
"

Agent #6 ID: a237a04
```

### Step 6: Verify Integration

After Agent #6 completes:

```bash
# Check that main.py was updated
grep -n "redis_manager" app/main.py
# Should show Redis imports and lifecycle

grep -n "include_router(upload.router" app/main.py
# Should show upload router registered

grep -n "include_router(search.router" app/main.py
# Should show search router registered

# Check workers directory created
ls -la app/workers/
# Should show __init__.py and processor.py
```

### Step 7: Run Integration Tests

After all files verified:

```bash
# Run existing test suite
pytest tests/ -v

# Test imports work
python -c "from app.parsers import parse_json_file, parse_nginx_file"
python -c "from app.core.redis import redis_manager"
python -c "from app.api import upload, search"
python -c "from app.workers.processor import process_uploaded_file"

# All imports should succeed without errors
```

## Troubleshooting

### Problem: Agent Reports Complete but File Missing

**Symptom:**
```
Agent #2 (acb731e): completed
$ ls -la app/parsers/json_parser.py
ls: cannot access 'app/parsers/json_parser.py': No such file or directory
```

**Solution:**
1. Check agent output in detail
2. Look for error messages in agent execution
3. Re-launch agent with same prompt
4. Add explicit debugging to prompt:
   ```
   After Write tool call:
   - Immediately run: $ ls -lah app/parsers/json_parser.py
   - If error, report it
   - Retry Write tool if needed
   ```

### Problem: File Exists but Empty

**Symptom:**
```
$ ls -la app/parsers/json_parser.py
-rw-r--r--  0 user staff app/parsers/json_parser.py
```

**Solution:**
1. Check file size is > 0 bytes
2. Add to agent prompt:
   ```
   If [ -s app/parsers/json_parser.py ] fails:
   - File is empty
   - DO NOT mark complete
   - Check for Write tool errors
   - Retry the write operation
   ```

### Problem: Syntax Errors in Generated Code

**Symptom:**
```
python -c "from app.parsers import parse_json_file"
SyntaxError: invalid syntax (json_parser.py, line 42)
```

**Solution:**
1. Agent should catch this with `python -m py_compile`
2. Ensure prompt includes syntax check
3. Add to verification checklist:
   ```
   $ python -m py_compile app/parsers/json_parser.py
   # Should return without errors
   ```

### Problem: Import Errors Between Modules

**Symptom:**
```
from app.parsers import parse_json_file
ModuleNotFoundError: No module named 'app.parsers'
```

**Solution:**
1. Check `app/parsers/__init__.py` exports the functions
2. Ensure `__init__.py` exists (Agent should create it)
3. Verify `__init__.py` content:
   ```python
   from .json_parser import parse_json_file
   from .nginx_parser import parse_nginx_file
   __all__ = ["parse_json_file", "parse_nginx_file"]
   ```

## File Verification Checklist

Before considering Phase 1 complete, verify:

### Parsers Module
```
✓ app/parsers/__init__.py (exists, > 5 lines)
✓ app/parsers/json_parser.py (exists, > 100 lines)
  - Contains: parse_json_file function
  - Contains: _normalize_log_entry function
  - Contains: _parse_timestamp function

✓ app/parsers/nginx_parser.py (exists, > 80 lines)
  - Contains: parse_nginx_file function
  - Contains: NGINX_COMBINED_PATTERN regex
  - Contains: STATUS_LEVEL_MAP dict
```

### Models Module
```
✓ app/models/upload.py (exists, > 40 lines)
  - Contains: UploadInitRequest class
  - Contains: UploadInitResponse class
  - Contains: UploadCompleteRequest class
  - Contains: UploadStatusResponse class

✓ app/models/search.py (exists, > 40 lines)
  - Contains: SearchRequest class
  - Contains: SearchResponse class
  - Contains: LogEntry class
```

### API Module
```
✓ app/api/upload.py (exists, > 150 lines)
  - Contains: APIRouter instance
  - Contains: /file/init endpoint
  - Contains: /file/chunk endpoint
  - Contains: /file/complete endpoint
  - Contains: /file/status endpoint

✓ app/api/search.py (exists, > 100 lines)
  - Contains: APIRouter instance
  - Contains: /logs endpoint
  - Contains: /recent endpoint
```

### Core Module
```
✓ app/core/redis.py (exists, > 100 lines)
  - Contains: RedisManager class
  - Contains: __init__ method
  - Contains: connect method
  - Contains: disconnect method
  - Contains: cache_recent_log method
  - Contains: get_recent_logs method
  - Contains: redis_manager instance
```

### Workers Module
```
✓ app/workers/__init__.py (exists)

✓ app/workers/processor.py (exists, > 150 lines)
  - Contains: process_uploaded_file function
  - Contains: _batch_insert_logs function
  - Contains: _insert_batch function
```

### Main Application
```
✓ app/main.py (updated)
  - Import redis_manager
  - Redis connect in startup event
  - Redis disconnect in shutdown event
  - Upload router registered
  - Search router registered
```

## Verification Command Reference

```bash
# List all Day 2 component files
find app -type f \( \
  -path "*/parsers/*.py" -o \
  -path "*/redis.py" -o \
  -path "*/upload.py" -o \
  -path "*/search.py" -o \
  -path "*/processor.py" \
) | sort

# Count lines in all Day 2 files
find app -type f \( \
  -path "*/parsers/*.py" -o \
  -path "*/redis.py" -o \
  -path "*/upload.py" -o \
  -path "*/search.py" -o \
  -path "*/processor.py" \
) | xargs wc -l | tail -1

# Check for syntax errors
for file in $(find app -path "*/parsers/*.py" -o \
  -name "redis.py" -o -name "upload.py" -o \
  -name "search.py" -o -name "processor.py"); do
  python -m py_compile "$file" || echo "ERROR: $file"
done

# Verify imports
python -c "from app.parsers import parse_json_file, parse_nginx_file; print('✓ parsers')"
python -c "from app.core.redis import redis_manager; print('✓ redis')"
python -c "from app.api import upload, search; print('✓ api')"
python -c "from app.workers.processor import process_uploaded_file; print('✓ workers')"
```

## Status Report Template

After each phase, generate a status report:

```markdown
## Phase [N] Status Report

**Date:** [Date/Time]
**Duration:** [X minutes]

### Agents Launched
- [ ] Agent #1: [Component] - ID: [agent_id]
- [ ] Agent #2: [Component] - ID: [agent_id]
- [ ] Agent #3: [Component] - ID: [agent_id]

### Completion Status
- [x] All agents reported complete
- [x] All files verified to exist
- [x] File sizes reasonable (> X lines each)
- [x] No syntax errors detected
- [x] All imports successful
- [x] Ready for Phase [N+1]

### Files Created/Updated
| File | Status | Lines | Size |
|------|--------|-------|------|
| app/parsers/json_parser.py | ✓ | 145 | 5.2K |
| app/parsers/nginx_parser.py | ✓ | 120 | 4.1K |
| ... | ... | ... | ... |

### Issues
- [x] None

### Next Steps
Proceed to Phase [N+1].
```

## Environment Setup (Before Starting)

```bash
# Ensure working directory is correct
cd /Users/beatrice_at_pursuit/Desktop/punkt_project/punkt-backend

# Verify Python environment
python --version  # Should be 3.10+

# Verify venv active
source venv/bin/activate

# Verify FastAPI available
python -c "import fastapi; print(fastapi.__version__)"

# Verify project structure
ls -la app/
# Should show: api/, core/, models/, middleware/, __init__.py, main.py, etc.
```

---

See AGENT_COORDINATION.md for detailed best practices and ROADMAP.md for Day 2 example.
