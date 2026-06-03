# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions module
"""

import os
import json
import hashlib
import time
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

class FileUtils:
    """File utilities"""
    
    @staticmethod
    def read_file(file_path: str) -> str:
        """Read file content"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def write_file(file_path: str, content: str) -> None:
        """Write content to file"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def read_json(file_path: str) -> Dict[str, Any]:
        """Read JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def write_json(file_path: str, data: Dict[str, Any], indent: int = 2) -> None:
        """Write JSON file"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """Check if file exists"""
        return os.path.exists(file_path)
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        return os.path.getsize(file_path)
    
    @staticmethod
    def list_files(directory: str, pattern: str = "*") -> List[str]:
        """List files in directory matching pattern"""
        path = Path(directory)
        return [str(f) for f in path.glob(pattern) if f.is_file()]
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete file"""
        try:
            os.remove(file_path)
            return True
        except Exception:
            return False
    
    @staticmethod
    def backup_file(file_path: str, backup_dir: str = "backups") -> str:
        """Create backup of file"""
        os.makedirs(backup_dir, exist_ok=True)
        file_name = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{backup_dir}/{file_name}_{timestamp}.bak"
        
        with open(file_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        
        return backup_path

class StringUtils:
    """String utilities"""
    
    @staticmethod
    def md5_hash(text: str) -> str:
        """Compute MD5 hash"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def sha256_hash(text: str) -> str:
        """Compute SHA256 hash"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate UUID"""
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate string to max length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def remove_special_chars(text: str) -> str:
        """Remove special characters"""
        return re.sub(r'[^\w\s]', '', text)
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace"""
        return ' '.join(text.strip().split())
    
    @staticmethod
    def to_snake_case(text: str) -> str:
        """Convert to snake_case"""
        text = re.sub(r'[^a-zA-Z0-9]', '_', text)
        text = re.sub(r'_+', '_', text)
        return text.lower().strip('_')
    
    @staticmethod
    def to_camel_case(text: str) -> str:
        """Convert to CamelCase"""
        words = re.sub(r'[^a-zA-Z0-9]', ' ', text).split()
        return ''.join(word.capitalize() for word in words)

class TimeUtils:
    """Time utilities"""
    
    @staticmethod
    def get_current_time() -> datetime:
        """Get current datetime"""
        return datetime.now()
    
    @staticmethod
    def get_current_timestamp() -> int:
        """Get current timestamp in seconds"""
        return int(time.time())
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime"""
        return dt.strftime(format_str)
    
    @staticmethod
    def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
        """Parse datetime string"""
        return datetime.strptime(date_str, format_str)
    
    @staticmethod
    def time_since(dt: datetime) -> str:
        """Get time since datetime"""
        delta = datetime.now() - dt
        
        if delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600} hours ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60} minutes ago"
        else:
            return "just now"
    
    @staticmethod
    def measure_time(func):
        """Decorator to measure execution time"""
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            print(f"Function {func.__name__} executed in {end - start:.4f}s")
            return result
        return wrapper

class ValidationUtils:
    """Validation utilities"""
    
    @staticmethod
    def is_email(email: str) -> bool:
        """Check if string is valid email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_url(url: str) -> bool:
        """Check if string is valid URL"""
        pattern = r'^https?://[^\s]+$'
        return re.match(pattern, url) is not None
    
    @staticmethod
    def is_ip_address(ip: str) -> bool:
        """Check if string is valid IP address"""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(pattern, ip):
            parts = ip.split('.')
            return all(0 <= int(p) <= 255 for p in parts)
        return False
    
    @staticmethod
    def is_valid_json(text: str) -> bool:
        """Check if string is valid JSON"""
        try:
            json.loads(text)
            return True
        except ValueError:
            return False

class DataUtils:
    """Data manipulation utilities"""
    
    @staticmethod
    def merge_dicts(*dicts: Dict) -> Dict:
        """Merge multiple dictionaries"""
        result = {}
        for d in dicts:
            result.update(d)
        return result
    
    @staticmethod
    def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DataUtils.deep_merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    @staticmethod
    def chunk_list(lst: List, chunk_size: int) -> List[List]:
        """Split list into chunks"""
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    
    @staticmethod
    def flatten_list(nested_list: List) -> List:
        """Flatten nested list"""
        result = []
        for item in nested_list:
            if isinstance(item, list):
                result.extend(DataUtils.flatten_list(item))
            else:
                result.append(item)
        return result
