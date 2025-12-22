# TickTick Automations

Automate your TickTick tasks with powerful automation scripts. Currently supports automatic task duplication for recurring workflows.

## Features

### Task Duplication Automation

Automatically duplicates completed tasks based on filters:
- ✅ Filter by task name (substring match)
- ✅ Filter by tags (any matching tag)
- ✅ Duplicates task with same name, list, content, and checklist items
- ✅ New task has no due date (as per design)
- ✅ Tracks processed tasks to avoid duplicates
- ✅ Can run via GitHub Actions (scheduled) or locally in tmux

## Setup

### Prerequisites

- Python 3.8 or higher
- TickTick account
- TickTick Open API credentials

### Getting TickTick API Credentials

1. Go to [TickTick Developer Console](https://developer.ticktick.com/)
2. Create a new application
3. Get your Client ID and Client Secret
4. Follow the OAuth flow to get an access token
   - You'll need to implement OAuth authorization or use a tool like Postman
   - The access token is what you'll use for this automation

### Installation

1. Clone this repository:
```bash
git clone https://github.com/arjunagarwal899/ticktick_automations.git
cd ticktick_automations
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file from the example:
```bash
cp .env.example .env
```

4. Edit `.env` and add your credentials:
```env
TICKTICK_ACCESS_TOKEN=your_access_token_here
TASK_FILTER_TAGS=recurring,daily
TASK_NAME_FILTER=
POLLING_INTERVAL=300
```

## Usage

### Running Locally

#### Run Once
Process completed tasks once and exit:
```bash
python main.py --once
```

#### Run Continuously (Polling Mode)
Run continuously, checking for new completed tasks at regular intervals:
```bash
python main.py
```

With custom interval (in seconds):
```bash
python main.py --interval 600  # Check every 10 minutes
```

#### Run in tmux Session
For long-running processes, use tmux:
```bash
# Create a new tmux session
tmux new -s ticktick

# Inside tmux, run the automation
python main.py

# Detach from tmux: Press Ctrl+B, then D
# Reattach later: tmux attach -t ticktick
```

### Running on GitHub Actions

The automation can run automatically on GitHub Actions on a schedule.

#### Setup GitHub Actions

1. Go to your repository Settings → Secrets and variables → Actions

2. Add the following **Secret**:
   - `TICKTICK_ACCESS_TOKEN`: Your TickTick access token

3. Add the following **Variables** (optional):
   - `TASK_FILTER_TAGS`: Comma-separated tags (e.g., `recurring,daily`)
   - `TASK_NAME_FILTER`: Substring to filter task names

4. The workflow is configured to run every 5 minutes. Edit `.github/workflows/automation.yml` to change the schedule:
```yaml
schedule:
  - cron: '*/5 * * * *'  # Every 5 minutes
  # - cron: '0 * * * *'  # Every hour
  # - cron: '0 0 * * *'  # Once a day at midnight
```

5. You can also trigger the workflow manually from the Actions tab.

## Configuration

### Environment Variables

- **TICKTICK_ACCESS_TOKEN** (required): OAuth access token for TickTick API
- **TASK_FILTER_TAGS** (optional): Comma-separated list of tags. Tasks with ANY of these tags will be duplicated.
- **TASK_NAME_FILTER** (optional): Substring to match in task names. Only matching tasks will be duplicated.
- **POLLING_INTERVAL** (optional): Seconds between checks when running in polling mode. Default: 300 (5 minutes)

### Filters

The automation will only duplicate tasks that match ALL configured filters:
- If `TASK_FILTER_TAGS` is set, task must have at least one of the specified tags
- If `TASK_NAME_FILTER` is set, task name must contain the filter string (case-insensitive)
- If both are set, both conditions must be met

#### Examples

**Duplicate all completed tasks with "daily" or "recurring" tag:**
```env
TASK_FILTER_TAGS=daily,recurring
TASK_NAME_FILTER=
```

**Duplicate all completed tasks with "exercise" in the name:**
```env
TASK_FILTER_TAGS=
TASK_NAME_FILTER=exercise
```

**Duplicate only tasks tagged "recurring" with "workout" in the name:**
```env
TASK_FILTER_TAGS=recurring
TASK_NAME_FILTER=workout
```

## How It Works

1. **Fetch Completed Tasks**: Queries TickTick API for all completed tasks
2. **Apply Filters**: Checks each task against name and tag filters
3. **Check State**: Skips tasks that have already been processed
4. **Duplicate Task**: Creates a new task with:
   - Same title, content, description
   - Same project/list
   - Same priority and tags
   - Same checklist items (if any)
   - **No due date** (intentionally left empty)
5. **Save State**: Records processed task IDs to avoid re-processing

## Files

- `main.py`: Main entry point for the automation
- `ticktick_client.py`: TickTick API client wrapper
- `automation.py`: Core automation logic for task duplication
- `requirements.txt`: Python dependencies
- `.env.example`: Example environment configuration
- `.github/workflows/automation.yml`: GitHub Actions workflow
- `processed_tasks.json`: State file tracking processed tasks (auto-generated)
- `ticktick_automation.log`: Log file (auto-generated)

## Troubleshooting

### Authentication Errors
- Verify your access token is correct and not expired
- TickTick access tokens may need to be refreshed periodically

### Tasks Not Being Duplicated
- Check the filters in your `.env` file
- Review `ticktick_automation.log` for details
- Verify tasks are marked as completed in TickTick
- Check `processed_tasks.json` - tasks listed here won't be processed again

### GitHub Actions Not Running
- Verify secrets and variables are set correctly in repository settings
- Check workflow permissions in repository settings
- Review workflow runs in the Actions tab for errors

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new automation ideas
- Submit pull requests

## License

See LICENSE file for details.