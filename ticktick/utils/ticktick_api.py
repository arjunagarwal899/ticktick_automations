"""
TickTick API Client with OAuth Authentication

This module provides a wrapper around the TickTick Open API with OAuth2 authentication.
Documentation: https://developer.ticktick.com/api
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import requests


class TickTickAPIError(Exception):
    """Custom exception for TickTick API errors"""

    pass


class TickTickClient:
    """Client for interacting with TickTick Open API with OAuth2"""

    BASE_URL_v1 = "https://api.ticktick.com/open/v1"
    BASE_URL_v2 = "https://api.ticktick.com/api/v2"
    AUTH_URL = "https://ticktick.com/oauth/token"

    def __init__(self, client_id: str, client_secret: str, access_token: str | None = None):
        """
        Initialize TickTick client with OAuth credentials

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            access_token: cached access token
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
        self.session.headers.update({"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"})

    def authenticate(self, code: str | None = None, redirect_uri: str | None = None):
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
                f"1. Visit: https://ticktick.com/oauth/authorize?client_id={self.client_id}&scope=tasks:read tasks:write&redirect_uri={{redirect_uri}}\n"
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
                    "redirect_uri": redirect_uri or "http://localhost",
                },
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

    def _make_request(self, method: str, api_ver: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """
        Make HTTP request to TickTick API

        Args:
            method: HTTP method (GET, POST, etc.)
            api_ver: API version. v1 or v2 (undocumented)
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to requests

        Returns:
            JSON response as dictionary

        Raises:
            TickTickAPIError: If the API request fails
        """
        if not self.access_token:
            raise TickTickAPIError("Not authenticated. Please authenticate first.")

        if api_ver == "v1":
            url = f"{self.BASE_URL_v1}{endpoint}"
        elif api_ver == "v2":
            url = f"{self.BASE_URL_v2}{endpoint}"
        else:
            raise ValueError(f"Invalid API version: {api_ver}")

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()

            # Some endpoints return empty response
            if response.status_code == 204 or not response.content:
                return {}

            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                self.logger.error(f"Response: {e.response.text}")
            raise TickTickAPIError(f"API request failed: {e}")

    def get_projects(self) -> list[dict[str, Any]]:
        """
        Get all projects/lists

        Returns:
            list of project objects
        """
        endpoint = "/project"
        response = self._make_request("GET", "v1", endpoint)
        return response if isinstance(response, list) else []

    def get_project_data(self, project_id: str) -> dict[str, Any]:
        """
        Get detailed data of a specific project/list

        Args:
            project_id: Project/list ID

        Returns:
            Project data object
        """
        endpoint = f"/project/{project_id}/data"
        response = self._make_request("GET", "v1", endpoint)
        return response if isinstance(response, dict) else {}

    def get_all_pending_tasks(self, project_id: str | None = None) -> list[dict[str, Any]]:
        """
        Get list of all pending tasks

        Args:
            project_id: project/list ID to filter tasks

        Returns:
            list of all task objects
        """
        if project_id is None:
            project_ids = [proj["id"] for proj in self.get_projects()]
        else:
            project_ids = [project_id]

        tasks = []
        for project_id in project_ids:
            response = self.get_project_data(project_id)
            tasks.extend(response.get("tasks", []))
        return tasks

    def get_task(self, project_id: str, task_id) -> list[dict[str, Any]]:
        """Get details of a particular task"""
        endpoint = f"/project/{project_id}/task/{task_id}"
        response = self._make_request("GET", "v1", endpoint)
        return response if isinstance(response, dict) else {}

    def create_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new task

        Args:
            task_data: Task object containing task details

        Returns:
            Created task object
        """
        endpoint = "/task"
        return self._make_request("POST", "v1", endpoint, json=task_data)
