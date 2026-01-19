"""
Utility functions for TickTick automations
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Set, Any


def load_state(state_file: str) -> Dict[str, Any]:
    """
    Load state from JSON file
    
    Args:
        state_file: Path to state file
        
    Returns:
        Dictionary containing state data
    """
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load state from {state_file}: {e}")
    return {}


def save_state(state_file: str, state_data: Dict[str, Any]):
    """
    Save state to JSON file
    
    Args:
        state_file: Path to state file
        state_data: Dictionary containing state data
    """
    try:
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to save state to {state_file}: {e}")


def get_processed_tasks(state_file: str) -> Set[str]:
    """
    Get set of processed task IDs from state file
    
    Args:
        state_file: Path to state file
        
    Returns:
        Set of processed task IDs
    """
    state = load_state(state_file)
    return set(state.get("processed_tasks", []))


def save_processed_tasks(state_file: str, task_ids: Set[str]):
    """
    Save processed task IDs to state file
    
    Args:
        state_file: Path to state file
        task_ids: Set of processed task IDs
    """
    from datetime import timezone
    state_data = {
        "processed_tasks": list(task_ids),
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    save_state(state_file, state_data)


def create_duplicate_task(original_task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a duplicate of the task without due date
    
    Args:
        original_task: Original completed task
        
    Returns:
        New task data object
    """
    # Create new task with same properties
    new_task = {
        "title": original_task.get("title"),
        "projectId": original_task.get("projectId"),
        "content": original_task.get("content", ""),
        "desc": original_task.get("desc", ""),
        "priority": original_task.get("priority", 0),
        "tags": original_task.get("tags", []),
    }
    
    # Copy items (checklist) if present
    if "items" in original_task and original_task["items"]:
        new_task["items"] = original_task["items"]
    
    # Explicitly exclude dueDate, startDate, and completedTime
    # The new task should have no due date as per requirements
    
    return new_task
