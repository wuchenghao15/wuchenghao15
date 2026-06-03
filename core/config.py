# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration management module - Enhanced Version
"""

import os
import json
from typing import Dict, Any, Optional, List, Union
import logging
import sys

class ConfigManager:
    """Enhanced centralized configuration manager"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self._version = "3.1.0"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    return self._merge_configs(self._get_default_config(), loaded_config)
            except Exception as e:
                print(f"Error loading config: {e}")
        return self._get_default_config()
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Merge loaded config with defaults, preserving new keys"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get enhanced default configuration"""
        return {
            "version": "3.0.0",
            "database": {
                "path": "app.db",
                "backup_path": "backups/",
                "auto_backup": True,
                "backup_interval_hours": 24,
                "enable_wal": True,
                "cache_size": -20000
            },
            "api": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False,
                "timeout": 30,
                "cors_enabled": True,
                "rate_limit_per_minute": 60
            },
            "ai": {
                "model_path": "models/",
                "max_tokens": 8192,
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "api_timeout": 120,
                "default_provider": "auto",
                "providers": {
                    "openai": {
                        "api_key": os.environ.get("OPENAI_API_KEY", ""),
                        "base_url": "https://api.openai.com/v1",
                        "default_model": "gpt-4o",
                        "available_models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
                    },
                    "ollama": {
                        "base_url": "http://localhost:11434",
                        "default_model": "llama3.1",
                        "available_models": ["llama3.1", "mistral", "gemma2"]
                    },
                    "anthropic": {
                        "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
                        "default_model": "claude-3-5-sonnet",
                        "available_models": ["claude-3-5-sonnet", "claude-3-opus"]
                    }
                },
                "cache_enabled": True,
                "cache_ttl_seconds": 3600,
                "streaming_enabled": True
            },
            "logging": {
                "level": "INFO",
                "file_path": "logs/system.log",
                "max_file_size_mb": 100,
                "backup_count": 10,
                "console_level": "INFO",
                "file_level": "DEBUG",
                "json_format": False
            },
            "security": {
                "secret_key": os.environ.get("SECRET_KEY", os.urandom(32).hex()),
                "token_expire_hours": 24,
                "allowed_ips": [],
                "rate_limit": 100,
                "enable_https": False,
                "ssl_cert_path": "",
                "ssl_key_path": ""
            },
            "system": {
                "auto_recovery": True,
                "maintenance_interval_hours": 6,
                "max_workers": 8,
                "health_check_interval_seconds": 30,
                "performance_monitoring_enabled": True,
                "auto_update_check": False
            },
            "features": {
                "code_generation": True,
                "code_analysis": True,
                "text_summarization": True,
                "translation": True,
                "rag_enabled": False,
                "vector_db_path": "vectors/"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value using dot notation"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete config dictionary"""
        return self.config.copy()
    
    def set(self, key: str, value: Any) -> None:
        """Set config value using dot notation"""
        keys = key.split('.')
        config = self.config
        
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def has(self, key: str) -> bool:
        """Check if config key exists"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return False
        
        return True
    
    def delete(self, key: str) -> bool:
        """Delete a config key"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                return False
            config = config[k]
        
        if keys[-1] in config:
            del config[keys[-1]]
            return True
        return False
    
    def reload(self) -> None:
        """Reload configuration from file"""
        self.config = self._load_config()
    
    def save(self) -> None:
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file) or '.', exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_version(self) -> str:
        """Get config version"""
        return self._version

# Global config instance
config = ConfigManager()
