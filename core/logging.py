"""
Logging System for AI Agent Orchestrator
Provides structured logging, traceability, and metrics.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
from pathlib import Path


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Log categories"""
    MISSION = "mission"
    ORCHESTRATOR = "orchestrator"
    AGENT = "agent"
    TOOL = "tool"
    MEMORY = "memory"
    POLICY = "policy"
    EXECUTION = "execution"
    METRICS = "metrics"


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "category": self.category.value,
            "message": self.message,
            "context": self.context,
            "trace_id": self.trace_id,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class Logger:
    """Structured logger for orchestrator"""
    
    def __init__(self, log_file: Optional[str] = None, level: LogLevel = LogLevel.INFO):
        self.log_file = log_file
        self.level = level
        self.logs: List[LogEntry] = []
        self.trace_map: Dict[str, List[LogEntry]] = {}
        
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        self._setup_python_logging()
    
    def _setup_python_logging(self):
        """Setup Python logging"""
        logging.basicConfig(
            level=getattr(logging, self.level.value),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.log_file) if self.log_file else logging.NullHandler()
            ]
        )
        self.py_logger = logging.getLogger("ai_orchestrator")
    
    def log(self, level: LogLevel, category: LogCategory, message: str,
           context: Optional[Dict[str, Any]] = None,
           trace_id: Optional[str] = None,
           mission_id: Optional[str] = None,
           task_id: Optional[str] = None,
           agent_id: Optional[str] = None) -> LogEntry:
        """Create log entry"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            category=category,
            message=message,
            context=context or {},
            trace_id=trace_id,
            mission_id=mission_id,
            task_id=task_id,
            agent_id=agent_id
        )
        
        self.logs.append(entry)
        
        if trace_id:
            if trace_id not in self.trace_map:
                self.trace_map[trace_id] = []
            self.trace_map[trace_id].append(entry)
        
        log_method = getattr(self.py_logger, level.value.lower())
        log_method(f"[{category.value}] {message}", extra=entry.context)
        
        if self.log_file:
            self._write_to_file(entry)
        
        return entry
    
    def _write_to_file(self, entry: LogEntry):
        """Write log entry to file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(entry.to_json() + '\n')
        except Exception:
            pass
    
    def get_logs(self, category: Optional[LogCategory] = None,
                mission_id: Optional[str] = None,
                trace_id: Optional[str] = None) -> List[LogEntry]:
        """Get logs with filters"""
        logs = self.logs
        if category:
            logs = [l for l in logs if l.category == category]
        if mission_id:
            logs = [l for l in logs if l.mission_id == mission_id]
        if trace_id:
            logs = [l for l in logs if l.trace_id == trace_id]
        return logs
    
    def get_trace(self, trace_id: str) -> List[LogEntry]:
        """Get all logs for a trace"""
        return self.trace_map.get(trace_id, [])
    
    def clear_logs(self):
        """Clear all logs"""
        self.logs.clear()
        self.trace_map.clear()


@dataclass
class Metric:
    """Performance metric"""
    name: str
    value: float
    unit: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "mission_id": self.mission_id,
            "task_id": self.task_id
        }


class MetricsCollector:
    """Collects and aggregates metrics"""
    
    def __init__(self):
        self.metrics: List[Metric] = []
        self.aggregations: Dict[str, List[float]] = {}
    
    def record(self, name: str, value: float, unit: str = "",
              tags: Optional[Dict[str, str]] = None,
              mission_id: Optional[str] = None,
              task_id: Optional[str] = None) -> Metric:
        """Record a metric"""
        metric = Metric(
            name=name,
            value=value,
            unit=unit,
            tags=tags or {},
            mission_id=mission_id,
            task_id=task_id
        )
        self.metrics.append(metric)
        
        if name not in self.aggregations:
            self.aggregations[name] = []
        self.aggregations[name].append(value)
        
        return metric
    
    def get_metric(self, name: str, mission_id: Optional[str] = None) -> List[Metric]:
        """Get metrics by name"""
        metrics = [m for m in self.metrics if m.name == name]
        if mission_id:
            metrics = [m for m in metrics if m.mission_id == mission_id]
        return metrics
    
    def get_statistics(self, name: str) -> Dict[str, float]:
        """Get statistics for a metric"""
        if name not in self.aggregations:
            return {}
        
        values = self.aggregations[name]
        if not values:
            return {}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "sum": sum(values)
        }
    
    def get_mission_metrics(self, mission_id: str) -> Dict[str, Any]:
        """Get all metrics for a mission"""
        mission_metrics = [m for m in self.metrics if m.mission_id == mission_id]
        
        result = {
            "mission_id": mission_id,
            "metrics": [m.to_dict() for m in mission_metrics],
            "summary": {}
        }
        
        metric_names = set(m.name for m in mission_metrics)
        for name in metric_names:
            result["summary"][name] = self.get_statistics(name)
        
        return result
    
    def clear_metrics(self):
        """Clear all metrics"""
        self.metrics.clear()
        self.aggregations.clear()


class Traceability:
    """Traceability system for end-to-end tracking"""
    
    def __init__(self, logger: Logger, metrics: MetricsCollector):
        self.logger = logger
        self.metrics = metrics
        self.traces: Dict[str, Dict[str, Any]] = {}
    
    def start_trace(self, trace_id: str, mission_id: str, goal: str) -> str:
        """Start a new trace"""
        self.traces[trace_id] = {
            "trace_id": trace_id,
            "mission_id": mission_id,
            "goal": goal,
            "start_time": datetime.now(),
            "events": [],
            "metrics": []
        }
        
        self.logger.log(
            LogLevel.INFO,
            LogCategory.EXECUTION,
            f"Trace started: {trace_id}",
            trace_id=trace_id,
            mission_id=mission_id
        )
        
        return trace_id
    
    def add_event(self, trace_id: str, event_type: str, description: str,
                 context: Optional[Dict[str, Any]] = None):
        """Add event to trace"""
        if trace_id not in self.traces:
            return
        
        event = {
            "event_type": event_type,
            "description": description,
            "timestamp": datetime.now(),
            "context": context or {}
        }
        
        self.traces[trace_id]["events"].append(event)
        
        self.logger.log(
            LogLevel.INFO,
            LogCategory.EXECUTION,
            f"Event: {event_type} - {description}",
            context=context,
            trace_id=trace_id,
            mission_id=self.traces[trace_id]["mission_id"]
        )
    
    def end_trace(self, trace_id: str, status: str, result: Optional[Dict[str, Any]] = None):
        """End a trace"""
        if trace_id not in self.traces:
            return
        
        trace = self.traces[trace_id]
        trace["end_time"] = datetime.now()
        trace["status"] = status
        trace["result"] = result
        trace["duration"] = (trace["end_time"] - trace["start_time"]).total_seconds()
        
        self.logger.log(
            LogLevel.INFO,
            LogCategory.EXECUTION,
            f"Trace ended: {trace_id} - Status: {status}",
            trace_id=trace_id,
            mission_id=trace["mission_id"]
        )
        
        self.metrics.record(
            "trace_duration",
            trace["duration"],
            "seconds",
            {"status": status},
            trace["mission_id"]
        )
    
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get trace information"""
        return self.traces.get(trace_id)
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get trace summary"""
        trace = self.traces.get(trace_id)
        if not trace:
            return {}
        
        return {
            "trace_id": trace_id,
            "mission_id": trace["mission_id"],
            "goal": trace["goal"],
            "status": trace.get("status", "in_progress"),
            "duration": trace.get("duration", 0.0),
            "event_count": len(trace["events"]),
            "events": trace["events"][-10:] if len(trace["events"]) > 10 else trace["events"]
        }


