"""Simple REST API example."""

from typing import List, Dict

class TaskAPI:
    """Task management API."""
    
    def __init__(self):
        self.tasks: List[Dict] = []
    
    def create_task(self, title: str, description: str) -> Dict:
        """Create a new task."""
        task = {
            "id": len(self.tasks) + 1,
            "title": title,
            "description": description,
            "completed": False
        }
        self.tasks.append(task)
        return task
    
    def get_task(self, task_id: int) -> Dict:
        """Get a task by ID."""
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None  # Bug: Should raise exception
    
    def complete_task(self, task_id: int) -> bool:
        """Mark task as completed."""
        task = self.get_task(task_id)
        if task:
            task["completed"] = True
            return True
        return False
