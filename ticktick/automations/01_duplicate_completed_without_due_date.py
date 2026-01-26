import os
import subprocess
from typing import Any

from dotenv import load_dotenv
from loguru import logger

from ticktick.utils import TickTickClient, load_state, save_state

load_dotenv()


def duplicate_task_without_due_date(original_task: dict[str, Any]) -> dict[str, Any]:
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
    }

    # Copy items (checklist) if present
    if "items" in original_task and original_task["items"]:
        new_task["items"] = original_task["items"]

    return new_task


def automation(pending_valid_tasks_path: str):
    """Duplicates valid tasks with no due date upon completion

    Definition of a valid task:
    - Task title should start with the string "Zap:" (case insensitive)

    Args:
        pending_valid_tasks_path: Path to JSON file containing state of valid tasks
    """
    valid_task_title_prefix = "zap:"

    client = TickTickClient(
        os.environ["TICKTICK_CLIENT_ID"],
        os.environ["TICKTICK_CLIENT_SECRET"],
        os.environ["TICKTICK_ACCESS_TOKEN"],
    )

    old_state = load_state(pending_valid_tasks_path)
    logger.info(f"Loaded {len(old_state)} tasks from {pending_valid_tasks_path}")
    new_state = {task["id"]: task for task in client.get_all_pending_tasks()}
    logger.info(f"Found {len(new_state)} pending tasks")

    for task_id in set(old_state.keys()) - set(new_state.keys()):
        logger.info(f"Task not found in current state: {task_id}")

        # Update the task with the new state
        task = old_state[task_id]
        task = client.get_task(task["projectId"], task["id"])

        # Check if task was completed
        if task["status"] == 2:
            # Task was completed
            logger.info(f"Duplicating {task['title']}")

            # Duplicate the task
            new_task = duplicate_task_without_due_date(task)
            new_task = client.create_task(new_task)

            # Mark as processed
            new_state[new_task["id"]] = new_task

    # Limit new state to only valid tasks
    new_state = {
        key: value for key, value in new_state.items() if value["title"].lower().startswith(valid_task_title_prefix)
    }

    # Save new state
    save_state(pending_valid_tasks_path, new_state)
    logger.info(f"Saved {len(new_state)} tasks to {pending_valid_tasks_path}")


def mac_alert(title, message):
    script = f"""
    display alert "{title}" message "{message}"
    """
    subprocess.run(["osascript", "-e", script])


if __name__ == "__main__":
    import atexit
    import time

    import schedule

    atexit.register(mac_alert, "Ticktick", "Automation ending")

    pending_valid_tasks_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "rsrc", "01_pending_valid_tasks.json")
    )

    while True:
        # Schedule the job if not scheduled till now
        if not schedule.get_jobs():
            logger.info("Starting automation")
            mac_alert("Ticktick", "Automation (re)starting")
            schedule.every().minute.do(automation, pending_valid_tasks_path)
            automation(pending_valid_tasks_path)

        try:
            schedule.run_pending()
        except Exception as e:
            mac_alert("Ticktick", f"Automation error: {e}")
        time.sleep(1)  # Sleep for a short interval to avoid high CPU usage
