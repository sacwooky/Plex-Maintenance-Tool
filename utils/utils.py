import os
from plexapi.server import PlexServer
from typing import Optional

def clear_screen():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════╗
║          Plex Maintenance Tool           ║
║------------------------------------------║
║  Manage your Plex server with ease       ║
╚══════════════════════════════════════════╝
"""
    print(banner)

def connect_to_plex(url: str, token: str) -> Optional[PlexServer]:
    """Connect to Plex server"""
    try:
        print("\nConnecting to Plex server...")
        plex = PlexServer(url, token)
        print(f"Connected to: {plex.friendlyName}")
        return plex
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def format_progress_bar(current: int, total: int, width: int = 40) -> str:
    """Create a progress bar string"""
    progress = current / total
    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)
    percent = progress * 100
    return f"[{bar}] {percent:.1f}% ({current}/{total})"

def confirm_action(message: str) -> bool:
    """Get user confirmation for an action"""
    while True:
        response = input(f"{message} (yes/no): ").lower().strip()
        if response in ('yes', 'y'):
            return True
        if response in ('no', 'n'):
            return False
        print("Please answer 'yes' or 'no'")

def print_operation_header(operation: str, library: str):
    """Print formatted operation header"""
    print("\n" + "=" * 50)
    print(f"{operation} - {library}")
    print("=" * 50)

def handle_error(error: Exception, context: str):
    """Handle and format error messages"""
    print(f"\nError during {context}:")
    print(f"  Type: {type(error).__name__}")
    print(f"  Details: {str(error)}")
    input("\nPress Enter to continue...")
