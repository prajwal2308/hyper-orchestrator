#!/usr/bin/env python3
"""
REAL Benchmark: Sequential vs Parallel - No Timeout
Small scope (4 tasks) so it actually completes with real data
"""

import asyncio
import time
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

API_TOKEN = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN")
MODEL_NAME = "vercel:moonshotai/kimi-k2.5"
ZO_API_URL = "https://api.zo.computer/zo/ask"

# 4 simple tasks - realistic but completable
TASKS = [
    "Summarize what Kubernetes is in 3 sentences",
    "Summarize what Docker is in 3 sentences", 
    "Summarize what React is in 3 sentences",
    "Summarize what Python is in 3 sentences"
]

import aiohttp


async def run_single_task(prompt: str) -> tuple[str, float]:
    """Run one task via Zo API, return result + duration"""
    start = time.time()
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            ZO_API_URL,
            headers={
                "Authorization": f"Bearer {API_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "input": prompt,
                "model_name": MODEL_NAME
            }
        ) as resp:
            data = await resp.json()
            result = data.get("output", "Error")
    
    duration = time.time() - start
    return result, duration


async def run_sequential():
    """Run all tasks one by one"""
    print("\n[SEQUENTIAL MODE - Running 4 tasks one-by-one]\n")
    
    results = []
    total_start = time.time()
    
    for i, task in enumerate(TASKS, 1):
        print(f"  Task {i}/4: Starting...")
        result, duration = await run_single_task(task)
        results.append({
            "task": task[:50],
            "duration": duration,
            "result": result[:100]
        })
        print(f"  Task {i}/4: Complete in {duration:.2f}s")
    
    total_time = time.time() - total_start
    return results, total_time


async def run_parallel():
    """Run all tasks at once"""
    print("\n[PARALLEL MODE - Running 4 tasks simultaneously]\n")
    
    total_start = time.time()
    
    # Launch all at once
    coros = [run_single_task(t) for t in TASKS]
    print(f"  Launching {len(TASKS)} tasks in parallel...")
    
    raw_results = await asyncio.gather(*coros)
    
    results = []
    for i, (result, duration) in enumerate(raw_results, 1):
        results.append({
            "task": TASKS[i-1][:50],
            "duration": duration,
            "result": result[:100]
        })
        print(f"  Task {i}/4: Complete in {duration:.2f}s")
    
    total_time = time.time() - total_start
    return results, total_time


def print_report(seq_time: float, par_time: float):
    """Print comparison report"""
    print("\n" + "="*70)
    print("               REAL BENCHMARK RESULTS")
    print("="*70)
    print()
    print(f"  Tasks:           4 identical complexity tasks")
    print(f"  Sequential Time: {seq_time:.2f}s")
    print(f"  Parallel Time:   {par_time:.2f}s")
    print()
    
    speedup = seq_time / par_time if par_time > 0 else 0
    time_saved = seq_time - par_time
    
    print(f"  🚀 SPEEDUP:      {speedup:.2f}x faster")
    print(f"  ⏱️  TIME SAVED:  {time_saved:.2f}s")
    print()
    
    print("="*70)
    print("  SAVED TO: /home/workspace/Skills/hyper-orchestrator/REAL_RESULTS.json")
    print("="*70)
    
    return {
        "sequential_time": seq_time,
        "parallel_time": par_time,
        "speedup": speedup,
        "time_saved": time_saved,
        "task_count": 4,
        "timestamp": time.time()
    }


async def main():
    print("\n" + "="*70)
    print("  HYPER-ORCHESTRATOR: REAL PERFORMANCE TEST")
    print("  No Timeout - Actual API Calls")
    print("="*70)
    
    if not API_TOKEN:
        print("\n❌ No API token found. Set ZO_CLIENT_IDENTITY_TOKEN")
        return
    
    # Run sequential first
    seq_results, seq_time = await run_sequential()
    
    # Small delay between tests
    await asyncio.sleep(2)
    
    # Run parallel
    par_results, par_time = await run_parallel()
    
    # Generate report
    report = print_report(seq_time, par_time)
    
    # Save results
    import json
    with open("/home/workspace/Skills/hyper-orchestrator/REAL_RESULTS.json", "w") as f:
        json.dump({
            "report": report,
            "sequential": seq_results,
            "parallel": par_results
        }, f, indent=2)
    
    print("\n✅ Benchmark complete with real measured data")


if __name__ == "__main__":
    asyncio.run(main())
