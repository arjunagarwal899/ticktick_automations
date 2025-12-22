"""
TickTick Task Duplication Automation

This module contains the core logic for automatically duplicating completed tasks
based on specified filters (task name and tags).
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Set, Any, Optional

from ticktick_client import TickTickClient, TickTickAPIError


class TaskDuplicator:
    """Handles automatic duplication of completed tasks"""
    
    STATE_FILE = "processed_tasks.json"
    
    def __init__(
        self,
        client: TickTickClient,
        name_filter: Optional[str] = None,
        tag_filters: Optional[List[str]] = None
    ):
        """
        Initialize task duplicator
        
        Args:
            client: TickTickClient instance
            name_filter: Optional string to filter task names (substring match)
            tag_filters: Optional list of tags to filter tasks
        """
        self.client = client
        self.name_filter = name_filter
        self.tag_filters = tag_filters or []
        self.logger = logging.getLogger(__name__)
        self.processed_task_ids = self._load_processed_tasks()
    
    def _load_processed_tasks(self) -> Set[str]:
        """
        Load set of already processed task IDs from state file
        
        Returns:
            Set of processed task IDs
        """
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, 'r') as f:
                    data = json.load(f)
                    return set(data.get("processed_tasks", []))
            except Exception as e:
                self.logger.warning(f"Failed to load processed tasks: {e}")
        return set()
    
    def _save_processed_tasks(self):
        """Save processed task IDs to state file"""
        try:
            with open(self.STATE_FILE, 'w') as f:
                json.dump({
                    "processed_tasks": list(self.processed_task_ids),
                    "last_updated": datetime.utcnow().isoformat()
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save processed tasks: {e}")
    
    def _matches_filters(self, task: Dict[str, Any]) -> bool:
        """
        Check if task matches the configured filters
        
        Args:
            task: Task object from TickTick API
            
        Returns:
            True if task matches all filters, False otherwise
        """
        # Check name filter
        if self.name_filter:
            task_title = task.get("title", "").lower()
            if self.name_filter.lower() not in task_title:
                return False
        
        # Check tag filters
        if self.tag_filters:
            task_tags = task.get("tags", [])
            # Task must have at least one of the specified tags
            if not any(tag in task_tags for tag in self.tag_filters):
                return False
        
        return True
    
    def _create_duplicate_task(self, original_task: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def process_completed_tasks(self) -> Dict[str, int]:
        """
        Process completed tasks and duplicate matching ones
        
        Returns:
            Dictionary with statistics (checked, matched, duplicated, errors)
        """
        stats = {
            "checked": 0,
            "matched": 0,
            "duplicated": 0,
            "errors": 0
        }
        
        try:
            # Get all completed tasks
            completed_tasks = self.client.get_completed_tasks()
            self.logger.info(f"Found {len(completed_tasks)} completed tasks")
            
            for task in completed_tasks:
                stats["checked"] += 1
                task_id = task.get("id")
                
                # Skip if already processed
                if task_id in self.processed_task_ids:
                    continue
                
                # Check if task matches filters
                if not self._matches_filters(task):
                    # Mark as processed even if it doesn't match
                    # to avoid checking it again
                    self.processed_task_ids.add(task_id)
                    continue
                
                stats["matched"] += 1
                self.logger.info(f"Processing task: {task.get('title')} (ID: {task_id})")
                
                try:
                    # Create duplicate task
                    new_task_data = self._create_duplicate_task(task)
                    new_task = self.client.create_task(new_task_data)
                    
                    self.logger.info(
                        f"Successfully duplicated task '{task.get('title')}'. "
                        f"New task ID: {new_task.get('id')}"
                    )
                    stats["duplicated"] += 1
                    
                    # Mark as processed
                    self.processed_task_ids.add(task_id)
                    
                except TickTickAPIError as e:
                    self.logger.error(f"Failed to duplicate task {task_id}: {e}")
                    stats["errors"] += 1
            
            # Save processed tasks state
            self._save_processed_tasks()
            
        except TickTickAPIError as e:
            self.logger.error(f"Failed to fetch completed tasks: {e}")
            stats["errors"] += 1
        
        return stats
