import asyncio
import inquirer
from config.config_manager import ConfigManager
from config.setup_wizard import SetupWizard
from operations.operations import cleanup_labels_operation, reset_posters_operation, delete_recent_movies_operation
from utils.utils import clear_screen, connect_to_plex

class PlexMaintenanceTool:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.setup_wizard = SetupWizard(self.config_manager)

    async def run(self):
        """Main application loop"""
        if self.config_manager.needs_setup():
            await self.setup_wizard.run_setup()

        while True:
            clear_screen()
            action = await self._show_main_menu()
            
            if action == 'exit':
                break
            
            if action:
                await self._handle_action(action)

    async def _show_main_menu(self):
        """Display main menu and get user selection"""
        questions = [
            inquirer.List('action',
                message="Select an operation",
                choices=[
                    ('Clean Up Labels', 'cleanup_labels'),
                    ('Reset Posters', 'reset_posters'),
                    ('Reconfigure Settings', 'reconfigure'),
                    ('Exit', 'exit')
                ])
        ]
        
        answers = inquirer.prompt(questions)
        return answers['action']

    async def _select_library(self):
        """Display library selection menu"""
        libraries = self.config_manager.get_libraries()
        
        questions = [
            inquirer.List('library',
                message="Select a library",
                choices=libraries + ['Back to Main Menu'])
        ]
        
        answers = inquirer.prompt(questions)
        return None if answers['library'] == 'Back to Main Menu' else answers['library']

    async def _handle_action(self, action):
        """Handle selected action"""
        if action == 'reconfigure':
            await self.setup_wizard.run_setup()
            return

        library = await self._select_library()
        if not library:
            return

        # Get Plex connection details from config
        plex_url = self.config_manager.config["plex"]["url"]
        plex_token = self.config_manager.config["plex"]["token"]
        
        plex = connect_to_plex(plex_url, plex_token)
        if not plex:
            input("Press Enter to continue...")
            return

        try:
            if action == 'cleanup_labels':
                await cleanup_labels_operation(
                    plex, 
                    library, 
                    self.config_manager.get_worker_count(),
                    self.config_manager.get_preserve_labels()
                )
            elif action == 'reset_posters':
                await reset_posters_operation(
                    plex,
                    library,
                    self.config_manager.get_worker_count()
                )
            elif action == 'delete_recent':
                await delete_recent_movies_operation(
                    plex,
                    library
                )
            
            input("\nOperation complete. Press Enter to continue...")
            
        except Exception as e:
            print(f"\nError during operation: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    tool = PlexMaintenanceTool()
    asyncio.run(tool.run())