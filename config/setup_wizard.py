from typing import Dict, Any
from plexapi.server import PlexServer
import inquirer
from config.config_manager import ConfigManager

class SetupWizard:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    async def run_setup(self) -> None:
        """Run the setup wizard"""
        print("\n=== Plex Maintenance Tool Setup ===\n")
        
        # Get Plex connection details
        await self._setup_plex_connection()
        
        # Get available libraries
        await self._setup_libraries()
        
        # Configure processing mode
        await self._setup_processing_mode()
        
        # Configure label preservation
        await self._setup_preserve_labels()
        
        # Mark setup as complete
        self.config_manager.update_config("initialized", True)
        print("\nSetup complete! Configuration saved.")

    async def _setup_plex_connection(self) -> None:
        """Setup Plex server connection"""
        current_url = self.config_manager.config["plex"]["url"]
        current_token = self.config_manager.config["plex"]["token"]

        questions = [
            inquirer.Text('url', 
                message="Enter your Plex server URL (e.g., http://192.168.1.100:32400)",
                default=current_url,
                validate=lambda _, x: x.startswith(('http://', 'https://'))),
            inquirer.Text('token',
                message="Enter your Plex authentication token",
                default=current_token)
        ]
        
        answers = inquirer.prompt(questions)
        
        print("\nTesting connection...")
        if await self.config_manager.test_connection(answers['url'], answers['token']):
            print("Connection successful!")
            self.config_manager.update_config("plex.url", answers['url'])
            self.config_manager.update_config("plex.token", answers['token'])
        else:
            print("Connection failed. Please check your settings and try again.")
            await self._setup_plex_connection()

    async def _setup_libraries(self) -> None:
        """Setup library selection"""
        current_libraries = self.config_manager.config.get("libraries", [])

        change_libraries_question = [
            inquirer.Confirm('change_libraries',
                message="Do you want to change the selected libraries?",
                default=False)
        ]

        change_libraries_answer = inquirer.prompt(change_libraries_question)

        if change_libraries_answer['change_libraries']:
            plex = PlexServer(
                self.config_manager.config["plex"]["url"],
                self.config_manager.config["plex"]["token"]
            )
            
            available_libraries = [lib.title for lib in plex.library.sections()]

            questions = [
                inquirer.Checkbox('libraries',
                    message="Select libraries to manage",
                    choices=available_libraries,
                    default=current_libraries)
            ]
            
            answers = inquirer.prompt(questions)
            self.config_manager.update_config("libraries", answers['libraries'])
        else:
            print("Keeping the current library selection.")

    async def _setup_processing_mode(self) -> None:
        """Setup processing mode"""
        current_mode = self.config_manager.config["processing"]["mode"]

        questions = [
            inquirer.List('mode',
                message="Select processing mode (affects server load)",
                choices=[
                    ('Light (1 worker - Minimal server impact)', 'light'),
                    ('Medium (2 workers - Balanced)', 'medium'),
                    ('Heavy (4 workers - Fastest, highest server load)', 'heavy')
                ],
                default=current_mode)
        ]
        
        answers = inquirer.prompt(questions)
        self.config_manager.update_config("processing.mode", answers['mode'])

    async def _setup_preserve_labels(self) -> None:
        """Setup label preservation"""
        current_labels = self.config_manager.config.get("preserve_labels", [])

        if current_labels:
            remove_questions = [
                inquirer.Checkbox('remove_labels',
                    message="Select labels to remove from preservation",
                    choices=current_labels)
            ]

            remove_answers = inquirer.prompt(remove_questions)

            for label in remove_answers['remove_labels']:
                current_labels.remove(label)

        add_label_question = [
            inquirer.Confirm('add_label',
                message="Do you want to add labels to preserve?",
                default=False)
        ]

        add_label_answer = inquirer.prompt(add_label_question)

        if add_label_answer['add_label']:
            while True:
                add_question = [
                    inquirer.Text('new_label',
                        message="Enter a label to preserve (or leave blank to finish)")
                ]

                add_answer = inquirer.prompt(add_question)

                if add_answer['new_label'].strip():
                    current_labels.append(add_answer['new_label'].strip())
                else:
                    break

        self.config_manager.update_config("preserve_labels", current_labels)

    @staticmethod
    def print_config_summary(config: Dict[str, Any]) -> None:
        """Print configuration summary"""
        print("\nConfiguration Summary:")
        print("=====================")
        print(f"Plex Server: {config['plex']['url']}")
        print(f"Libraries: {', '.join(config['libraries'])}")
        print(f"Processing Mode: {config['processing']['mode']}")
        print(f"Preserved Labels: {', '.join(config['preserve_labels'])}")