# Hyper-Orchestrator

**Intelligent Parallel Task Orchestration for Zo Computer**

A lightweight parallel execution engine with dynamic planning, DAG-based dependency resolution, and real-time progress streaming. Built specifically for Zo Computer's architecture.

## Why This Exists

While frameworks like LangGraph and PydanticAI handle complex orchestration, Hyper-Orchestrator focuses on:
- **Simplicity**: Single-file implementation, no heavy dependencies
- **Real-time streaming**: See every sub-task start/complete as it happens
- **Dynamic planning**: AI analyzes goals and creates execution strategies on-the-fly
- **Zo-native**: Built specifically for Zo Computer's /zo/ask API

## Features

- **Dynamic Planning**: Planner Agent analyzes high-level goals and decomposes into optimal sub-tasks
- **Parallel Execution**: Multiple worker agents run simultaneously with adaptive concurrency
- **DAG Support**: Dependency chains with automatic resolution
- **Real-time Streaming**: Watch progress live — no waiting in the dark
- **Result Fusion**: Intelligent merging of parallel outputs

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Planner    │────▶│   Worker    │────▶│   Fusion    │
│  (Agent 0)  │     │  (Agents    │     │  (Agent N)  │
│             │     │   1-N)      │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Status**: Portfolio project demonstrating parallel AI orchestration concepts. Not battle-tested for production workflows.

---

*Created by Prajwal Srinivas as a portfolio showcase for Zo Computer parallel execution capabilities.*
