"""Command handlers for console server."""
import asyncio
import logging
from typing import Dict, List, Tuple

from app.manager.server import AutomationManager

log = logging.getLogger(__name__)


class CommandHandler:
    """Handles console commands for the automation manager."""
    
    def __init__(self, manager: AutomationManager):
        self.manager = manager
    
    async def handle_command(self, command: str) -> Tuple[bool, str]:
        """
        Handle a console command.
        
        Args:
            command: Command string (e.g., "start stake", "status")
            
        Returns:
            Tuple of (should_exit, response_message)
        """
        parts = command.strip().split()
        if not parts:
            return False, ""
        
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd == 'exit' or cmd == 'quit':
            return True, "Shutting down..."
        
        elif cmd == 'help':
            return False, self._get_help_text()
        
        elif cmd == 'status':
            return False, await self._handle_status()
        
        elif cmd == 'list':
            return False, await self._handle_list()
        
        elif cmd == 'start':
            if not args:
                return False, "Usage: start <site> or start all"
            return False, await self._handle_start(args)
        
        elif cmd == 'stop':
            if not args:
                return False, "Usage: stop <site> or stop all"
            return False, await self._handle_stop(args)
        
        elif cmd == 'restart':
            if not args:
                return False, "Usage: restart <site>"
            return False, await self._handle_restart(args[0])
        
        elif cmd == 'enable':
            if not args:
                return False, "Usage: enable <site>"
            return False, await self._handle_enable(args[0])
        
        elif cmd == 'disable':
            if not args:
                return False, "Usage: disable <site>"
            return False, await self._handle_disable(args[0])
        
        else:
            return False, f"Unknown command: {cmd}. Type 'help' for available commands."
    
    def _get_help_text(self) -> str:
        """Get help text for available commands."""
        return """
Available commands:
  help                    - Show this help message
  status                  - Show status of all workers
  list                    - List all available sites
  start <site>            - Start a worker for a site
  start all               - Start all enabled workers
  stop <site>             - Stop a worker for a site
  stop all                - Stop all running workers
  restart <site>          - Restart a worker for a site
  enable <site>           - Enable a site in config
  disable <site>          - Disable a site in config
  exit / quit             - Shutdown all workers and exit
"""
    
    async def _handle_status(self) -> str:
        """Handle status command."""
        status = await self.manager.get_status()
        running = self.manager.list_running_workers()
        
        lines = ["\n=== Worker Status ==="]
        lines.append(f"Running: {len(running)}/{len(status)}")
        lines.append("")
        lines.append(f"{'Status':<8} {'Enabled':<8} {'Site':<15} {'State':<12} {'Mode':<10} {'Details'}")
        lines.append("-" * 80)
        
        for site_key, info in sorted(status.items()):
            state = info.get('state', 'unknown')
            is_running = info.get('is_running', False)
            enabled = info.get('enabled', True)
            headless = info.get('headless', False)
            profile_dir = info.get('profile_dir', 'N/A')
            target_url = info.get('target_url', 'N/A')
            
            status_icon = "🟢 RUN" if is_running else "🔴 STOP"
            enabled_icon = "✓" if enabled else "✗"
            mode = "headless" if headless else "headful"
            
            line = f"{status_icon:<8} {enabled_icon:<8} {site_key:<15} {state:<12} {mode:<10}"
            
            details = []
            if is_running:
                uptime = info.get('uptime_seconds')
                if uptime:
                    details.append(f"uptime: {uptime:.0f}s")
                page_url = info.get('page_url')
                if page_url:
                    details.append(f"url: {page_url[:30]}...")
            else:
                details.append(f"profile: {profile_dir}")
            
            if details:
                line += " | ".join(details)
            
            lines.append(line)
        
        lines.append("")
        return "\n".join(lines)
    
    async def _handle_list(self) -> str:
        """Handle list command."""
        sites = self.manager.list_workers()
        running = self.manager.list_running_workers()
        
        lines = ["\n=== Available Sites ==="]
        for site in sorted(sites):
            status = "🟢 RUNNING" if site in running else "🔴 STOPPED"
            lines.append(f"  {site:20} {status}")
        lines.append("")
        return "\n".join(lines)
    
    async def _handle_start(self, args: List[str]) -> str:
        """Handle start command."""
        if args[0].lower() == 'all':
            results = await self.manager.start_all()
            success_count = sum(1 for v in results.values() if v)
            total_count = len(results)
            return f"Started {success_count}/{total_count} workers"
        else:
            site_key = args[0]
            success = await self.manager.start_worker(site_key)
            if success:
                return f"Started worker for {site_key}"
            else:
                return f"Failed to start worker for {site_key}"
    
    async def _handle_stop(self, args: List[str]) -> str:
        """Handle stop command."""
        if args[0].lower() == 'all':
            results = await self.manager.stop_all()
            success_count = sum(1 for v in results.values() if v)
            total_count = len(results)
            return f"Stopped {success_count}/{total_count} workers"
        else:
            site_key = args[0]
            success = await self.manager.stop_worker(site_key)
            if success:
                return f"Stopped worker for {site_key}"
            else:
                return f"Failed to stop worker for {site_key}"
    
    async def _handle_restart(self, site_key: str) -> str:
        """Handle restart command."""
        success = await self.manager.restart_worker(site_key)
        if success:
            return f"Restarted worker for {site_key}"
        else:
            return f"Failed to restart worker for {site_key}"
    
    async def _handle_enable(self, site_key: str) -> str:
        """Handle enable command."""
        if site_key not in self.manager.site_configs:
            return f"Unknown site: {site_key}"
        
        self.manager.site_configs[site_key]['enabled'] = True
        return f"Enabled {site_key}"
    
    async def _handle_disable(self, site_key: str) -> str:
        """Handle disable command."""
        if site_key not in self.manager.site_configs:
            return f"Unknown site: {site_key}"
        
        self.manager.site_configs[site_key]['enabled'] = False
        # Also stop if running
        if site_key in self.manager.workers:
            await self.manager.stop_worker(site_key)
        return f"Disabled {site_key}"
