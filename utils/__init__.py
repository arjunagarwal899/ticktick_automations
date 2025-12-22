"""Utils package for TickTick automations"""

from .ticktick_api import TickTickClient, TickTickAPIError
from .helpers import (
    load_state,
    save_state,
    get_processed_tasks,
    save_processed_tasks,
    create_duplicate_task
)

__all__ = [
    'TickTickClient',
    'TickTickAPIError',
    'load_state',
    'save_state',
    'get_processed_tasks',
    'save_processed_tasks',
    'create_duplicate_task'
]
