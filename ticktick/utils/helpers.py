"""
Utility functions for TickTick automations
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Set


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
            with open(state_file, "r") as f:
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
        with open(state_file, "w") as f:
            json.dump(state_data, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to save state to {state_file}: {e}")
