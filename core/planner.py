#!/usr/bin/env python3
"""
Planner Agent (Agent 0): Analyzes goals and creates dynamic execution plans
"""

import json
import aiohttp
import os
from typing import Dict, List, Any

ZO_API_URL = "https://api.zo.computer/zo/ask"
MODEL_NAME = "vercel:moonshotai/kimi-k2.5"
API_TOKEN = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN")

AGENT_TYPES = {
    "research": {
        "description": "Information gathering from web sources",
        "tools": ["web_search", "read_webpage", "web_research"],
        "parallel_safe": True
    },
    "browser": {
        "description": "Interactive web browsing and verification",
        "tools": ["open_webpage", "view_webpage", "use_webpage"],
        "parallel_safe": True  # Can run multiple browsers in parallel
    },
    "code": {
        "description": "Code generation, editing, and file operations",
        "tools": ["edit_file_llm", "create_or_rewrite_file", "run_bash_command"],
        "parallel_safe": True  # Parallel file editing is safe
    },
    "test": {
        "description": "Validation, testing, and verification",
        "tools": ["run_bash_command", "view_webpage"],
        "parallel_safe": True
    },
    "deploy": {
        "description": "Deployment and service management",
        "tools": ["update_space_route", "register_user_service"],
        "parallel_safe": False  # Usually sequential
    },
    "integrate": {
        "description": "Result synthesis and final assembly",
        "tools": ["send_email_to_user", "edit_file_llm"],
        "parallel_safe": False
    }
}


class PlannerAgent:
    """
    Agent 0: The Foreman
    Analyzes high-level goals and creates execution plans
    """
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or API_TOKEN
    
    async def create_plan(self, goal: str, max_workers: int = 10) -> Dict[str, Any]:
        """
        Analyze goal and create execution plan with dynamic task decomposition
        """
        
        planner_prompt = f"""You are the Planner Agent for Hyper-Orchestrator. Your job is to analyze a high-level goal and create a detailed execution plan.

GOAL TO ANALYZE:
"{goal}"

AVAILABLE AGENT TYPES:
{json.dumps(AGENT_TYPES, indent=2)}

YOUR TASK:
1. Break the goal into atomic sub-tasks
2. Assign each sub-task to an agent type (research/browser/code/test/deploy/integrate)
3. Identify dependencies (what must finish before what can start)
4. Determine which tasks can run in parallel
5. Estimate optimal worker count for each phase

OUTPUT FORMAT (JSON):
{{
    "phases": [
        {{
            "name": "phase name",
            "description": "what this phase accomplishes",
            "tasks": [
                {{
                    "id": "task_001",
                    "agent_type": "research|browser|code|test|deploy|integrate",
                    "prompt": "detailed instructions for this agent",
                    "estimated_duration": "short|medium|long",
                    "outputs": ["what this produces"],
                    "deps": ["task_ids that must complete first"]
                }}
            ],
            "parallel_strategy": "all_parallel|some_sequential|fully_sequential",
            "workers_needed": 5
        }}
    ],
    "estimated_total_time": "15 minutes",
    "critical_path": ["task_001", "task_002"],
    "risk_factors": ["what could go wrong"]
}}

RULES:
- Max {max_workers} workers total
- Use 'research' agents for gathering information
- Use 'browser' agents for verification and interaction
- Use 'code' agents for file operations and generation
- Use 'test' agents for validation
- Use 'integrate' for final assembly
- Dependencies must form a valid DAG (no cycles)
- When in doubt, prefer parallel over sequential

Provide ONLY the JSON output, no other text."""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                ZO_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": planner_prompt,
                    "model_name": MODEL_NAME
                }
            ) as resp:
                data = await resp.json()
                response = data.get("output", "")
                
                # Extract JSON from response
                try:
                    # Try to find JSON in markdown code block
                    if "```json" in response:
                        json_str = response.split("```json")[1].split("```")[0].strip()
                    elif "```" in response:
                        json_str = response.split("```")[1].split("```")[0].strip()
                    else:
                        json_str = response.strip()
                    
                    plan = json.loads(json_str)
                    return plan
                except json.JSONDecodeError:
                    # Return a fallback plan if parsing fails
                    return self._fallback_plan(goal, max_workers)
    
    def _fallback_plan(self, goal: str, max_workers: int) -> Dict[str, Any]:
        """Create a simple fallback plan if AI planning fails"""
        return {
            "phases": [
                {
                    "name": "analyze",
                    "description": "Understand the task requirements",
                    "tasks": [
                        {
                            "id": "task_001",
                            "agent_type": "research",
                            "prompt": f"Analyze this goal and determine best approach: {goal}",
                            "estimated_duration": "short",
                            "outputs": ["analysis"],
                            "deps": []
                        }
                    ],
                    "parallel_strategy": "all_parallel",
                    "workers_needed": 1
                },
                {
                    "name": "execute",
                    "description": "Execute the main task",
                    "tasks": [
                        {
                            "id": "task_002",
                            "agent_type": "code",
                            "prompt": f"Execute: {goal}",
                            "estimated_duration": "medium",
                            "outputs": ["result"],
                            "deps": ["task_001"]
                        }
                    ],
                    "parallel_strategy": "fully_sequential",
                    "workers_needed": 1
                }
            ],
            "estimated_total_time": "10 minutes",
            "critical_path": ["task_001", "task_002"],
            "risk_factors": ["AI planning failed, using fallback"]
        }
    
    def print_plan(self, plan: Dict[str, Any]):
        """Pretty print the execution plan"""
        print("\n" + "="*60)
        print("📋 EXECUTION PLAN CREATED")
        print("="*60)
        
        for i, phase in enumerate(plan.get("phases", []), 1):
            print(f"\n🔹 Phase {i}: {phase['name']}")
            print(f"   Description: {phase['description']}")
            print(f"   Strategy: {phase['parallel_strategy']}")
            print(f"   Workers: {phase['workers_needed']}")
            print(f"   Tasks:")
            for task in phase['tasks']:
                deps_str = f" (→ after: {', '.join(task['deps'])})" if task['deps'] else ""
                print(f"      • [{task['agent_type']}] {task['id']}: {task['prompt'][:50]}...{deps_str}")
        
        print(f"\n⏱️  Estimated total time: {plan.get('estimated_total_time', 'unknown')}")
        print(f"🎯 Critical path: {' → '.join(plan.get('critical_path', []))}")
        print("="*60 + "\n")


if __name__ == "__main__":
    import asyncio
    import argparse
    
    parser = argparse.ArgumentParser(description="Planner Agent - Creates execution plans")
    parser.add_argument("--goal", required=True, help="High-level goal to plan")
    parser.add_argument("--max-workers", type=int, default=10, help="Maximum parallel workers")
    parser.add_argument("--output", help="Save plan to file")
    
    args = parser.parse_args()
    
    planner = PlannerAgent()
    plan = asyncio.run(planner.create_plan(args.goal, args.max_workers))
    planner.print_plan(plan)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(plan, f, indent=2)
        print(f"💾 Plan saved to: {args.output}")