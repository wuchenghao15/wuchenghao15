# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库升级和双备份管理系统
支持题库、脑库、特征库等数据库的升级和备份
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

class DatabaseUpgradeManager:
    """数据库升级和备份管理器"""
    
    def __init__(self):
        self.base_dir = Path("/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project")
        self.backup_dir = self.base_dir / "backups"
        self.db_dir = self.base_dir / "Database"
        self.backup_dir.mkdir(exist_ok=True)
        self.db_dir.mkdir(exist_ok=True)
        
        self.databases = {
            "app": {"path": self.base_dir / "app.db", "description": "主应用数据库"},
            "ai_brain": {"path": self.db_dir / "ai_brain.db", "description": "AI脑库"},
            "engineer_ai": {"path": self.base_dir / "engineer_ai.db", "description": "工程师AI数据库"},
            "mtscos": {"path": self.base_dir / "mtscos.db", "description": "MTSCOS主数据库"},
            "primary": {"path": self.base_dir / "primary.db", "description": "主数据库"},
            "shadow_app": {"path": self.base_dir / "shadow_app.db", "description": "影子应用数据库"}
        }
        
        self.features = {
            "question_bank": {"table": "questions", "description": "题库"},
            "knowledge_base": {"tables": ["ai_brain_knowledge", "ai_brain_knowledge_master"], "description": "知识脑库"},
            "feature_store": {"table": "ai_brain_features", "description": "特征库"},
            "capabilities": {"table": "ai_capabilities", "description": "AI能力库"},
            "models": {"table": "ai_models", "description": "模型库"},
            "performance": {"table": "ai_performance_metrics", "description": "性能指标库"}
        }
        
    def get_timestamp(self) -> str:
        """获取时间戳"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def backup_database(self, db_name: str, backup_type: str = "full") -> str:
        """备份单个数据库"""
        if db_name not in self.databases:
            raise ValueError(f"未知数据库: {db_name}")
        
        db_info = self.databases[db_name]
        db_path = db_info["path"]
        
        if not db_path.exists():
            print(f"⚠ 数据库不存在: {db_path}")
            return ""
        
        timestamp = self.get_timestamp()
        backup_filename = f"{db_name}_{timestamp}_{backup_type}.db"
        backup_path = self.backup_dir / backup_filename
        
        try:
            shutil.copy2(db_path, backup_path)
            print(f"✓ 已备份 {db_name} -> {backup_path}")
            return str(backup_path)
        except Exception as e:
            print(f"✗ 备份失败 {db_name}: {e}")
            return ""
    
    def backup_all_databases(self) -> List[str]:
        """备份所有数据库"""
        print("\n == 开始备份所有数据库 ===")
        backups = []
        for db_name in self.databases:
            backup_path = self.backup_database(db_name)
            if backup_path:
                backups.append(backup_path)
        
        # 创建双备份 - 额外备份到另一个位置
        print("\n == 创建双备份 ===")
        dual_backup_dir = self.base_dir / "Database" / "backups" / "dual_backup"
        dual_backup_dir.mkdir(exist_ok=True)
        
        for backup in backups:
            backup_file = Path(backup)
            dual_backup_path = dual_backup_dir / backup_file.name
            shutil.copy2(backup, dual_backup_path)
            print(f"✓ 双备份: {backup_file.name} -> dual_backup/")
        
        return backups
    
    def upgrade_ai_brain_database(self) -> bool:
        """升级AI脑库数据库"""
        print("\n == 升级AI脑库数据库 ===")
        db_path = self.databases["ai_brain"]["path"]
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 添加新表：特征库
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_feature_store (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feature_name TEXT NOT NULL UNIQUE,
                    feature_vector TEXT,
                    feature_type TEXT,
                    description TEXT,
                    category TEXT,
                    relevance_score REAL DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    last_used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 添加新表：技能库
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL UNIQUE,
                    skill_level TEXT DEFAULT 'basic',
                    description TEXT,
                    proficiency REAL DEFAULT 0.0,
                    last_practiced_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 添加新表：知识库索引
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_knowledge_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_id INTEGER,
                    keywords TEXT,
                    embedding_vector TEXT,
                    category TEXT,
                    FOREIGN KEY (knowledge_id) REFERENCES ai_brain_knowledge(id)
                )
            """)
            
            # 为现有表添加索引
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_brain_features_type ON ai_brain_features(feature_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_technologies_category ON ai_technologies(category)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_feature_store_category ON ai_feature_store(category)")
            except Exception as e:
                print(f"索引已存在: {e}")
            
            conn.commit()
            conn.close()
            print("✓ AI脑库升级完成")
            return True
            
        except Exception as e:
            print(f"✗ AI脑库升级失败: {e}")
            return False
    
    def upgrade_question_bank(self) -> bool:
        """升级题库数据库"""
        print("\n == 升级题库数据库 ===")
        db_path = self.databases["app"]["path"]
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 升级questions表
            try:
                cursor.execute("ALTER TABLE questions ADD COLUMN difficulty_level INTEGER DEFAULT 1")
            except Exception:
                pass  # 列已存在
            
            try:
                cursor.execute("ALTER TABLE questions ADD COLUMN question_type TEXT DEFAULT 'single_choice'")
            except Exception:
                pass
            
            try:
                cursor.execute("ALTER TABLE questions ADD COLUMN tags TEXT")
            except Exception:
                pass
            
            try:
                cursor.execute("ALTER TABLE questions ADD COLUMN usage_count INTEGER DEFAULT 0")
            except Exception:
                pass
            
            try:
                cursor.execute("ALTER TABLE questions ADD COLUMN last_used_at TIMESTAMP")
            except Exception:
                pass
            
            # 创建题库统计视图
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS v_question_stats AS
                SELECT 
                    q.category_id,
                    c.name as category_name,
                    COUNT(q.id) as total_questions,
                    AVG(q.difficulty_level) as avg_difficulty
                FROM questions q
                LEFT JOIN question_categories c ON q.category_id = c.id
                GROUP BY q.category_id
            """)
            
            # 创建索引
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty_level)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(question_type)")
            except Exception as e:
                print(f"索引已存在: {e}")
            
            conn.commit()
            conn.close()
            print("✓ 题库升级完成")
            return True
            
        except Exception as e:
            print(f"✗ 题库升级失败: {e}")
            return False
    
    def upgrade_knowledge_base(self) -> bool:
        """升级知识库"""
        print("\n == 升级知识库 ===")
        db_path = self.databases["app"]["path"]
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 升级ai_brain_knowledge表
            try:
                cursor.execute("ALTER TABLE ai_brain_knowledge ADD COLUMN embedding TEXT")
            except Exception:
                pass
            
            try:
                cursor.execute("ALTER TABLE ai_brain_knowledge ADD COLUMN confidence REAL DEFAULT 0.8")
            except Exception:
                pass
            
            try:
                cursor.execute("ALTER TABLE ai_brain_knowledge ADD COLUMN source_type TEXT")
            except Exception:
                pass
            
            # 创建知识库更新记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_knowledge_updates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_id INTEGER,
                    update_type TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    updated_by TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (knowledge_id) REFERENCES ai_brain_knowledge(id)
                )
            """)
            
            conn.commit()
            conn.close()
            print("✓ 知识库升级完成")
            return True
            
        except Exception as e:
            print(f"✗ 知识库升级失败: {e}")
            return False
    
    def upgrade_capabilities_database(self) -> bool:
        """升级能力库"""
        print("\n == 升级能力库 ===")
        db_path = self.databases["app"]["path"]
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建能力详情表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_capability_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    capability_id INTEGER,
                    detail_key TEXT,
                    detail_value TEXT,
                    FOREIGN KEY (capability_id) REFERENCES ai_capabilities(id)
                )
            """)
            
            # 创建能力版本表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_capability_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    capability_id INTEGER,
                    version TEXT,
                    release_notes TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    released_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (capability_id) REFERENCES ai_capabilities(id)
                )
            """)
            
            conn.commit()
            conn.close()
            print("✓ 能力库升级完成")
            return True
            
        except Exception as e:
            print(f"✗ 能力库升级失败: {e}")
            return False
    
    def upgrade_model_performance(self) -> bool:
        """升级模型性能数据库"""
        print("\n == 升级模型性能数据库 ===")
        db_path = self.databases["app"]["path"]
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建性能趋势表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_model_performance_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id INTEGER,
                    metric_type TEXT,
                    metric_value REAL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (model_id) REFERENCES ai_models(id)
                )
            """)
            
            # 创建模型评估表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_model_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id INTEGER,
                    evaluation_type TEXT,
                    score REAL,
                    feedback TEXT,
                    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (model_id) REFERENCES ai_models(id)
                )
            """)
            
            conn.commit()
            conn.close()
            print("✓ 模型性能库升级完成")
            return True
            
        except Exception as e:
            print(f"✗ 模型性能库升级失败: {e}")
            return False
    
    def upgrade_all_databases(self) -> Dict[str, bool]:
        """升级所有数据库"""
        print("=" * 70)
        print("开始升级所有数据库")
        print("=" * 70)
        
        results = {}
        
        results["ai_brain"] = self.upgrade_ai_brain_database()
        results["question_bank"] = self.upgrade_question_bank()
        results["knowledge_base"] = self.upgrade_knowledge_base()
        results["capabilities"] = self.upgrade_capabilities_database()
        results["model_performance"] = self.upgrade_model_performance()
        
        return results
    
    def verify_databases(self) -> Dict[str, Dict[str, Any]]:
        """验证数据库完整性"""
        print("\n == 验证数据库完整性 ===")
        results = {}
        
        for db_name, db_info in self.databases.items():
            db_path = db_info["path"]
            if not db_path.exists():
                results[db_name] = {"status": "missing", "tables": []}
                print(f"⚠ {db_name}: 数据库文件不存在")
                continue
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                results[db_name] = {
                    "status": "ok",
                    "tables": tables,
                    "table_count": len(tables)
                }
                print(f"✓ {db_name}: {len(tables)} 个表")
            except Exception as e:
                results[db_name] = {"status": "error", "error": str(e)}
                print(f"✗ {db_name}: {e}")
        
        return results
    
    def run_full_upgrade(self) -> Dict[str, Any]:
        """运行完整的数据库升级流程"""
        print("=" * 70)
        print("MTSCOS AI 数据库升级和双备份系统")
        print("=" * 70)
        
        # 1. 先进行双备份
        print("\n[步骤1] 创建双备份")
        backups = self.backup_all_databases()
        
        # 2. 验证现有数据库
        print("\n[步骤2] 验证现有数据库")
        verification = self.verify_databases()
        
        # 3. 升级数据库
        print("\n[步骤3] 升级数据库")
        upgrades = self.upgrade_all_databases()
        
        # 4. 再次备份（升级后）
        print("\n[步骤4] 升级后再次备份")
        post_upgrade_backups = self.backup_all_databases()
        
        # 5. 验证升级结果
        print("\n[步骤5] 验证升级结果")
        final_verification = self.verify_databases()
        
        # 输出总结
        print("\n" + "=" * 70)
        print("升级完成总结")
        print("=" * 70)
        
        print("\n备份统计:")
        print(f"  升级前备份: {len(backups)} 个文件")
        print(f"  升级后备份: {len(post_upgrade_backups)} 个文件")
        
        print("\n升级结果:")
        for db_name, success in upgrades.items():
            status = "✓ 成功" if success else "✗ 失败"
            print(f"  {db_name}: {status}")
        
        print("\n数据库状态:")
        for db_name, info in final_verification.items():
            print(f"  {db_name}: {info['status']} ({info.get('table_count', 0)} 个表)")
        
        print("\n" + "=" * 70)
        
        return {
            "backups": {
                "pre_upgrade": backups,
                "post_upgrade": post_upgrade_backups
            },
            "verification": final_verification,
            "upgrades": upgrades,
            "timestamp": self.get_timestamp()
        }

def main():
    """主入口"""
    manager = DatabaseUpgradeManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "backup":
            manager.backup_all_databases()
        elif command == "upgrade":
            manager.upgrade_all_databases()
        elif command == "verify":
            manager.verify_databases()
        elif command == "full":
            manager.run_full_upgrade()
        else:
            print(f"未知命令: {command}")
            print("可用命令: backup, upgrade, verify, full")
    else:
        # 默认执行完整升级流程
        manager.run_full_upgrade()

if __name__ == "__main__":
    main()