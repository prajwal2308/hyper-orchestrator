#!/usr/bin/env python3
"""
Hyper-Orchestrator: One-Command Workflow Runner
No script writing required — just run and go
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from orchestrator import HyperOrchestrator, Task

API_TOKEN = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN")
MODEL_NAME = "vercel:moonshotai/kimi-k2.5"


def run_dag_workflow(args):
    """Pre-built DAG workflow — with real-time progress (generic)"""
    import time
    start_time = time.time()
    
    print(f"\n🚀 Parallel Workflow Execution")
    print(f"   Tasks: {args.count} | Workers: {args.workers}\n")
    
    # Build generic multi-phase DAG
    tasks = []
    
    # Phase 1: Parallel independent tasks
    print(f"📋 PHASE 1: Parallel Execution ({args.count} tasks)")
    for i in range(args.count):
        tasks.append(Task(
            id=f"task_1_{i}",
            prompt=f"Execute task batch {i+1}/{args.count}. Process and return results.",
            deps=[]
        ))
        print(f"   └─ Task 1.{i+1}: Ready (no dependencies)")
    
    # Phase 2: Aggregation (depends on Phase 1)
    phase1_ids = [f"task_1_{i}" for i in range(args.count)]
    print(f"\n📋 PHASE 2: Aggregation")
    tasks.append(Task(
        id="aggregate",
        prompt="Aggregate all Phase 1 results. Remove duplicates, validate output.",
        deps=phase1_ids
    ))
    print(f"   └─ Aggregation: Ready (depends on {args.count} Phase 1 tasks)")
    
    # Phase 3: Parallel processing of aggregated data
    print(f"\n📋 PHASE 3: Post-Processing (3 parallel tasks)")
    for i in range(min(3, args.count)):
        tasks.append(Task(
            id=f"task_3_{i}",
            prompt=f"Process aggregated data chunk {i+1}. Extract insights and format output.",
            deps=["aggregate"]
        ))
        print(f"   └─ Task 3.{i+1}: Ready (depends on aggregation)")
    
    total_tasks = len(tasks)
    print(f"\n▶️  EXECUTING: {total_tasks} tasks total")
    print(f"   Workers: {args.workers} | Mode: DAG with dependencies\n")
    
    # Force unbuffered output
    sys.stdout.reconfigure(line_buffering=True)
    
    completed = 0
    failed = 0
    
    async def execute():
        orch = HyperOrchestrator(max_workers=args.workers, enable_streaming=False)
        
        # Progress tracking with immediate output
        original_execute = orch.execute_single_task
        start = time.time()
        
        async def wrapped_execute(task, worker_id, context=""):
            nonlocal completed, failed
            print(f"   ▶️  [{time.time() - start:05.1f}s] Worker {worker_id}: Starting {task.id}", flush=True)
            
            await original_execute(task, worker_id, context)
            
            if task.status == "completed":
                completed += 1
                pct = completed / total_tasks * 100
                print(f"   ✅ [{time.time() - start:05.1f}s] {task.id} done ({completed}/{total_tasks}, {pct:.0f}%)", flush=True)
            else:
                failed += 1
                print(f"   ❌ [{time.time() - start:05.1f}s] {task.id} FAILED", flush=True)
        
        # Heartbeat while running
        async def heartbeat():
            while True:
                await asyncio.sleep(10)
                elapsed = time.time() - start
                print(f"   ⏱️  [{elapsed:05.1f}s] Still running... ({completed}/{total_tasks} done)", flush=True)
        
        orch.execute_single_task = wrapped_execute
        
        heartbeat_task = asyncio.create_task(heartbeat())
        result = await orch.execute_dag(tasks)
        
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        
        elapsed = time.time() - start
        success_count = len([t for t in result.tasks if t.status=='completed'])
        
        print(f"\n{'='*60}")
        print(f"✅ COMPLETE: {success_count}/{len(tasks)} tasks in {elapsed:.1f}s")
        print(f"   Success Rate: {success_count/len(tasks)*100:.0f}%")
        print(f"{'='*60}\n")
        
        return result
    
    return asyncio.run(execute())


def run_research(args):
    """Pre-built research workflow"""
    print(f"\n🔬 Research Pipeline: {args.topic} with {args.sources} parallel sources\n")
    
    tasks = [
        Task(
            id=f"source_{i}",
            prompt=f"Research '{args.topic}' from source type {i+1}. Return key findings, sources, and relevance score.",
            deps=[]
        )
        for i in range(args.sources)
    ]
    
    tasks.append(Task(
        id="synthesize",
        prompt=f"Synthesize all research on '{args.topic}' into coherent summary with citations. Resolve conflicts.",
        deps=[f"source_{i}" for i in range(args.sources)]
    ))
    
    async def execute():
        orch = HyperOrchestrator(max_workers=args.sources, enable_streaming=True)
        result = await orch.execute_dag(tasks)
        print(f"\n✅ Complete: {result.total_time:.1f}s | Research synthesized")
        return result
    
    return asyncio.run(execute())


def run_benchmark(args):
    """Built-in speed comparison"""
    print(f"\n📊 Benchmark: {args.tasks} tasks, sequential vs parallel\n")
    
    from real_benchmark import run_sequential, run_parallel, print_report, TASKS
    
    async def execute():
        # Sequential
        print("[SEQUENTIAL]")
        seq_results, seq_time = await run_sequential()
        
        await asyncio.sleep(1)
        
        # Parallel
        print("\n[PARALLEL]")
        par_results, par_time = await run_parallel()
        
        # Report
        report = print_report(seq_time, par_time)
        return report
    
    return asyncio.run(execute())


def run_generic(args):
    """Generic: Run ANY list of tasks in parallel"""
    print(f"\n⚡ Generic Parallel Execution: {len(args.tasks)} tasks with {args.workers} workers\n")
    
    tasks = [
        Task(
            id=f"task_{i}",
            prompt=task_prompt,
            deps=[]
        )
        for i, task_prompt in enumerate(args.tasks)
    ]
    
    async def execute():
        orch = HyperOrchestrator(
            max_workers=args.workers,
            enable_streaming=True,
            fusion_mode=args.fusion
        )
        result = await orch.execute_parallel(tasks)
        
        completed = len([t for t in result.tasks if t.status == 'completed'])
        print(f"\n✅ Complete: {result.total_time:.1f}s | {completed}/{len(tasks)} tasks | Speedup vs sequential: ~{len(tasks) * 8 / result.total_time:.1f}x")
        
        if args.output:
            with open(args.output, 'w') as f:
                for t in result.tasks:
                    f.write(f"\n=== {t.id} ===\n{t.result}\n")
            print(f"📄 Results saved to: {args.output}")
        
        return result
    
    return asyncio.run(execute())


def main():
    parser = argparse.ArgumentParser(
        description="Hyper-Orchestrator: One-Command Workflow Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Job search with defaults (5 jobs, 3 workers)
  python3 run-workflow.py job-search
  
  # Research a topic with 5 parallel sources  
  python3 run-workflow.py research --topic "Kubernetes" --sources 5
  
  # Speed test
  python3 run-workflow.py benchmark --tasks 8
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available workflows")
    
    # DAG workflow command (generic multi-phase)
    dag_parser = subparsers.add_parser("dag", help="Multi-phase DAG workflow with dependencies")
    dag_parser.add_argument("--count", type=int, default=5, help="Number of initial parallel tasks")
    dag_parser.add_argument("--workers", type=int, default=3, help="Parallel workers")
    
    # Research command
    research_parser = subparsers.add_parser("research", help="Multi-source research synthesis")
    research_parser.add_argument("--topic", type=str, required=True, help="Research topic")
    research_parser.add_argument("--sources", type=int, default=4, help="Number of parallel sources")
    
    # Benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Compare sequential vs parallel")
    bench_parser.add_argument("--tasks", type=int, default=4, help="Number of benchmark tasks")
    
    # Generic run command
    run_parser = subparsers.add_parser("run", help="Run ANY parallel tasks (generic)")
    run_parser.add_argument("--tasks", nargs="+", required=True, 
                           help="List of task prompts to execute in parallel")
    run_parser.add_argument("--workers", type=int, default=5, help="Parallel workers")
    run_parser.add_argument("--fusion", choices=["intelligent", "concatenate", "vote"],
                           default="concatenate", help="How to fuse results")
    run_parser.add_argument("--output", type=str, help="Save results to file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if not API_TOKEN:
        print("❌ Error: Set ZO_CLIENT_IDENTITY_TOKEN environment variable")
        sys.exit(1)
    
    # Route to workflow
    if args.command == "dag":
        run_dag_workflow(args)
    elif args.command == "research":
        run_research(args)
    elif args.command == "benchmark":
        run_benchmark(args)
    elif args.command == "run":
        run_generic(args)


if __name__ == "__main__":
    main()
