#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System Integration Module - Ensures all system components work together
as a unified whole, with all actions tracked and logged.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from .event_tracker import event_tracker, EventCategory, EventAction, EventPriority, SystemEvent
from .database import db
from .logging import logger

class SystemIntegrator:
    """
    Central integration hub that ensures all system components are connected.
    All actions flow through this integrator to ensure tracking and logging.
    """
    
    def __init__(self):
        self._modules = {}
        self._dependencies = {}
        self._initialized = False
        
    def initialize(self):
        """Initialize the integrator and all registered modules"""
        if self._initialized:
            return
            
        event_tracker.track(SystemEvent(
            category=EventCategory.SYSTEM,
            action=EventAction.EXECUTE,
            subject="System Integration Initialized",
            details={
                'timestamp': datetime.now().isoformat(),
                'modules_count': len(self._modules)
            },
            priority=EventPriority.HIGH
        ))
        
        for module_name, module in self._modules.items():
            if hasattr(module, 'initialize'):
                try:
                    module.initialize()
                    event_tracker.track(SystemEvent(
                        category=EventCategory.SYSTEM,
                        action=EventAction.EXECUTE,
                        subject=f"Module Initialized: {module_name}",
                        priority=EventPriority.LOW
                    ))
                except Exception as e:
                    event_tracker.track_system_error(
                        f"Module Initialization Failed: {module_name}",
                        str(e)
                    )
        
        self._initialized = True
        logger.info("System integrator initialized successfully")
    
    def register_module(self, name: str, module, dependencies: list = None):
        """
        Register a module with the integrator
        All modules must declare their dependencies to ensure proper initialization order
        """
        self._modules[name] = module
        self._dependencies[name] = dependencies or []
        
        event_tracker.track(SystemEvent(
            category=EventCategory.SYSTEM,
            action=EventAction.CREATE,
            subject=f"Module Registered: {name}",
            details={
                'dependencies': dependencies or [],
                'registered_at': datetime.now().isoformat()
            },
            priority=EventPriority.LOW
        ))
    
    def get_module(self, name: str):
        """Retrieve a registered module"""
        if name not in self._modules:
            raise ValueError(f"Module '{name}' not registered")
        return self._modules[name]
    
    def execute_action(self, module_name: str, action_name: str, params: Dict[str, Any] = None, user_id: str = None) -> Any:
        """
        Execute an action on a module with full tracking
        This is the primary way to interact with modules
        """
        if module_name not in self._modules:
            raise ValueError(f"Module '{module_name}' not registered")
        
        module = self._modules[module_name]
        
        if not hasattr(module, action_name):
            raise ValueError(f"Action '{action_name}' not found in module '{module_name}'")
        
        action_func = getattr(module, action_name)
        
        with event_tracker.EventContext(event_tracker, f"{module_name}.{action_name}", user_id) as ctx:
            try:
                ctx.track(SystemEvent(
                    category=EventCategory.SYSTEM,
                    action=EventAction.EXECUTE,
                    subject=f"Action Started: {module_name}.{action_name}",
                    details={
                        'params': params or {},
                        'user_id': user_id,
                        'timestamp': datetime.now().isoformat()
                    },
                    priority=EventPriority.MEDIUM
                ))
                
                result = action_func(**(params or {}))
                
                ctx.track(SystemEvent(
                    category=EventCategory.SYSTEM,
                    action=EventAction.EXECUTE,
                    subject=f"Action Completed: {module_name}.{action_name}",
                    details={
                        'success': True,
                        'result_type': type(result).__name__ if result else 'None',
                        'completed_at': datetime.now().isoformat()
                    },
                    priority=EventPriority.LOW
                ))
                
                return result
                
            except Exception as e:
                ctx.track(SystemEvent(
                    category=EventCategory.SYSTEM,
                    action=EventAction.ERROR,
                    subject=f"Action Failed: {module_name}.{action_name}",
                    details={
                        'error': str(e),
                        'params': params or {},
                        'failed_at': datetime.now().isoformat()
                    },
                    priority=EventPriority.CRITICAL
                ))
                raise
    
    def update_setting(self, setting_name: str, value: Any, user_id: str = None) -> str:
        """
        Update a system setting with full tracking
        Ensures all setting changes are logged and linked
        """
        from .config import config
        
        old_value = config.get(setting_name)
        
        config.set(setting_name, value)
        
        event_id = event_tracker.track_settings_change(
            setting_name, old_value, value, user_id
        )
        
        return event_id
    
    def validate_system_consistency(self) -> Dict[str, Any]:
        """
        Validate that all system components are consistent
        Checks database integrity, module dependencies, and event tracking
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'database': self._check_database(),
            'modules': self._check_modules(),
            'events': self._check_events()
        }
        
        event_tracker.track(SystemEvent(
            category=EventCategory.SYSTEM,
            action=EventAction.VALIDATE,
            subject="System Consistency Check",
            details=results,
            priority=EventPriority.MEDIUM
        ))
        
        return results
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database integrity"""
        try:
            tables = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
            return {
                'status': 'healthy',
                'tables_count': len(tables),
                'tables': [t['name'] for t in tables]
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_modules(self) -> Dict[str, Any]:
        """Check module dependencies"""
        results = {
            'total_modules': len(self._modules),
            'dependencies': {}
        }
        
        for module_name, deps in self._dependencies.items():
            satisfied = all(dep in self._modules for dep in deps)
            results['dependencies'][module_name] = {
                'dependencies': deps,
                'satisfied': satisfied
            }
        
        return results
    
    def _check_events(self) -> Dict[str, Any]:
        """Check event tracking system"""
        try:
            recent_events = event_tracker.get_recent_events(10)
            return {
                'status': 'healthy',
                'recent_events_count': len(recent_events)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

class ActionWrapper:
    """
    Decorator class to wrap functions with event tracking
    Ensures all function calls are tracked in the event system
    """
    
    @staticmethod
    def track_event(category: EventCategory, action: EventAction, subject_template: str = None):
        """
        Decorator that tracks function calls as events
        
        Args:
            category: Event category
            action: Event action
            subject_template: Template for subject (can use {func_name})
        """
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                func_name = func.__name__
                subject = subject_template.format(func_name=func_name) if subject_template else f"Function: {func_name}"
                
                event = SystemEvent(
                    category=category,
                    action=action,
                    subject=subject,
                    details={
                        'function': func_name,
                        'args': str(args)[:100],
                        'kwargs': {k: str(v)[:50] for k, v in kwargs.items()},
                        'timestamp': datetime.now().isoformat()
                    },
                    priority=EventPriority.MEDIUM
                )
                
                event_id = event_tracker.track(event)
                
                try:
                    result = func(*args, **kwargs)
                    
                    event_tracker.track(SystemEvent(
                        category=category,
                        action=EventAction.EXECUTE,
                        subject=f"{subject} - Completed",
                        details={
                            'event_id': event_id,
                            'success': True,
                            'result_type': type(result).__name__ if result else 'None'
                        },
                        priority=EventPriority.LOW
                    ))
                    
                    return result
                except Exception as e:
                    event_tracker.track(SystemEvent(
                        category=category,
                        action=EventAction.ERROR,
                        subject=f"{subject} - Failed",
                        details={
                            'event_id': event_id,
                            'error': str(e),
                            'success': False
                        },
                        priority=EventPriority.HIGH
                    ))
                    raise
            return wrapper
        return decorator

class SettingsManager:
    """
    Central settings management with full tracking
    All setting changes are tracked and logged
    """
    
    def __init__(self):
        from .config import config
        self.config = config
        self._setting_change_callbacks = []
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any, user_id: str = None) -> str:
        """
        Set a setting value with full tracking
        Returns the event ID for reference
        """
        old_value = self.config.get(key)
        self.config.set(key, value)
        
        event_id = event_tracker.track_settings_change(key, old_value, value, user_id)
        
        for callback in self._setting_change_callbacks:
            try:
                callback(key, old_value, value, user_id)
            except Exception as e:
                logger.error(f"Setting change callback failed for {key}: {str(e)}")
        
        return event_id
    
    def register_change_callback(self, callback: Callable):
        """Register a callback to be called when settings change"""
        self._setting_change_callbacks.append(callback)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings with their current values"""
        return self.config.get_all()
    
    def export_settings(self) -> str:
        """Export all settings as JSON"""
        settings = self.get_all_settings()
        return json.dumps(settings, indent=2, ensure_ascii=False)
    
    def import_settings(self, settings_json: str, user_id: str = None):
        """Import settings from JSON"""
        try:
            settings = json.loads(settings_json)
            
            with event_tracker.EventContext(event_tracker, "Settings Import", user_id) as ctx:
                for key, value in settings.items():
                    ctx.track(SystemEvent(
                        category=EventCategory.SETTINGS,
                        action=EventAction.UPDATE,
                        subject=f"Setting Imported: {key}",
                        details={
                            'value': str(value),
                            'imported_by': user_id
                        },
                        priority=EventPriority.LOW
                    ))
                    self.config.set(key, value)
            
            event_tracker.track(SystemEvent(
                category=EventCategory.SETTINGS,
                action=EventAction.CONFIGURE,
                subject="Settings Import Completed",
                details={
                    'settings_count': len(settings),
                    'imported_by': user_id,
                    'timestamp': datetime.now().isoformat()
                },
                priority=EventPriority.MEDIUM
            ))
            
        except json.JSONDecodeError as e:
            event_tracker.track_system_error("Settings Import Failed", f"Invalid JSON: {str(e)}")
            raise

# Global system integrator instance
system_integrator = SystemIntegrator()

# Global settings manager instance
settings_manager = SettingsManager()

# Convenience functions
def track_settings_change(key: str, old_value: Any, new_value: Any, user_id: str = None):
    """Convenience function to track settings changes"""
    return event_tracker.track_settings_change(key, old_value, new_value, user_id)

def validate_system():
    """Convenience function to validate system consistency"""
    return system_integrator.validate_system_consistency()

def init_system():
    """Convenience function to initialize the system"""
    system_integrator.initialize()
