#!/usr/bin/env python3
"""
Hyper-Orchestrator CLI v2.0
Dynamic Planning + Parallel Execution

Usage:
    python3 hyper-cli.py --goal "Create portfolio website" --max-workers 6
    python3 hyper-cli.py --goal "Find 10 jobs and create resumes" --workers 10
    python3 hyper-cli.py --goal "Research AI frameworks" --dry-run
"""

import sys
import os
import json
import asyncio
import aiohttp
import time
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from planner import PlannerAgent, AGENT_TYPES

ZO_API_URL = "https://api.zo.computer/zo/ask"
MODEL_NAME = "vercel:moonshotai/kimi-k2.5"
API_TOKEN = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN")


@dataclass
class TaskResult:
    task_id: str
    agent_type: str
    status: str  # pending, running, completed, failed
    start_time: float = 0
    end_time: float = 0
    output: str = ""
    error: str = ""


class WorkerAgent:
    """
    Specialized worker that executes a single task
    Calls Zo API with appropriate tool context
    """
    
    def __init__(self, worker_id: int, api_token: str):
        self.worker_id = worker_id
        self.api_token = api_token
        self.agent_type = "generic"
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> TaskResult:
        """Execute a single task"""
        task_id = task['id']
        agent_type = task['agent_type']
        prompt = task['prompt']
        
        result = TaskResult(
            task_id=task_id,
            agent_type=agent_type,
            status="running",
            start_time=time.time()
        )
        
        # Build system prompt based on agent type
        tools_available = AGENT_TYPES.get(agent_type, {}).get('tools', [])
        
        # Convert context to serializable format
        serializable_context = {}
        for key, value in context.items():
            if isinstance(value, TaskResult):
                serializable_context[key] = {
                    "status": value.status,
                    "output": value.output[:500] if len(value.output) > 500 else value.output,
                    "agent_type": value.agent_type
                }
            else:
                serializable_context[key] = value
        
        system_prompt = f"""You are a {agent_type} agent in Hyper-Orchestrator.
Your role: {AGENT_TYPES.get(agent_type, {}).get('description', 'Execute tasks')}

AVAILABLE TOOLS:
{chr(10).join(f"- {tool}" for tool in tools_available)}

EXECUTION CONTEXT:
- Previous results: {json.dumps(serializable_context, indent=2)[:800] if serializable_context else 'None'}
- You are Worker #{self.worker_id}
- Task ID: {task_id}

INSTRUCTIONS:
1. Use available tools to complete the task
2. Return results in clear, structured format
3. If you need to save files, use absolute paths in /home/workspace/
4. Report success/failure clearly

YOUR TASK:
{prompt}
"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    ZO_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": system_prompt,
                        "model_name": MODEL_NAME
                    },
                    timeout=aiohttp.ClientTimeout(total=300)  # 5 min timeout
                ) as resp:
                    data = await resp.json()
                    output = data.get("output", "")
                    
                    result.status = "completed"
                    result.output = output
                    result.end_time = time.time()
                    
        except Exception as e:
            result.status = "failed"
            result.error = str(e)
            result.end_time = time.time()
        
        return result


class HyperOrchestrator:
    """Main orchestrator: plans and executes with parallel workers"""
    
    def __init__(self, api_token: str = None, max_workers: int = 10):
        self.api_token = api_token or API_TOKEN
        self.max_workers = max_workers
        self.planner = PlannerAgent(self.api_token)
        self.results: Dict[str, TaskResult] = {}
        self.start_time = None
    
    def print_progress(self, message: str, emoji: str = "ℹ️"):
        """Print progress with timestamp"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"[{elapsed:06.1f}s] {emoji} {message}", flush=True)
    
    async def execute_phase(self, phase: Dict[str, Any], phase_num: int, 
                           previous_results: Dict[str, Any]) -> Dict[str, TaskResult]:
        """Execute all tasks in a phase"""
        tasks = phase['tasks']
        strategy = phase.get('parallel_strategy', 'all_parallel')
        
        self.print_progress(f"Phase {phase_num}: {phase['name']} — {len(tasks)} tasks", "📋")
        
        phase_results = {}
        
        if strategy == 'all_parallel':
            # Run all tasks in parallel
            workers = [WorkerAgent(i+1, self.api_token) for i in range(len(tasks))]
            
            async def run_task(worker, task):
                self.print_progress(f"Worker {worker.worker_id}: Starting '{task['id']}' [{task['agent_type']}]", "▶️")
                result = await worker.execute(task, previous_results)
                duration = result.end_time - result.start_time
                
                if result.status == "completed":
                    self.print_progress(f"Worker {worker.worker_id}: ✅ '{task['id']}' done ({duration:.1f}s)", "✅")
                else:
                    self.print_progress(f"Worker {worker.worker_id}: ❌ '{task['id']}' failed: {result.error[:50]}", "❌")
                
                return result
            
            # Execute all in parallel
            coros = [run_task(workers[i], tasks[i]) for i in range(len(tasks))]
            results = await asyncio.gather(*coros, return_exceptions=True)
            
            for task, result in zip(tasks, results):
                if isinstance(result, Exception):
                    phase_results[task['id']] = TaskResult(
                        task_id=task['id'],
                        agent_type=task['agent_type'],
                        status="failed",
                        error=str(result)
                    )
                else:
                    phase_results[task['id']] = result
                    
        elif strategy == 'fully_sequential':
            # Run one at a time
            for i, task in enumerate(tasks):
                worker = WorkerAgent(i+1, self.api_token)
                result = await worker.execute(task, {**previous_results, **phase_results})
                phase_results[task['id']] = result
                
        else:  # some_sequential
            # Group by dependencies
            # Simplified: run in order but allow same-level parallelism
            for task in tasks:
                # Safely check dependencies
                deps_met = True
                for dep in task.get('deps', []):
                    dep_result = phase_results.get(dep) or previous_results.get(dep)
                    if not dep_result or dep_result.status != "completed":
                        deps_met = False
                        break
                
                if deps_met:
                    worker = WorkerAgent(1, self.api_token)
                    result = await worker.execute(task, {**previous_results, **phase_results})
                    phase_results[task['id']] = result
                else:
                    # Mark as failed due to unmet dependencies
                    phase_results[task['id']] = TaskResult(
                        task_id=task['id'],
                        agent_type=task['agent_type'],
                        status="failed",
                        error="Dependencies not met"
                    )
        
        return phase_results
    
    async def run(self, goal: str, dry_run: bool = False) -> Dict[str, Any]:
        """Main execution flow"""
        print("\n" + "="*60)
        print("🚀 HYPER-ORCHESTRATOR v2.0 — Dynamic Planning")
        print("="*60)
        print(f"Goal: {goal}")
        print(f"Max Workers: {self.max_workers}")
        print("="*60 + "\n")
        
        # Phase 1: Planning
        print("🧠 PHASE 1: Planning — Creating execution strategy...")
        plan = await self.planner.create_plan(goal, self.max_workers)
        self.planner.print_plan(plan)
        
        if dry_run:
            print("\n⛔ DRY RUN — Plan created but not executed")
            return {"plan": plan, "executed": False}
        
        # Phase 2: Execution
        print("\n⚡ PHASE 2: Execution — Running parallel workers...")
        self.start_time = time.time()
        
        all_results = {}
        phases = plan.get('phases', [])
        
        for i, phase in enumerate(phases, 1):
            phase_results = await self.execute_phase(phase, i, all_results)
            all_results.update(phase_results)
        
        # Summary
        total_time = time.time() - self.start_time
        completed = sum(1 for r in all_results.values() if r.status == "completed")
        failed = sum(1 for r in all_results.values() if r.status == "failed")
        
        print("\n" + "="*60)
        print("🎉 EXECUTION COMPLETE")
        print("="*60)
        print(f"⏱️  Total Time: {total_time:.1f}s ({total_time/60:.1f} min)")
        print(f"✅ Completed: {completed}/{len(all_results)}")
        print(f"❌ Failed: {failed}/{len(all_results)}")
        print("="*60 + "\n")
        
        return {
            "plan": plan,
            "results": {k: {
                "status": v.status,
                "output": v.output[:200] + "..." if len(v.output) > 200 else v.output,
                "duration": v.end_time - v.start_time if v.end_time else 0
            } for k, v in all_results.items()},
            "total_time": total_time
        }


def print_progress(msg: str):
    """Print with immediate flush for real-time streaming"""
    print(msg, flush=True)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Hyper-Orchestrator: Intelligent Dynamic Task Execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Plan and execute
    python3 hyper-cli.py --goal "Create a React portfolio website"
    
    # Dry run (see plan only)
    python3 hyper-cli.py --goal "Research AI frameworks" --dry-run
    
    # More workers for faster execution
    python3 hyper-cli.py --goal "Find 10 jobs and create resumes" --max-workers 15
        """
    )
    
    parser.add_argument("--goal", "-g", required=True, help="High-level goal to accomplish")
    parser.add_argument("--max-workers", "-w", type=int, default=10, help="Maximum parallel workers")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Create plan but don't execute")
    parser.add_argument("--output", "-o", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    if not API_TOKEN:
        print("❌ Error: Set ZO_CLIENT_IDENTITY_TOKEN environment variable")
        sys.exit(1)
    
    orchestrator = HyperOrchestrator(max_workers=args.max_workers)
    
    try:
        results = asyncio.run(orchestrator.run(args.goal, args.dry_run))
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"💾 Results saved to: {args.output}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()