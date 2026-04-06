# How to Use Hyper-Orchestrator — Generic Parallel Execution

**Execute ANY workflow in parallel. Not specific to any domain.**

---

## What It Is

Hyper-Orchestrator is a **generic parallel task execution engine**:

- Takes ANY list of tasks
- Runs independent ones in parallel (1-20 workers)
- Resolves dependencies via DAG
- Fuses results with AI
- Returns unified output

**Use it for:** Research, code generation, data processing, document analysis, job search, content creation — literally anything.

---

## Instant Usage (No Setup)

### 1. Benchmark — See Your Speedup

```bash
python3 Skills/hyper-orchestrator/scripts/run-workflow.py benchmark --tasks 8
```

**What it does:**
- Runs 8 tasks sequentially → measures time
- Runs same 8 tasks in parallel → measures time  
- Shows speedup ratio

**Example output:**
```
Sequential: 36.2s
Parallel:    8.6s
Speedup:     4.2x
```

---

### 2. Custom Parallel Tasks — ANY Workflow

```bash
python3 Skills/hyper-orchestrator/scripts/run-workflow.py custom \
  --tasks "summarize_section_1,summarize_section_2,summarize_section_3,summarize_section_4" \
  --fusion intelligent
```

**Use cases:**
- Summarize 20 documents
- Analyze 50 data chunks
- Generate 10 creative drafts
- Check 100 files for issues

---

### 3. DAG Workflow — With Dependencies

Create `my-workflow.json`:

```json
{
  "tasks": [
    {"id": "fetch_a", "prompt": "Fetch data source A", "deps": []},
    {"id": "fetch_b", "prompt": "Fetch data source B", "deps": []},
    {"id": "fetch_c", "prompt": "Fetch data source C", "deps": []},
    {"id": "analyze", "prompt": "Analyze all data", "deps": ["fetch_a", "fetch_b", "fetch_c"]},
    {"id": "report", "prompt": "Generate final report", "deps": ["analyze"]}
  ]
}
```

Run it:

```bash
python3 Skills/hyper-orchestrator/scripts/run-workflow.py dag \
  --config my-workflow.json
```

**What happens:**
- `fetch_a`, `fetch_b`, `fetch_c` run **in parallel**
- `analyze` waits for all fetches, then runs
- `report` waits for analyze, then runs

---

## Generic Python API

For programmatic use in ANY workflow:

```python
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, "Skills/hyper-orchestrator/scripts")
from orchestrator import HyperOrchestrator, Task

async def run_any_workflow():
    orch = HyperOrchestrator(max_workers=10)
    
    # Define YOUR tasks (any domain)
    tasks = [
        Task(id="task_1", prompt="Your prompt 1", deps=[]),
        Task(id="task_2", prompt="Your prompt 2", deps=[]),
        Task(id="task_3", prompt="Your prompt 3", deps=["task_1", "task_2"]),
    ]
    
    result = await orch.execute_dag(tasks)
    
    print(f"Completed in {result.total_time:.1f}s")
    print(f"Success rate: {result.success_rate:.0%}")
    print(f"Fused output: {result.fused_output[:500]}")

asyncio.run(run_any_workflow())
```

---

## Example Use Cases

### Research Synthesis
```python
tasks = [
    Task(id="search_1", prompt="Search topic X on web", deps=[]),
    Task(id="search_2", prompt="Search topic X on papers", deps=[]),
    Task(id="search_3", prompt="Search topic X on news", deps=[]),
    Task(id="synthesize", prompt="Combine all sources into summary", 
         deps=["search_1", "search_2", "search_3"]),
]
```

### Code Generation
```python
tasks = [
    Task(id="draft_api", prompt="Generate API module draft", deps=[]),
    Task(id="draft_db", prompt="Generate database module draft", deps=[]),
    Task(id="draft_ui", prompt="Generate UI module draft", deps=[]),
    Task(id="review", prompt="Review all drafts, select best approach",
         deps=["draft_api", "draft_db", "draft_ui"]),
    Task(id="finalize", prompt="Finalize integrated solution",
         deps=["review"]),
]
```

### Data Processing
```python
tasks = [
    Task(id="chunk_1", prompt="Process data chunk 1/10", deps=[]),
    Task(id="chunk_2", prompt="Process data chunk 2/10", deps=[]),
    # ... 8 more chunks in parallel
    Task(id="aggregate", prompt="Combine all chunk results",
         deps=["chunk_1", "chunk_2", "chunk_3", "chunk_4", "chunk_5",
               "chunk_6", "chunk_7", "chunk_8", "chunk_9", "chunk_10"]),
]
```

---

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_workers` | 10 | Max parallel tasks (1-20) |
| `fusion_mode` | intelligent | How to combine results: intelligent / concatenate / vote |
| `enable_caching` | True | Cache repeated prompts |
| `token_budget` | 100000 | Max tokens for all tasks |

---

## Files Reference

| File | Purpose |
|------|---------|
| `orchestrator.py` | Core engine (generic, any workflow) |
| `run-workflow.py` | CLI runner (any workflow) |
| `benchmark.py` | Performance testing (any workflow) |
| `examples/` | Sample workflows (just illustrations) |

---

## Documentation Index

- `QUICKSTART.md` — 30-second reference
- `HOW_TO_USE.md` — This file — full guide
- `SKILL.md` — Technical specification  
- `README.md` — API documentation
- `ARCHITECTURE.md` — Deep technical dive

**Generic. Fast. Intelligent.**