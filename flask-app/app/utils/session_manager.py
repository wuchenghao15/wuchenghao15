#!/usr/bin/env python3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SessionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions = {}
        return cls._instance

    def create_session(self, user_id, username, role, ip_address, user_agent):
        session_data = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'status': 'active'
        }
        self._sessions[f"{user_id}_{username}"] = session_data
        logger.info(f"会话已创建: 用户={username}, 角色={role}, IP={ip_address}")
        return session_data

    def get_session(self, user_id, username=None):
        key = f"{user_id}_{username}" if username else f"{user_id}_"
        for k, v in self._sessions.items():
            if k.startswith(f"{user_id}_"):
                return v
        return None

    def update_activity(self, user_id):
        for k, v in self._sessions.items():
            if k.startswith(f"{user_id}_"):
                v['last_activity'] = datetime.now().isoformat()
                return True
        return False

    def destroy_session(self, user_id, username=None):
        key = f"{user_id}_{username}" if username else None
        if key and key in self._sessions:
            del self._sessions[key]
            return True
        for k in list(self._sessions.keys()):
            if k.startswith(f"{user_id}_"):
                del self._sessions[k]
                return True
        return False

    def get_active_sessions(self):
        return [s for s in self._sessions.values() if s.get('status') == 'active']

    def get_session_count(self):
        return len(self._sessions)

def get_session_manager():
    return SessionManager()
