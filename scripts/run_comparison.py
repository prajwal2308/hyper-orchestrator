#!/usr/bin/env python3
"""
Sequential vs Parallel Job Search - Real Performance Test
Generates actual results for Prajwal's portfolio
"""

import asyncio
import time
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from orchestrator import HyperOrchestrator, Task

API_TOKEN = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN")

# Real job search subtasks
JOB_TASKS = [
    Task(id="search1", prompt="Search web: Software Engineer jobs New York posted today. List 3 with company, title, link.", deps=[]),
    Task(id="search2", prompt="Search web: Backend Engineer remote US posted today. List 3 with company, title, link.", deps=[]),
    Task(id="search3", prompt="Search web: Full-Stack Developer jobs posted last 24 hours. List 3 with company, title, link.", deps=[]),
    Task(id="search4", prompt="Search web: Cloud Engineer jobs AWS/GCP posted today. List 3 with company, title, link.", deps=[]),
    Task(id="analyze", prompt="Analyze all search results above. Identify which 3 jobs best match a Full-Stack Cloud Developer profile. Return ranked list with reasoning.", deps=["search1", "search2", "search3", "search4"]),
    Task(id="company-research", prompt="Research the top 3 companies from analysis. Find: company size, funding stage, tech stack, culture highlights. Return structured info.", deps=["analyze"]),
]


async def run_sequential():
    """Run tasks one by one"""
    print("\n" + "="*60)
    print("MODE 1: SEQUENTIAL EXECUTION")
    print("="*60)
    
    results = {}
    start = time.time()
    
    # First batch: independent searches (run in forced sequence)
    search_tasks = ["search1", "search2", "search3", "search4"]
    for task_id in search_tasks:
        task = next(t for t in JOB_TASKS if t.id == task_id)
        print(f"\n[Sequential] Running {task_id}...")
        
        # Call API directly
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.zo.computer/zo/ask",
                headers={"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"},
                json={"input": task.prompt, "model_name": "vercel:moonshotai/kimi-k2.5"}
            ) as resp:
                data = await resp.json()
                results[task_id] = data.get("output", "")
                elapsed = time.time() - start
                print(f"  ✅ {task_id} complete ({elapsed:.1f}s elapsed)")
    
    # Dependent tasks
    for task_id in ["analyze", "company-research"]:
        task = next(t for t in JOB_TASKS if t.id == task_id)
        # Add context from dependencies
        context = "\n\n".join([f"Result from {dep}:\n{results.get(dep, '')}" for dep in task.deps])
        full_prompt = context + "\n\n" + task.prompt
        
        print(f"\n[Sequential] Running {task_id} (depends on: {', '.join(task.deps)})...")
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.zo.computer/zo/ask",
                headers={"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"},
                json={"input": full_prompt, "model_name": "vercel:moonshotai/kimi-k2.5"}
            ) as resp:
                data = await resp.json()
                results[task_id] = data.get("output", "")
                elapsed = time.time() - start
                print(f"  ✅ {task_id} complete ({elapsed:.1f}s elapsed)")
    
    total_time = time.time() - start
    return results, total_time


async def run_parallel():
    """Run tasks with Hyper-Orchestrator DAG"""
    print("\n" + "="*60)
    print("MODE 2: HYPER-ORCHESTRATOR (DAG MODE)")
    print("="*60)
    
    orchestrator = HyperOrchestrator(
        api_token=API_TOKEN,
        max_workers=6,
        enable_streaming=True,
        enable_caching=False,
        fusion_mode="intelligent"
    )
    
    result = await orchestrator.execute_dag(JOB_TASKS)
    
    # Extract results
    results = {t.id: t.result or "" for t in result.tasks}
    
    return results, result.total_time, result


async def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     JOB SEARCH WORKFLOW: SEQUENTIAL vs PARALLEL                  ║
║     Real Performance Benchmark by Prajwal Srinivas              ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Run both modes
    seq_results, seq_time = await run_sequential()
    par_results, par_time, par_obj = await run_parallel()
    
    # Print comparison
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60)
    
    speedup = seq_time / par_time if par_time > 0 else 0
    time_saved = seq_time - par_time
    
    print(f"""
┌──────────────────────────────────────────────────────────────┐
│                    RESULTS SUMMARY                           │
├──────────────────┬─────────────────┬───────────────────────┤
│     Metric       │    Sequential   │  Hyper-Orchestrator   │
├──────────────────┼─────────────────┼───────────────────────┤
│  Execution Time  │  {seq_time:>11.1f}s  │  {par_time:>16.1f}s    │
│  Tasks Completed │  {len([r for r in seq_results.values() if r]):>11}   │  {len([r for r in par_results.values() if r]):>16}     │
│  Success Rate    │  {100:>10}%    │  {par_obj.success_rate*100:>15.0f}%     │
├──────────────────┴─────────────────┴───────────────────────┤
│  🚀 SPEEDUP: {speedup:.1f}x FASTER                              │
│  ⏱️  TIME SAVED: {time_saved:.1f} seconds ({time_saved/60:.1f} minutes)      │
└──────────────────────────────────────────────────────────────┘
    """)
    
    # Save detailed results
    output = {
        "timestamp": time.time(),
        "sequential": {
            "time_seconds": seq_time,
            "results": {k: v[:500] + "..." if len(v) > 500 else v for k, v in seq_results.items()}
        },
        "parallel": {
            "time_seconds": par_time,
            "speedup": speedup,
            "time_saved_seconds": time_saved,
            "success_rate": par_obj.success_rate,
            "total_tokens": par_obj.total_tokens,
            "results": {k: v[:500] + "..." if len(v) > 500 else v for k, v in par_results.items()}
        }
    }
    
    output_path = "/home/workspace/Skills/hyper-orchestrator/comparison-results.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"📊 Full results saved to: {output_path}")
    
    # Show sample results
    print("\n" + "="*60)
    print("SAMPLE RESULTS (from parallel run)")
    print("="*60)
    for task_id, result in par_results.items():
        preview = result[:300].replace('\n', ' ')
        print(f"\n📌 {task_id}:")
        print(f"   {preview}...")


if __name__ == "__main__":
    asyncio.run(main())
