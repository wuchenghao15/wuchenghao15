# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""数学公式数据库服务 - 收录和管理数学公式"""
import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class MathFormulaService:
    """数学公式服务"""
    
    def __init__(self, db_path: str = 'app.db'):
        self.db_path = db_path
        self._create_tables()
    
    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def _create_tables(self):
        """创建数学公式相关表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 数学公式表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS math_formulas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                formula TEXT NOT NULL UNIQUE,
                latex TEXT,
                name TEXT,
                category TEXT,
                formula_type TEXT DEFAULT 'basic',
                description TEXT,
                variables TEXT,
                examples TEXT,
                derivation_steps TEXT,
                source TEXT,
                difficulty_level INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # 公式分类表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS formula_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                parent_id INTEGER,
                description TEXT,
                color TEXT DEFAULT '#667eea',
                created_at TEXT NOT NULL,
                FOREIGN KEY (parent_id) REFERENCES formula_categories(id)
            )
        ''')
        
        # 公式标签表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS formula_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#718096'
            )
        ''')
        
        # 公式-标签关联表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS formula_tag_mapping (
                formula_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (formula_id, tag_id),
                FOREIGN KEY (formula_id) REFERENCES math_formulas(id),
                FOREIGN KEY (tag_id) REFERENCES formula_tags(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("数学公式表创建完成")
    
    def add_formula(self, formula: str, latex: str = '', name: str = '',
                    category: str = '', formula_type: str = 'basic', description: str = '', 
                    variables: Dict = None, examples: List = None, derivation_steps: List = None,
                    source: str = '', difficulty_level: int = 1) -> int:
        """添加数学公式
        
        Args:
            formula_type: 公式类型
                - 'basic': 基础公式
                - 'induction': 诱导公式
                - 'derivation': 推导公式
        """
        now = datetime.now().isoformat()
        variables_json = json.dumps(variables) if variables else '{}'
        examples_json = json.dumps(examples) if examples else '[]'
        derivation_json = json.dumps(derivation_steps) if derivation_steps else '[]'
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO math_formulas 
                (formula, latex, name, category, formula_type, description, variables, examples, derivation_steps, source, difficulty_level, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (formula, latex, name, category, formula_type, description, variables_json, examples_json, derivation_json, source, difficulty_level, now, now))
            
            # 获取插入的ID
            cursor.execute('SELECT id FROM math_formulas WHERE formula = ?', (formula,))
            result = cursor.fetchone()
            formula_id = result[0] if result else None
            
            conn.commit()
            logger.info(f"数学公式添加成功: {name or formula}")
            return formula_id
        except Exception as e:
            logger.error(f"添加数学公式失败: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_formula(self, formula_id: int) -> Optional[Dict[str, Any]]:
        """获取单个公式"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM math_formulas WHERE id = ?', (formula_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'formula': row[1],
                'latex': row[2],
                'name': row[3],
                'category': row[4],
                'formula_type': row[5] if len(row) > 5 else 'basic',
                'description': row[6] if len(row) > 6 else '',
                'variables': json.loads(row[7]) if len(row) > 7 and row[7] else {},
                'examples': json.loads(row[8]) if len(row) > 8 and row[8] else [],
                'derivation_steps': json.loads(row[9]) if len(row) > 9 and row[9] else [],
                'source': row[10] if len(row) > 10 else '',
                'difficulty_level': row[11] if len(row) > 11 else 1,
                'created_at': row[12] if len(row) > 12 else '',
                'updated_at': row[13] if len(row) > 13 else ''
            }
        return None
    
    def search_formulas(self, keyword: str = '', category: str = '', formula_type: str = '', limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """搜索公式
        
        Args:
            keyword: 搜索关键词
            category: 分类名称
            formula_type: 公式类型 (basic/induction/derivation)
            limit: 返回数量限制
            offset: 偏移量
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM math_formulas WHERE 1=1'
        params = []
        
        if keyword:
            query += ' AND (formula LIKE ? OR name LIKE ? OR description LIKE ?)'
            params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        if formula_type:
            query += ' AND formula_type = ?'
            params.append(formula_type)
        
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            result.append({
                'id': row[0],
                'formula': row[1],
                'latex': row[2],
                'name': row[3],
                'category': row[4],
                'formula_type': row[5] if len(row) > 5 else 'basic',
                'description': row[6] if len(row) > 6 else '',
                'variables': json.loads(row[7]) if len(row) > 7 and row[7] else {},
                'examples': json.loads(row[8]) if len(row) > 8 and row[8] else [],
                'derivation_steps': json.loads(row[9]) if len(row) > 9 and row[9] else [],
                'source': row[10] if len(row) > 10 else '',
                'difficulty_level': row[11] if len(row) > 11 else 1,
                'created_at': row[12] if len(row) > 12 else '',
                'updated_at': row[13] if len(row) > 13 else ''
            })
        
        return result
    
    def update_formula(self, formula_id: int, **kwargs) -> bool:
        """更新公式"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 准备更新字段
            update_fields = []
            params = []
            
            if 'formula' in kwargs:
                update_fields.append('formula = ?')
                params.append(kwargs['formula'])
            if 'latex' in kwargs:
                update_fields.append('latex = ?')
                params.append(kwargs['latex'])
            if 'name' in kwargs:
                update_fields.append('name = ?')
                params.append(kwargs['name'])
            if 'category' in kwargs:
                update_fields.append('category = ?')
                params.append(kwargs['category'])
            if 'description' in kwargs:
                update_fields.append('description = ?')
                params.append(kwargs['description'])
            if 'variables' in kwargs:
                update_fields.append('variables = ?')
                params.append(json.dumps(kwargs['variables']))
            if 'examples' in kwargs:
                update_fields.append('examples = ?')
                params.append(json.dumps(kwargs['examples']))
            if 'source' in kwargs:
                update_fields.append('source = ?')
                params.append(kwargs['source'])
            if 'difficulty_level' in kwargs:
                update_fields.append('difficulty_level = ?')
                params.append(kwargs['difficulty_level'])
            
            update_fields.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(formula_id)
            
            if update_fields:
                query = 'UPDATE math_formulas SET ' + ', '.join(update_fields) + ' WHERE id = ?'
                cursor.execute(query, params)
                conn.commit()
                logger.info(f"数学公式更新成功: {formula_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"更新数学公式失败: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def delete_formula(self, formula_id: int) -> bool:
        """删除公式"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 先删除关联的标签映射
            cursor.execute('DELETE FROM formula_tag_mapping WHERE formula_id = ?', (formula_id,))
            # 删除公式
            cursor.execute('DELETE FROM math_formulas WHERE id = ?', (formula_id,))
            conn.commit()
            logger.info(f"数学公式删除成功: {formula_id}")
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"删除数学公式失败: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_all_formulas(self) -> List[Dict[str, Any]]:
        """获取所有公式"""
        return self.search_formulas()
    
    def get_formula_count(self, category: str = '') -> int:
        """获取公式数量"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute('SELECT COUNT(*) FROM math_formulas WHERE category = ?', (category,))
        else:
            cursor.execute('SELECT COUNT(*) FROM math_formulas')
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    
    def add_category(self, name: str, parent_id: int = None, description: str = '', color: str = '#667eea') -> int:
        """添加分类"""
        now = datetime.now().isoformat()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO formula_categories (name, parent_id, description, color, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, parent_id, description, color, now))
            
            cursor.execute('SELECT id FROM formula_categories WHERE name = ?', (name,))
            result = cursor.fetchone()
            category_id = result[0] if result else None
            
            conn.commit()
            logger.info(f"公式分类添加成功: {name}")
            return category_id
        except Exception as e:
            logger.error(f"添加公式分类失败: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """获取所有分类"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM formula_categories ORDER BY name')
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'name': row[1],
            'parent_id': row[2],
            'description': row[3],
            'color': row[4],
            'created_at': row[5]
        } for row in rows]
    
    def add_tag(self, tag: str, color: str = '#718096') -> int:
        """添加标签"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT OR IGNORE INTO formula_tags (tag, color) VALUES (?, ?)', (tag, color))
            
            cursor.execute('SELECT id FROM formula_tags WHERE tag = ?', (tag,))
            result = cursor.fetchone()
            tag_id = result[0] if result else None
            
            conn.commit()
            logger.info(f"标签添加成功: {tag}")
            return tag_id
        except Exception as e:
            logger.error(f"添加标签失败: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def add_formula_tag(self, formula_id: int, tag_id: int) -> bool:
        """为公式添加标签"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT OR IGNORE INTO formula_tag_mapping (formula_id, tag_id) VALUES (?, ?)', (formula_id, tag_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"添加公式标签失败: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def import_formulas_from_json(self, json_path: str) -> int:
        """从JSON文件导入公式"""
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"文件不存在: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            formulas = json.load(f)
        
        imported_count = 0
        for formula_data in formulas:
            try:
                self.add_formula(
                    formula=formula_data.get('formula', ''),
                    latex=formula_data.get('latex', ''),
                    name=formula_data.get('name', ''),
                    category=formula_data.get('category', ''),
                    formula_type=formula_data.get('formula_type', 'basic'),
                    description=formula_data.get('description', ''),
                    variables=formula_data.get('variables'),
                    examples=formula_data.get('examples'),
                    derivation_steps=formula_data.get('derivation_steps'),
                    source=formula_data.get('source', ''),
                    difficulty_level=formula_data.get('difficulty_level', 1)
                )
                imported_count += 1
            except Exception as e:
                logger.warning(f"导入公式失败: {formula_data.get('name', 'unknown')} - {str(e)}")
        
        logger.info(f"成功导入 {imported_count} 个数学公式")
        return imported_count

# 全局实例
formula_service = MathFormulaService()

def init_math_formulas():
    """初始化数学公式数据库"""
    logger.info("初始化数学公式数据库...")
    
    # 添加默认分类
    categories = [
        ('代数', None, '代数相关公式', '#667eea'),
        ('几何', None, '几何相关公式', '#48bb78'),
        ('微积分', None, '微积分相关公式', '#ed8936'),
        ('概率统计', None, '概率与统计相关公式', '#9f7aea'),
        ('线性代数', None, '线性代数相关公式', '#38b2ac'),
        ('三角', None, '三角函数相关公式', '#f56565'),
        ('数论', None, '数论相关公式', '#718096'),
        ('级数', None, '级数相关公式', '#4299e1')
    ]
    
    for name, parent_id, description, color in categories:
        formula_service.add_category(name, parent_id, description, color)
    
    # 添加默认标签
    tags = [
        ('基础', '#48bb78'),
        ('进阶', '#ed8936'),
        ('高级', '#f56565'),
        ('常用', '#4299e1'),
        ('重要', '#9f7aea'),
        ('推导', '#38b2ac'),
        ('证明', '#718096'),
        ('应用', '#667eea')
    ]
    
    for tag, color in tags:
        formula_service.add_tag(tag, color)
    
    logger.info("数学公式数据库初始化完成")
