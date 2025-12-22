# TickTick Automations

Automate your TickTick tasks with powerful automation scripts. This project provides a modular framework for creating custom TickTick automations.

## Project Structure

```
ticktick_automations/
├── automations/              # Individual automation scripts
│   └── duplicate_completed_tasks.py
├── utils/                    # Shared utilities and API client
│   ├── __init__.py
│   ├── ticktick_api.py      # TickTick API client
│   └── helpers.py           # Helper functions
├── .github/workflows/        # GitHub Actions workflows
├── .env.example             # Environment variable template
└── README.md
```

## Available Automations

### 1. Duplicate Completed Tasks

Automatically duplicates tasks completed in the last 24 hours that match specified filters:
- ✅ Filter by task name (substring match)
- ✅ Filter by tags (any matching tag)
- ✅ Duplicates task with same name, list, content, and checklist items
- ✅ New task has no due date (as per design)
- ✅ Tracks processed tasks to avoid duplicates
- ✅ Only processes tasks completed in the last 24 hours
- ✅ Can run via GitHub Actions (scheduled) or locally

## Setup

### Prerequisites

- Python 3.8 or higher
- TickTick account
- TickTick Open API credentials (Client ID and Client Secret)

### Getting TickTick API Credentials

1. Go to [TickTick Developer Console](https://developer.ticktick.com/)
2. Create a new application
3. Note your **Client ID** and **Client Secret**

### Getting an Access Token

You need to complete the OAuth flow to get an access token:

1. **Authorization Request**: Visit this URL in your browser (replace YOUR_CLIENT_ID and YOUR_REDIRECT_URI):
   ```
   https://ticktick.com/oauth/authorize?client_id=YOUR_CLIENT_ID&scope=tasks:read%20tasks:write&redirect_uri=YOUR_REDIRECT_URI&response_type=code
   ```

2. **Authorize the App**: You'll be asked to log in and authorize your application

3. **Get the Code**: After authorization, you'll be redirected to your redirect URI with a code parameter:
   ```
   http://YOUR_REDIRECT_URI?code=AUTHORIZATION_CODE
   ```

4. **Exchange for Token**: Use curl or a tool like Postman to exchange the code for an access token:
   ```bash
   curl -X POST https://ticktick.com/oauth/token \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "code=AUTHORIZATION_CODE" \
     -d "grant_type=authorization_code" \
     -d "redirect_uri=YOUR_REDIRECT_URI"
   ```

5. **Save the Access Token**: The response will contain an `access_token` - save this for your `.env` file

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
TICKTICK_CLIENT_ID=your_client_id_here
TICKTICK_CLIENT_SECRET=your_client_secret_here
TICKTICK_ACCESS_TOKEN=your_access_token_here
TASK_FILTER_TAGS=recurring,daily
TASK_NAME_FILTER=
```

## Usage

### Running Locally

#### Duplicate Completed Tasks Automation

Run once:
```bash
python automations/duplicate_completed_tasks.py --once
```

With verbose logging:
```bash
python automations/duplicate_completed_tasks.py --once --verbose
```

#### Run in tmux Session
For long-running processes or to keep the script running:
```bash
# Create a new tmux session
tmux new -s ticktick

# Inside tmux, run the automation
python automations/duplicate_completed_tasks.py --once

# Detach from tmux: Press Ctrl+B, then D
# Reattach later: tmux attach -t ticktick
```

### Running on GitHub Actions

The automation can run automatically on GitHub Actions on a schedule (main branch only).

#### Setup GitHub Actions

1. Go to your repository Settings → Secrets and variables → Actions

2. Add the following **Secrets**:
   - `TICKTICK_CLIENT_ID`: Your TickTick client ID
   - `TICKTICK_CLIENT_SECRET`: Your TickTick client secret
   - `TICKTICK_ACCESS_TOKEN`: Your TickTick access token

3. Add the following **Variables** (optional):
   - `TASK_FILTER_TAGS`: Comma-separated tags (e.g., `recurring,daily`)
   - `TASK_NAME_FILTER`: Substring to filter task names

4. The workflow is configured to:
   - Run every 5 minutes on the **main** branch only
   - Can be triggered manually from the Actions tab
   - All secrets are properly masked in logs

5. Edit `.github/workflows/automation.yml` to change the schedule:
```yaml
schedule:
  - cron: '*/5 * * * *'  # Every 5 minutes
  # - cron: '0 * * * *'  # Every hour
  # - cron: '0 0 * * *'  # Once a day at midnight
```

## Configuration

### Environment Variables

- **TICKTICK_CLIENT_ID** (required): OAuth client ID from TickTick Developer Console
- **TICKTICK_CLIENT_SECRET** (required): OAuth client secret from TickTick Developer Console
- **TICKTICK_ACCESS_TOKEN** (required): OAuth access token obtained through OAuth flow
- **TASK_FILTER_TAGS** (optional): Comma-separated list of tags. Tasks with ANY of these tags will be duplicated.
- **TASK_NAME_FILTER** (optional): Substring to match in task names. Only matching tasks will be duplicated.

### Filters

The automation will only duplicate tasks that match ALL configured filters:
- Tasks must be completed in the last 24 hours
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

### Duplicate Completed Tasks Automation

1. **Fetch Recent Completed Tasks**: Queries TickTick API for tasks completed in the last 24 hours
2. **Apply Filters**: Checks each task against name and tag filters
3. **Check State**: Skips tasks that have already been processed
4. **Duplicate Task**: Creates a new task with:
   - Same title, content, description
   - Same project/list
   - Same priority and tags
   - Same checklist items (if any)
   - **No due date** (intentionally left empty)
5. **Save State**: Records processed task IDs to avoid re-processing

## Adding New Automations

To add a new automation:

1. Create a new file in the `automations/` directory (e.g., `automations/my_automation.py`)
2. Import utilities from the `utils/` package:
   ```python
   from utils import TickTickClient, TickTickAPIError
   ```
3. Implement your automation logic
4. Create a corresponding GitHub workflow in `.github/workflows/` if needed
5. Update this README with documentation for your automation

## Files

### Core Files
- `automations/duplicate_completed_tasks.py`: Main automation for duplicating completed tasks
- `utils/ticktick_api.py`: TickTick API client wrapper with OAuth support
- `utils/helpers.py`: Helper functions for state management and task operations
- `requirements.txt`: Python dependencies
- `.env.example`: Example environment configuration

### GitHub Actions
- `.github/workflows/automation.yml`: Workflow for duplicate completed tasks automation

### Auto-generated Files
- `duplicate_completed_tasks_state.json`: State file tracking processed tasks (auto-generated)
- `duplicate_completed_tasks.log`: Log file (auto-generated)

## Troubleshooting

### Authentication Errors
- Verify your client ID, client secret, and access token are correct
- Access tokens may expire - obtain a new one through the OAuth flow if needed
- Ensure you've granted the correct scopes: `tasks:read tasks:write`

### Tasks Not Being Duplicated
- Check the filters in your `.env` file
- Review the log file for details
- Verify tasks were completed in the last 24 hours
- Check the state file - tasks listed there won't be processed again

### GitHub Actions Not Running
- Verify the workflow only runs on the main branch
- Ensure secrets are set correctly in repository settings
- Check workflow permissions in repository settings
- Review workflow runs in the Actions tab for errors
- Make sure you're on the main branch

### Environment Variables Not Hidden
- All sensitive values (CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN) are stored as GitHub Secrets
- Secrets are automatically masked in workflow logs
- Never commit `.env` file to the repository

## Security Notes

- Never commit your `.env` file or expose your credentials
- Use GitHub Secrets for all sensitive values in workflows
- Access tokens should be treated as passwords
- Regularly rotate your access tokens for security

## Contributing

Contributions are welcome! To add new automations:
1. Create the automation script in `automations/`
2. Use shared utilities from `utils/`
3. Add documentation to this README
4. Create a workflow file if needed
5. Submit a pull request

## License

See LICENSE file for details.