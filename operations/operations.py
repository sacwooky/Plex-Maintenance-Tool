from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import asyncio
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from utils.utils import format_progress_bar, print_operation_header, confirm_action

class OperationStats:
    def __init__(self):
        self.stats = defaultdict(int)
        self.start_time = datetime.now()
        self.errors = []
        # Get the directory where your main script (pmt.py) is located
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # Create path to logs directory
        self.log_dir = os.path.join(os.path.dirname(self.base_dir), "logs")
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            self.stats[key] += value

    def log_error(self, item_title, error_msg):
        """Log an error message"""
        self.errors.append(f"{item_title}: {error_msg}")

    def get_summary(self) -> Dict[str, Any]:
        duration = datetime.now() - self.start_time
        self.stats['duration_seconds'] = duration.total_seconds()
        return dict(self.stats)

    def save_logs(self, operation_name, library_name):
        """Save logs to files"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        separator = f"\n{'='*50}\n{timestamp} - {operation_name} - {library_name}\n{'='*50}\n"
        
        # Save errors log
        if self.errors:
            error_file = os.path.join(self.log_dir, "errors.log")
            with open(error_file, "a") as f:
                f.write(separator)
                for error in self.errors:
                    f.write(f"{error}\n")

        # Save summary log
        summary = self.get_summary()
        summary_file = os.path.join(self.log_dir, "summary.log")
        with open(summary_file, "a") as f:
            f.write(separator)
            f.write(f"Items Processed: {summary['processed']}/{self.stats.get('total', 0)}\n")
            f.write(f"Labels Removed: {summary.get('removed', 0)}\n")
            f.write(f"Errors Encountered: {summary.get('errors', 0)}\n")
            f.write(f"Duration: {summary['duration_seconds']:.1f} seconds\n")

async def cleanup_labels_operation(plex, library_name: str, worker_count: int, preserve_labels: List[str]):
    """Clean up labels for a specific library"""
    try:
        print_operation_header("Label Cleanup", library_name)
        library = plex.library.section(library_name)
        all_items = library.all()
        total_items = len(all_items)
        
        if not total_items:
            print(f"No items found in library: {library_name}")
            return
        
        stats = OperationStats()
        stats.update(total=total_items)
        
        def process_item(item, index):
            try:
                original_labels = item.labels
                if original_labels:
                    labels_to_remove = [
                        label for label in original_labels
                        if label.tag.lower() not in preserve_labels
                    ]
                    
                    if labels_to_remove:
                        for label in labels_to_remove:
                            item.removeLabel(label.tag) # Use removeLabel instead of removeLabels
                        print(f"\r{format_progress_bar(index, total_items)} - Removed {len(labels_to_remove)} labels from: {item.title}")
                        return {"removed": len(labels_to_remove), "processed": 1}
                return {"removed": 0, "processed": 1}
            except Exception as e:
                print(f"\nError processing {item.title}: {e}")
                stats.log_error(item.title, str(e))
                return {"removed": 0, "processed": 0, "errors": 1}
        
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(process_item, item, i+1) 
                for i, item in enumerate(all_items)
            ]
            
            for future in as_completed(futures):
                stats.update(**future.result())
        
        summary = stats.get_summary()
        print("\nOperation Summary:")
        print(f"Items Processed: {summary['processed']}/{total_items}")
        print(f"Labels Removed: {summary['removed']}")
        print(f"Errors Encountered: {summary.get('errors', 0)}")
        print(f"Duration: {summary['duration_seconds']:.1f} seconds")
        
        # Save logs
        stats.save_logs("Label Cleanup", library_name)
        
    except Exception as e:
        raise Exception(f"Label cleanup failed: {e}")

async def reset_posters_operation(plex, library_name: str, worker_count: int):
    """Reset posters for a specific library"""
    try:
        print_operation_header("Poster Reset", library_name)
        library = plex.library.section(library_name)
        all_items = library.all()
        total_items = len(all_items)
        
        if not total_items:
            print(f"No items found in library: {library_name}")
            return
        
        stats = OperationStats()
        stats.update(total=total_items)
        
        def process_item(item, index):
            try:
                posters = item.posters()
                if posters:
                    item.setPoster(posters[0])
                    print(f"\r{format_progress_bar(index, total_items)} - Reset poster for: {item.title}")
                    return {"reset": 1, "processed": 1}
                else:
                    item.refresh()
                    print(f"\r{format_progress_bar(index, total_items)} - Refreshed metadata for: {item.title}")
                    return {"refreshed": 1, "processed": 1}
            except Exception as e:
                print(f"\nError processing {item.title}: {e}")
                stats.log_error(item.title, str(e))
                return {"reset": 0, "refreshed": 0, "processed": 0, "errors": 1}
        
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(process_item, item, i+1) 
                for i, item in enumerate(all_items)
            ]
            
            for future in as_completed(futures):
                stats.update(**future.result())
        
        summary = stats.get_summary()
        print("\nOperation Summary:")
        print(f"Items Processed: {summary['processed']}/{total_items}")
        print(f"Posters Reset: {summary.get('reset', 0)}")
        print(f"Metadata Refreshed: {summary.get('refreshed', 0)}")
        print(f"Errors Encountered: {summary.get('errors', 0)}")
        print(f"Duration: {summary['duration_seconds']:.1f} seconds")
        
        # Save logs
        stats.save_logs("Poster Reset", library_name)
        
    except Exception as e:
        raise Exception(f"Poster reset failed: {e}")

async def delete_recent_movies_operation(plex, library_name: str, hours: int = 48):
    """Delete movies added in the last specified hours"""
    try:
        print_operation_header("Recent Movie Deletion", library_name)
        library = plex.library.section(library_name)
        
        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Get recent items
        recent_items = []
        for item in library.all():
            if item.addedAt and item.addedAt > cutoff_time:
                recent_items.append(item)
        
        if not recent_items:
            print(f"No items found added in the last {hours} hours")
            return
        
        # Show items to be deleted
        print(f"\nFound {len(recent_items)} items added in the last {hours} hours:")
        for idx, item in enumerate(recent_items, 1):
            print(f"{idx}. {item.title} (Added: {item.addedAt})")
        
        # Confirm deletion
        if not confirm_action("\nAre you sure you want to delete these items?"):
            print("Operation cancelled")
            return
        
        stats = OperationStats()
        total_items = len(recent_items)
        stats.update(total=total_items)
        
        # Process deletions
        for idx, item in enumerate(recent_items, 1):
            try:
                print(f"\r{format_progress_bar(idx, total_items)} - Deleting: {item.title}")
                item.delete()
                stats.update(deleted=1, processed=1)
            except Exception as e:
                print(f"\nError deleting {item.title}: {e}")
                stats.log_error(item.title, str(e))
                stats.update(errors=1)
        
        summary = stats.get_summary()
        print("\nOperation Summary:")
        print(f"Items Found: {total_items}")
        print(f"Items Deleted: {summary.get('deleted', 0)}")
        print(f"Errors Encountered: {summary.get('errors', 0)}")
        print(f"Duration: {summary['duration_seconds']:.1f} seconds")
        
        # Save logs
        stats.save_logs("Recent Movie Deletion", library_name)
        
        if summary.get('deleted', 0) > 0:
            print("\nNote: You may want to empty the trash in Plex to fully remove these items")
        
    except Exception as e:
        raise Exception(f"Recent movie deletion failed: {e}")