#!/usr/bin/env python3
"""
Duplicate Completed Tasks Automation

This automation duplicates completed tasks from the last 24 hours that match
specified filters (task name and tags).

Usage:
    python automations/duplicate_completed_tasks.py --once
    python automations/duplicate_completed_tasks.py --interval 600
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Set

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from utils import (
    TickTickClient,
    TickTickAPIError,
    get_processed_tasks,
    save_processed_tasks,
    create_duplicate_task
)


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('duplicate_completed_tasks.log')
        ]
    )


def load_config() -> dict:
    """
    Load configuration from environment variables
    
    Returns:
        Dictionary with configuration values
        
    Raises:
        ValueError: If required environment variables are missing
    """
    load_dotenv()
    
    client_id = os.getenv("TICKTICK_CLIENT_ID")
    client_secret = os.getenv("TICKTICK_CLIENT_SECRET")
    access_token = os.getenv("TICKTICK_ACCESS_TOKEN")
    
    if not client_id or not client_secret:
        raise ValueError(
            "TICKTICK_CLIENT_ID and TICKTICK_CLIENT_SECRET environment variables are required. "
            "Please set them in .env file or as environment variables."
        )
    
    if not access_token:
        raise ValueError(
            "TICKTICK_ACCESS_TOKEN is required. Please obtain an access token through OAuth flow.\n"
            "See README for instructions on how to get an access token."
        )
    
    # Parse tag filters
    tag_filters_str = os.getenv("TASK_FILTER_TAGS", "")
    tag_filters = [tag.strip() for tag in tag_filters_str.split(",") if tag.strip()]
    
    # Get name filter
    name_filter = os.getenv("TASK_NAME_FILTER", "").strip() or None
    
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "access_token": access_token,
        "tag_filters": tag_filters,
        "name_filter": name_filter
    }


def matches_filters(task: Dict, name_filter: Optional[str], tag_filters: list) -> bool:
    """
    Check if task matches the configured filters
    
    Args:
        task: Task object from TickTick API
        name_filter: Optional name filter
        tag_filters: List of tag filters
        
    Returns:
        True if task matches all filters, False otherwise
    """
    # Check name filter
    if name_filter:
        task_title = task.get("title", "").lower()
        if name_filter.lower() not in task_title:
            return False
    
    # Check tag filters
    if tag_filters:
        task_tags = task.get("tags", [])
        # Task must have at least one of the specified tags
        if not any(tag in task_tags for tag in tag_filters):
            return False
    
    return True


def run_automation(client: TickTickClient, config: dict, state_file: str) -> dict:
    """
    Run the task duplication automation
    
    Args:
        client: TickTickClient instance
        config: Configuration dictionary
        state_file: Path to state file
        
    Returns:
        Statistics dictionary
    """
    logger = logging.getLogger(__name__)
    stats = {
        "checked": 0,
        "matched": 0,
        "duplicated": 0,
        "errors": 0
    }
    
    # Load processed tasks
    processed_task_ids = get_processed_tasks(state_file)
    
    logger.info("Starting task duplication automation...")
    if config["name_filter"]:
        logger.info(f"Name filter: '{config['name_filter']}'")
    if config["tag_filters"]:
        logger.info(f"Tag filters: {config['tag_filters']}")
    
    try:
        # Get completed tasks from the last 24 hours
        from datetime import timezone
        from_date = datetime.now(timezone.utc) - timedelta(days=1)
        logger.info(f"Fetching tasks completed after: {from_date.isoformat()}")
        
        completed_tasks = client.get_completed_tasks(from_date=from_date)
        logger.info(f"Found {len(completed_tasks)} completed tasks in the last 24 hours")
        
        for task in completed_tasks:
            stats["checked"] += 1
            task_id = task.get("id")
            
            # Skip tasks without valid ID
            if not task_id:
                logger.warning(f"Skipping task without ID: {task.get('title', 'Unknown')}")
                continue
            
            # Skip if already processed
            if task_id in processed_task_ids:
                continue
            
            # Check if task matches filters
            if not matches_filters(task, config["name_filter"], config["tag_filters"]):
                # Mark as processed even if it doesn't match to avoid checking again
                processed_task_ids.add(task_id)
                continue
            
            stats["matched"] += 1
            logger.info(f"Processing task: {task.get('title')} (ID: {task_id})")
            
            try:
                # Create duplicate task
                new_task_data = create_duplicate_task(task)
                new_task = client.create_task(new_task_data)
                
                logger.info(
                    f"Successfully duplicated task '{task.get('title')}'. "
                    f"New task ID: {new_task.get('id')}"
                )
                stats["duplicated"] += 1
                
                # Mark as processed
                processed_task_ids.add(task_id)
                
            except TickTickAPIError as e:
                logger.error(f"Failed to duplicate task {task_id}: {e}")
                stats["errors"] += 1
        
        # Save processed tasks state
        save_processed_tasks(state_file, processed_task_ids)
        
    except TickTickAPIError as e:
        logger.error(f"Failed to fetch completed tasks: {e}")
        stats["errors"] += 1
    
    logger.info(
        f"Automation completed - "
        f"Checked: {stats['checked']}, "
        f"Matched: {stats['matched']}, "
        f"Duplicated: {stats['duplicated']}, "
        f"Errors: {stats['errors']}"
    )
    
    return stats


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="TickTick Task Duplication Automation"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (default: run once)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)
    
    # State file for this automation
    state_file = "duplicate_completed_tasks_state.json"
    
    try:
        # Load configuration
        config = load_config()
        
        # Create TickTick client
        client = TickTickClient(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            access_token=config["access_token"]
        )
        
        logger.info("Running task duplication automation (single run)")
        run_automation(client, config, state_file)
        logger.info("Automation completed")
    
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
