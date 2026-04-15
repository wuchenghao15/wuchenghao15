#!/usr/bin/env python3
"""
Library Management Module - Handles system library management, registration, and dependency tracking
"""

import os
import sys
import importlib
import json
import datetime
import threading
from typing import Dict, List, Any, Optional

class LibraryManager:
    """Library Manager - Handles system library management, registration, and dependency tracking"""
    
    def __init__(self, libraries_dir: str = "data/libraries"):
        self.libraries_dir = libraries_dir
        self.libraries = {}
        self.dependencies = {}
        self.loaded_libraries = {}
        self.lock = threading.RLock()
        
        # Ensure libraries directory exists
        os.makedirs(self.libraries_dir, exist_ok=True)
        
        # Load libraries from file
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
            print(f"Error loading libraries: {e}")
            self.libraries = {}
            self.dependencies = {}
    
    def _save_libraries(self):
        """Save libraries to configuration file"""
        try:
            libraries_file = os.path.join(self.libraries_dir, "libraries.json")
            library_data = {
                'libraries': self.libraries,
                'dependencies': self.dependencies,
                'last_updated': datetime.datetime.now().isoformat()
            }
            with open(libraries_file, 'w', encoding='utf-8') as f:
                json.dump(library_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving libraries: {e}")
    
    def register_library(self, name: str, library_info: Dict[str, Any]):
        """Register a new library"""
        with self.lock:
            # Validate library info
            if not all(key in library_info for key in ['version', 'path', 'description']):
                raise ValueError("Library info must contain version, path, and description")
            
            # Add default values
            library_info.setdefault('enabled', True)
            library_info.setdefault('dependencies', [])
            library_info.setdefault('created_at', datetime.datetime.now().isoformat())
            library_info.setdefault('last_updated', datetime.datetime.now().isoformat())
            
            # Register the library
            self.libraries[name] = library_info
            
            # Update dependencies
            for dep in library_info['dependencies']:
                if dep not in self.dependencies:
                    self.dependencies[dep] = []
                if name not in self.dependencies[dep]:
                    self.dependencies[dep].append(name)
            
            # Save to file
            self._save_libraries()
            
            print(f"Library {name} registered successfully")
            return True
    
    def unregister_library(self, name: str):
        """Unregister a library"""
        with self.lock:
            if name in self.libraries:
                # Remove from dependencies
                library = self.libraries[name]
                for dep in library['dependencies']:
                    if dep in self.dependencies and name in self.dependencies[dep]:
                        self.dependencies[dep].remove(name)
                
                # Remove the library
                del self.libraries[name]
                
                # Unload if loaded
                if name in self.loaded_libraries:
                    self.unload_library(name)
                
                # Save to file
                self._save_libraries()
                
                print(f"Library {name} unregistered successfully")
                return True
            return False
    
    def get_library(self, name: str) -> Optional[Dict[str, Any]]:
        """Get library information"""
        with self.lock:
            return self.libraries.get(name, None)
    
    def list_libraries(self, enabled_only: bool = False) -> Dict[str, Any]:
        """List all libraries"""
        with self.lock:
            if enabled_only:
                return {k: v for k, v in self.libraries.items() if v.get('enabled', True)}
            return self.libraries.copy()
    
    def load_library(self, name: str) -> bool:
        """Load a library"""
        with self.lock:
            if name not in self.libraries:
                print(f"Library {name} not registered")
                return False
            
            if name in self.loaded_libraries:
                print(f"Library {name} already loaded")
                return True
            
            library = self.libraries[name]
            if not library.get('enabled', True):
                print(f"Library {name} is disabled")
                return False
            
            try:
                # Check dependencies first
                for dep in library['dependencies']:
                    if dep not in self.loaded_libraries:
                        if not self.load_library(dep):
                            print(f"Failed to load dependency {dep} for library {name}")
                            return False
                
                # Add library path to sys.path if needed
                lib_path = library['path']
                if lib_path not in sys.path:
                    sys.path.insert(0, lib_path)
                
                # Import the library
                module = importlib.import_module(name)
                self.loaded_libraries[name] = {
                    'module': module,
                    'loaded_at': datetime.datetime.now().isoformat()
                }
                
                print(f"Library {name} loaded successfully")
                return True
            except Exception as e:
                print(f"Failed to load library {name}: {e}")
                return False
    
    def unload_library(self, name: str) -> bool:
        """Unload a library"""
        with self.lock:
            if name not in self.loaded_libraries:
                print(f"Library {name} not loaded")
                return False
            
            # Check if any other library depends on this one
            if name in self.dependencies:
                dependent_libraries = self.dependencies[name]
                for dep_lib in dependent_libraries:
                    if dep_lib in self.loaded_libraries:
                        print(f"Cannot unload {name}: {dep_lib} depends on it")
                        return False
            
            try:
                # Remove from loaded libraries
                del self.loaded_libraries[name]
                
                # Remove from sys.path if not needed by other libraries
                if name in self.libraries:
                    lib_path = self.libraries[name]['path']
                    if lib_path in sys.path:
                        # Check if other libraries use the same path
                        other_uses = any(
                            lib['path'] == lib_path and lib_name != name and lib_name in self.loaded_libraries
                            for lib_name, lib in self.libraries.items()
                        )
                        if not other_uses:
                            sys.path.remove(lib_path)
                
                print(f"Library {name} unloaded successfully")
                return True
            except Exception as e:
                print(f"Failed to unload library {name}: {e}")
                return False
    
    def is_loaded(self, name: str) -> bool:
        """Check if a library is loaded"""
        with self.lock:
            return name in self.loaded_libraries
    
    def get_loaded_libraries(self) -> List[str]:
        """Get list of loaded libraries"""
        with self.lock:
            return list(self.loaded_libraries.keys())
    
    def enable_library(self, name: str) -> bool:
        """Enable a library"""
        with self.lock:
            if name in self.libraries:
                self.libraries[name]['enabled'] = True
                self.libraries[name]['last_updated'] = datetime.datetime.now().isoformat()
                self._save_libraries()
                print(f"Library {name} enabled")
                return True
            return False
    
    def disable_library(self, name: str) -> bool:
        """Disable a library"""
        with self.lock:
            if name in self.libraries:
                self.libraries[name]['enabled'] = False
                self.libraries[name]['last_updated'] = datetime.datetime.now().isoformat()
                
                # Unload if currently loaded
                if name in self.loaded_libraries:
                    self.unload_library(name)
                
                self._save_libraries()
                print(f"Library {name} disabled")
                return True
            return False
    
    def check_dependencies(self, name: str) -> Dict[str, Any]:
        """Check dependencies for a library"""
        with self.lock:
            if name not in self.libraries:
                return {
                    'library': name,
                    'exists': False,
                    'dependencies': [],
                    'missing_dependencies': [],
                    'status': 'error'
                }
            
            library = self.libraries[name]
            dependencies = library['dependencies']
            missing_deps = [dep for dep in dependencies if dep not in self.libraries]
            
            return {
                'library': name,
                'exists': True,
                'dependencies': dependencies,
                'missing_dependencies': missing_deps,
                'status': 'ok' if not missing_deps else 'missing_dependencies'
            }
    
    def get_dependency_tree(self, name: str) -> Dict[str, Any]:
        """Get dependency tree for a library"""
        with self.lock:
            if name not in self.libraries:
                return {
                    'library': name,
                    'exists': False,
                    'tree': {}
                }
            
            def build_tree(lib_name):
                if lib_name not in self.libraries:
                    return None
                
                lib = self.libraries[lib_name]
                tree = {
                    'info': lib,
                    'dependencies': {}
                }
                
                for dep in lib['dependencies']:
                    dep_tree = build_tree(dep)
                    if dep_tree:
                        tree['dependencies'][dep] = dep_tree
                
                return tree
            
            return {
                'library': name,
                'exists': True,
                'tree': build_tree(name)
            }
    
    def reload_library(self, name: str) -> bool:
        """Reload a library"""
        with self.lock:
            if name not in self.loaded_libraries:
                return self.load_library(name)
            
            # Unload first, then load again
            self.unload_library(name)
            return self.load_library(name)
    
    def reload_all_libraries(self) -> Dict[str, bool]:
        """Reload all loaded libraries"""
        with self.lock:
            results = {}
            loaded_libs = list(self.loaded_libraries.keys())
            
            # Unload all first
            for lib_name in loaded_libs:
                self.unload_library(lib_name)
            
            # Load them back
            for lib_name in loaded_libs:
                results[lib_name] = self.load_library(lib_name)
            
            return results


# Global library manager instance
library_manager = LibraryManager()
