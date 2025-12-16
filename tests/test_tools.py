import unittest
import tempfile
import os
from pathlib import Path
from core.tools import (
    ToolRegistry,
    ToolPermission,
    ToolResultStatus,
    CodeRunnerTool,
    TestRunnerTool,
    FileIOTool,
    ShellCommandTool,
    PermissionManager
)


class TestCodeRunnerTool(unittest.TestCase):
    
    def setUp(self):
        self.tool = CodeRunnerTool()
    
    def test_validate_parameters(self):
        valid, error = self.tool.validate_parameters({"code": "print('test')", "language": "python"})
        self.assertTrue(valid)
        
        valid, error = self.tool.validate_parameters({"code": "test"})
        self.assertFalse(valid)
        self.assertIsNotNone(error)
    
    def test_execute_with_permission(self):
        context = {
            "agent_id": "test_agent",
            "mission_id": "mission_1",
            "task_id": "task_1"
        }
        result = self.tool.execute(
            {"code": "print('hello')", "language": "python"},
            [ToolPermission.EXECUTE],
            context
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.tool_id, self.tool.tool_id)
    
    def test_execute_without_permission(self):
        context = {
            "agent_id": "test_agent",
            "mission_id": "mission_1",
            "task_id": "task_1"
        }
        result = self.tool.execute(
            {"code": "print('test')", "language": "python"},
            [],
            context
        )
        self.assertEqual(result.result_status, ToolResultStatus.PERMISSION_DENIED)


class TestFileIOTool(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.tool = FileIOTool(allowed_paths=[self.temp_dir])
        self.test_file = os.path.join(self.temp_dir, "test.txt")
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_write_file(self):
        context = {
            "agent_id": "test_agent",
            "mission_id": "mission_1",
            "task_id": "task_1"
        }
        result = self.tool.execute(
            {
                "operation": "write",
                "path": self.test_file,
                "content": "test content"
            },
            [ToolPermission.WRITE],
            context
        )
        self.assertEqual(result.result_status, ToolResultStatus.SUCCESS)
        self.assertTrue(os.path.exists(self.test_file))
    
    def test_read_file(self):
        with open(self.test_file, 'w') as f:
            f.write("test content")
        
        context = {
            "agent_id": "test_agent",
            "mission_id": "mission_1",
            "task_id": "task_1"
        }
        result = self.tool.execute(
            {
                "operation": "read",
                "path": self.test_file
            },
            [ToolPermission.READ],
            context
        )
        self.assertEqual(result.result_status, ToolResultStatus.SUCCESS)
        self.assertIn("content", result.output)
    
    def test_rollback(self):
        with open(self.test_file, 'w') as f:
            f.write("original content")
        
        context = {
            "agent_id": "test_agent",
            "mission_id": "mission_1",
            "task_id": "task_1"
        }
        result = self.tool.execute(
            {
                "operation": "write",
                "path": self.test_file,
                "content": "new content"
            },
            [ToolPermission.WRITE],
            context
        )
        self.assertTrue(result.rollback_available)
        self.assertTrue(self.tool.rollback(result))
        
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, "original content")


class TestShellCommandTool(unittest.TestCase):
    
    def setUp(self):
        self.tool = ShellCommandTool()
    
    def test_validate_parameters(self):
        valid, error = self.tool.validate_parameters({"command": "echo test"})
        self.assertTrue(valid)
        
        valid, error = self.tool.validate_parameters({"command": "rm -rf /"})
        self.assertFalse(valid)
    
    def test_execute_safe_command(self):
        context = {
            "agent_id": "test_agent",
            "mission_id": "mission_1",
            "task_id": "task_1"
        }
        result = self.tool.execute(
            {"command": "echo hello"},
            [ToolPermission.EXECUTE, ToolPermission.SYSTEM],
            context
        )
        self.assertIsNotNone(result)
        if result.output:
            self.assertIn("stdout", result.output)


class TestPermissionManager(unittest.TestCase):
    
    def setUp(self):
        self.manager = PermissionManager()
    
    def test_grant_permissions(self):
        self.manager.grant_permissions(
            "agent_1",
            "tool_1",
            [ToolPermission.READ, ToolPermission.WRITE]
        )
        has_permission, granted = self.manager.check_permissions(
            "agent_1",
            "tool_1",
            [ToolPermission.READ]
        )
        self.assertTrue(has_permission)
    
    def test_revoke_permissions(self):
        self.manager.grant_permissions(
            "agent_1",
            "tool_1",
            [ToolPermission.READ]
        )
        self.manager.revoke_permissions("agent_1", "tool_1")
        has_permission, _ = self.manager.check_permissions(
            "agent_1",
            "tool_1",
            [ToolPermission.READ]
        )
        self.assertFalse(has_permission)


class TestToolRegistry(unittest.TestCase):
    
    def setUp(self):
        self.registry = ToolRegistry()
    
    def test_register_tool(self):
        tool = CodeRunnerTool("custom_runner")
        self.registry.register(tool)
        self.assertIsNotNone(self.registry.get_tool("custom_runner"))
    
    def test_execute_tool_with_permission(self):
        self.registry.grant_tool_access(
            "agent_1",
            "code_runner",
            [ToolPermission.EXECUTE]
        )
        
        context = {
            "agent_id": "agent_1",
            "mission_id": "mission_1",
            "task_id": "task_1"
        }
        
        result = self.registry.execute_tool(
            "code_runner",
            "agent_1",
            {"code": "print('test')", "language": "python"},
            context
        )
        self.assertIsNotNone(result)
    
    def test_execute_tool_without_permission(self):
        context = {
            "agent_id": "agent_1",
            "mission_id": "mission_1",
            "task_id": "task_1"
        }
        
        result = self.registry.execute_tool(
            "code_runner",
            "agent_1",
            {"code": "print('test')", "language": "python"},
            context
        )
        self.assertEqual(result.result_status, ToolResultStatus.PERMISSION_DENIED)
    
    def test_list_tools(self):
        tools = self.registry.list_tools()
        self.assertGreater(len(tools), 0)
        self.assertIn("tool_id", tools[0])
        self.assertIn("tool_name", tools[0])
    
    def test_get_audit_log(self):
        self.registry.grant_tool_access(
            "agent_1",
            "code_runner",
            [ToolPermission.EXECUTE]
        )
        
        context = {
            "agent_id": "agent_1",
            "mission_id": "mission_1",
            "task_id": "task_1"
        }
        
        self.registry.execute_tool(
            "code_runner",
            "agent_1",
            {"code": "print('test')", "language": "python"},
            context
        )
        
        logs = self.registry.get_audit_log()
        self.assertGreater(len(logs), 0)


if __name__ == "__main__":
    unittest.main()

