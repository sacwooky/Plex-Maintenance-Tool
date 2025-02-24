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
                    ('Verify Release Dates', 'verify_dates'),
                    ('Find Incomplete Metadata', 'find_incomplete'),
                    ('Verify Media Paths', 'verify_paths'),
                    ('Check Media Integrity', 'verify_integrity'),
                    ('Find Abnormal Runtimes', 'find_abnormal'),
                    ('Bulk Label Operation', 'bulk_label'),
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

    async def _get_bulk_label_criteria(self):
        """Get criteria for bulk label operation"""
        questions = [
            inquirer.List('criteria_type',
                message="Select criteria type",
                choices=[
                    ('Resolution', 'resolution'),
                    ('Video Codec', 'codec'),
                    ('Genre', 'genre'),
                    ('Year', 'year'),
                    ('Rating', 'rating')
                ]),
            inquirer.Text('value',
                message="Enter criteria value"),
            inquirer.Text('label',
                message="Enter label to apply")
        ]
        
        answers = inquirer.prompt(questions)
        return {
            'criteria': {answers['criteria_type']: answers['value']},
            'label': answers['label']
        }

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
        worker_count = self.config_manager.get_worker_count()
        
        plex = connect_to_plex(plex_url, plex_token)
        if not plex:
            input("Press Enter to continue...")
            return

        try:
            if action == 'cleanup_labels':
                await cleanup_labels_operation(
                    plex, 
                    library, 
                    worker_count,
                    self.config_manager.get_preserve_labels()
                )
                
            elif action == 'reset_posters':
                await reset_posters_operation(
                    plex,
                    library,
                    worker_count
                )
                
            elif action == 'verify_dates':
                print_operation_header("Release Date Verification", library)
                issues = await verify_release_dates(plex, library, worker_count)
                
                if issues:
                    print("\nIssues found:")
                    for issue in issues:
                        if "item" in issue:
                            print(f"\n{issue['item'].title}:")
                            for key, value in issue.items():
                                if key != "item":
                                    print(f"  - {key}: {value}")
                else:
                    print("\nNo release date issues found.")
                    
            elif action == 'find_incomplete':
                print_operation_header("Metadata Completeness Check", library)
                issues = await find_incomplete_metadata(plex, library, worker_count)
                
                if issues:
                    print("\nItems with incomplete metadata:")
                    for issue in issues:
                        print(f"\n{issue['item'].title}:")
                        for field, missing in issue['issues'].items():
                            print(f"  - Missing: {field}")
                else:
                    print("\nNo metadata issues found.")
                    
            elif action == 'verify_paths':
                print_operation_header("Media Path Verification", library)
                issues = await verify_media_paths(plex, library)
                
                if issues:
                    print("\nMedia path issues found:")
                    for issue in issues:
                        print(f"\n{issue['item'].title}:")
                        print(f"  - Issue: {issue['issue']}")
                        if 'path' in issue:
                            print(f"  - Path: {issue['path']}")
                else:
                    print("\nNo media path issues found.")
                    
            elif action == 'verify_integrity':
                print_operation_header("Media Integrity Check", library)
                issues = await verify_media_integrity(plex, library, worker_count)
                
                if issues:
                    print("\nMedia integrity issues found:")
                    for issue in issues:
                        print(f"\n{issue['item'].title}:")
                        if 'issues' in issue:
                            for problem in issue['issues']:
                                print(f"  - {problem}")
                        if 'error' in issue:
                            print(f"  - Error: {issue['error']}")
                else:
                    print("\nNo media integrity issues found.")
                    
            elif action == 'find_abnormal':
                print_operation_header("Runtime Analysis", library)
                results = await find_abnormal_runtimes(plex, library, worker_count)
                
                if results['movies'] or results['episodes']:
                    print("\nAbnormal runtimes found:")
                    
                    if results['movies']:
                        print("\nMovies:")
                        for item in results['movies']:
                            print(f"\n{item['item'].title}:")
                            print(f"  - Duration: {item['duration']/60000:.1f} minutes")
                            print(f"  - Expected: {item['mean_duration']/60000:.1f} minutes")
                            print(f"  - Deviation: {item['deviation']:.1f} standard deviations")
                            
                    if results['episodes']:
                        print("\nTV Episodes:")
                        for item in results['episodes']:
                            print(f"\n{item['item'].grandparentTitle} - {item['item'].title}:")
                            print(f"  - Duration: {item['duration']/60000:.1f} minutes")
                            print(f"  - Expected: {item['mean_duration']/60000:.1f} minutes")
                            print(f"  - Deviation: {item['deviation']:.1f} standard deviations")
                else:
                    print("\nNo abnormal runtimes found.")
                    
            elif action == 'bulk_label':
                criteria_info = await self._get_bulk_label_criteria()
                
                if confirm_action(f"\nApply label '{criteria_info['label']}' to all items matching criteria?"):
                    results = await bulk_label_operation(
                        plex,
                        library,
                        worker_count,
                        criteria_info['criteria'],
                        criteria_info['label']
                    )
                    
                    labeled = sum(1 for r in results if 'labeled' in r)
                    errors = sum(1 for r in results if 'error' in r)
                    
                    print(f"\nOperation complete:")
                    print(f"  - Items labeled: {labeled}")
                    print(f"  - Errors: {errors}")
                else:
                    print("\nOperation cancelled.")
            
            input("\nOperation complete. Press Enter to continue...")
            
        except Exception as e:
            print(f"\nError during operation: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    tool = PlexMaintenanceTool()
    asyncio.run(tool.run())