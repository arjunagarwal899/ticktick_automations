#!/usr/bin/env python3
"""
TickTick Automations Main Script

This script runs TickTick automations. It can run once or continuously poll
at specified intervals.

Usage:
    # Run once
    python main.py --once
    
    # Run continuously (polling mode)
    python main.py
    
    # Run with custom polling interval
    python main.py --interval 600
"""

import argparse
import logging
import os
import sys
import time
from typing import Optional

from dotenv import load_dotenv

from ticktick_client import TickTickClient
from automation import TaskDuplicator


def setup_logging(verbose: bool = False):
    """
    Setup logging configuration
    
    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('ticktick_automation.log')
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
    
    access_token = os.getenv("TICKTICK_ACCESS_TOKEN")
    if not access_token:
        raise ValueError(
            "TICKTICK_ACCESS_TOKEN environment variable is required. "
            "Please set it in .env file or as environment variable."
        )
    
    # Parse tag filters
    tag_filters_str = os.getenv("TASK_FILTER_TAGS", "")
    tag_filters = [tag.strip() for tag in tag_filters_str.split(",") if tag.strip()]
    
    # Get name filter
    name_filter = os.getenv("TASK_NAME_FILTER", "").strip() or None
    
    # Get polling interval
    try:
        polling_interval = int(os.getenv("POLLING_INTERVAL", "300"))
    except ValueError:
        polling_interval = 300
    
    return {
        "access_token": access_token,
        "tag_filters": tag_filters,
        "name_filter": name_filter,
        "polling_interval": polling_interval
    }


def run_automation(client: TickTickClient, config: dict) -> dict:
    """
    Run the task duplication automation
    
    Args:
        client: TickTickClient instance
        config: Configuration dictionary
        
    Returns:
        Statistics dictionary
    """
    logger = logging.getLogger(__name__)
    
    duplicator = TaskDuplicator(
        client=client,
        name_filter=config["name_filter"],
        tag_filters=config["tag_filters"]
    )
    
    logger.info("Starting task duplication automation...")
    if config["name_filter"]:
        logger.info(f"Name filter: '{config['name_filter']}'")
    if config["tag_filters"]:
        logger.info(f"Tag filters: {config['tag_filters']}")
    
    stats = duplicator.process_completed_tasks()
    
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
        help="Run once and exit (default: run continuously)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Polling interval in seconds (overrides POLLING_INTERVAL env var)"
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
    
    try:
        # Load configuration
        config = load_config()
        
        # Override polling interval if provided
        if args.interval:
            config["polling_interval"] = args.interval
        
        # Create TickTick client
        client = TickTickClient(config["access_token"])
        
        if args.once:
            # Run once and exit
            logger.info("Running in single-run mode")
            run_automation(client, config)
            logger.info("Automation completed")
        else:
            # Run continuously
            logger.info(
                f"Running in polling mode with interval: "
                f"{config['polling_interval']} seconds"
            )
            logger.info("Press Ctrl+C to stop")
            
            while True:
                try:
                    run_automation(client, config)
                    logger.info(
                        f"Sleeping for {config['polling_interval']} seconds..."
                    )
                    time.sleep(config["polling_interval"])
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal, shutting down...")
                    break
                except Exception as e:
                    logger.error(f"Error during automation run: {e}", exc_info=True)
                    logger.info(
                        f"Will retry in {config['polling_interval']} seconds..."
                    )
                    time.sleep(config["polling_interval"])
    
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
