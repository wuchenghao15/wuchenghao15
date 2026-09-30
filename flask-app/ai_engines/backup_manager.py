"""backup_manager with file type auto-archiving."""
import os
from datetime import datetime
import shutil

class BackupManager:
    def backup(self, file_path, *a, **kw):
        file_type = self._get_file_type(file_path)
        archive_dir = os.path.join(os.path.dirname(file_path), file_type)
        os.makedirs(archive_dir, exist_ok=True)
        
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        new_file_name = f"{base_name}_{timestamp}{ext}"
        new_file_path = os.path.join(archive_dir, new_file_name)
        
        shutil.copy2(file_path, new_file_path)
        return True

    def _get_file_type(self, file_path):
        _, ext = os.path.splitext(file_path)
        if ext in ['.log']:
            return 'logs'
        elif ext in ['.bak', '.zip']:
            return 'backups'
        elif ext in ['.py', '.sh']:
            return 'scripts'
        elif ext in ['.pdf', '.doc', '.docx']:
            return 'docs'
        else:
            return 'other'

backup_manager = BackupManager()
