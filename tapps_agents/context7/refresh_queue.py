"""
Refresh Queue for Context7 KB cache.

Manages a queue of cache entries that need to be refreshed, with support for
priority, scheduling, and batch processing.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import yaml

from .staleness_policies import StalenessPolicyManager, StalenessPolicy


@dataclass
class RefreshTask:
    """Represents a refresh task in the queue."""
    library: str
    topic: Optional[str] = None  # None means refresh entire library
    priority: int = 5  # 1-10, higher = more urgent
    reason: str = "staleness"
    added_at: str = None
    scheduled_for: Optional[str] = None
    attempts: int = 0
    last_attempt: Optional[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.added_at is None:
            self.added_at = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RefreshTask":
        """Create from dictionary."""
        return cls(**data)


class RefreshQueue:
    """Manages refresh queue for Context7 KB cache."""
    
    def __init__(self, queue_file: Path, policy_manager: Optional[StalenessPolicyManager] = None):
        """
        Initialize refresh queue.
        
        Args:
            queue_file: Path to queue file (YAML or JSON)
            policy_manager: Optional StalenessPolicyManager instance
        """
        self.queue_file = Path(queue_file)
        self.policy_manager = policy_manager or StalenessPolicyManager()
        self.tasks: List[RefreshTask] = []
        self._load_queue()
    
    def _load_queue(self):
        """Load queue from file."""
        if not self.queue_file.exists():
            self.tasks = []
            return
        
        try:
            if self.queue_file.suffix == '.yaml' or self.queue_file.suffix == '.yml':
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
            else:
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            tasks_data = data.get('tasks', [])
            self.tasks = [RefreshTask.from_dict(task) for task in tasks_data]
        except Exception as e:
            # If we can't load, start with empty queue
            self.tasks = []
    
    def _save_queue(self):
        """Save queue to file."""
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'version': '1.0',
            'last_updated': datetime.utcnow().isoformat() + "Z",
            'tasks': [task.to_dict() for task in self.tasks]
        }
        
        try:
            if self.queue_file.suffix == '.yaml' or self.queue_file.suffix == '.yml':
                with open(self.queue_file, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
            else:
                with open(self.queue_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            # Log error but don't fail
            pass
    
    def add_task(
        self,
        library: str,
        topic: Optional[str] = None,
        priority: int = 5,
        reason: str = "staleness",
        scheduled_for: Optional[str] = None
    ) -> RefreshTask:
        """
        Add a task to the refresh queue.
        
        Args:
            library: Library name
            topic: Optional topic name (None = entire library)
            priority: Priority (1-10, higher = more urgent)
            reason: Reason for refresh
            scheduled_for: Optional scheduled timestamp
        
        Returns:
            RefreshTask instance
        """
        # Check if task already exists
        existing = self._find_task(library, topic)
        if existing:
            # Update existing task
            existing.priority = max(existing.priority, priority)
            existing.reason = reason
            if scheduled_for:
                existing.scheduled_for = scheduled_for
            self._save_queue()
            return existing
        
        # Create new task
        task = RefreshTask(
            library=library,
            topic=topic,
            priority=priority,
            reason=reason,
            scheduled_for=scheduled_for
        )
        
        self.tasks.append(task)
        self._save_queue()
        return task
    
    def _find_task(self, library: str, topic: Optional[str] = None) -> Optional[RefreshTask]:
        """Find existing task for library/topic."""
        for task in self.tasks:
            if task.library == library and task.topic == topic:
                return task
        return None
    
    def remove_task(self, library: str, topic: Optional[str] = None) -> bool:
        """
        Remove a task from the queue.
        
        Args:
            library: Library name
            topic: Optional topic name
        
        Returns:
            True if task was removed, False if not found
        """
        task = self._find_task(library, topic)
        if task:
            self.tasks.remove(task)
            self._save_queue()
            return True
        return False
    
    def get_next_task(self, max_priority: int = 10) -> Optional[RefreshTask]:
        """
        Get next task from queue, prioritized by urgency.
        
        Args:
            max_priority: Maximum priority to consider
        
        Returns:
            RefreshTask or None if queue is empty
        """
        # Filter by priority and schedule
        now = datetime.utcnow().isoformat() + "Z"
        available_tasks = [
            task for task in self.tasks
            if task.priority <= max_priority
            and (not task.scheduled_for or task.scheduled_for <= now)
        ]
        
        if not available_tasks:
            return None
        
        # Sort by priority (higher first), then by added_at (older first)
        available_tasks.sort(key=lambda t: (-t.priority, t.added_at))
        return available_tasks[0]
    
    def get_all_tasks(self) -> List[RefreshTask]:
        """Get all tasks in the queue."""
        return self.tasks.copy()
    
    def mark_task_completed(self, library: str, topic: Optional[str] = None, error: Optional[str] = None):
        """
        Mark a task as completed (success or failure).
        
        Args:
            library: Library name
            topic: Optional topic name
            error: Optional error message (if failed)
        """
        task = self._find_task(library, topic)
        if task:
            task.attempts += 1
            task.last_attempt = datetime.utcnow().isoformat() + "Z"
            if error:
                task.error = error
                # Keep task in queue if it failed (for retry)
            else:
                # Remove from queue on success
                self.remove_task(library, topic)
            self._save_queue()
    
    def queue_stale_entries(
        self,
        entries: List[Dict[str, Any]],
        library_type_map: Optional[Dict[str, str]] = None,
        reference_date: Optional[datetime] = None
    ) -> int:
        """
        Queue multiple stale entries for refresh.
        
        Args:
            entries: List of entry dictionaries with 'library', 'topic', 'last_updated'
            library_type_map: Optional mapping of library -> library_type
        
        Returns:
            Number of entries queued
        """
        queued = 0
        
        for entry in entries:
            library = entry.get('library')
            topic = entry.get('topic')
            last_updated = entry.get('last_updated')
            
            if not library or not last_updated:
                continue
            
            library_type = None
            if library_type_map:
                library_type = library_type_map.get(library)
            
            is_stale = self.policy_manager.is_entry_stale(library, last_updated, library_type, reference_date=reference_date)
            
            if is_stale:
                # Determine priority based on staleness
                # Use reference_date or current time for recommendations
                if reference_date is None:
                    from datetime import datetime
                    reference_date = datetime.utcnow()
                recommendation = self.policy_manager.get_refresh_recommendation(
                    library, last_updated, library_type, reference_date=reference_date
                )
                
                priority = 5  # Default
                days_until_stale = recommendation.get('days_until_stale', 0)
                if days_until_stale < -7:  # Very stale (more than 7 days past max age)
                    priority = 9
                elif days_until_stale < 0:  # Stale (past max age)
                    priority = 7
                elif recommendation.get('recommendation') == 'consider_refresh':
                    priority = 3
                
                self.add_task(
                    library=library,
                    topic=topic,
                    priority=priority,
                    reason="staleness"
                )
                queued += 1
        
        return queued
    
    def clear_queue(self):
        """Clear all tasks from the queue."""
        self.tasks = []
        self._save_queue()
    
    def size(self) -> int:
        """Get queue size."""
        return len(self.tasks)

