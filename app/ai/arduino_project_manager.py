#!/usr/bin/env python3
import sqlite3
import os
import json
from uuid import uuid4
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

class ArduinoProjectManager:
    """Arduino项目管理器 - 管理Arduino项目、代码、文档"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """创建项目相关表（安全迁移模式）"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS arduino_projects (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'other',
                difficulty TEXT DEFAULT 'beginner',
                status TEXT DEFAULT 'draft',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                likes INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0
            )
        ''')
        
        self._add_column_if_not_exists('arduino_projects', 'category', 'TEXT DEFAULT "other"')
        self._add_column_if_not_exists('arduino_projects', 'difficulty', 'TEXT DEFAULT "beginner"')
        self._add_column_if_not_exists('arduino_projects', 'status', 'TEXT DEFAULT "draft"')
        self._add_column_if_not_exists('arduino_projects', 'likes', 'INTEGER DEFAULT 0')
        self._add_column_if_not_exists('arduino_projects', 'views', 'INTEGER DEFAULT 0')
    
    def _add_column_if_not_exists(self, table_name, column_name, column_def):
        """安全添加列（如果不存在）"""
        try:
            self.cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}')
        except sqlite3.OperationalError:
            pass
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS arduino_project_files (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                filename TEXT NOT NULL,
                content TEXT,
                file_type TEXT DEFAULT 'cpp',
                is_main INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES arduino_projects(id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS arduino_project_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                component_name TEXT,
                quantity INTEGER DEFAULT 1,
                category TEXT,
                FOREIGN KEY(project_id) REFERENCES arduino_projects(id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS arduino_project_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                tag TEXT,
                FOREIGN KEY(project_id) REFERENCES arduino_projects(id),
                UNIQUE(project_id, tag)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS arduino_project_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                project_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, project_id)
            )
        ''')
        
        self.conn.commit()
    
    def create_project(self, user_id, name, description='', category='other', difficulty='beginner'):
        """创建项目"""
        project_id = str(uuid4())
        self.cursor.execute('''
            INSERT INTO arduino_projects 
            (id, user_id, name, description, category, difficulty)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (project_id, user_id, name, description, category, difficulty))
        self.conn.commit()
        return project_id
    
    def get_project(self, project_id):
        """获取项目详情"""
        self.cursor.execute('''
            SELECT ap.*, u.username 
            FROM arduino_projects ap
            LEFT JOIN users u ON ap.user_id = u.id
            WHERE ap.id = ?
        ''', (project_id,))
        project = self.cursor.fetchone()
        if not project:
            return None
        
        project_dict = dict(project)
        
        self.cursor.execute('SELECT * FROM arduino_project_files WHERE project_id = ?', (project_id,))
        files = [dict(row) for row in self.cursor.fetchall()]
        project_dict['files'] = files
        
        self.cursor.execute('SELECT * FROM arduino_project_components WHERE project_id = ?', (project_id,))
        components = [dict(row) for row in self.cursor.fetchall()]
        project_dict['components'] = components
        
        self.cursor.execute('SELECT tag FROM arduino_project_tags WHERE project_id = ?', (project_id,))
        tags = [row['tag'] for row in self.cursor.fetchall()]
        project_dict['tags'] = tags
        
        return project_dict
    
    def update_project(self, project_id, **kwargs):
        """更新项目"""
        update_fields = []
        params = []
        
        if 'name' in kwargs:
            update_fields.append('name = ?')
            params.append(kwargs['name'])
        if 'description' in kwargs:
            update_fields.append('description = ?')
            params.append(kwargs['description'])
        if 'category' in kwargs:
            update_fields.append('category = ?')
            params.append(kwargs['category'])
        if 'difficulty' in kwargs:
            update_fields.append('difficulty = ?')
            params.append(kwargs['difficulty'])
        if 'status' in kwargs:
            update_fields.append('status = ?')
            params.append(kwargs['status'])
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        params.append(project_id)
        
        query = f'UPDATE arduino_projects SET {", ".join(update_fields)} WHERE id = ?'
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def delete_project(self, project_id):
        """删除项目"""
        self.cursor.execute('DELETE FROM arduino_project_files WHERE project_id = ?', (project_id,))
        self.cursor.execute('DELETE FROM arduino_project_components WHERE project_id = ?', (project_id,))
        self.cursor.execute('DELETE FROM arduino_project_tags WHERE project_id = ?', (project_id,))
        self.cursor.execute('DELETE FROM arduino_project_likes WHERE project_id = ?', (project_id,))
        self.cursor.execute('DELETE FROM arduino_projects WHERE id = ?', (project_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def add_file(self, project_id, filename, content, file_type='cpp', is_main=False):
        """添加项目文件"""
        file_id = str(uuid4())
        self.cursor.execute('''
            INSERT INTO arduino_project_files 
            (id, project_id, filename, content, file_type, is_main)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (file_id, project_id, filename, content, file_type, 1 if is_main else 0))
        self.conn.commit()
        return file_id
    
    def update_file(self, file_id, content=None, filename=None):
        """更新文件"""
        update_fields = []
        params = []
        
        if content is not None:
            update_fields.append('content = ?')
            params.append(content)
        if filename is not None:
            update_fields.append('filename = ?')
            params.append(filename)
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        params.append(file_id)
        
        query = f'UPDATE arduino_project_files SET {", ".join(update_fields)} WHERE id = ?'
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def delete_file(self, file_id):
        """删除文件"""
        self.cursor.execute('DELETE FROM arduino_project_files WHERE id = ?', (file_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def add_component(self, project_id, component_name, quantity=1, category=''):
        """添加组件"""
        self.cursor.execute('''
            INSERT INTO arduino_project_components 
            (project_id, component_name, quantity, category)
            VALUES (?, ?, ?, ?)
        ''', (project_id, component_name, quantity, category))
        self.conn.commit()
    
    def add_tag(self, project_id, tag):
        """添加标签"""
        try:
            self.cursor.execute('''
                INSERT INTO arduino_project_tags (project_id, tag)
                VALUES (?, ?)
            ''', (project_id, tag))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def like_project(self, user_id, project_id):
        """点赞项目"""
        try:
            self.cursor.execute('''
                INSERT INTO arduino_project_likes (user_id, project_id)
                VALUES (?, ?)
            ''', (user_id, project_id))
            
            self.cursor.execute('''
                UPDATE arduino_projects SET likes = likes + 1 WHERE id = ?
            ''', (project_id,))
            
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_projects(self, page=1, page_size=10, category=None, difficulty=None, user_id=None):
        """获取项目列表"""
        offset = (page - 1) * page_size
        query = '''
            SELECT ap.*, u.username 
            FROM arduino_projects ap
            LEFT JOIN users u ON ap.user_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if category:
            query += ' AND ap.category = ?'
            params.append(category)
        if difficulty:
            query += ' AND ap.difficulty = ?'
            params.append(difficulty)
        if user_id:
            query += ' AND ap.user_id = ?'
            params.append(user_id)
        
        query += ' ORDER BY ap.created_at DESC LIMIT ? OFFSET ?'
        params.extend([page_size, offset])
        
        self.cursor.execute(query, params)
        projects = [dict(row) for row in self.cursor.fetchall()]
        
        return projects
    
    def get_project_categories(self):
        """获取项目分类"""
        self.cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM arduino_projects 
            GROUP BY category
        ''')
        return [dict(row) for row in self.cursor.fetchall()]
    
    def search_projects(self, keyword, page=1, page_size=10):
        """搜索项目"""
        offset = (page - 1) * page_size
        self.cursor.execute('''
            SELECT ap.*, u.username 
            FROM arduino_projects ap
            LEFT JOIN users u ON ap.user_id = u.id
            WHERE ap.name LIKE ? OR ap.description LIKE ?
            ORDER BY ap.created_at DESC LIMIT ? OFFSET ?
        ''', (f'%{keyword}%', f'%{keyword}%', page_size, offset))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == '__main__':
    manager = ArduinoProjectManager()
    
    logger.info("=== Arduino项目管理器 ===")
    
    project_id = manager.create_project(
        user_id=1,
        name='智能温湿度监控系统',
        description='使用DHT11传感器监控环境温湿度，通过LCD显示',
        category='sensors',
        difficulty='intermediate'
    )
    logger.info(f"\n创建项目成功: {project_id}")
    
    manager.add_file(project_id, 'main.ino', '''#include <DHT.h>
#include <LiquidCrystal.h>

#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

void setup() {
  Serial.begin(9600);
  dht.begin();
  lcd.begin(16, 2);
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  
  lcd.setCursor(0, 0);
  lcd.logger.info("Temp: ");
  lcd.logger.info(t);
  lcd.logger.info("C");
  
  lcd.setCursor(0, 1);
  lcd.logger.info("Hum: ");
  lcd.logger.info(h);
  lcd.logger.info("%");
  
  delay(2000);
}
''', 'cpp', is_main=True)
    
    manager.add_component(project_id, 'DHT11温湿度传感器', 1, '传感器')
    manager.add_component(project_id, 'LCD 1602显示屏', 1, '显示')
    manager.add_component(project_id, 'Arduino Uno', 1, '主控')
    
    manager.add_tag(project_id, '传感器')
    manager.add_tag(project_id, '物联网')
    
    project = manager.get_project(project_id)
    logger.info(f"\n项目名称: {project['name']}")
    logger.info(f"描述: {project['description']}")
    logger.info(f"文件数: {len(project['files'])}")
    logger.info(f"组件数: {len(project['components'])}")
    logger.info(f"标签: {project['tags']}")
    
    projects = manager.get_projects(page=1, page_size=5)
    logger.info(f"\n项目总数: {len(projects)}")
    
    categories = manager.get_project_categories()
    logger.info(f"\n项目分类:")
    for cat in categories:
        logger.info(f"  {cat['category']}: {cat['count']}个项目")
    
    manager.like_project(2, project_id)
    project = manager.get_project(project_id)
    logger.info(f"\n点赞后: {project['likes']}赞")
    
    manager.close()