# -*- coding: utf-8 -*-
"""
系统增强服务
包含文件上传下载、搜索功能、数据导出导入等通用功能
"""

import logging
import sqlite3
import os
import json
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class FileStorageService:
    """文件存储服务"""

    _instance = None

    def __new__(cls, db_path: str = None, upload_dir: str = None):
        if not cls._instance:
            cls._instance = super(FileStorageService, cls).__new__(cls)
            cls._instance._initialize(db_path, upload_dir)
        return cls._instance

    def _initialize(self, db_path: str = None, upload_dir: str = None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'app.db'
            )

        if upload_dir:
            self.upload_dir = upload_dir
        else:
            self.upload_dir = os.path.join(
                os.path.dirname(__file__), '..', '..', 'uploads'
            )

        os.makedirs(self.upload_dir, exist_ok=True)
        self._init_tables()
        logger.info("文件存储服务初始化完成")

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_name TEXT,
                file_path TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                file_type TEXT,
                mime_type TEXT,
                uploader_id INTEGER,
                uploader_name TEXT,
                category TEXT,
                description TEXT,
                download_count INTEGER DEFAULT 0,
                is_public INTEGER DEFAULT 0,
                checksum TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_uploader ON files(uploader_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_category ON files(category)')

            conn.commit()

    def upload_file(self, file_data, filename: str, uploader_id: int = None,
                    uploader_name: str = None, category: str = 'general',
                    description: str = None, is_public: int = 0) -> Dict:
        """上传文件"""
        try:
            file_id = str(uuid.uuid4())[:8]
            ext = os.path.splitext(filename)[1]
            stored_name = f"{file_id}{ext}"
            file_path = os.path.join(self.upload_dir, stored_name)

            if isinstance(file_data, bytes):
                with open(file_path, 'wb') as f:
                    f.write(file_data)
            elif hasattr(file_data, 'save'):
                file_data.save(file_path)
            elif isinstance(file_data, str) and os.path.exists(file_data):
                import shutil
                shutil.copy(file_data, file_path)
            else:
                return {'success': False, 'error': '不支持的文件数据类型'}

            file_size = os.path.getsize(file_path)

            checksum = self._calculate_checksum(file_path)

            file_type = self._detect_file_type(filename)
            mime_type = self._get_mime_type(filename)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT INTO files 
                       (filename, original_name, file_path, file_size, file_type, 
                        mime_type, uploader_id, uploader_name, category, 
                        description, is_public, checksum)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (stored_name, filename, file_path, file_size, file_type,
                     mime_type, uploader_id, uploader_name, category,
                     description, is_public, checksum)
                )
                conn.commit()
                file_id = cursor.lastrowid

            logger.info(f"文件上传成功: {filename}, 大小: {file_size}字节")

            return {
                'success': True,
                'file_id': file_id,
                'filename': stored_name,
                'original_name': filename,
                'file_size': file_size,
                'file_type': file_type,
                'checksum': checksum
            }
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件MD5校验和"""
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()

    def _detect_file_type(self, filename: str) -> str:
        """检测文件类型"""
        ext = os.path.splitext(filename)[1].lower()
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
        doc_exts = ['.doc', '.docx', '.pdf', '.txt', '.rtf', '.odt']
        excel_exts = ['.xls', '.xlsx', '.csv']
        ppt_exts = ['.ppt', '.pptx']
        video_exts = ['.mp4', '.avi', '.mov', '.wmv', '.flv']
        audio_exts = ['.mp3', '.wav', '.ogg', '.flac']
        code_exts = ['.py', '.js', '.java', '.cpp', '.c', '.h', '.html', '.css', '.json']
        archive_exts = ['.zip', '.rar', '.7z', '.tar', '.gz']

        if ext in image_exts: return 'image'
        if ext in doc_exts: return 'document'
        if ext in excel_exts: return 'spreadsheet'
        if ext in ppt_exts: return 'presentation'
        if ext in video_exts: return 'video'
        if ext in audio_exts: return 'audio'
        if ext in code_exts: return 'code'
        if ext in archive_exts: return 'archive'
        return 'other'

    def _get_mime_type(self, filename: str) -> str:
        """获取MIME类型"""
        ext = os.path.splitext(filename)[1].lower()
        mime_map = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.gif': 'image/gif',
            '.pdf': 'application/pdf', '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.txt': 'text/plain', '.csv': 'text/csv',
            '.zip': 'application/zip', '.json': 'application/json',
            '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript'
        }
        return mime_map.get(ext, 'application/octet-stream')

    def get_file(self, file_id: int) -> Optional[Dict]:
        """获取文件信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_file_by_path(self, filename: str) -> Optional[Dict]:
        """通过文件名获取文件"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM files WHERE filename = ?', (filename,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_files(self, uploader_id: int, category: str = None, limit: int = 50) -> List[Dict]:
        """获取用户上传的文件"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute(
                    '''SELECT * FROM files WHERE uploader_id = ? AND category = ?
                       ORDER BY created_at DESC LIMIT ?''',
                    (uploader_id, category, limit)
                )
            else:
                cursor.execute(
                    '''SELECT * FROM files WHERE uploader_id = ?
                       ORDER BY created_at DESC LIMIT ?''',
                    (uploader_id, limit)
                )
            return [dict(row) for row in cursor.fetchall()]

    def delete_file(self, file_id: int, uploader_id: int = None) -> bool:
        """删除文件"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM files WHERE id = ?'
            params = [file_id]
            if uploader_id:
                query += ' AND uploader_id = ?'
                params.append(uploader_id)

            cursor.execute(query, params)
            file_info = cursor.fetchone()

            if not file_info:
                return False

            try:
                if os.path.exists(file_info['file_path']):
                    os.remove(file_info['file_path'])
            except Exception as e:
                logger.warning(f"删除物理文件失败: {e}")

            cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
            conn.commit()

            logger.info(f"文件删除: {file_info['original_name']}")
            return True

    def increment_download(self, file_id: int):
        """增加下载次数"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE files SET download_count = download_count + 1 WHERE id = ?',
                (file_id,)
            )
            conn.commit()

    def get_stats(self, uploader_id: int = None) -> Dict:
        """获取文件统计"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if uploader_id:
                cursor.execute(
                    'SELECT COUNT(*) as count, COALESCE(SUM(file_size), 0) as total_size FROM files WHERE uploader_id = ?',
                    (uploader_id,)
                )
            else:
                cursor.execute(
                    'SELECT COUNT(*) as count, COALESCE(SUM(file_size), 0) as total_size FROM files'
                )

            row = cursor.fetchone()
            return {
                'file_count': row['count'],
                'total_size': row['total_size'],
                'total_size_mb': round(row['total_size'] / 1024 / 1024, 2)
            }


class SearchService:
    """搜索服务"""

    _instance = None

    def __new__(cls, db_path: str = None):
        if not cls._instance:
            cls._instance = super(SearchService, cls).__new__(cls)
            cls._instance._initialize(db_path)
        return cls._instance

    def _initialize(self, db_path: str = None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'app.db'
            )
        logger.info("搜索服务初始化完成")

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def search(self, query: str, search_type: str = 'all', limit: int = 20) -> Dict:
        """全局搜索"""
        results = {
            'query': query,
            'total': 0,
            'results': []
        }

        if not query or len(query.strip()) < 1:
            return results

        search_query = f"%{query.strip()}%"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if search_type in ['all', 'exams']:
                try:
                    cursor.execute(
                        '''SELECT id, title, description, 'exam' as type, 
                           created_at FROM exams 
                           WHERE title LIKE ? OR description LIKE ?
                           ORDER BY created_at DESC LIMIT ?''',
                        (search_query, search_query, limit)
                    )
                    for row in cursor.fetchall():
                        results['results'].append({
                            'id': row['id'],
                            'title': row['title'],
                            'description': row['description'] or '',
                            'type': 'exam',
                            'type_label': '考试',
                            'url': f'/exam_page/{row["id"]}',
                            'created_at': row['created_at']
                        })
                except Exception as e:
                    logger.debug(f"搜索考试失败: {e}")

            if search_type in ['all', 'questions']:
                try:
                    cursor.execute(
                        '''SELECT id, question_text, category, 'question' as type,
                           created_at FROM questions
                           WHERE question_text LIKE ?
                           ORDER BY created_at DESC LIMIT ?''',
                        (search_query, limit)
                    )
                    for row in cursor.fetchall():
                        results['results'].append({
                            'id': row['id'],
                            'title': row['question_text'][:50] + '...',
                            'description': row.get('category', ''),
                            'type': 'question',
                            'type_label': '题目',
                            'url': f'#/question/{row["id"]}',
                            'created_at': row['created_at']
                        })
                except Exception as e:
                    logger.debug(f"搜索题目失败: {e}")

            if search_type in ['all', 'users']:
                try:
                    cursor.execute(
                        '''SELECT id, username, 'user' as type
                           FROM users WHERE username LIKE ?
                           ORDER BY username LIMIT ?''',
                        (search_query, limit)
                    )
                    for row in cursor.fetchall():
                        results['results'].append({
                            'id': row['id'],
                            'title': row['username'],
                            'description': '用户',
                            'type': 'user',
                            'type_label': '用户',
                            'url': f'#/user/{row["id"]}',
                            'created_at': ''
                        })
                except Exception as e:
                    logger.debug(f"搜索用户失败: {e}")

        results['total'] = len(results['results'])
        results['results'] = results['results'][:limit]

        return results

    def search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """搜索建议"""
        results = set()

        if not query or len(query.strip()) < 1:
            return []

        search_query = f"%{query.strip()}%"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    'SELECT title FROM exams WHERE title LIKE ? LIMIT ?',
                    (search_query, limit)
                )
                for row in cursor.fetchall():
                    results.add(row['title'])
            except Exception:
                pass

        return list(results)[:limit]


class DataExportService:
    """数据导出服务"""

    _instance = None

    def __new__(cls, db_path: str = None):
        if not cls._instance:
            cls._instance = super(DataExportService, cls).__new__(cls)
            cls._instance._initialize(db_path)
        return cls._instance

    def _initialize(self, db_path: str = None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'app.db'
            )
        logger.info("数据导出服务初始化完成")

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def export_to_csv(self, data: List[Dict], filename: str) -> Dict:
        """导出数据为CSV"""
        try:
            import csv
            import io

            output = io.StringIO()

            if not data:
                return {'success': False, 'error': '没有数据可导出'}

            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

            return {
                'success': True,
                'content': output.getvalue(),
                'filename': filename,
                'mime_type': 'text/csv',
                'row_count': len(data)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def export_to_json(self, data: List[Dict], filename: str) -> Dict:
        """导出数据为JSON"""
        try:
            content = json.dumps(data, ensure_ascii=False, indent=2)
            return {
                'success': True,
                'content': content,
                'filename': filename,
                'mime_type': 'application/json',
                'row_count': len(data)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def export_user_data(self, user_id: int, format: str = 'json') -> Dict:
        """导出用户数据"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if not user:
                return {'success': False, 'error': '用户不存在'}

            data = {
                'export_time': datetime.now().isoformat(),
                'user': dict(user),
                'activity_logs': []
            }

            try:
                cursor.execute(
                    'SELECT * FROM user_activity_logs WHERE user_id = ? ORDER BY created_at',
                    (user_id,)
                )
                data['activity_logs'] = [dict(row) for row in cursor.fetchall()]
            except Exception:
                pass

        if format == 'csv':
            return self.export_to_csv([data['user']], 'user_profile.csv')
        else:
            return self.export_to_json([data], f'user_{user_id}_data.json')

    def export_exam_results(self, exam_id: int, format: str = 'json') -> Dict:
        """导出考试结果"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    '''SELECT er.*, u.username 
                       FROM exam_results er 
                       LEFT JOIN users u ON er.user_id = u.id
                       WHERE er.exam_id = ?
                       ORDER BY er.score DESC''',
                    (exam_id,)
                )
                results = [dict(row) for row in cursor.fetchall()]

                if not results:
                    return {'success': False, 'error': '没有考试结果数据'}

                if format == 'csv':
                    return self.export_to_csv(results, f'exam_{exam_id}_results.csv')
                else:
                    return self.export_to_json(results, f'exam_{exam_id}_results.json')
            except Exception as e:
                return {'success': False, 'error': str(e)}
