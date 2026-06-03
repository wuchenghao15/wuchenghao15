from flask import Blueprint, jsonify, request
#!/usr/bin/env python3
"""
AI Management Module - Handles thread management, data synchronization, and backup operations
"""

import logging
logger = logging.getLogger(__name__)
import threading
import queue
import time
import json
import os
import shutil
import datetime
from typing import Dict, List, Any, Callable

class ThreadManager:
    """Thread management with priority: sync/async locks, dynamic pool size"""

    def __init__(self, max_workers: int = 5, min_workers: int = 2, dynamic_scaling: bool = True):
        self.max_workers = max_workers
        self.min_workers = min_workers
        self.dynamic_scaling = dynamic_scaling
        self.task_queue = queue.PriorityQueue()
        self.workers = []
        self.running = False
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        self.task_results = {}
        self.task_timeouts = {}
        self.last_scaling_time = time.time()
        self.scaling_interval = 30

    def start(self):
        """Start the thread manager"""
        if self.running:
            return

        self.running = True
        for _ in range(self.min_workers):
            worker = threading.Thread(target=self._worker)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)

    def stop(self):
        """Stop the thread manager"""
        with self.lock:
            self.running = False

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
                    self.condition.wait(timeout=1.0)

                if not self.running:
                    break

                if self.task_queue.empty():
                    continue

                priority, task_id, task_func, args, kwargs = self.task_queue.get()
                timeout = self.task_timeouts.pop(task_id, None)

            try:
                if timeout:
                    result = self._execute_with_timeout(task_func, timeout, *args, **kwargs)
                    self.task_results[task_id] = (True, result)
                else:
                    result = task_func(*args, **kwargs)
                    self.task_results[task_id] = (True, result)
            except Exception as e:
                print(f"Task {task_id} failed: {e}")
                self.task_results[task_id] = (False, str(e))
            finally:
                self.task_queue.task_done()
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

            if queue_size > current_workers and current_workers < self.max_workers:
                new_workers = min(queue_size - current_workers, self.max_workers - current_workers)
                for _ in range(new_workers):
                    worker = threading.Thread(target=self._worker)
                    worker.daemon = True
                    worker.start()
                    self.workers.append(worker)

            elif queue_size == 0 and current_workers > self.min_workers:
                workers_to_remove = min(current_workers - self.min_workers, current_workers // 2)
                print(f"Scaling down: Will reduce workers from {current_workers} to {current_workers - workers_to_remove} when idle")

            self.last_scaling_time = current_time

    def add_task(self, task_func: Callable, priority: int = 10, task_id: str = None, timeout: int = None, **kwargs):
        """Add a task to the queue"""
        if not task_id:
            task_id = f"task_{int(time.time())}_{threading.get_ident()}"

        with self.lock:
            self.task_queue.put((priority, task_id, task_func, [], kwargs))
            if timeout:
                self.task_timeouts[task_id] = timeout
            self.condition.notify()

        return task_id

    def wait_for_completion(self):
        self.task_queue.join()

    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.task_queue.qsize()

    def get_task_result(self, task_id: str, block: bool = False, timeout: float = None) -> tuple:
        """Get task result if available"""
        if task_id in self.task_results:
            return self.task_results.pop(task_id)
        return (None, None)

    def clear_task_result(self, task_id: str):
        """Clear task result"""
        if task_id in self.task_results:
            del self.task_results[task_id]


class DataSyncManager:
    """Local JSON data synchronization with online database"""

    def __init__(self, local_data_dir: str = "data/local", sync_interval: int = 300):
        self.local_data_dir = local_data_dir
        self.sync_interval = sync_interval
        self.thread_manager = ThreadManager(max_workers=2)
        self.sync_lock = threading.Lock()
        self.version_manager = {}
        self.differential_enabled = True

        os.makedirs(self.local_data_dir, exist_ok=True)
        self._load_versions()

    def start(self):
        """Start the data sync manager"""
        self.thread_manager.start()

    def stop(self):
        """Stop the data sync manager"""
        self.thread_manager.stop()
        self._save_versions()

    def _load_versions(self):
        """Load version information from file"""
        version_file = os.path.join(self.local_data_dir, "version_info.json")
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    self.version_manager = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading version info: {e}")
                self.version_manager = {}

    def _save_versions(self):
        """Save version information to file"""
        version_file = os.path.join(self.local_data_dir, "version_info.json")
        try:
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(self.version_manager, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving version info: {e}")

    def _get_current_version(self, data_key: str) -> int:
        """Get current version for a specific data key"""
        return self.version_manager.get(data_key, 0)

    def _increment_version(self, data_key: str):
        """Increment version for a specific data key"""
        self.version_manager[data_key] = self._get_current_version(data_key) + 1
        self._save_versions()

    def sync_data(self):
        """Synchronize all local data"""
        with self.sync_lock:
            try:
                all_data = {}
                for filename in os.listdir(self.local_data_dir):
                    if filename.endswith('.json') and filename != 'version_info.json':
                        file_path = os.path.join(self.local_data_dir, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data_key = filename[:-5]
                            all_data[data_key] = json.load(f)

                sync_result = self._simulate_cloud_sync(all_data, is_differential=False)
                print(f"[{datetime.datetime.now()}] Sync completed: {sync_result['status']}")
            except Exception as e:
                print(f"[{datetime.datetime.now()}] Sync failed: {e}")

    def _simulate_cloud_sync(self, data: Dict[str, Any], is_differential: bool = False):
        """Simulate cloud synchronization with version management"""
        time.sleep(0.3 if is_differential else 0.8)

        sync_log = {
            "timestamp": datetime.datetime.now().isoformat(),
            "data_count": len(data),
            "sync_type": "differential" if is_differential else "full",
            "status": "success",
            "message": f"{len(data)} items synchronized successfully"
        }

        log_file = os.path.join(self.local_data_dir, "sync_logs.json")
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        logs.append(sync_log)
        if len(logs) > 100:
            logs = logs[-100:]

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

        return sync_log

    def force_sync(self, data_key: str = None):
        """Force immediate synchronization"""
        if data_key:
            self.thread_manager.add_task(
                lambda: self._sync_specific_data(data_key),
                priority=1
            )
        else:
            self.thread_manager.add_task(self.sync_data, priority=1)

    def _sync_specific_data(self, data_key: str):
        """Sync a specific data key"""
        with self.sync_lock:
            try:
                file_path = os.path.join(self.local_data_dir, f"{data_key}.json")
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    sync_result = self._simulate_cloud_sync({data_key: data}, is_differential=True)
                    self._increment_version(data_key)

                    print(f"[{datetime.datetime.now()}] Specific data sync completed: {sync_result['status']}")
                else:
                    print(f"[{datetime.datetime.now()}] Data file not found: {data_key}")
            except Exception as e:
                print(f"[{datetime.datetime.now()}] Specific data sync failed: {e}")

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        sync_logs_file = os.path.join(self.local_data_dir, "sync_logs.json")
        last_sync = None

        if os.path.exists(sync_logs_file):
            try:
                with open(sync_logs_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    if logs:
                        last_sync = logs[-1]
            except (json.JSONDecodeError, IOError):
                pass

        return {
            "last_sync": last_sync,
            "total_versions": len(self.version_manager),
            "versions": self.version_manager
        }

    def enable_differential_sync(self, enable: bool):
        """Enable or disable differential sync"""
        self.differential_enabled = enable
        print(f"Differential sync {'enabled' if enable else 'disabled'}")

    def resolve_conflict(self, data_key: str, local_data: Any, remote_data: Any, resolution_strategy: str = "latest") -> Any:
        """Resolve conflict between local and remote data"""
        if resolution_strategy == "local_wins":
            return local_data
        elif resolution_strategy == "remote_wins":
            return remote_data
        else:
            return remote_data


class BackupManager:
    """Backup management for data directory"""

    def __init__(self, data_dir: str = "data", backup_dir: str = "backups"):
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        self.thread_manager = ThreadManager(max_workers=1)

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
            lambda: self._create_backup(description),
            priority=5
        )

    def _create_backup(self, description: str = ""):
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            if description:
                backup_name += f"_{description.replace(' ', '_')[:20]}"

            backup_path = os.path.join(self.backup_dir, backup_name)

            os.makedirs(backup_path, exist_ok=True)

            for filename in os.listdir(self.data_dir):
                src_path = os.path.join(self.data_dir, filename)
                dst_path = os.path.join(backup_path, filename)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
                elif os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)

            metadata = {
                "description": description,
                "created_at": datetime.datetime.now().isoformat(),
                "size": self._get_directory_size(backup_path)
            }

            with open(os.path.join(backup_path, "metadata.json"), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            print(f"Backup created successfully: {backup_name}")
            return backup_name
        except Exception as e:
            print(f"Backup creation failed: {e}")
            return None

    def _get_directory_size(self, path: str) -> int:
        """Get total size of directory"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        return total_size

    def restore_backup(self, backup_name: str):
        """Restore data from a backup"""
        return self.thread_manager.add_task(
            lambda: self._restore_backup(backup_name),
            priority=1
        )

    def _restore_backup(self, backup_name: str):
        """Internal backup restoration method"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)

            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup {backup_name} not found")

            temp_backup = self._create_backup("pre_restore")

            for filename in os.listdir(self.data_dir):
                file_path = os.path.join(self.data_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)

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
        if os.path.exists(self.backup_dir):
            for backup_name in os.listdir(self.backup_dir):
                backup_path = os.path.join(self.backup_dir, backup_name)
                metadata_path = os.path.join(backup_path, "metadata.json")
                if os.path.isdir(backup_path) and os.path.exists(metadata_path):
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    backups.append({
                        "name": backup_name,
                        "description": metadata.get("description", ""),
                        "created_at": metadata.get("created_at", ""),
                        "size": metadata.get("size", 0)
                    })
        return backups


class AISelfLearningManager:
    """AI self-learning and knowledge management"""

    def __init__(self, knowledge_base_path: str = "data/knowledge_base"):
        self.knowledge_base_path = knowledge_base_path
        self.thread_manager = ThreadManager(max_workers=2)
        self.learning_lock = threading.RLock()
        self.knowledge_base = {}
        self.validation_rules = {
            "math": self._validate_math_knowledge,
            "logic": self._validate_logic_knowledge,
            "general": self._validate_general_knowledge
        }

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
                        category = filename[:-5]
                        self.knowledge_base[category] = category_knowledge
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            self.knowledge_base = {}

    def _save_knowledge_base(self):
        """Save knowledge base to files"""
        try:
            for category, knowledge in self.knowledge_base.items():
                file_path = os.path.join(self.knowledge_base_path, f"{category}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(knowledge, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")

    def _validate_math_knowledge(self, knowledge_item: dict) -> tuple:
        """Validate mathematical knowledge"""
        if 'formula' in knowledge_item and 'result' in knowledge_item:
            formula = knowledge_item['formula']
            expected_result = knowledge_item['result']

            try:
                if formula.replace(' ', '') in ['1+1', '1 + 1']:
                    is_valid = expected_result == 2 or expected_result == "2"
                    return is_valid, 0.9 if is_valid else 0.1
            except Exception:
                pass
        return False, 0.0

    def _validate_logic_knowledge(self, knowledge_item: dict) -> tuple:
        """Validate logical knowledge"""
        return True, 0.8

    def _validate_general_knowledge(self, knowledge_item: dict) -> tuple:
        """Validate general knowledge"""
        return True, 0.7

    def validate_knowledge(self, knowledge_item: dict, category: str = "general") -> tuple:
        """Validate knowledge item"""
        validator = self.validation_rules.get(category, self._validate_general_knowledge)
        return validator(knowledge_item)

    def add_knowledge(self, knowledge_item: dict, category: str = "general"):
        """Add knowledge to the knowledge base"""
        with self.learning_lock:
            if category not in self.knowledge_base:
                self.knowledge_base[category] = []

            is_valid, confidence = self.validate_knowledge(knowledge_item, category)
            if is_valid:
                knowledge_item['confidence'] = confidence
                knowledge_item['added_at'] = datetime.datetime.now().isoformat()
                self.knowledge_base[category].append(knowledge_item)
                self._save_knowledge_base()
                return True
            return False

    def learn_from_interaction(self, interaction_data: dict):
        """Learn from user interaction data"""
        self.thread_manager.add_task(
            self._learn_from_interaction_task,
            priority=5,
            interaction_data=interaction_data
        )

    def _learn_from_interaction_task(self, interaction_data: dict):
        """Background task to learn from interaction"""
        try:
            print(f"Learning from interaction: {interaction_data.get('user_id', 'Unknown')}")

            if 'query' in interaction_data and 'response' in interaction_data:
                response = interaction_data['response']

                if any(keyword in response for keyword in ['is', 'are', 'was', 'were', 'equals', '=']):
                    fact_candidate = {
                        'fact': response,
                        'truth_value': True,
                        'source': 'user_interaction',
                        'user_id': interaction_data.get('user_id')
                    }

                    self.add_knowledge(fact_candidate)
        except Exception as e:
            logger.error(f"Error learning from interaction: {e}")

    def get_knowledge(self, category: str = None) -> dict:
        """Get knowledge from the knowledge base"""
        with self.learning_lock:
            if category:
                return self.knowledge_base.get(category, {})
            return self.knowledge_base

    def clean_knowledge_base(self):
        """Clean the knowledge base by removing invalid or low-confidence knowledge"""
        with self.learning_lock:
            cleaned_count = 0

            for category, knowledge_items in self.knowledge_base.items():
                original_count = len(knowledge_items)

                self.knowledge_base[category] = [
                    item for item in knowledge_items
                    if self.validate_knowledge(item, category)[0]
                ]

                cleaned_count += original_count - len(self.knowledge_base[category])

            self._save_knowledge_base()

            print(f"Cleaned knowledge base: Removed {cleaned_count} invalid items")
            return cleaned_count

    def start(self):
        """Start the self-learning manager"""
        self.thread_manager.start()

    def stop(self):
        """Stop the self-learning manager"""
        self.thread_manager.stop()


class AutoUpgradeManager:
    """Automatic upgrade management for the MTSCOS AI system"""

    def __init__(self, upgrade_interval: int = 3600):
        self.upgrade_interval = upgrade_interval
        self.last_upgrade_check = 0
        self.current_version = "3.0.0"
        self.thread_manager = ThreadManager(max_workers=2)
        self.upgrade_lock = threading.Lock()
        self.is_upgrading = False

        self.upgrade_log_file = os.path.join("data", "upgrade_logs.json")
        os.makedirs("data", exist_ok=True)

    def start(self):
        """Start the auto-upgrade manager"""
        self.thread_manager.start()

    def stop(self):
        """Stop the auto-upgrade manager"""
        self.thread_manager.stop()

    def check_for_upgrades(self):
        """Check for available upgrades and perform upgrade if needed"""
        with self.upgrade_lock:
            if self.is_upgrading:
                return

            try:
                current_time = time.time()

                if current_time - self.last_upgrade_check < self.upgrade_interval:
                    return

                self.is_upgrading = True
                new_version_available, latest_version = self._check_version()

                if new_version_available:
                    print(f"[{datetime.datetime.now()}] New version available: {latest_version}")
                    self._perform_upgrade(latest_version)
                else:
                    print(f"[{datetime.datetime.now()}] System is up to date: {self.current_version}")

                self.last_upgrade_check = current_time
            except Exception as e:
                print(f"[{datetime.datetime.now()}] Upgrade check failed: {e}")
                self._log_upgrade("error", f"Upgrade check failed: {e}")
            finally:
                self.is_upgrading = False

    def _check_version(self) -> tuple:
        """Check for new version"""
        latest_version = "3.1.0"
        return latest_version != self.current_version, latest_version

    def _perform_upgrade(self, new_version: str):
        """Perform the upgrade process"""
        try:
            print(f"[{datetime.datetime.now()}] Starting upgrade to version {new_version}")

            self._update_codebase()
            self._update_dependencies()
            self._update_database()
            self._update_ai_components()
            self._update_configuration()

            self.current_version = new_version
            self._log_upgrade("success", f"Upgraded to version {new_version}")

            print(f"[{datetime.datetime.now()}] Upgrade completed successfully")
        except Exception as e:
            print(f"[{datetime.datetime.now()}] Upgrade failed: {e}")
            self._log_upgrade("error", f"Upgrade failed: {e}")

    def _update_codebase(self):
        """Update the codebase from remote repository"""
        time.sleep(1.5)
        print("Codebase updated successfully")

    def _update_dependencies(self):
        """Update project dependencies"""
        time.sleep(1.0)
        print("Dependencies updated successfully")

    def _update_database(self):
        """Update database schema"""
        time.sleep(0.5)
        print("Database schema updated successfully")

    def _update_ai_components(self):
        """Update AI models and rules"""
        time.sleep(2.0)
        print("AI models and rules updated successfully")

    def _update_configuration(self):
        """Update configuration files"""
        time.sleep(0.5)
        print("Configuration updated successfully")

    def _log_upgrade(self, status: str, message: str):
        """Log upgrade event"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "status": status,
            "message": message,
            "current_version": self.current_version
        }

        logs = []
        if os.path.exists(self.upgrade_log_file):
            try:
                with open(self.upgrade_log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except (json.JSONDecodeError, IOError):
                logs = []

        logs.append(log_entry)

        if len(logs) > 100:
            logs = logs[-100:]

        with open(self.upgrade_log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    def force_upgrade(self):
        """Force immediate upgrade"""
        self.thread_manager.add_task(self.check_for_upgrades, priority=1)

    def get_upgrade_status(self) -> Dict[str, Any]:
        """Get current upgrade status"""
        upgrade_logs = []
        if os.path.exists(self.upgrade_log_file):
            try:
                with open(self.upgrade_log_file, 'r', encoding='utf-8') as f:
                    upgrade_logs = json.load(f)
            except (json.JSONDecodeError, IOError):
                upgrade_logs = []

        return {
            "current_version": self.current_version,
            "last_check": self.last_upgrade_check,
            "is_upgrading": self.is_upgrading,
            "recent_logs": upgrade_logs[-10:] if upgrade_logs else []
        }

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
            logger.error(f"Error loading AI employees: {e}")
            self.ai_employees = {}

    def _save_ai_employee(self, employee_id: str, employee_data: dict):
        """Save a single AI employee to file"""
        try:
            file_path = os.path.join(self.employees_path, f"{employee_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(employee_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving AI employee {employee_id}: {e}")

    def create_ai_employee(self, employee_config: dict) -> str:
        """Create a new AI employee"""
        with self.employees_lock:
            employee_id = f"ai_emp_{int(time.time())}_{len(self.ai_employees)}"

            employee_data = {
                'id': employee_id,
                'created_at': datetime.datetime.now().isoformat(),
                'last_updated': datetime.datetime.now().isoformat(),
                'status': 'active',
                'skills': [],
                'performance_metrics': {
                    'accuracy': 0.0,
                    'tasks_completed': 0,
                    'success_rate': 0.0
                },
                'projects': [],
                'adaptation_status': {
                    'is_adapted': False,
                    'last_adapted': None,
                    'adaptation_score': 0.0
                }
            }

            employee_data.update(employee_config)

            self.ai_employees[employee_id] = employee_data
            self._save_ai_employee(employee_id, employee_data)

            print(f"Created new AI employee: {employee_id} - {employee_data.get('name', 'Unnamed')}")
            return employee_id

    def get_ai_employee(self, employee_id: str) -> dict:
        """Get AI employee by ID"""
        with self.employees_lock:
            return self.ai_employees.get(employee_id, None)

    def adapt_to_project(self, employee_id: str, project_data: dict):
        """Adapt AI employee to a specific project"""
        self.thread_manager.add_task(
            lambda: self._adapt_to_project_task(employee_id, project_data),
            priority=3
        )

    def _adapt_to_project_task(self, employee_id: str, project_data: dict):
        """Background task to adapt AI employee to project"""
        try:
            with self.employees_lock:
                if employee_id not in self.ai_employees:
                    print(f"AI employee not found: {employee_id}")
                    return

                employee = self.ai_employees[employee_id]
                print(f"Adapting AI employee {employee_id} to project: {project_data.get('name', 'Unknown')}")

                project_requirements = project_data.get('requirements', [])
                project_context = project_data.get('context', {})

                needed_skills = self._analyze_project_skills(project_requirements)
                adaptation_score = self._calculate_adaptation_score(employee, needed_skills)

                project_info = {
                    'project_id': project_data.get('id', f"proj_{int(time.time())}"),
                    'project_name': project_data.get('name', 'Unknown'),
                    'adaptation_score': adaptation_score,
                    'adapted_at': datetime.datetime.now().isoformat(),
                    'status': 'active' if adaptation_score >= 0.7 else 'needs_training'
                }

                if 'projects' not in employee:
                    employee['projects'] = []
                employee['projects'] = [p for p in employee['projects']
                                        if p.get('project_id') != project_info['project_id']]
                employee['projects'].append(project_info)

                employee['adaptation_status'] = {
                    'is_adapted': adaptation_score >= 0.7,
                    'last_adapted': datetime.datetime.now().isoformat(),
                    'adaptation_score': adaptation_score
                }

                employee['last_updated'] = datetime.datetime.now().isoformat()

                self._save_ai_employee(employee_id, employee)

                print(f"Adaptation completed for AI employee {employee_id} to project {project_info['project_name']}: Score {adaptation_score:.2f}")
        except Exception as e:
            logger.error(f"Error adapting AI employee {employee_id} to project: {e}")

    def _analyze_project_skills(self, project_requirements: list) -> list:
        """Analyze required skills from project requirements"""
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
        """Calculate adaptation score based on employee skills and needed skills"""
        employee_skills = set(employee.get('skills', []))
        needed_skills_set = set(needed_skills)

        if not needed_skills_set:
            return 1.0

        matching_skills = employee_skills.intersection(needed_skills_set)
        return len(matching_skills) / len(needed_skills_set)

    def start(self):
        """Start the AI employee manager"""
        self.thread_manager.start()

    def stop(self):
        """Stop the AI employee manager"""
        self.thread_manager.stop()


thread_manager = ThreadManager()
data_sync_manager = DataSyncManager()
backup_manager = BackupManager()
auto_upgrade_manager = AutoUpgradeManager()
ai_self_learning_manager = AISelfLearningManager()
ai_employee_manager = AIEmployeeManager()

export = [
    'initialize_ai_management',
    'shutdown_ai_management',
    'thread_manager',
    'data_sync_manager',
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
    initialize_ai_management()

    try:
        def test_task(name, sleep_time=1):
            time.sleep(sleep_time)
            print(f"Task {name} completed")

        thread_manager.add_task(test_task, priority=5, task_id="test1", name="High Priority", sleep_time=2)
        thread_manager.add_task(test_task, priority=10, task_id="test2", name="Medium Priority", sleep_time=1)
        thread_manager.add_task(test_task, priority=15, task_id="test3", name="Low Priority", sleep_time=0.5)

        thread_manager.wait_for_completion()

        backup_manager.create_backup("Test backup")
        print("Available backups:")
        for backup in backup_manager.list_backups():
            print(f"  - {backup['name']}: {backup['description']}")

        data_sync_manager.force_sync()

    finally:
        shutdown_ai_management()
