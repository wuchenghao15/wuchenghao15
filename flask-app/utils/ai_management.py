#!/usr/bin/env python3
"""
AI Management Module - Handles thread management, data synchronization, and backup operations
"""

import threading
import queue
import time
import json
import os
import shutil
import datetime
from typing import Dict, List, Any, Callable

class ThreadManager:
    """Thread management with priority, sync/async locks, dynamic pool size"""
    
    def __init__(self, max_workers: int = 5, min_workers: int = 2, dynamic_scaling: bool = True):
        self.max_workers = max_workers
        self.min_workers = min_workers
        self.dynamic_scaling = dynamic_scaling
        self.task_queue = queue.PriorityQueue()
        self.workers = []
        self.running = False
        self.lock = threading.RLock()  # Reentrant lock for synchronization
        self.condition = threading.Condition(self.lock)
        self.task_results = {}  # Task ID to result mapping
        self.task_timeouts = {}  # Task ID to timeout mapping
        self.last_scaling_time = time.time()
        self.scaling_interval = 30  # seconds
        
    def start(self):
        """Start the thread manager"""
        if self.running:
            return
            
        self.running = True
        # Start with minimum workers
        for _ in range(self.min_workers):
            worker = threading.Thread(target=self._worker)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
    
    def stop(self):
        """Stop the thread manager"""
        with self.lock:
            self.running = False
            self.condition.notify_all()
        
        for worker in self.workers:
            worker.join(timeout=1.0)
        
        self.workers.clear()
        self.task_results.clear()
        self.task_timeouts.clear()
    
    def _worker(self):
        """Worker thread function"""
        while True:
            with self.lock:
                while self.running and self.task_queue.empty():
                    self.condition.wait()
                
                if not self.running:
                    break
                    
                priority, task_id, task_func, args, kwargs = self.task_queue.get()
                
                # Get task timeout if set
                timeout = self.task_timeouts.pop(task_id, None)
            
            try:
                if timeout:
                    # Execute with timeout
                    result = self._execute_with_timeout(task_func, timeout, *args, **kwargs)
                    self.task_results[task_id] = (True, result)
                else:
                    # Normal execution
                    result = task_func(*args, **kwargs)
                    self.task_results[task_id] = (True, result)
            except Exception as e:
                print(f"Task {task_id} failed: {e}")
                self.task_results[task_id] = (False, str(e))
            finally:
                self.task_queue.task_done()
                # Check if we need to scale the pool
                self._dynamic_scaling()
    
    def _execute_with_timeout(self, func, timeout, *args, **kwargs):
        """Execute function with timeout"""
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            raise TimeoutError(f"Task timed out after {timeout} seconds")
        
        if exception[0]:
            raise exception[0]
        
        return result[0]
    
    def _dynamic_scaling(self):
        """Dynamically adjust the thread pool size based on load"""
        if not self.dynamic_scaling:
            return
        
        current_time = time.time()
        if current_time - self.last_scaling_time < self.scaling_interval:
            return
        
        with self.lock:
            queue_size = self.task_queue.qsize()
            current_workers = len(self.workers)
            
            # Scale up if queue is growing and we have room
            if queue_size > current_workers and current_workers < self.max_workers:
                new_workers = min(queue_size - current_workers, self.max_workers - current_workers)
                for _ in range(new_workers):
                    worker = threading.Thread(target=self._worker)
                    worker.daemon = True
                    worker.start()
                    self.workers.append(worker)
                print(f"Scaled up: Added {new_workers} workers, total: {len(self.workers)}")
            
            # Scale down if we have too many idle workers
            elif queue_size == 0 and current_workers > self.min_workers:
                # Remove up to half of the excess workers
                workers_to_remove = min(current_workers - self.min_workers, current_workers // 2)
                # We can't directly remove workers, so we'll just let them exit when idle
                # This is a simplified approach
                print(f"Scaling down: Will reduce workers from {current_workers} to {current_workers - workers_to_remove} when idle")
            
            self.last_scaling_time = current_time
    
    def add_task(self, task_func: Callable, priority: int = 10, task_id: str = None, timeout: int = None, **kwargs):
        """Add a task to the queue
        
        Args:
            task_func: The function to execute
            priority: Priority level (lower number = higher priority)
            task_id: Optional task identifier
            timeout: Optional task timeout in seconds
            **kwargs: Arguments to pass to the task function
        """
        if not task_id:
            task_id = f"task_{int(time.time())}_{threading.get_ident()}"
        
        with self.lock:
            self.task_queue.put((priority, task_id, task_func, [], kwargs))
            if timeout:
                self.task_timeouts[task_id] = timeout
            self.condition.notify()
        
        return task_id
    
    def wait_for_completion(self):
        """Wait for all tasks to complete"""
        self.task_queue.join()
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.task_queue.qsize()
    
    def get_task_result(self, task_id: str, block: bool = False, timeout: float = None) -> tuple:
        """Get task result if available
        
        Returns:
            tuple: (success, result) if task completed, (None, None) if not completed
        """
        if task_id in self.task_results:
            return self.task_results.pop(task_id)
        
        if block:
            start_time = time.time()
            while True:
                if task_id in self.task_results:
                    return self.task_results.pop(task_id)
                if timeout and (time.time() - start_time) > timeout:
                    break
                time.sleep(0.1)
        
        return (None, None)
    
    def clear_task_result(self, task_id: str):
        """Clear task result"""
        if task_id in self.task_results:
            del self.task_results[task_id]


class DataSyncManager:
    """Local JSON data synchronization with online database - Enhanced with version management and differential sync"""
    
    def __init__(self, local_data_dir: str = "data", sync_interval: int = 300):
        self.local_data_dir = local_data_dir
        self.sync_interval = sync_interval
        self.last_sync = 0
        self.thread_manager = ThreadManager(max_workers=2)
        self.sync_lock = threading.Lock()
        self.version_manager = {}
        self.differential_enabled = True
        
        # Ensure local data directory exists
        os.makedirs(self.local_data_dir, exist_ok=True)
        # Load version information
        self._load_versions()
    
    def start(self):
        """Start the data sync manager"""
        self.thread_manager.start()
        # Add initial sync task
        self.thread_manager.add_task(self.sync_data, priority=5)
    
    def stop(self):
        """Stop the data sync manager"""
        self.thread_manager.stop()
        # Save versions before stopping
        self._save_versions()
    
    def _load_versions(self):
        """Load version information from file"""
        version_file = os.path.join(self.local_data_dir, "version_info.json")
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    self.version_manager = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading version info: {e}")
                self.version_manager = {}
    
    def _save_versions(self):
        """Save version information to file"""
        version_file = os.path.join(self.local_data_dir, "version_info.json")
        try:
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(self.version_manager, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving version info: {e}")
    
    def _get_current_version(self, data_key: str) -> int:
        """Get current version for a specific data key"""
        return self.version_manager.get(data_key, 0)
    
    def _increment_version(self, data_key: str) -> int:
        """Increment version for a specific data key"""
        current_version = self._get_current_version(data_key)
        new_version = current_version + 1
        self.version_manager[data_key] = new_version
        self._save_versions()
        return new_version
    
    def sync_data(self):
        """Synchronize local data with online database - Enhanced with differential sync"""
        with self.sync_lock:
            try:
                # Get current time
                current_time = time.time()
                
                # Check if sync interval has passed
                if current_time - self.last_sync < self.sync_interval:
                    return
                
                print(f"[{datetime.datetime.now()}] Starting data synchronization...")
                
                # Step 1: Read local JSON files
                local_data = self._read_local_data()
                
                # Step 2: Get local versions
                local_versions = {k: self._get_current_version(k) for k in local_data.keys()}
                
                # Step 3: Check for changes since last sync
                if self.differential_enabled:
                    # Get changed data only
                    changed_data = self._get_changed_data(local_data)
                    if changed_data:
                        # Step 4: Sync only changed data
                        sync_result = self._simulate_cloud_sync(changed_data, is_differential=True)
                        # Step 5: Update versions for synced data
                        for data_key in changed_data.keys():
                            self._increment_version(data_key)
                    else:
                        print(f"[{datetime.datetime.now()}] No changes detected, skipping sync")
                        sync_result = {"status": "skipped", "message": "No changes detected"}
                else:
                    # Full sync
                    sync_result = self._simulate_cloud_sync(local_data, is_differential=False)
                    # Update all versions
                    for data_key in local_data.keys():
                        self._increment_version(data_key)
                
                # Step 6: Update last sync time
                self.last_sync = current_time
                
                print(f"[{datetime.datetime.now()}] Data synchronization completed: {sync_result['status']} - {sync_result['message']}")
                
            except Exception as e:
                print(f"[{datetime.datetime.now()}] Data synchronization failed: {e}")
    
    def _read_local_data(self) -> Dict[str, Any]:
        """Read local JSON data files"""
        local_data = {}
        
        for filename in os.listdir(self.local_data_dir):
            if filename.endswith('.json') and filename not in ['sync_logs.json', 'version_info.json', 'upgrade_logs.json']:
                file_path = os.path.join(self.local_data_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        file_key = filename[:-5]  # Remove .json extension
                        local_data[file_key] = data
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error reading {file_path}: {e}")
        
        return local_data
    
    def _get_changed_data(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect changed data since last sync"""
        changed_data = {}
        
        # Check for changes in each data file
        for data_key, current_content in current_data.items():
            # Get last synced version
            last_version = self._get_current_version(data_key)
            
            # Check if file has changed by comparing content hashes
            current_hash = self._calculate_content_hash(current_content)
            
            # Store current hash for future comparison
            if 'last_hashes' not in self.version_manager:
                self.version_manager['last_hashes'] = {}
            
            last_hash = self.version_manager['last_hashes'].get(data_key, '')
            
            if current_hash != last_hash:
                # Data has changed
                changed_data[data_key] = current_content
                # Update last hash
                self.version_manager['last_hashes'][data_key] = current_hash
        
        self._save_versions()
        return changed_data
    
    def _calculate_content_hash(self, data: Any) -> str:
        """Calculate SHA256 hash of data for change detection"""
        import hashlib
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    def _simulate_cloud_sync(self, data: Dict[str, Any], is_differential: bool = False):
        """Simulate cloud synchronization with version management"""
        # Simulate network delay
        time.sleep(0.3 if is_differential else 0.8)
        
        # Log the sync operation
        sync_log = {
            "timestamp": datetime.datetime.now().isoformat(),
            "data_count": len(data),
            "sync_type": "differential" if is_differential else "full",
            "status": "success",
            "message": f"{len(data)} items synchronized successfully"
        }
        
        # Save sync log
        log_file = os.path.join(self.local_data_dir, "sync_logs.json")
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(sync_log)
        # Keep only last 100 logs
        if len(logs) > 100:
            logs = logs[-100:]
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        
        return sync_log
    
    def force_sync(self, data_key: str = None):
        """Force immediate synchronization - can sync specific data key"""
        if data_key:
            # Sync only specific data key
            self.thread_manager.add_task(
                lambda: self._sync_specific_data(data_key),
                priority=1
            )
        else:
            # Full sync
            self.thread_manager.add_task(self.sync_data, priority=1)
    
    def _sync_specific_data(self, data_key: str):
        """Sync a specific data key"""
        with self.sync_lock:
            try:
                # Read specific data file
                file_path = os.path.join(self.local_data_dir, f"{data_key}.json")
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Sync the data
                    sync_result = self._simulate_cloud_sync({data_key: data}, is_differential=True)
                    # Update version
                    self._increment_version(data_key)
                    
                    print(f"[{datetime.datetime.now()}] Specific data sync completed: {sync_result['status']} - {sync_result['message']}")
                else:
                    print(f"[{datetime.datetime.now()}] Data file not found: {data_key}")
            except Exception as e:
                print(f"[{datetime.datetime.now()}] Specific data sync failed: {e}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status with version info"""
        sync_logs_file = os.path.join(self.local_data_dir, "sync_logs.json")
        last_sync = None
        sync_history = []
        
        if os.path.exists(sync_logs_file):
            try:
                with open(sync_logs_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    if logs:
                        last_sync = logs[-1]
                        # Keep only last 10 sync records for status
                        sync_history = logs[-10:]
            except (json.JSONDecodeError, IOError):
                pass
        
        # Get version summary
        version_summary = {
            "total_versions": len(self.version_manager) - (1 if 'last_hashes' in self.version_manager else 0),
            "last_hashes_count": len(self.version_manager.get('last_hashes', {})),
            "versions": {k: v for k, v in self.version_manager.items() if k != 'last_hashes'}
        }
        
        return {
            "last_sync": last_sync,
            "sync_interval": self.sync_interval,
            "queue_size": self.thread_manager.get_queue_size(),
            "differential_enabled": self.differential_enabled,
            "version_info": version_summary,
            "sync_history": sync_history
        }
    
    def enable_differential_sync(self, enable: bool):
        """Enable or disable differential sync"""
        self.differential_enabled = enable
        print(f"Differential sync {'enabled' if enable else 'disabled'}")
    
    def resolve_conflict(self, data_key: str, local_data: Any, remote_data: Any, resolution_strategy: str = "latest") -> Any:
        """Resolve conflict between local and remote data"""
        # Simple conflict resolution strategies
        if resolution_strategy == "local_wins":
            return local_data
        elif resolution_strategy == "remote_wins":
            return remote_data
        elif resolution_strategy == "latest":
            # Compare timestamps if available
            local_time = local_data.get('last_updated', 0)
            remote_time = remote_data.get('last_updated', 0)
            return local_data if local_time >= remote_time else remote_data
        else:
            # Default to remote wins
            return remote_data
    
    def get_version_history(self, data_key: str) -> list:
        """Get version history for a specific data key"""
        # This would normally fetch from cloud storage
        # For now, return a simulated version history
        return [
            {
                "version": self._get_current_version(data_key),
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "current"
            },
            {
                "version": self._get_current_version(data_key) - 1,
                "timestamp": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),
                "status": "previous"
            },
            {
                "version": self._get_current_version(data_key) - 2,
                "timestamp": (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat(),
                "status": "previous"
            }
        ]


class BackupManager:
    """Data backup and recovery management"""
    
    def __init__(self, data_dir: str = "data", backup_dir: str = "backups"):
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        self.thread_manager = ThreadManager(max_workers=1)
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def start(self):
        """Start the backup manager"""
        self.thread_manager.start()
    
    def stop(self):
        """Stop the backup manager"""
        self.thread_manager.stop()
    
    def create_backup(self, description: str = ""):
        """Create a backup of the data directory"""
        return self.thread_manager.add_task(
            self._create_backup,
            priority=5,
            description=description
        )
    
    def _create_backup(self, description: str = ""):
        """Internal backup creation method"""
        try:
            # Create backup filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            if description:
                backup_name += f"_{description.replace(' ', '_')[:20]}"
            
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Copy all files from data directory to backup directory
            for filename in os.listdir(self.data_dir):
                src_path = os.path.join(self.data_dir, filename)
                dst_path = os.path.join(backup_path, filename)
                
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
                elif os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)
            
            # Create backup metadata
            metadata = {
                "timestamp": datetime.datetime.now().isoformat(),
                "description": description,
                "files": [f for f in os.listdir(self.data_dir)],
                "size": self._get_directory_size(backup_path)
            }
            
            # Save metadata
            with open(os.path.join(backup_path, "metadata.json"), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"Backup created successfully: {backup_name}")
            return backup_name
            
        except Exception as e:
            print(f"Backup creation failed: {e}")
            return None
    
    def restore_backup(self, backup_name: str):
        """Restore data from a backup"""
        return self.thread_manager.add_task(
            self._restore_backup,
            priority=1,
            backup_name=backup_name
        )
    
    def _restore_backup(self, backup_name: str):
        """Internal backup restoration method"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup {backup_name} not found")
            
            # Create a temporary backup of current data
            temp_backup = self._create_backup("pre_restore")
            
            # Clear current data directory
            for filename in os.listdir(self.data_dir):
                file_path = os.path.join(self.data_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            
            # Copy files from backup to data directory
            for filename in os.listdir(backup_path):
                if filename == "metadata.json":
                    continue
                    
                src_path = os.path.join(backup_path, filename)
                dst_path = os.path.join(self.data_dir, filename)
                
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
                elif os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)
            
            print(f"Backup restored successfully: {backup_name}")
            return True
            
        except Exception as e:
            print(f"Backup restoration failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        backups = []
        
        for backup_name in os.listdir(self.backup_dir):
            backup_path = os.path.join(self.backup_dir, backup_name)
            if os.path.isdir(backup_path):
                metadata_path = os.path.join(backup_path, "metadata.json")
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            backups.append({
                                "name": backup_name,
                                "timestamp": metadata.get("timestamp"),
                                "description": metadata.get("description", ""),
                                "files": metadata.get("files", []),
                                "size": metadata.get("size", 0)
                            })
                    except (json.JSONDecodeError, IOError):
                        continue
        
        # Sort backups by timestamp (newest first)
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        return backups
    
    def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
                return True
            return False
        except Exception as e:
            print(f"Failed to delete backup {backup_name}: {e}")
            return False
    
    def clear_data(self, clear_logs: bool = False, clear_cache: bool = False, clear_temp: bool = False) -> bool:
        """Clear specified data types"""
        try:
            items_to_clear = []
            
            if clear_logs:
                items_to_clear.extend([f for f in os.listdir(self.data_dir) if f.endswith('_logs.json')])
            
            if clear_cache:
                items_to_clear.extend([f for f in os.listdir(self.data_dir) if 'cache' in f.lower()])
            
            if clear_temp:
                items_to_clear.extend([f for f in os.listdir(self.data_dir) if f.startswith('temp_')])
            
            for item in items_to_clear:
                item_path = os.path.join(self.data_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            
            print(f"Cleared {len(items_to_clear)} items from data directory")
            return True
        except Exception as e:
            print(f"Failed to clear data: {e}")
            return False
    
    def _get_directory_size(self, directory: str) -> int:
        """Get directory size in bytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size


class AISelfLearningManager:
    """AI Self-Learning Manager - Handles self-learning, knowledge validation, and knowledge base management"""
    
    def __init__(self, knowledge_base_path: str = "data/knowledge_base"):
        self.knowledge_base_path = knowledge_base_path
        self.thread_manager = ThreadManager(max_workers=3)
        self.learning_lock = threading.RLock()
        self.knowledge_base = {}
        self.validation_rules = {
            "math": self._validate_math_knowledge,
            "logic": self._validate_logic_knowledge,
            "general": self._validate_general_knowledge
        }
        self.confidence_threshold = 0.8
        
        # Initialize knowledge base
        os.makedirs(self.knowledge_base_path, exist_ok=True)
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load knowledge base from files"""
        try:
            for filename in os.listdir(self.knowledge_base_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.knowledge_base_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        category_knowledge = json.load(f)
                        category = filename[:-5]  # Remove .json extension
                        self.knowledge_base[category] = category_knowledge
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
            # Initialize with empty knowledge base if loading fails
            self.knowledge_base = {}
    
    def _save_knowledge_base(self):
        """Save knowledge base to files"""
        try:
            for category, knowledge in self.knowledge_base.items():
                file_path = os.path.join(self.knowledge_base_path, f"{category}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(knowledge, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving knowledge base: {e}")
    
    def _validate_math_knowledge(self, knowledge_item: dict) -> tuple:
        """Validate mathematical knowledge"""
        # Simple validation for mathematical knowledge
        # Example: 1+1=2 is valid, 1+1=8 is invalid
        if 'formula' in knowledge_item and 'result' in knowledge_item:
            formula = knowledge_item['formula']
            expected_result = knowledge_item['result']
            
            try:
                # Evaluate the formula safely
                # Note: This is a simplified example, in production we'd use a safer approach
                if formula.replace(' ', '') in ['1+1', '1 + 1']:
                    is_valid = expected_result == 2 or expected_result == "2"
                    confidence = 1.0 if is_valid else 0.0
                    return is_valid, confidence, "Mathematical validation"
            except Exception as e:
                return False, 0.0, f"Validation error: {e}"
        
        return False, 0.0, "Invalid math knowledge format"
    
    def _validate_logic_knowledge(self, knowledge_item: dict) -> tuple:
        """Validate logical knowledge"""
        if 'premise' in knowledge_item and 'conclusion' in knowledge_item:
            # Simple logical validation
            # Check if conclusion follows from premise
            premise = knowledge_item['premise'].lower()
            conclusion = knowledge_item['conclusion'].lower()
            
            if 'all' in premise and 'some' in conclusion:
                confidence = 0.9
            elif 'no' in premise and 'all' in conclusion:
                confidence = 0.1
            else:
                confidence = 0.5
            
            is_valid = confidence >= self.confidence_threshold
            return is_valid, confidence, "Logical validation"
        
        return False, 0.0, "Invalid logic knowledge format"
    
    def _validate_general_knowledge(self, knowledge_item: dict) -> tuple:
        """Validate general knowledge"""
        if 'fact' in knowledge_item and 'truth_value' in knowledge_item:
            # Simple truth value validation
            # In production, this would use external knowledge sources or more complex logic
            fact = knowledge_item['fact'].lower()
            truth_value = knowledge_item['truth_value']
            
            # Example validation rules for common facts
            known_truths = [
                "the earth is round",
                "water boils at 100 degrees celsius",
                "humans need oxygen to survive"
            ]
            
            known_falsehoods = [
                "the earth is flat",
                "water boils at 0 degrees celsius",
                "humans can breathe underwater without equipment"
            ]
            
            if fact in known_truths:
                is_valid = truth_value is True
                confidence = 1.0
            elif fact in known_falsehoods:
                is_valid = truth_value is False
                confidence = 1.0
            else:
                # Unknown fact, use confidence threshold
                confidence = 0.6
                is_valid = confidence >= self.confidence_threshold
            
            return is_valid, confidence, "General knowledge validation"
        
        return False, 0.0, "Invalid general knowledge format"
    
    def validate_knowledge(self, knowledge_item: dict, category: str = "general") -> tuple:
        """Validate knowledge item based on category"""
        with self.learning_lock:
            validator = self.validation_rules.get(category, self._validate_general_knowledge)
            return validator(knowledge_item)
    
    def add_knowledge(self, knowledge_item: dict, category: str = "general") -> bool:
        """Add validated knowledge to the knowledge base"""
        with self.learning_lock:
            # Validate the knowledge
            is_valid, confidence, validation_message = self.validate_knowledge(knowledge_item, category)
            
            if is_valid:
                # Add metadata
                knowledge_item['added_at'] = datetime.datetime.now().isoformat()
                knowledge_item['confidence'] = confidence
                knowledge_item['validation_message'] = validation_message
                
                # Initialize category if it doesn't exist
                if category not in self.knowledge_base:
                    self.knowledge_base[category] = []
                
                # Add to knowledge base
                self.knowledge_base[category].append(knowledge_item)
                
                # Save to file
                self._save_knowledge_base()
                
                print(f"Added valid knowledge to {category} category: {knowledge_item.get('fact', 'Unknown')}")
                return True
            else:
                print(f"Rejected invalid knowledge: {validation_message}, Confidence: {confidence}")
                return False
    
    def learn_from_interaction(self, interaction_data: dict):
        """Learn from user interaction data"""
        # Add learning task to queue
        self.thread_manager.add_task(
            self._learn_from_interaction_task,
            priority=5,
            interaction_data=interaction_data
        )
    
    def _learn_from_interaction_task(self, interaction_data: dict):
        """Background task to learn from interaction"""
        try:
            print(f"Learning from interaction: {interaction_data.get('user_id', 'Unknown')}")
            
            # Extract potential knowledge from interaction
            # This is a simplified example, in production this would be more sophisticated
            if 'query' in interaction_data and 'response' in interaction_data:
                query = interaction_data['query'].lower()
                response = interaction_data['response'].lower()
                
                # Example: If response is a fact, add to knowledge base
                if any(keyword in response for keyword in ['is', 'are', 'was', 'were', 'equals', '=']):
                    # Simple fact extraction
                    fact_candidate = {
                        'fact': response,
                        'truth_value': True,
                        'source': 'user_interaction',
                        'user_id': interaction_data.get('user_id')
                    }
                    
                    # Add to knowledge base after validation
                    self.add_knowledge(fact_candidate)
        except Exception as e:
            print(f"Error learning from interaction: {e}")
    
    def get_knowledge(self, category: str = None) -> dict:
        """Get knowledge from the knowledge base"""
        with self.learning_lock:
            if category:
                return self.knowledge_base.get(category, {})
            return self.knowledge_base.copy()
    
    def clean_knowledge_base(self):
        """Clean the knowledge base by removing invalid or low-confidence knowledge"""
        with self.learning_lock:
            cleaned_count = 0
            
            for category, knowledge_items in self.knowledge_base.items():
                original_count = len(knowledge_items)
                
                # Validate each knowledge item and keep only valid ones
                self.knowledge_base[category] = [
                    item for item in knowledge_items 
                    if self.validate_knowledge(item, category)[0]
                ]
                
                cleaned_count += original_count - len(self.knowledge_base[category])
            
            # Save cleaned knowledge base
            self._save_knowledge_base()
            
            print(f"Cleaned knowledge base: Removed {cleaned_count} invalid items")
            return cleaned_count
    
    def detect_contamination(self) -> dict:
        """Detect potential contamination in the knowledge base"""
        with self.learning_lock:
            contamination_report = {
                'total_items': 0,
                'invalid_items': 0,
                'by_category': {}
            }
            
            for category, knowledge_items in self.knowledge_base.items():
                category_report = {
                    'total': len(knowledge_items),
                    'invalid': 0,
                    'invalid_items': []
                }
                
                for item in knowledge_items:
                    is_valid, confidence, message = self.validate_knowledge(item, category)
                    contamination_report['total_items'] += 1
                    
                    if not is_valid:
                        contamination_report['invalid_items'] += 1
                        category_report['invalid'] += 1
                        category_report['invalid_items'].append({
                            'item': item,
                            'confidence': confidence,
                            'message': message
                        })
                
                contamination_report['by_category'][category] = category_report
            
            return contamination_report
    
    def start(self):
        """Start the self-learning manager"""
        self.thread_manager.start()
    
    def stop(self):
        """Stop the self-learning manager"""
        self.thread_manager.stop()


class AutoUpgradeManager:
    """Automatic upgrade management for the MTSCOS AI system"""
    
    def __init__(self, upgrade_interval: int = 3600):
        self.upgrade_interval = upgrade_interval  # Default: check every hour
        self.last_upgrade_check = 0
        self.current_version = "3.0.0"  # Current system version
        self.thread_manager = ThreadManager(max_workers=2)
        self.upgrade_lock = threading.Lock()
        self.is_upgrading = False
        
        # Upgrade log file
        self.upgrade_log_file = os.path.join("data", "upgrade_logs.json")
        os.makedirs("data", exist_ok=True)
    
    def start(self):
        """Start the auto-upgrade manager"""
        self.thread_manager.start()
        # Add initial upgrade check task
        self.thread_manager.add_task(self.check_for_upgrades, priority=5)
    
    def stop(self):
        """Stop the auto-upgrade manager"""
        self.thread_manager.stop()
    
    def check_for_upgrades(self):
        """Check for available upgrades and perform upgrade if needed"""
        with self.upgrade_lock:
            if self.is_upgrading:
                return
            
            try:
                # Get current time
                current_time = time.time()
                
                # Check if upgrade interval has passed
                if current_time - self.last_upgrade_check < self.upgrade_interval:
                    return
                
                print(f"[{datetime.datetime.now()}] Checking for upgrades...")
                
                # Step 1: Check for new version
                new_version_available, latest_version = self._check_version()
                
                if new_version_available:
                    print(f"[{datetime.datetime.now()}] New version available: {latest_version} (current: {self.current_version})")
                    
                    # Step 2: Perform upgrade
                    self._perform_upgrade(latest_version)
                else:
                    print(f"[{datetime.datetime.now()}] System is up to date: {self.current_version}")
                
                # Update last upgrade check time
                self.last_upgrade_check = current_time
                
            except Exception as e:
                print(f"[{datetime.datetime.now()}] Upgrade check failed: {e}")
                self._log_upgrade("error", f"Upgrade check failed: {e}")
    
    def _check_version(self) -> tuple:
        """Check if a new version is available"""
        # For now, we'll simulate this check
        # In a real system, this would call an API or check a remote repository
        latest_version = "3.1.0"  # Simulate a newer version
        return latest_version != self.current_version, latest_version
    
    def _perform_upgrade(self, new_version: str):
        """Perform the upgrade process"""
        self.is_upgrading = True
        upgrade_start_time = datetime.datetime.now()
        
        try:
            print(f"[{upgrade_start_time}] Starting upgrade to version {new_version}...")
            self._log_upgrade("info", f"Starting upgrade to version {new_version}")
            
            # Step 1: Create backup before upgrade
            print(f"[{datetime.datetime.now()}] Creating backup before upgrade...")
            backup_manager.create_backup(f"pre_upgrade_{new_version}")
            
            # Step 2: Update codebase
            print(f"[{datetime.datetime.now()}] Updating codebase...")
            self._update_codebase()
            
            # Step 3: Update dependencies
            print(f"[{datetime.datetime.now()}] Updating dependencies...")
            self._update_dependencies()
            
            # Step 4: Update database schema
            print(f"[{datetime.datetime.now()}] Updating database schema...")
            self._update_database()
            
            # Step 5: Update AI models and rules
            print(f"[{datetime.datetime.now()}] Updating AI models and rules...")
            self._update_ai_components()
            
            # Step 6: Update configuration
            print(f"[{datetime.datetime.now()}] Updating configuration...")
            self._update_configuration()
            
            # Step 7: Update version information
            self.current_version = new_version
            
            upgrade_end_time = datetime.datetime.now()
            upgrade_duration = (upgrade_end_time - upgrade_start_time).total_seconds()
            
            print(f"[{upgrade_end_time}] Upgrade completed successfully in {upgrade_duration:.2f} seconds")
            self._log_upgrade("success", f"Upgraded to version {new_version} in {upgrade_duration:.2f} seconds")
            
        except Exception as e:
            upgrade_end_time = datetime.datetime.now()
            print(f"[{upgrade_end_time}] Upgrade failed: {e}")
            self._log_upgrade("error", f"Upgrade to {new_version} failed: {e}")
        finally:
            self.is_upgrading = False
    
    def _update_codebase(self):
        """Update the codebase from remote repository"""
        # Simulate code update
        time.sleep(1.5)
        print("Codebase updated successfully")
    
    def _update_dependencies(self):
        """Update project dependencies"""
        # Simulate dependency update
        time.sleep(1.0)
        print("Dependencies updated successfully")
    
    def _update_database(self):
        """Update database schema"""
        # Simulate database update
        time.sleep(0.5)
        print("Database schema updated successfully")
    
    def _update_ai_components(self):
        """Update AI models and rules"""
        # Simulate AI components update
        time.sleep(2.0)
        print("AI models and rules updated successfully")
    
    def _update_configuration(self):
        """Update configuration files"""
        # Simulate configuration update
        time.sleep(0.5)
        print("Configuration updated successfully")
    
    def _log_upgrade(self, status: str, message: str):
        """Log upgrade information"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "status": status,
            "message": message,
            "current_version": self.current_version
        }
        
        # Read existing logs
        logs = []
        if os.path.exists(self.upgrade_log_file):
            try:
                with open(self.upgrade_log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except (json.JSONDecodeError, IOError):
                logs = []
        
        # Add new log entry
        logs.append(log_entry)
        
        # Keep only last 100 logs
        if len(logs) > 100:
            logs = logs[-100:]
        
        # Save logs
        with open(self.upgrade_log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    
    def force_upgrade(self):
        """Force immediate upgrade"""
        self.thread_manager.add_task(self.check_for_upgrades, priority=1)
    
    def get_upgrade_status(self) -> Dict[str, Any]:
        """Get current upgrade status"""
        # Read upgrade logs
        upgrade_logs = []
        if os.path.exists(self.upgrade_log_file):
            try:
                with open(self.upgrade_log_file, 'r', encoding='utf-8') as f:
                    upgrade_logs = json.load(f)
            except (json.JSONDecodeError, IOError):
                upgrade_logs = []
        
        return {
            "current_version": self.current_version,
            "last_upgrade_check": self.last_upgrade_check,
            "upgrade_interval": self.upgrade_interval,
            "is_upgrading": self.is_upgrading,
            "upgrade_logs": upgrade_logs[-10:]  # Return only last 10 logs
        }
    
    def get_current_version(self) -> str:
        """Get current system version"""
        return self.current_version
    
    def set_upgrade_interval(self, interval: int):
        """Set upgrade check interval in seconds"""
        self.upgrade_interval = interval
        print(f"Upgrade interval set to {interval} seconds")


class AIEmployeeManager:
    """AI Employee Manager - Handles AI employee instantiation and project adaptation"""
    
    def __init__(self, employees_path: str = "data/ai_employees"):
        self.employees_path = employees_path
        self.thread_manager = ThreadManager(max_workers=4)
        self.employees_lock = threading.RLock()
        self.ai_employees = {}
        self.project_adaptation_rules = {}
        
        # Initialize employees directory
        os.makedirs(self.employees_path, exist_ok=True)
        self._load_ai_employees()
    
    def _load_ai_employees(self):
        """Load AI employees from files"""
        try:
            for filename in os.listdir(self.employees_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.employees_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        employee_data = json.load(f)
                        employee_id = employee_data.get('id', filename[:-5])
                        self.ai_employees[employee_id] = employee_data
        except Exception as e:
            print(f"Error loading AI employees: {e}")
            # Initialize with empty employees if loading fails
            self.ai_employees = {}
    
    def _save_ai_employee(self, employee_id: str, employee_data: dict):
        """Save a single AI employee to file"""
        try:
            file_path = os.path.join(self.employees_path, f"{employee_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(employee_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving AI employee {employee_id}: {e}")
    
    def create_ai_employee(self, employee_config: dict) -> str:
        """Create a new AI employee instance"""
        with self.employees_lock:
            # Generate unique employee ID
            employee_id = f"ai_emp_{int(time.time())}_{threading.get_ident()}"
            
            # Set default values and merge with config
            employee_data = {
                'id': employee_id,
                'created_at': datetime.datetime.now().isoformat(),
                'last_updated': datetime.datetime.now().isoformat(),
                'status': 'active',
                'skills': [],
                'projects': [],
                'performance_metrics': {
                    'tasks_completed': 0,
                    'accuracy': 0.0,
                    'efficiency': 0.0
                }
            }
            
            employee_data.update(employee_config)
            
            # Initialize adaptation status
            employee_data['adaptation_status'] = {
                'is_adapted': False,
                'last_adapted': None,
                'adaptation_score': 0.0
            }
            
            # Save to memory and file
            self.ai_employees[employee_id] = employee_data
            self._save_ai_employee(employee_id, employee_data)
            
            print(f"Created new AI employee: {employee_id} - {employee_data.get('name', 'Unnamed')}")
            return employee_id
    
    def get_ai_employee(self, employee_id: str) -> dict:
        """Get AI employee by ID"""
        with self.employees_lock:
            return self.ai_employees.get(employee_id, None)
    
    def list_ai_employees(self) -> list:
        """List all AI employees"""
        with self.employees_lock:
            return list(self.ai_employees.values())
    
    def delete_ai_employee(self, employee_id: str) -> bool:
        """Delete AI employee"""
        with self.employees_lock:
            if employee_id in self.ai_employees:
                # Remove from memory
                del self.ai_employees[employee_id]
                
                # Remove from file
                file_path = os.path.join(self.employees_path, f"{employee_id}.json")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted AI employee: {employee_id}")
                    return True
        
        print(f"AI employee not found: {employee_id}")
        return False
    
    def adapt_to_project(self, employee_id: str, project_data: dict) -> dict:
        """Adapt AI employee to a specific project"""
        # Add adaptation task to queue
        task_id = self.thread_manager.add_task(
            self._adapt_to_project_task,
            priority=3,
            employee_id=employee_id,
            project_data=project_data
        )
        
        return {
            'task_id': task_id,
            'message': 'Project adaptation started',
            'employee_id': employee_id
        }
    
    def _adapt_to_project_task(self, employee_id: str, project_data: dict):
        """Background task to adapt AI employee to project"""
        try:
            with self.employees_lock:
                if employee_id not in self.ai_employees:
                    print(f"AI employee not found: {employee_id}")
                    return
                
                employee = self.ai_employees[employee_id]
                print(f"Adapting AI employee {employee_id} to project: {project_data.get('name', 'Unknown')}")
                
                # Extract project requirements and context
                project_requirements = project_data.get('requirements', [])
                project_context = project_data.get('context', {})
                
                # Analyze skills needed for the project
                needed_skills = self._analyze_project_skills(project_requirements)
                
                # Calculate adaptation score
                adaptation_score = self._calculate_adaptation_score(employee, needed_skills)
                
                # Update employee's project list and adaptation status
                project_info = {
                    'project_id': project_data.get('id', f"proj_{int(time.time())}"),
                    'name': project_data.get('name', 'Unknown'),
                    'adaptation_score': adaptation_score,
                    'adapted_at': datetime.datetime.now().isoformat(),
                    'status': 'active' if adaptation_score >= 0.7 else 'needs_training'
                }
                
                # Remove existing project if it exists
                employee['projects'] = [p for p in employee['projects'] 
                                     if p['project_id'] != project_info['project_id']]
                
                # Add new project
                employee['projects'].append(project_info)
                
                # Update adaptation status
                employee['adaptation_status'] = {
                    'is_adapted': adaptation_score >= 0.7,
                    'last_adapted': datetime.datetime.now().isoformat(),
                    'adaptation_score': adaptation_score
                }
                
                # Update last updated time
                employee['last_updated'] = datetime.datetime.now().isoformat()
                
                # Save changes
                self._save_ai_employee(employee_id, employee)
                
                print(f"Adaptation completed for AI employee {employee_id} to project {project_info['name']}: Score {adaptation_score:.2f}")
                
        except Exception as e:
            print(f"Error adapting AI employee {employee_id} to project: {e}")
    
    def _analyze_project_skills(self, project_requirements: list) -> list:
        """Analyze project requirements to determine needed skills"""
        # Simple skill extraction from requirements
        # In production, this would use NLP or more sophisticated analysis
        needed_skills = set()
        
        skill_keywords = {
            'python': ['python', 'py'],
            'javascript': ['javascript', 'js', 'node'],
            'flask': ['flask'],
            'react': ['react'],
            'database': ['database', 'db', 'sql', 'nosql'],
            'ai': ['ai', 'machine learning', 'ml', 'deep learning', 'dl'],
            'devops': ['devops', 'docker', 'kubernetes', 'ci/cd'],
            'frontend': ['frontend', 'ui', 'ux'],
            'backend': ['backend', 'server', 'api']
        }
        
        for requirement in project_requirements:
            req_text = requirement.lower()
            for skill, keywords in skill_keywords.items():
                if any(keyword in req_text for keyword in keywords):
                    needed_skills.add(skill)
        
        return list(needed_skills)
    
    def _calculate_adaptation_score(self, employee: dict, needed_skills: list) -> float:
        """Calculate how well the employee adapts to the needed skills"""
        if not needed_skills:
            return 1.0
        
        employee_skills = employee.get('skills', [])
        matching_skills = [skill for skill in needed_skills if skill in employee_skills]
        
        # Calculate base adaptation score based on matching skills
        base_score = len(matching_skills) / len(needed_skills)
        
        # Adjust based on performance metrics
        performance = employee.get('performance_metrics', {})
        accuracy = performance.get('accuracy', 0.0)
        efficiency = performance.get('efficiency', 0.0)
        
        # Final score is weighted average: 70% skills, 15% accuracy, 15% efficiency
        final_score = (base_score * 0.7) + (accuracy * 0.15) + (efficiency * 0.15)
        
        return min(final_score, 1.0)  # Ensure score doesn't exceed 1.0
    
    def update_employee_skills(self, employee_id: str, skills: list) -> bool:
        """Update AI employee skills"""
        with self.employees_lock:
            if employee_id in self.ai_employees:
                employee = self.ai_employees[employee_id]
                employee['skills'] = skills
                employee['last_updated'] = datetime.datetime.now().isoformat()
                self._save_ai_employee(employee_id, employee)
                print(f"Updated skills for AI employee {employee_id}")
                return True
        
        print(f"AI employee not found: {employee_id}")
        return False
    
    def update_performance_metrics(self, employee_id: str, metrics: dict) -> bool:
        """Update AI employee performance metrics"""
        with self.employees_lock:
            if employee_id in self.ai_employees:
                employee = self.ai_employees[employee_id]
                performance = employee.get('performance_metrics', {})
                performance.update(metrics)
                employee['performance_metrics'] = performance
                employee['last_updated'] = datetime.datetime.now().isoformat()
                self._save_ai_employee(employee_id, employee)
                print(f"Updated performance metrics for AI employee {employee_id}")
                return True
        
        print(f"AI employee not found: {employee_id}")
        return False
    
    def get_adaptation_status(self, employee_id: str) -> dict:
        """Get AI employee adaptation status"""
        with self.employees_lock:
            if employee_id in self.ai_employees:
                employee = self.ai_employees[employee_id]
                return {
                    'employee_id': employee_id,
                    'name': employee.get('name', 'Unknown'),
                    'adaptation_status': employee.get('adaptation_status', {}),
                    'projects': employee.get('projects', []),
                    'skills': employee.get('skills', []),
                    'performance': employee.get('performance_metrics', {})
                }
        
        return None
    
    def start(self):
        """Start the AI employee manager"""
        self.thread_manager.start()
    
    def stop(self):
        """Stop the AI employee manager"""
        self.thread_manager.stop()


# Global instances
thread_manager = ThreadManager(max_workers=10)
data_sync_manager = DataSyncManager()
backup_manager = BackupManager()
auto_upgrade_manager = AutoUpgradeManager()
ai_self_learning_manager = AISelfLearningManager()
ai_employee_manager = AIEmployeeManager()

# Export these for external use
export = [
    'initialize_ai_management',
    'shutdown_ai_management',
    'thread_manager',
    'data_sync_manager',
    'backup_manager',
    'auto_upgrade_manager',
    'ai_self_learning_manager',
    'ai_employee_manager',
    'ThreadManager',
    'DataSyncManager',
    'BackupManager',
    'AutoUpgradeManager',
    'AISelfLearningManager',
    'AIEmployeeManager'
]


def initialize_ai_management():
    """Initialize AI management components"""
    print("Initializing AI management components...")
    thread_manager.start()
    data_sync_manager.start()
    backup_manager.start()
    auto_upgrade_manager.start()
    ai_self_learning_manager.start()
    ai_employee_manager.start()
    print("AI management components initialized successfully")


def shutdown_ai_management():
    """Shutdown AI management components"""
    print("Shutting down AI management components...")
    thread_manager.stop()
    data_sync_manager.stop()
    backup_manager.stop()
    auto_upgrade_manager.stop()
    ai_self_learning_manager.stop()
    ai_employee_manager.stop()
    print("AI management components shutdown successfully")


if __name__ == "__main__":
    # Test the AI management components
    initialize_ai_management()
    
    try:
        # Test thread management
        def test_task(name, sleep_time=1):
            print(f"Task {name} started")
            time.sleep(sleep_time)
            print(f"Task {name} completed")
        
        thread_manager.add_task(test_task, priority=5, task_id="test1", name="High Priority", sleep_time=2)
        thread_manager.add_task(test_task, priority=10, task_id="test2", name="Medium Priority", sleep_time=1)
        thread_manager.add_task(test_task, priority=15, task_id="test3", name="Low Priority", sleep_time=0.5)
        
        # Wait for tasks to complete
        thread_manager.wait_for_completion()
        
        # Test backup functionality
        backup_manager.create_backup("Test backup")
        print("Available backups:")
        for backup in backup_manager.list_backups():
            print(f"  - {backup['name']}: {backup['description']}")
            
        # Test data sync
        data_sync_manager.force_sync()
        time.sleep(1)
        
    finally:
        shutdown_ai_management()
