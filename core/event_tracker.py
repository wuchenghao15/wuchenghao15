# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Event Tracking System - Core module for tracking all system events
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional, Union
from enum import Enum
from .database import db
from .logging import logger
import logging
import sys
import os

class EventCategory(Enum):
    """Categories of system events"""
    AUTHENTICATION = "authentication"
    SETTINGS = "settings"
    EXAM = "exam"
    PERMISSION = "permission"
    USER = "user"
    SYSTEM = "system"
    API = "api"
    DATABASE = "database"
    SECURITY = "security"

class EventAction(Enum):
    """Types of actions for events"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    VIEW = "view"
    EXECUTE = "execute"
    CONFIGURE = "configure"
    VALIDATE = "validate"
    ERROR = "error"
    WARNING = "warning"

class EventPriority(Enum):
    """Priority levels for events"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class SystemEvent:
    """
    Represents a system event that needs to be tracked.
    All actions in the system should create an event.
    """
    
    def __init__(
        self,
        category: Union[EventCategory, str],
        action: Union[EventAction, str],
        subject: str,
        details: Dict[str, Any] = None,
        user_id: Optional[str] = None,
        user_ip: Optional[str] = None,
        priority: Union[EventPriority, int] = EventPriority.MEDIUM,
        metadata: Dict[str, Any] = None
    ):
        self.event_id = str(uuid.uuid4())
        self.category = category.value if isinstance(category, Enum) else category
        self.action = action.value if isinstance(action, Enum) else action
        self.subject = subject
        self.details = details or {}
        self.user_id = user_id
        self.user_ip = user_ip
        self.priority = priority.value if isinstance(priority, Enum) else priority
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.processed = False
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for storage"""
        return {
            'event_id': self.event_id,
            'category': self.category,
            'action': self.action,
            'subject': self.subject,
            'details': json.dumps(self.details, ensure_ascii=False),
            'user_id': self.user_id,
            'user_ip': self.user_ip,
            'priority': self.priority,
            'metadata': json.dumps(self.metadata, ensure_ascii=False),
            'timestamp': self.timestamp.isoformat(),
            'processed': 1 if self.processed else 0
        }
        
    def __repr__(self) -> str:
        return f"<SystemEvent {self.category}.{self.action}: {self.subject}>"

class EventTracker:
    """
    Central event tracking system that records all system events to both
    database and log files. Ensures complete traceability of all actions.
    """
    
    def __init__(self):
        self._init_database()
        self._event_hooks = []
        
    def _init_database(self):
        """Initialize event tracking tables if they don't exist"""
        db.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                action TEXT NOT NULL,
                subject TEXT NOT NULL,
                details TEXT,
                user_id TEXT,
                user_ip TEXT,
                priority INTEGER DEFAULT 2,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                processed INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        db.execute("""
            CREATE TABLE IF NOT EXISTS event_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_event_id TEXT NOT NULL,
                target_event_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                FOREIGN KEY (source_event_id) REFERENCES system_events(event_id),
                FOREIGN KEY (target_event_id) REFERENCES system_events(event_id)
            )
        """)
        
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_category ON system_events(category)
        """)
        
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_action ON system_events(action)
        """)
        
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON system_events(timestamp)
        """)
        
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_user ON system_events(user_id)
        """)
        
        db.commit()
        
    def track(self, event: SystemEvent) -> str:
        """
        Track an event - record to database and log
        Returns the event_id for reference
        """
        try:
            event_dict = event.to_dict()
            
            db.execute("""
                INSERT INTO system_events (
                    event_id, category, action, subject, details,
                    user_id, user_ip, priority, metadata, timestamp, processed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.category,
                event.action,
                event.subject,
                event.details,
                event.user_id,
                event.user_ip,
                event.priority,
                event.metadata,
                event.timestamp.isoformat(),
                0
            ))
            db.commit()
            
            self._log_event(event)
            self._trigger_hooks(event)
            
            logger.info(f"Event tracked: {event.category}.{event.action} - {event.subject}")
            return event.event_id
            
        except Exception as e:
            logger.error(f"Failed to track event: {str(e)}", exception=e)
            return ""
    
    def _log_event(self, event: SystemEvent):
        """Log event to system logs"""
        priority_label = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}.get(event.priority, "MEDIUM")
        log_message = (
            f"[EVENT] [{priority_label}] [{event.category.upper()}] "
            f"{event.action.upper()} :: {event.subject}"
        )
        
        if event.user_id:
            log_message += f" | User: {event.user_id}"
        if event.user_ip:
            log_message += f" | IP: {event.user_ip}"
        if event.details:
            log_message += f" | Details: {json.dumps(event.details, ensure_ascii=False)[:200]}..."
        
        if event.priority >= 3:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _trigger_hooks(self, event: SystemEvent):
        """Trigger registered event hooks"""
        for hook in self._event_hooks:
            try:
                hook(event)
            except Exception as e:
                logger.error(f"Event hook failed: {str(e)}", exception=e)
    
    def register_hook(self, hook_func):
        """Register a function to be called when events are tracked"""
        self._event_hooks.append(hook_func)
    
    def link_events(self, source_event_id: str, target_event_id: str, relationship: str = "related"):
        """
        Link two events together to establish relationships
        This ensures events are not isolated but connected
        """
        try:
            db.execute("""
                INSERT INTO event_links (source_event_id, target_event_id, relationship)
                VALUES (?, ?, ?)
            """, (source_event_id, target_event_id, relationship))
            db.commit()
            logger.info(f"Linked events: {source_event_id} -> {target_event_id} ({relationship})")
        except Exception as e:
            logger.error(f"Failed to link events: {str(e)}", exception=e)
    
    def get_events_by_category(self, category: str) -> list:
        """Retrieve events by category"""
        return db.fetch_all("SELECT * FROM system_events WHERE category = ? ORDER BY timestamp DESC", (category,))
    
    def get_events_by_user(self, user_id: str) -> list:
        """Retrieve events by user"""
        return db.fetch_all("SELECT * FROM system_events WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    
    def get_event_by_id(self, event_id: str) -> Optional[dict]:
        """Retrieve a specific event by ID"""
        return db.fetch_one("SELECT * FROM system_events WHERE event_id = ?", (event_id,))
    
    def get_related_events(self, event_id: str) -> list:
        """Get all events related to a specific event"""
        return db.fetch_all("""
            SELECT e.* FROM system_events e
            JOIN event_links el ON e.event_id = el.target_event_id
            WHERE el.source_event_id = ?
            ORDER BY e.timestamp DESC
        """, (event_id,))
    
    def get_recent_events(self, limit: int = 100) -> list:
        """Get most recent events"""
        return db.fetch_all("SELECT * FROM system_events ORDER BY timestamp DESC LIMIT ?", (limit,))
    
    def track_settings_change(self, setting_name: str, old_value: Any, new_value: Any, user_id: str = None):
        """Convenience method for tracking settings changes"""
        event = SystemEvent(
            category=EventCategory.SETTINGS,
            action=EventAction.UPDATE,
            subject=f"Setting: {setting_name}",
            details={
                'setting_name': setting_name,
                'old_value': str(old_value),
                'new_value': str(new_value),
                'changed_at': datetime.now().isoformat()
            },
            user_id=user_id,
            priority=EventPriority.MEDIUM
        )
        return self.track(event)
    
    def track_login(self, user_id: str, user_ip: str, success: bool, reason: str = ""):
        """Convenience method for tracking login attempts"""
        action = EventAction.LOGIN if success else EventAction.ERROR
        event = SystemEvent(
            category=EventCategory.AUTHENTICATION,
            action=action,
            subject=f"User Login: {user_id}",
            details={
                'success': success,
                'reason': reason,
                'attempted_at': datetime.now().isoformat()
            },
            user_id=user_id,
            user_ip=user_ip,
            priority=EventPriority.HIGH if not success else EventPriority.MEDIUM
        )
        return self.track(event)
    
    def track_exam_action(self, exam_id: str, action: str, details: Dict[str, Any] = None, user_id: str = None):
        """Convenience method for tracking exam-related actions"""
        event = SystemEvent(
            category=EventCategory.EXAM,
            action=action,
            subject=f"Exam: {exam_id}",
            details=details or {},
            user_id=user_id,
            priority=EventPriority.MEDIUM
        )
        return self.track(event)
    
    def track_permission_change(self, role_id: str, permission_name: str, granted: bool, user_id: str = None):
        """Convenience method for tracking permission changes"""
        action = EventAction.UPDATE
        event = SystemEvent(
            category=EventCategory.PERMISSION,
            action=action,
            subject=f"Permission: {permission_name} for role {role_id}",
            details={
                'role_id': role_id,
                'permission_name': permission_name,
                'granted': granted,
                'changed_at': datetime.now().isoformat()
            },
            user_id=user_id,
            priority=EventPriority.HIGH
        )
        return self.track(event)
    
    def track_system_error(self, error_type: str, message: str, traceback: str = "", user_id: str = None):
        """Convenience method for tracking system errors"""
        event = SystemEvent(
            category=EventCategory.SYSTEM,
            action=EventAction.ERROR,
            subject=f"System Error: {error_type}",
            details={
                'error_type': error_type,
                'message': message,
                'traceback': traceback[:2000] if traceback else "",
                'occurred_at': datetime.now().isoformat()
            },
            user_id=user_id,
            priority=EventPriority.CRITICAL
        )
        return self.track(event)

class EventContext:
    """
    Context manager for tracking related events as a transaction
    Ensures all events in a transaction are linked together
    """
    
    def __init__(self, tracker: EventTracker, transaction_name: str, user_id: str = None):
        self.tracker = tracker
        self.transaction_name = transaction_name
        self.user_id = user_id
        self.events = []
        self.transaction_event = None
        
    def __enter__(self):
        self.transaction_event = SystemEvent(
            category=EventCategory.SYSTEM,
            action=EventAction.EXECUTE,
            subject=f"Transaction: {self.transaction_name}",
            details={'status': 'started'},
            user_id=self.user_id,
            priority=EventPriority.MEDIUM
        )
        self.tracker.track(self.transaction_event)
        return self
    
    def track(self, event: SystemEvent) -> str:
        """Track an event within this context"""
        event_id = self.tracker.track(event)
        self.events.append(event_id)
        
        if self.transaction_event:
            self.tracker.link_events(self.transaction_event.event_id, event_id, "contains")
        
        return event_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.transaction_event:
            status = 'completed' if not exc_type else 'failed'
            self.transaction_event.details['status'] = status
            self.transaction_event.details['event_count'] = len(self.events)
            
            if exc_type:
                self.transaction_event.details['error'] = str(exc_val)
                self.transaction_event.priority = EventPriority.HIGH
            
            self.tracker.track(SystemEvent(
                category=EventCategory.SYSTEM,
                action=EventAction.EXECUTE if not exc_type else EventAction.ERROR,
                subject=f"Transaction: {self.transaction_name} ({status})",
                details=self.transaction_event.details,
                user_id=self.user_id,
                priority=self.transaction_event.priority
            ))

# Global event tracker instance
event_tracker = EventTracker()

def track_event(category: Union[EventCategory, str], action: Union[EventAction, str], 
                subject: str, details: Dict[str, Any] = None, user_id: str = None, 
                priority: Union[EventPriority, int] = EventPriority.MEDIUM) -> str:
    """
    Convenience function to track an event without creating SystemEvent directly
    """
    event = SystemEvent(
        category=category,
        action=action,
        subject=subject,
        details=details,
        user_id=user_id,
        priority=priority
    )
    return event_tracker.track(event)
