"""
TickTick API Client

This module provides a wrapper around the TickTick Open API.
Documentation: https://developer.ticktick.com/api
"""

import requests
import logging
from typing import Dict, List, Optional, Any


class TickTickAPIError(Exception):
    """Custom exception for TickTick API errors"""
    pass


class TickTickClient:
    """Client for interacting with TickTick Open API"""
    
    BASE_URL = "https://api.ticktick.com/open/v1"
    
    def __init__(self, access_token: str):
        """
        Initialize TickTick client
        
        Args:
            access_token: OAuth access token for TickTick API
        """
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        })
        self.logger = logging.getLogger(__name__)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to TickTick API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            JSON response as dictionary
            
        Raises:
            TickTickAPIError: If the API request fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            # Some endpoints return empty response
            if response.status_code == 204 or not response.content:
                return {}
                
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response: {e.response.text}")
            raise TickTickAPIError(f"API request failed: {e}")
    
    def get_completed_tasks(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of completed tasks
        
        Args:
            project_id: Optional project/list ID to filter tasks
            
        Returns:
            List of completed task objects
        """
        endpoint = "/task/completed"
        params = {}
        if project_id:
            params["projectId"] = project_id
            
        response = self._make_request("GET", endpoint, params=params)
        return response if isinstance(response, list) else []
    
    def get_task(self, task_id: str, project_id: str) -> Dict[str, Any]:
        """
        Get details of a specific task
        
        Args:
            task_id: Task ID
            project_id: Project/List ID the task belongs to
            
        Returns:
            Task object
        """
        endpoint = f"/task/{task_id}"
        params = {"projectId": project_id}
        return self._make_request("GET", endpoint, params=params)
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new task
        
        Args:
            task_data: Task object containing task details
            
        Returns:
            Created task object
        """
        endpoint = "/task"
        return self._make_request("POST", endpoint, json=task_data)
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get all projects/lists
        
        Returns:
            List of project objects
        """
        endpoint = "/project"
        response = self._make_request("GET", endpoint)
        return response if isinstance(response, list) else []
