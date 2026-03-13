# Automation Console Server

A Python console server for managing browser automation workers across multiple gambling platforms.

## Overview

The console server allows you to:
- Start/stop individual site workers
- Monitor worker status
- Enable/disable sites
- Manage multiple workers concurrently
- Gracefully shutdown all workers

## Quick Start

### 1. Start the Console Server

```bash
# Inside Docker container
docker compose exec app python run_server.py

# Or locally (requires Playwright browsers installed)
python run_server.py
```

### 2. Available Commands

Once the server starts, you'll see a prompt: `automation> `

**Basic Commands:**
- `help` - Show help message
- `status` - Show status of all workers
- `list` - List all available sites
- `exit` / `quit` - Shutdown and exit

**Worker Control:**
- `start <site>` - Start a worker for a site (e.g., `start stake`)
- `start all` - Start all enabled workers
- `stop <site>` - Stop a worker for a site
- `stop all` - Stop all running workers
- `restart <site>` - Restart a worker for a site

**Configuration:**
- `enable <site>` - Enable a site in config
- `disable <site>` - Disable a site in config

### 3. Example Session

```
automation> status
=== Worker Status ===
Running: 0/14
...
automation> start stake
Started worker for stake
automation> start roobet
Started worker for roobet
automation> status
=== Worker Status ===
Running: 2/14
🟢 ✓ stake          running     (uptime: 15s)
🟢 ✓ roobet         running     (uptime: 8s)
...
automation> stop stake
Stopped worker for stake
automation> exit
Shutting down all workers...
Goodbye!
```

## Available Sites

The following sites are available:

- `shuffle` - Shuffle.com
- `winna` - Winna.com
- `gamdom` - Gamdom.com
- `thrill` - Thrill.global
- `roobet` - Roobet.com
- `stake` - Stake.com
- `stake_us` - Stake.us
- `rollbit` - Rollbit.com
- `bcgame` - BC.Game
- `duelbits` - Duelbits.com
- `packdraw` - PackDraw.com
- `metawin` - MetaWin.com
- `metawin_us` - MetaWin.us
- `razed` - Razed.com

## Configuration

Site configuration is managed in `config/sites.yaml`. Each site can be configured with:

- `enabled` - Enable/disable the site
- `headless` - Run browser in headless mode
- `launch_on_start` - Auto-start on server launch (future feature)
- `max_retries` - Maximum navigation retries
- `timeout_seconds` - Navigation timeout

Example:
```yaml
stake:
  key: stake
  name: Stake
  url: https://stake.com
  enabled: true
  headless: true
  launch_on_start: false
  max_retries: 3
  timeout_seconds: 30
```

## Architecture

### Components

1. **Base Worker** (`app/automations/base.py`)
   - Handles browser lifecycle
   - Manages worker state
   - Provides navigation and cleanup

2. **Site Workers** (`app/automations/*.py`)
   - One worker per gambling platform
   - Inherits from `BaseAutomationWorker`
   - Implements site-specific logic

3. **Registry** (`app/manager/registry.py`)
   - Maps site keys to worker classes
   - Creates worker instances

4. **Manager** (`app/manager/server.py`)
   - Manages multiple workers
   - Handles start/stop/restart operations
   - Tracks worker status

5. **Command Handler** (`app/manager/commands.py`)
   - Parses console commands
   - Executes operations
   - Formats responses

6. **Console Server** (`run_server.py`)
   - Main entry point
   - Interactive console loop
   - Signal handling for graceful shutdown

## Worker Lifecycle

1. **IDLE** - Worker created but not started
2. **STARTING** - Browser launching, page loading
3. **RUNNING** - Worker active, executing main loop
4. **STOPPING** - Shutdown initiated
5. **STOPPED** - Worker stopped
6. **ERROR** - Worker encountered an error

## Development

### Adding a New Site

1. Create worker class in `app/automations/<site>.py`:
```python
from app.automations.base import BaseAutomationWorker

class NewSiteWorker(BaseAutomationWorker):
    def __init__(self, **kwargs):
        super().__init__(
            site_key='newsite',
            site_name='New Site',
            site_url='https://newsite.com',
            **kwargs
        )
    
    async def bootstrap_page(self):
        # Site-specific initialization
        pass
    
    async def run(self):
        # Main worker loop
        while not self._stop_event.is_set():
            # Do work
            await asyncio.sleep(5)
```

2. Register in `app/automations/__init__.py`:
```python
from app.automations.newsite import NewSiteWorker

WORKER_REGISTRY = {
    ...
    'newsite': NewSiteWorker,
}
```

3. Add config in `config/sites.yaml`:
```yaml
newsite:
  key: newsite
  name: New Site
  url: https://newsite.com
  enabled: true
  headless: true
  ...
```

### Extending Worker Functionality

Each worker has placeholder methods for future features:

- `bootstrap_page()` - Site-specific initialization
- `run()` - Main scraping loop
- Future: `collect_live_feed()`, `collect_chat()`, `extract_usernames()`, etc.

## Troubleshooting

### Worker Won't Start

- Check if site is enabled in `config/sites.yaml`
- Verify site URL is correct
- Check browser logs for navigation errors
- Ensure Playwright browsers are installed: `playwright install chromium`

### Browser Processes Not Closing

- Workers should clean up on stop
- If orphaned, kill manually: `pkill -f chromium`
- Check worker state with `status` command

### Port Conflicts

- Each worker uses isolated browser context
- No port conflicts expected
- If issues occur, check system resources

## Integration with Database

Workers can be extended to persist data using the existing database layer:

```python
from app.db.session import SessionLocal
from app.db.models import RawPlayer

# In worker run() method:
async def run(self):
    while not self._stop_event.is_set():
        # Extract usernames
        usernames = await self.extract_usernames()
        
        # Persist to database
        db = SessionLocal()
        try:
            for username in usernames:
                player = RawPlayer(
                    username=username,
                    source_site=self.site_key,
                    captured_at=datetime.now()
                )
                db.add(player)
            db.commit()
        finally:
            db.close()
```

## Future Enhancements

- Auto-start workers on server launch
- Web UI for monitoring
- Metrics and analytics
- Worker health checks
- Automatic retry on failures
- Rate limiting per site
- Proxy support
- Cookie/session persistence
