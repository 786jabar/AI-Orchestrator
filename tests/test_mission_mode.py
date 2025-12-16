import shutil
from pathlib import Path

from core import SoftwareFactory


def setup_function():
    ws = Path('workspace/mission_mode')
    if ws.exists():
        shutil.rmtree(ws)


def test_mission_mode_creates_files_and_runs_tests():
    factory = SoftwareFactory()
    result = factory.run_mission_mode('Build a Flask REST API with auth and tests')
    assert result['status'] in ('completed', 'partial')

    base = Path(result['workspace'])
    assert (base / 'src' / 'app.py').exists()
    assert (base / 'tests' / 'test_app.py').exists()
    assert (base / 'README.mission.md').exists()
    assert (base / 'DELIVERABLE.md').exists()

    test_task = next((t for t in result['tasks'] if t['task_id'] == 'task_test_exec'), None)
    assert test_task is not None
    assert test_task['status'] in ('completed', 'failed', 'partial')

    if test_task['status'] != 'completed':
        debug_task = next((t for t in result['tasks'] if t['task_id'] == 'task_debug'), None)
        assert debug_task is not None