#!/usr/bin/env python3
"""
Streaming Runner: Shows real-time progress instead of silence
"""

import asyncio
import sys
import os
import time
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)  # Force unbuffered output

sys.path.insert(0, str(Path(__file__).parent))
from orchestrator import HyperOrchestrator, Task

API_TOKEN = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN")


def print_immediate(msg):
    """Print immediately without buffering"""
    print(msg, flush=True)


async def run_with_streaming(tasks, workers=5):
    """Run tasks with visible real-time progress"""
    
    print_immediate(f"\n🚀 Hyper-Orchestrator Starting")
    print_immediate(f"   Tasks: {len(tasks)} | Workers: {workers}")
    print_immediate(f"   Mode: Parallel DAG Execution\n")
    
    # Show task plan
    print_immediate("📋 Execution Plan:")
    for i, task in enumerate(tasks, 1):
        deps = f" (depends on: {', '.join(task.deps)})" if task.deps else " (no dependencies)"
        print_immediate(f"   {i}. {task.id}{deps}")
    print_immediate("")
    
    start_time = time.time()
    completed = 0
    failed = 0
    
    # Create progress callback
    class ProgressCallback:
        def on_task_start(self, task_id, worker_id):
            print_immediate(f"   ▶️  [{time.time() - start_time:05.1f}s] Worker {worker_id}: Starting {task_id}")
        
        def on_task_complete(self, task_id, duration, tokens):
            nonlocal completed
            completed += 1
            progress = completed / len(tasks) * 100
            print_immediate(f"   ✅ [{time.time() - start_time:05.1f}s] {task_id} done ({completed}/{len(tasks)}, {progress:.0f}%)")
        
        def on_task_fail(self, task_id, error):
            nonlocal failed
            failed += 1
            print_immediate(f"   ❌ [{time.time() - start_time:05.1f}s] {task_id} FAILED: {error[:50]}")
    
    callback = ProgressCallback()
    
    print_immediate("▶️  Executing... (this may take 30-120 seconds)\n")
    
    # Progress heartbeat
    async def heartbeat():
        while True:
            await asyncio.sleep(10)
            elapsed = time.time() - start_time
            print_immediate(f"   ⏱️  [{elapsed:05.1f}s] Still running... ({completed}/{len(tasks)} done)")
    
    # Run with heartbeat
    orch = HyperOrchestrator(max_workers=workers, enable_streaming=False)  # Disable internal streaming
    
    heartbeat_task = asyncio.create_task(heartbeat())
    
    # Hook the orchestrator to emit progress
    original_execute = orch.execute_single_task
    
    async def wrapped_execute(task, worker_id, context=""):
        callback.on_task_start(task.id, worker_id)
        try:
            await original_execute(task, worker_id, context)
            if task.status == "completed":
                callback.on_task_complete(task.id, task.end_time - task.start_time if task.end_time and task.start_time else 0, task.token_count)
            else:
                callback.on_task_fail(task.id, task.error or "Unknown error")
        except Exception as e:
            callback.on_task_fail(task.id, str(e))
    
    orch.execute_single_task = wrapped_execute
    
    result = await orch.execute_dag(tasks)
    
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass
    
    elapsed = time.time() - start_time
    success_count = len([t for t in result.tasks if t.status == 'completed'])
    
    print_immediate(f"\n{'='*60}")
    print_immediate(f"✅ COMPLETE: {success_count}/{len(tasks)} tasks in {elapsed:.1f}s")
    print_immediate(f"   Success Rate: {success_count/len(tasks)*100:.0f}%")
    print_immediate(f"   Time per task: {elapsed/len(tasks):.1f}s (average)")
    print_immediate(f"{'='*60}\n")
    
    return result


def main():
    # Simple test with 4 tasks
    tasks = [
        Task(id="task_1", prompt="Summarize what Python is in 3 sentences", deps=[]),
        Task(id="task_2", prompt="Summarize what React is in 3 sentences", deps=[]),
        Task(id="task_3", prompt="Summarize what Docker is in 3 sentences", deps=[]),
        Task(id="task_4", prompt="Summarize what Kubernetes is in 3 sentences", deps=[]),
    ]
    
    asyncio.run(run_with_streaming(tasks, workers=4))


if __name__ == "__main__":
    main()
