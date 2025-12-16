# AI Agent Orchestrator

A professional, production-ready AI Agent Orchestrator system that transforms high-level human goals into working software through coordinated AI agents.

## Architecture

The system implements a hierarchical architecture:

- **Human (Product Owner/CEO)**: Defines high-level goals
- **Orchestrator (CTO/Engineering Manager)**: Coordinates execution
- **AI Agents (Specialized Engineers)**: Execute specific tasks

## Core Components

### 1. Mission System (`core/mission.py`)
- Defines core mission and role hierarchy
- Mission status tracking
- Protocol interfaces for all roles

### 2. Memory System (`core/memory.py`)
- **Short-term memory**: Current project state, tasks, outputs
- **Long-term memory**: Historical outcomes, agent performance, patterns
- Guides future planning, agent selection, and task decomposition

### 3. Orchestrator Intelligence (`core/orchestrator.py`)
- State machine for orchestrator lifecycle
- Policy-driven decision making
- Credit assignment for agent contributions
- Adaptive orchestration based on performance
- Configurable stopping conditions

### 4. Agent System (`core/agents.py`)
- **Planner**: Converts goal → structured product plan
- **Decomposer**: Splits plan → parallelizable tasks
- **Architect**: Defines system design and interfaces
- **Coder**: Implements production-quality code
- **Critic**: Reviews code/design, finds bugs and improvements
- **Tester**: Generates and runs tests
- **Tool Executor**: Safely executes code/scripts with logging
- **Evaluator**: Scores outputs against criteria
- **Integrator**: Merges solutions into coherent system
- **Controller**: Monitors execution, escalates failures, manages retries

### 5. Tools System (`core/tools.py`)
- Abstract interface with permissioned execution
- **Code Runner**: Executes code safely
- **Test Runner**: Runs tests
- **File I/O**: Safe file operations with rollback
- **Shell Commands**: Executes allowed shell commands
- All tools are auditable and support rollback

### 6. Execution Flow (`core/execution_flow.py`)
- Complete workflow orchestration
- Phase 1: Planning (goal → plan)
- Phase 2: Decomposition (plan → tasks)
- Phase 3: Execution (tasks → outputs)
- Phase 4: Integration (outputs → system)

### 7. Logging & Metrics (`core/logging.py`)
- Structured logging with traceability
- Performance metrics collection
- End-to-end trace tracking

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

Run the main program:

```bash
python main.py "Your goal here"
```

Or run interactively:

```bash
python main.py
# Then enter your goal when prompted
```

### Basic Example

```python
from core import ExecutionFlow

flow = ExecutionFlow()
result = flow.execute_mission("Build a REST API for user management")
print(f"Mission {result['mission_id']} completed with status: {result['status']}")
```

### End-to-End Examples

```bash
# Main entry point (recommended)
python main.py "Build a REST API"

# Software factory demo
python examples/software_factory_demo.py

# End-to-end example
python examples/end_to_end_example.py

# Human approval example
python examples/human_approval_example.py
```

## Project Structure

```
AI-Orchestrator/
├── core/
│   ├── __init__.py          # Module exports
│   ├── mission.py            # Core mission definition
│   ├── memory.py             # Memory system
│   ├── orchestrator.py       # Orchestrator intelligence
│   ├── agents.py             # Agent implementations
│   ├── tools.py              # Tool system
│   ├── execution_flow.py     # Execution workflow
│   └── logging.py            # Logging and metrics
├── tests/
│   ├── test_mission.py
│   ├── test_memory.py
│   ├── test_orchestrator.py
│   ├── test_agents.py
│   ├── test_tools.py
│   └── test_execution_flow.py
├── examples/
│   └── end_to_end_example.py
├── logs/                     # Log files (generated)
├── requirements.txt
├── setup.py
└── README.md
```

## Base Classes & Interfaces

All components follow a modular design with base classes:

- `BaseAgent`: Abstract base for all agents
- `BaseTool`: Abstract base for all tools
- `HumanInterface`, `OrchestratorInterface`, `AgentInterface`: Protocol interfaces
- `CoreMission`: Mission management
- `MemorySystem`: Unified memory interface
- `OrchestratorIntelligence`: Orchestration logic
- `ToolRegistry`: Tool management

## Features

- ✅ Modular, extensible architecture
- ✅ Full test coverage (92+ tests)
- ✅ Structured logging and traceability
- ✅ Performance metrics collection
- ✅ Permission-based tool access
- ✅ Audit logging for all operations
- ✅ Rollback support for file operations
- ✅ Adaptive learning from past performance
- ✅ Credit assignment for agent contributions
- ✅ Human-in-the-loop approval for key milestones
- ✅ Mock LLM interface when real models unavailable
- ✅ Minimal dependencies (only typing-extensions)

## Constraints & Design Principles

- **No metaphors, hype, or fictional claims**: Code uses precise, technical language
- **No unnecessary dependencies**: Only `typing-extensions` required
- **Mock LLM support**: `LLMInterface` provides mock implementations when real models unavailable
- **Correctness first**: All code is tested and validated
- **Clarity**: Well-documented with clear naming conventions
- **Extendability**: Base classes and interfaces for easy extension
- **Maintainability**: Modular structure, comprehensive tests
- **Human-in-the-loop**: Key milestones require human approval, not every step

## Testing

Run all tests:

```bash
python -m pytest tests/ -v
```

## Logging

Logs are written to `logs/orchestrator.log` with structured JSON format. Each log entry includes:
- Timestamp
- Log level and category
- Message and context
- Trace ID, Mission ID, Task ID, Agent ID

## Metrics

Metrics are collected automatically during execution:
- Execution times
- Success rates
- Quality scores
- Task completion rates

Access metrics via `MetricsCollector.get_mission_metrics(mission_id)`.

## License

This is a production-ready implementation for AI Agent Orchestration.

