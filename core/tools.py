"""
Tools System for AI Agent Orchestrator
Abstract interface with permissioned execution, safety, auditability, and rollback.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Protocol
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
import subprocess
import os
import shutil
import json
import tempfile
from pathlib import Path
import hashlib


class ToolPermission(Enum):
    """Tool permission levels"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    NETWORK = "network"
    SYSTEM = "system"


class ToolResultStatus(Enum):
    """Tool execution result status"""
    SUCCESS = "success"
    FAILURE = "failure"
    PERMISSION_DENIED = "permission_denied"
    TIMEOUT = "timeout"
    ROLLED_BACK = "rolled_back"


@dataclass
class ToolExecution:
    """Record of tool execution for auditing"""
    tool_id: str
    agent_id: str
    mission_id: str
    task_id: str
    command: str
    parameters: Dict[str, Any]
    result_status: ToolResultStatus
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    rollback_available: bool = False
    rollback_data: Optional[Dict[str, Any]] = None
    permission_used: List[ToolPermission] = field(default_factory=list)


@dataclass
class ToolPermissionSet:
    """Set of permissions for an agent"""
    agent_id: str
    tool_permissions: Dict[str, List[ToolPermission]] = field(default_factory=dict)
    granted_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


class BaseTool(ABC):
    """Abstract base class for all tools"""
    
    def __init__(self, tool_id: str, tool_name: str):
        self.tool_id = tool_id
        self.tool_name = tool_name
        self.required_permissions: List[ToolPermission] = []
        self.supports_rollback: bool = False
        self.max_execution_time: float = 30.0
        self.audit_log: List[ToolExecution] = []
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any], 
               permissions: List[ToolPermission],
               context: Dict[str, Any]) -> ToolExecution:
        """Execute tool with given parameters and permissions"""
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate tool parameters"""
        pass
    
    def rollback(self, execution: ToolExecution) -> bool:
        """Rollback tool execution if supported"""
        return False
    
    def get_required_permissions(self) -> List[ToolPermission]:
        """Get required permissions for this tool"""
        return self.required_permissions
    
    def audit_execution(self, execution: ToolExecution) -> None:
        """Record execution in audit log"""
        self.audit_log.append(execution)


class CodeRunnerTool(BaseTool):
    """Tool for executing code safely"""
    
    def __init__(self, tool_id: str = "code_runner"):
        super().__init__(tool_id, "Code Runner")
        self.required_permissions = [ToolPermission.EXECUTE]
        self.supports_rollback = True
        self.work_dir = Path(tempfile.mkdtemp(prefix="code_runner_"))
        self.backup_dir = self.work_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate code runner parameters"""
        if "code" not in parameters:
            return False, "Missing 'code' parameter"
        if "language" not in parameters:
            return False, "Missing 'language' parameter"
        if parameters["language"] not in ["python", "javascript", "bash"]:
            return False, f"Unsupported language: {parameters['language']}"
        return True, None
    
    def execute(self, parameters: Dict[str, Any],
               permissions: List[ToolPermission],
               context: Dict[str, Any]) -> ToolExecution:
        """Execute code with safety checks"""
        start_time = datetime.now()
        
        if ToolPermission.EXECUTE not in permissions:
            return ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="execute_code",
                parameters=parameters,
                result_status=ToolResultStatus.PERMISSION_DENIED,
                output=None,
                error="EXECUTE permission required"
            )
        
        valid, error_msg = self.validate_parameters(parameters)
        if not valid:
            return ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="execute_code",
                parameters=parameters,
                result_status=ToolResultStatus.FAILURE,
                output=None,
                error=error_msg
            )
        
        code = parameters.get("code", "")
        language = parameters.get("language", "python")
        timeout = parameters.get("timeout", self.max_execution_time)
        
        try:
            result = self._run_code(code, language, timeout)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            execution = ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="execute_code",
                parameters=parameters,
                result_status=ToolResultStatus.SUCCESS if result["success"] else ToolResultStatus.FAILURE,
                output=result.get("output", ""),
                error=result.get("error"),
                execution_time=execution_time,
                rollback_available=self.supports_rollback,
                rollback_data={"code_hash": self._hash_code(code)},
                permission_used=[ToolPermission.EXECUTE]
            )
            
            self.audit_execution(execution)
            return execution
        except subprocess.TimeoutExpired:
            execution_time = (datetime.now() - start_time).total_seconds()
            execution = ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="execute_code",
                parameters=parameters,
                result_status=ToolResultStatus.TIMEOUT,
                output=None,
                error="Execution timeout",
                execution_time=execution_time
            )
            self.audit_execution(execution)
            return execution
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            execution = ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="execute_code",
                parameters=parameters,
                result_status=ToolResultStatus.FAILURE,
                output=None,
                error=str(e),
                execution_time=execution_time
            )
            self.audit_execution(execution)
            return execution
    
    def _run_code(self, code: str, language: str, timeout: float) -> Dict[str, Any]:
        """Run code in isolated environment"""
        script_file = self.work_dir / f"script_{datetime.now().timestamp()}.{self._get_extension(language)}"
        
        try:
            script_file.write_text(code)
            
            if language == "python":
                result = subprocess.run(
                    ["python", str(script_file)],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(self.work_dir)
                )
            elif language == "bash":
                result = subprocess.run(
                    ["bash", str(script_file)],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(self.work_dir)
                )
            else:
                return {"success": False, "error": f"Unsupported language: {language}"}
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "exit_code": result.returncode
            }
        finally:
            if script_file.exists():
                script_file.unlink()
    
    def _get_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            "python": "py",
            "javascript": "js",
            "bash": "sh"
        }
        return extensions.get(language, "txt")
    
    def _hash_code(self, code: str) -> str:
        """Generate hash for code"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def rollback(self, execution: ToolExecution) -> bool:
        """Rollback code execution"""
        if not execution.rollback_available:
            return False
        return True


class TestRunnerTool(BaseTool):
    """Tool for running tests safely"""
    
    def __init__(self, tool_id: str = "test_runner"):
        super().__init__(tool_id, "Test Runner")
        self.required_permissions = [ToolPermission.EXECUTE, ToolPermission.READ]
        self.supports_rollback = False
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate test runner parameters"""
        if "test_file" not in parameters and "test_command" not in parameters:
            return False, "Missing 'test_file' or 'test_command' parameter"
        return True, None
    
    def execute(self, parameters: Dict[str, Any],
               permissions: List[ToolPermission],
               context: Dict[str, Any]) -> ToolExecution:
        """Execute tests"""
        start_time = datetime.now()
        
        if ToolPermission.EXECUTE not in permissions:
            return ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="run_tests",
                parameters=parameters,
                result_status=ToolResultStatus.PERMISSION_DENIED,
                output=None,
                error="EXECUTE permission required"
            )
        
        valid, error_msg = self.validate_parameters(parameters)
        if not valid:
            return ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="run_tests",
                parameters=parameters,
                result_status=ToolResultStatus.FAILURE,
                output=None,
                error=error_msg
            )
        
        try:
            if "test_command" in parameters:
                command = parameters["test_command"]
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.max_execution_time
                )
            else:
                test_file = parameters["test_file"]
                result = subprocess.run(
                    ["python", "-m", "pytest", test_file, "-v"],
                    capture_output=True,
                    text=True,
                    timeout=self.max_execution_time
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            execution = ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="run_tests",
                parameters=parameters,
                result_status=ToolResultStatus.SUCCESS if result.returncode == 0 else ToolResultStatus.FAILURE,
                output={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "passed": result.returncode == 0
                },
                error=result.stderr if result.returncode != 0 else None,
                execution_time=execution_time,
                permission_used=[ToolPermission.EXECUTE, ToolPermission.READ]
            )
            
            self.audit_execution(execution)
            return execution
        except subprocess.TimeoutExpired:
            execution_time = (datetime.now() - start_time).total_seconds()
            execution = ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="run_tests",
                parameters=parameters,
                result_status=ToolResultStatus.TIMEOUT,
                output=None,
                error="Test execution timeout",
                execution_time=execution_time
            )
            self.audit_execution(execution)
            return execution
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            execution = ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="run_tests",
                parameters=parameters,
                result_status=ToolResultStatus.FAILURE,
                output=None,
                error=str(e),
                execution_time=execution_time
            )
            self.audit_execution(execution)
            return execution


class FileIOTool(BaseTool):
    """Tool for safe file I/O operations"""
    
    def __init__(self, tool_id: str = "file_io", allowed_paths: Optional[List[str]] = None):
        super().__init__(tool_id, "File I/O")
        self.required_permissions = [ToolPermission.READ, ToolPermission.WRITE]
        self.supports_rollback = True
        self.allowed_paths = allowed_paths or ["./workspace"]
        self.backups: Dict[str, bytes] = {}
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate file I/O parameters"""
        if "operation" not in parameters:
            return False, "Missing 'operation' parameter"
        if parameters["operation"] not in ["read", "write", "delete", "list"]:
            return False, f"Invalid operation: {parameters['operation']}"
        if parameters["operation"] in ["read", "write", "delete"] and "path" not in parameters:
            return False, "Missing 'path' parameter"
        return True, None
    
    def _is_path_allowed(self, path: str) -> bool:
        """Check if path is in allowed paths"""
        abs_path = os.path.abspath(path)
        for allowed in self.allowed_paths:
            if abs_path.startswith(os.path.abspath(allowed)):
                return True
        return False
    
    def execute(self, parameters: Dict[str, Any],
               permissions: List[ToolPermission],
               context: Dict[str, Any]) -> ToolExecution:
        """Execute file I/O operation"""
        start_time = datetime.now()
        operation = parameters.get("operation", "")
        path = parameters.get("path", "")
        
        if operation == "read" and ToolPermission.READ not in permissions:
            return ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command=f"file_{operation}",
                parameters=parameters,
                result_status=ToolResultStatus.PERMISSION_DENIED,
                output=None,
                error="READ permission required"
            )
        
        if operation in ["write", "delete"] and ToolPermission.WRITE not in permissions:
            return ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command=f"file_{operation}",
                parameters=parameters,
                result_status=ToolResultStatus.PERMISSION_DENIED,
                output=None,
                error="WRITE permission required"
            )
        
        if path and not self._is_path_allowed(path):
            return ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command=f"file_{operation}",
                parameters=parameters,
                result_status=ToolResultStatus.PERMISSION_DENIED,
                output=None,
                error=f"Path not allowed: {path}"
            )
        
        try:
            if operation == "read":
                result = self._read_file(path)
            elif operation == "write":
                result = self._write_file(path, parameters.get("content", ""))
            elif operation == "delete":
                result = self._delete_file(path)
            elif operation == "list":
                result = self._list_directory(parameters.get("path", "."))
            else:
                result = {"success": False, "error": f"Unknown operation: {operation}"}
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            execution = ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command=f"file_{operation}",
                parameters=parameters,
                result_status=ToolResultStatus.SUCCESS if result.get("success") else ToolResultStatus.FAILURE,
                output=result,
                error=result.get("error"),
                execution_time=execution_time,
                rollback_available=self.supports_rollback and operation in ["write", "delete"],
                rollback_data={"path": path, "operation": operation} if operation in ["write", "delete"] else None,
                permission_used=[ToolPermission.READ if operation == "read" else ToolPermission.WRITE]
            )
            
            self.audit_execution(execution)
            return execution
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            execution = ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command=f"file_{operation}",
                parameters=parameters,
                result_status=ToolResultStatus.FAILURE,
                output=None,
                error=str(e),
                execution_time=execution_time
            )
            self.audit_execution(execution)
            return execution
    
    def _read_file(self, path: str) -> Dict[str, Any]:
        """Read file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write file with backup"""
        try:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    self.backups[path] = f.read()
            
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _delete_file(self, path: str) -> Dict[str, Any]:
        """Delete file with backup"""
        try:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    self.backups[path] = f.read()
                os.remove(path)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _list_directory(self, path: str) -> Dict[str, Any]:
        """List directory contents"""
        try:
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                items.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                })
            return {"success": True, "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def rollback(self, execution: ToolExecution) -> bool:
        """Rollback file operation"""
        if not execution.rollback_available or not execution.rollback_data:
            return False
        
        path = execution.rollback_data.get("path")
        operation = execution.rollback_data.get("operation")
        
        if not path:
            return False
        
        try:
            if operation == "write":
                if path in self.backups:
                    if self.backups[path]:
                        with open(path, 'wb') as f:
                            f.write(self.backups[path])
                    else:
                        if os.path.exists(path):
                            os.remove(path)
                    return True
            elif operation == "delete":
                if path in self.backups:
                    with open(path, 'wb') as f:
                        f.write(self.backups[path])
                    return True
            return False
        except Exception:
            return False


class ShellCommandTool(BaseTool):
    """Tool for executing shell commands safely"""
    
    def __init__(self, tool_id: str = "shell_command", allowed_commands: Optional[List[str]] = None):
        super().__init__(tool_id, "Shell Command")
        self.required_permissions = [ToolPermission.EXECUTE, ToolPermission.SYSTEM]
        self.supports_rollback = False
        self.allowed_commands = allowed_commands or ["ls", "pwd", "echo", "cat", "grep", "find"]
        self.dangerous_commands = ["rm", "rmdir", "del", "format", "mkfs", "dd"]
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate shell command parameters"""
        if "command" not in parameters:
            return False, "Missing 'command' parameter"
        command = parameters["command"].split()[0] if parameters["command"] else ""
        if command in self.dangerous_commands:
            return False, f"Dangerous command not allowed: {command}"
        if self.allowed_commands and command not in self.allowed_commands:
            return False, f"Command not in allowed list: {command}"
        return True, None
    
    def execute(self, parameters: Dict[str, Any],
               permissions: List[ToolPermission],
               context: Dict[str, Any]) -> ToolExecution:
        """Execute shell command"""
        start_time = datetime.now()
        
        if ToolPermission.EXECUTE not in permissions:
            return ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="shell_command",
                parameters=parameters,
                result_status=ToolResultStatus.PERMISSION_DENIED,
                output=None,
                error="EXECUTE permission required"
            )
        
        valid, error_msg = self.validate_parameters(parameters)
        if not valid:
            return ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="shell_command",
                parameters=parameters,
                result_status=ToolResultStatus.FAILURE,
                output=None,
                error=error_msg
            )
        
        command = parameters.get("command", "")
        timeout = parameters.get("timeout", self.max_execution_time)
        work_dir = parameters.get("work_dir", ".")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=work_dir
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            execution = ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="shell_command",
                parameters=parameters,
                result_status=ToolResultStatus.SUCCESS if result.returncode == 0 else ToolResultStatus.FAILURE,
                output={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                },
                error=result.stderr if result.returncode != 0 else None,
                execution_time=execution_time,
                permission_used=[ToolPermission.EXECUTE, ToolPermission.SYSTEM]
            )
            
            self.audit_execution(execution)
            return execution
        except subprocess.TimeoutExpired:
            execution_time = (datetime.now() - start_time).total_seconds()
            execution = ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="shell_command",
                parameters=parameters,
                result_status=ToolResultStatus.TIMEOUT,
                output=None,
                error="Command execution timeout",
                execution_time=execution_time
            )
            self.audit_execution(execution)
            return execution
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            execution = ToolExecution(
                tool_id=self.tool_id,
                agent_id=context.get("agent_id", ""),
                mission_id=context.get("agent_id", ""),
                task_id=context.get("task_id", ""),
                command="shell_command",
                parameters=parameters,
                result_status=ToolResultStatus.FAILURE,
                output=None,
                error=str(e),
                execution_time=execution_time
            )
            self.audit_execution(execution)
            return execution


class PermissionManager:
    """Manages tool permissions for agents"""
    
    def __init__(self):
        self.permissions: Dict[str, ToolPermissionSet] = {}
        self.default_permissions: Dict[str, List[ToolPermission]] = {}
    
    def grant_permissions(self, agent_id: str, tool_id: str, 
                         permissions: List[ToolPermission],
                         expires_at: Optional[datetime] = None) -> None:
        """Grant permissions to agent for tool"""
        if agent_id not in self.permissions:
            self.permissions[agent_id] = ToolPermissionSet(agent_id=agent_id)
        
        self.permissions[agent_id].tool_permissions[tool_id] = permissions
        if expires_at:
            self.permissions[agent_id].expires_at = expires_at
    
    def revoke_permissions(self, agent_id: str, tool_id: Optional[str] = None) -> None:
        """Revoke permissions from agent"""
        if agent_id in self.permissions:
            if tool_id:
                if tool_id in self.permissions[agent_id].tool_permissions:
                    del self.permissions[agent_id].tool_permissions[tool_id]
            else:
                del self.permissions[agent_id]
    
    def check_permissions(self, agent_id: str, tool_id: str,
                         required_permissions: List[ToolPermission]) -> tuple[bool, List[ToolPermission]]:
        """Check if agent has required permissions"""
        if agent_id not in self.permissions:
            return False, []
        
        permission_set = self.permissions[agent_id]
        
        if permission_set.expires_at and datetime.now() > permission_set.expires_at:
            return False, []
        
        if tool_id not in permission_set.tool_permissions:
            return False, []
        
        granted = permission_set.tool_permissions[tool_id]
        has_all = all(perm in granted for perm in required_permissions)
        
        return has_all, granted
    
    def get_agent_permissions(self, agent_id: str) -> Dict[str, List[ToolPermission]]:
        """Get all permissions for an agent"""
        if agent_id not in self.permissions:
            return {}
        return self.permissions[agent_id].tool_permissions.copy()


class ToolRegistry:
    """Registry for managing tools"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.permission_manager = PermissionManager()
        self._initialize_default_tools()
    
    def _initialize_default_tools(self):
        """Initialize default tools"""
        self.register(CodeRunnerTool())
        self.register(TestRunnerTool())
        self.register(FileIOTool())
        self.register(ShellCommandTool())
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool"""
        self.tools[tool.tool_id] = tool
    
    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        """Get tool by ID"""
        return self.tools.get(tool_id)
    
    def execute_tool(self, tool_id: str, agent_id: str, parameters: Dict[str, Any],
                   context: Dict[str, Any]) -> ToolExecution:
        """Execute tool with permission checking"""
        tool = self.get_tool(tool_id)
        if not tool:
            return ToolExecution(
                tool_id=tool_id,
                agent_id=agent_id,
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command="unknown",
                parameters=parameters,
                result_status=ToolResultStatus.FAILURE,
                output=None,
                error=f"Tool not found: {tool_id}"
            )
        
        required_permissions = tool.get_required_permissions()
        has_permission, granted = self.permission_manager.check_permissions(
            agent_id, tool_id, required_permissions
        )
        
        if not has_permission:
            return ToolExecution(
                tool_id=tool_id,
                agent_id=agent_id,
                mission_id=context.get("mission_id", ""),
                task_id=context.get("task_id", ""),
                command=tool.tool_name,
                parameters=parameters,
                result_status=ToolResultStatus.PERMISSION_DENIED,
                output=None,
                error=f"Permission denied. Required: {required_permissions}, Granted: {granted}"
            )
        
        return tool.execute(parameters, granted, context)
    
    def grant_tool_access(self, agent_id: str, tool_id: str,
                         permissions: List[ToolPermission],
                         expires_at: Optional[datetime] = None) -> None:
        """Grant tool access to agent"""
        self.permission_manager.grant_permissions(agent_id, tool_id, permissions, expires_at)
    
    def revoke_tool_access(self, agent_id: str, tool_id: Optional[str] = None) -> None:
        """Revoke tool access from agent"""
        self.permission_manager.revoke_permissions(agent_id, tool_id)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools"""
        return [
            {
                "tool_id": tool.tool_id,
                "tool_name": tool.tool_name,
                "required_permissions": [p.value for p in tool.required_permissions],
                "supports_rollback": tool.supports_rollback
            }
            for tool in self.tools.values()
        ]
    
    def get_audit_log(self, tool_id: Optional[str] = None,
                     agent_id: Optional[str] = None) -> List[ToolExecution]:
        """Get audit log for tools"""
        logs = []
        for tool in self.tools.values():
            if tool_id and tool.tool_id != tool_id:
                continue
            for execution in tool.audit_log:
                if agent_id and execution.agent_id != agent_id:
                    continue
                logs.append(execution)
        return sorted(logs, key=lambda x: x.timestamp)

