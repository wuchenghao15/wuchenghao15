# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Library Management Module - Handles system library management, registration, and dependency tracking
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import importlib
import json
import datetime
import threading
from typing import Dict, List, Any, Optional

class LibraryManager:
    """Library Manager - Handles system library management: registration, and dependency tracking"""

    def __init__(self, libraries_dir: str = "data/libraries"):
        self.libraries_dir = libraries_dir
        self.libraries = {}
        self.dependencies = {}
        self.loaded_libraries = {}
        self.lock = threading.RLock()

        os.makedirs(self.libraries_dir, exist_ok=True)

        self._load_libraries()

    def _load_libraries(self):
        """Load libraries from configuration file"""
        try:
            libraries_file = os.path.join(self.libraries_dir, "libraries.json")
            if os.path.exists(libraries_file):
                with open(libraries_file, 'r', encoding='utf-8') as f:
                    library_data = json.load(f)
                    self.libraries = library_data.get('libraries', {})
                    self.dependencies = library_data.get('dependencies', {})
        except Exception as e:
            logger.error(f"Error loading libraries: {e}")
            self.libraries = {}

    def _save_libraries(self):
        """Save libraries to configuration file"""
        try:
            libraries_file = os.path.join(self.libraries_dir, "libraries.json")
            library_data = {
                'libraries': self.libraries,
                'dependencies': self.dependencies
            }
            with open(libraries_file, 'w', encoding='utf-8') as f:
                json.dump(library_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving libraries: {e}")

    def register_library(self, name: str, library_info: Dict[str, Any]):
        """Register a new library"""
        with self.lock:
            if not all(key in library_info for key in ['version', 'path', 'description']):
                raise ValueError("Library info must contain version, path, and description")

            library_info.setdefault('enabled', True)
            library_info.setdefault('dependencies', [])
            library_info.setdefault('created_at', datetime.datetime.now().isoformat())
            library_info.setdefault('last_updated', datetime.datetime.now().isoformat())

            self.libraries[name] = library_info

            for dep in library_info['dependencies']:
                if dep not in self.dependencies:
                    self.dependencies[dep] = []
                if name not in self.dependencies[dep]:
                    self.dependencies[dep].append(name)

            self._save_libraries()

            print(f"Library {name} registered successfully")
            return True

    def unregister_library(self, name: str):
        """Unregister a library"""
        with self.lock:
            if name in self.libraries:
                library = self.libraries[name]
                for dep in library['dependencies']:
                    if dep in self.dependencies and name in self.dependencies[dep]:
                        self.dependencies[dep].remove(name)

                del self.libraries[name]

                if name in self.loaded_libraries:
                    self.unload_library(name)

                self._save_libraries()

                print(f"Library {name} unregistered successfully")
                return True
            return False

    def load_library(self, name: str):
        """Load a library"""
        if name not in self.libraries:
            print(f"Library {name} not found")
            return None

        if name in self.loaded_libraries:
            return self.loaded_libraries[name]

        try:
            library_info = self.libraries[name]
            module_path = library_info['path']
            
            if os.path.exists(module_path):
                spec = importlib.util.spec_from_file_location(name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.loaded_libraries[name] = module
                print(f"Library {name} loaded successfully")
                return module
            else:
                print(f"Library path not found: {module_path}")
                return None
        except Exception as e:
            print(f"Error loading library {name}: {e}")
            return None

    def unload_library(self, name: str):
        """Unload a library"""
        if name in self.loaded_libraries:
            del self.loaded_libraries[name]
            if name in sys.modules:
                del sys.modules[name]
            print(f"Library {name} unloaded successfully")
            return True
        return False

    def get_library(self, name: str):
        """Get a loaded library"""
        return self.loaded_libraries.get(name)

    def list_libraries(self):
        """List all registered libraries"""
        return list(self.libraries.keys())

    def get_library_info(self, name: str):
        """Get library information"""
        return self.libraries.get(name)

    def enable_library(self, name: str):
        """Enable a library"""
        if name in self.libraries:
            self.libraries[name]['enabled'] = True
            self.libraries[name]['last_updated'] = datetime.datetime.now().isoformat()
            self._save_libraries()
            return True
        return False

    def disable_library(self, name: str):
        """Disable a library"""
        if name in self.libraries:
            self.libraries[name]['enabled'] = False
            self.libraries[name]['last_updated'] = datetime.datetime.now().isoformat()
            self._save_libraries()
            return True
        return False

library_manager = LibraryManager()
