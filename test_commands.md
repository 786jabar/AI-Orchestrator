# Testing Commands for AI Agent Orchestrator

## 1. Run All Tests
```bash
python -m pytest tests/ -v
```

## 2. Run Tests with Coverage
```bash
python -m pytest tests/ -v --cov=core --cov-report=html
```

## 3. Run Quick Test Summary
```bash
python -m pytest tests/ -q
```

## 4. Run Specific Test Suite
```bash
# Test mission system
python -m pytest tests/test_mission.py -v

# Test memory system
python -m pytest tests/test_memory.py -v

# Test orchestrator
python -m pytest tests/test_orchestrator.py -v

# Test agents
python -m pytest tests/test_agents.py -v

# Test tools
python -m pytest tests/test_tools.py -v

# Test execution flow
python -m pytest tests/test_execution_flow.py -v

# Test automation
python -m pytest tests/test_automation.py -v
```

## 5. Run Example Demonstrations

### Basic End-to-End Example
```bash
python examples/end_to_end_example.py
```

### Human Approval Example
```bash
python examples/human_approval_example.py
```

### Full Cycle Demo
```bash
python examples/full_cycle_demo.py
```

### Software Factory Demo (Recommended)
```bash
python examples/software_factory_demo.py
```

## 6. Quick System Verification
```bash
python -c "from core import ExecutionFlow, SoftwareFactory; print('System OK')"
```

## 7. Interactive Python Test
```python
from core import SoftwareFactory, OrchestratorPolicy, HumanApprovalManager, MilestoneType

# Setup
approval_manager = HumanApprovalManager()
approval_manager.register_auto_approve(MilestoneType.MISSION_PLAN)
approval_manager.register_auto_approve(MilestoneType.FINAL_DELIVERY)

factory = SoftwareFactory(approval_manager=approval_manager)

# Execute
result = factory.execute_with_automation("Build a REST API")
print(f"Status: {result['status']}")
print(f"Mission ID: {result['mission_id']}")
```


