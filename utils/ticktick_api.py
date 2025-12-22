"""
TickTick API Client with OAuth Authentication

This module provides a wrapper around the TickTick Open API with OAuth2 authentication.
Documentation: https://developer.ticktick.com/api
"""

import requests
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


class TickTickAPIError(Exception):
    """Custom exception for TickTick API errors"""
    pass


class TickTickClient:
    """Client for interacting with TickTick Open API with OAuth2"""
    
    BASE_URL = "https://api.ticktick.com/open/v1"
    AUTH_URL = "https://ticktick.com/oauth/token"
    
    def __init__(self, client_id: str, client_secret: str, access_token: Optional[str] = None):
        """
        Initialize TickTick client with OAuth credentials
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            access_token: Optional cached access token
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.token_expires_at = None
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
        if access_token:
            self._update_auth_header(access_token)
    
    def _update_auth_header(self, access_token: str):
        """Update session headers with access token"""
        self.access_token = access_token
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        })
    
    def authenticate(self, code: Optional[str] = None, redirect_uri: Optional[str] = None):
        """
        Authenticate with TickTick OAuth
        
        Args:
            code: Authorization code from OAuth flow (if available)
            redirect_uri: Redirect URI used in OAuth flow
            
        Note:
            If code is not provided, you need to obtain an access token through
            the OAuth flow manually and initialize the client with it.
        """
        if not code:
            raise TickTickAPIError(
                "OAuth code required. Please complete the OAuth flow manually:\n"
                "1. Visit: https://ticktick.com/oauth/authorize?client_id={}&scope=tasks:read tasks:write&redirect_uri={}\n"
                "2. Get the authorization code\n"
                "3. Exchange it for an access token using the /oauth/token endpoint"
            )
        
        try:
            response = requests.post(
                self.AUTH_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri or "http://localhost"
                }
            )
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)
            
            self._update_auth_header(access_token)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            return token_data
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Authentication failed: {e}")
            raise TickTickAPIError(f"Authentication failed: {e}")
    
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
        if not self.access_token:
            raise TickTickAPIError("Not authenticated. Please authenticate first.")
        
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
    
    def get_completed_tasks(
        self,
        project_id: Optional[str] = None,
        from_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of completed tasks
        
        Args:
            project_id: Optional project/list ID to filter tasks
            from_date: Optional datetime to filter tasks completed after this date
            
        Returns:
            List of completed task objects filtered by date if specified
        """
        endpoint = "/task/completed"
        params = {}
        if project_id:
            params["projectId"] = project_id
            
        response = self._make_request("GET", endpoint, params=params)
        tasks = response if isinstance(response, list) else []
        
        # Filter by completion date if specified
        if from_date and tasks:
            filtered_tasks = []
            for task in tasks:
                completed_time_str = task.get("completedTime")
                if completed_time_str:
                    try:
                        # Parse ISO format timestamp
                        completed_time = datetime.fromisoformat(
                            completed_time_str.replace('Z', '+00:00')
                        )
                        if completed_time >= from_date:
                            filtered_tasks.append(task)
                    except (ValueError, AttributeError) as e:
                        self.logger.warning(f"Failed to parse completedTime: {e}")
                        continue
            return filtered_tasks
        
        return tasks
    
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
