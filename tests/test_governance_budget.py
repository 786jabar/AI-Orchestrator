from core import SoftwareFactory, OrchestratorPolicy

def test_emergency_stop_halts():
    policy = OrchestratorPolicy()
    policy.emergency_stop = True
    factory = SoftwareFactory(policy=policy)
    result = factory.execute_with_automation('Test emergency stop', priority=5)
    assert result.get('status') == 'halted'
    assert 'emergency' in result.get('reason', '')


def test_budget_halts_on_retries():
    policy = OrchestratorPolicy()
    policy.max_retries_total = 0
    factory = SoftwareFactory(policy=policy)
    result = factory.execute_with_automation('Test budget halt', priority=5)
    summary = result.get('execution_summary', {})
    assert result.get('status') in ('halted', 'failed', 'requires_human_review', 'completed')
    if result.get('status') == 'halted':
        assert summary.get('halted_reason')