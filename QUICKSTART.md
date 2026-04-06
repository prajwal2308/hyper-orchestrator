# Hyper-Orchestrator — Generic Parallel Execution Engine

**Run ANY workflow in parallel. Not job-search specific.**

---

## 3-Second Quickstart

Already installed at `Skills/hyper-orchestrator/`. Just run.

---

## Generic Commands (Works for Anything)

```bash
# Benchmark — See parallel speedup vs sequential
python3 Skills/hyper-orchestrator/scripts/run-workflow.py benchmark --tasks 8

# Custom parallel tasks — ANY prompts you want
python3 Skills/hyper-orchestrator/scripts/run-workflow.py custom \
  --tasks "analyze_doc,summarize,extract_keywords,check_format"

# DAG workflow with dependencies — YOUR config
python3 Skills/hyper-orchestrator/scripts/run-workflow.py dag \
  --config your-workflow.json
```

---

## What Can You Parallelize?

| Use Case | Parallel Tasks | Fusion |
|----------|---------------|--------|
| **Research** | 20 web searches → 1 synthesized report | Intelligent merge |
| **Code Generation** | 5 module drafts → best selected | Vote + AI review |
| **Data Processing** | 100 file chunks → aggregated results | Concatenate |
| **Document Analysis** | 50 PDFs → summary + insights | Intelligent fusion |
| **Content Creation** | 10 blog drafts → best refined | AI selection |
| **Job Search** | Find → Verify → Analyze → Tailor (example) | Pipeline |

---

## Real Performance (Any Workflow)

```
Sequential:  36.2 seconds (one-by-one)
Parallel:     8.6 seconds (all at once)
Speedup:      4.2x faster
```

---

## Examples (Just Samples)

The `examples/` folder has **illustrative templates**:
- `job-search-dag.json` — Example workflow
- `research-pipeline.json` — Example workflow  
- `code-generation-pipeline.json` — Example workflow

**Build your own.** The engine doesn't care what tasks you run.

---

## Documentation

| File | Purpose |
|------|---------|
| `QUICKSTART.md` | This file — quick reference |
| `HOW_TO_USE.md` | Full guide with examples |
| `SKILL.md` | Technical specification |
| `README.md` | API reference |

---

## Core Engine

- `orchestrator.py` — Generic DAG + parallel execution
- `run-workflow.py` — CLI for any workflow
- `benchmark.py` — Test your speedup

**Use it for literally anything that needs parallel execution.**