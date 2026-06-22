"""
数据库架构管理类
"""

import sqlite3
import time
from typing import Dict, List, Optional, Any


class DatabaseSchema:
    """数据库架构管理器"""
    
    def __init__(self):
        self.tables: Dict[str, Dict] = {}
        self.indexes: Dict[str, List[str]] = {}
    
    def add_table(self, table_name: str, config: Dict):
        """添加表定义"""
        self.tables[table_name] = config
        if 'indexes' in config:
            self.indexes[table_name] = config['indexes']
    
    def generate_sql(self) -> str:
        """生成创建所有表的SQL"""
        sql_statements = []
        
        for table_name, config in self.tables.items():
            fields = config.get('fields', {})
            indexes = config.get('indexes', [])
            
            # 生成CREATE TABLE语句
            field_defs = []
            for field_name, field_config in fields.items():
                field_def = f"    {field_name} {field_config['type']}"
                
                if field_config.get('primary'):
                    field_def += " PRIMARY KEY"
                if field_config.get('autoincrement'):
                    field_def += " AUTOINCREMENT"
                if field_config.get('unique'):
                    field_def += " UNIQUE"
                if not field_config.get('primary') and field_config.get('not_null'):
                    field_def += " NOT NULL"
                if 'default' in field_config:
                    default = field_config['default']
                    if isinstance(default, str):
                        field_def += f" DEFAULT '{default}'"
                    else:
                        field_def += f" DEFAULT {default}"
                
                field_defs.append(field_def)
            
            sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
            sql += ",\n".join(field_defs)
            sql += "\n);"
            sql_statements.append(sql)
            
            # 生成CREATE INDEX语句
            for index_name in indexes:
                sql_statements.append(
                    f"CREATE INDEX IF NOT EXISTS idx_{table_name}_{index_name} "
                    f"ON {table_name}({index_name});"
                )
        
        return "\n\n".join(sql_statements)
    
    def get_table_info(self, table_name: str) -> Optional[Dict]:
        """获取表信息"""
        return self.tables.get(table_name)
    
    def list_tables(self) -> List[str]:
        """列出所有表"""
        return list(self.tables.keys())
    
    def get_table_count(self) -> int:
        """获取表数量"""
        return len(self.tables)


class EnhancedDatabaseManager:
    """增强版数据库管理器 - 支持分表"""
    
    def __init__(self, db_path: str = "data/mtscos.db", schema: DatabaseSchema = None):
        self.db_path = db_path
        self.schema = schema
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        if schema:
            self.init_schema()
    
    def init_schema(self):
        """初始化数据库架构"""
        sql = self.schema.generate_sql()
        self.conn.executescript(sql)
        self.conn.commit()
        print(f"✅ 数据库架构初始化完成，共 {self.schema.get_table_count()} 个表")
    
    def create_table(self, table_name: str) -> bool:
        """创建单个表"""
        if not self.schema:
            return False
        
        config = self.schema.get_table_info(table_name)
        if not config:
            return False
        
        fields = config.get('fields', {})
        field_defs = []
        
        for field_name, field_config in fields.items():
            field_def = f"    {field_name} {field_config['type']}"
            if field_config.get('primary'):
                field_def += " PRIMARY KEY"
            if field_config.get('autoincrement'):
                field_def += " AUTOINCREMENT"
            if field_config.get('unique'):
                field_def += " UNIQUE"
            if not field_config.get('primary') and field_config.get('not_null'):
                field_def += " NOT NULL"
            if 'default' in field_config:
                default = field_config['default']
                if isinstance(default, str):
                    field_def += f" DEFAULT '{default}'"
                else:
                    field_def += f" DEFAULT {default}"
            field_defs.append(field_def)
        
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
        sql += ",\n".join(field_defs)
        sql += "\n);"
        
        try:
            self.conn.executescript(sql)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            return False
    
    def add(self, table: str, data: Dict[str, Any]) -> int:
        """添加数据"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        cursor = self.conn.execute(sql, list(data.values()))
        self.conn.commit()
        return cursor.lastrowid
    
    def get(self, table: str, id: int) -> Optional[Dict]:
        """获取单条数据"""
        row = self.conn.execute(f"SELECT * FROM {table} WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None
    
    def get_by(self, table: str, field: str, value: Any) -> Optional[Dict]:
        """按字段获取数据"""
        row = self.conn.execute(f"SELECT * FROM {table} WHERE {field} = ?", (value,)).fetchone()
        return dict(row) if row else None
    
    def get_all(self, table: str, filters: Dict = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """获取所有数据"""
        query = f"SELECT * FROM {table}"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += f" LIMIT {limit} OFFSET {offset}"
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    def update(self, table: str, id: int, data: Dict[str, Any]) -> bool:
        """更新数据"""
        fields = ', '.join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {fields} WHERE id = ?"
        
        self.conn.execute(sql, list(data.values()) + [id])
        self.conn.commit()
        return self.conn.total_changes > 0
    
    def delete(self, table: str, id: int) -> bool:
        """删除数据"""
        self.conn.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
        self.conn.commit()
        return self.conn.total_changes > 0
    
    def count(self, table: str, filters: Dict = None) -> int:
        """统计数据条数"""
        query = f"SELECT COUNT(*) FROM {table}"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        return self.conn.execute(query, params).fetchone()[0]
    
    def query(self, sql: str, params: List = None) -> List[Dict]:
        """执行自定义查询"""
        if params:
            rows = self.conn.execute(sql, params).fetchall()
        else:
            rows = self.conn.execute(sql).fetchall()
        return [dict(row) for row in rows]
    
    def execute(self, sql: str, params: List = None):
        """执行自定义SQL"""
        if params:
            self.conn.execute(sql, params)
        else:
            self.conn.execute(sql)
        self.conn.commit()
    
    def get_stats(self) -> Dict:
        """获取数据库统计"""
        stats = {}
        tables = self.schema.list_tables() if self.schema else []
        
        for table in tables:
            try:
                count = self.count(table)
                stats[table] = count
            except:
                stats[table] = 0
        
        return stats
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()


# 导出默认实例
default_schema = DatabaseSchema()
