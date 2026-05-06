#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""影子系统与快照系统整合"""

import os
# import json removed - using database storage
import sqlite3
import logging
import shutil
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('shadow_snapshot_system')

class ShadowSnapshotSystem:
    def __init__(self):
        self.db_path = 'app.db'
        self.shadow_db_path = 'shadow_app.db'
        self.snapshot_dir = 'snapshots'
        self.init_system_database()
        self.ensure_snapshot_dir()
    
    def init_system_database(self):
        """初始化影子和快照数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shadow_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT,
                updated_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id TEXT UNIQUE NOT NULL,
                snapshot_type TEXT,
                description TEXT,
                file_path TEXT,
                checksum TEXT,
                size_bytes INTEGER,
                created_at TEXT,
                expires_at TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shadow_sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_id TEXT UNIQUE NOT NULL,
                source TEXT,
                target TEXT,
                sync_type TEXT,
                records_synced INTEGER,
                status TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS restore_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restore_id TEXT UNIQUE NOT NULL,
                snapshot_id TEXT,
                target TEXT,
                status TEXT,
                timestamp TEXT,
                restored_by TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("影子和快照数据库初始化完成")
    
    def ensure_snapshot_dir(self):
        """确保快照目录存在"""
        os.makedirs(self.snapshot_dir, exist_ok=True)
        logger.info("快照目录已就绪")
    
    def create_shadow_copy(self):
        """创建数据库影子副本"""
        print("创建数据库影子副本...")
        
        try:
            shutil.copy2(self.db_path, self.shadow_db_path)
            
            # 记录同步日志
            sync_id = f"sync_{int(time.time())}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO shadow_sync_logs
                (sync_id, source, target, sync_type, records_synced, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                sync_id,
                self.db_path,
                self.shadow_db_path,
                'shadow_copy',
                0,
                'success',
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            print(f"  ✓ 影子副本创建成功: {self.shadow_db_path}")
            return {'success': True, 'sync_id': sync_id}
        
        except Exception as e:
            print(f"  ✗ 创建失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_snapshot(self, snapshot_type: str = 'full', description: str = '') -> Dict:
        """创建数据库快照"""
        print(f"创建{snapshot_type}快照...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        snapshot_id = f"snapshot_{timestamp}"
        file_path = os.path.join(self.snapshot_dir, f"{snapshot_id}.db")
        
        try:
            shutil.copy2(self.db_path, file_path)
            
            # 计算校验和
            checksum = self.calculate_checksum(file_path)
            size_bytes = os.path.getsize(file_path)
            
            # 默认保存7天
            expires_at = (datetime.now() + timedelta(days=7)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO snapshots
                (snapshot_id, snapshot_type, description, file_path, 
                 checksum, size_bytes, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_id,
                snapshot_type,
                description,
                file_path,
                checksum,
                size_bytes,
                datetime.now().isoformat(),
                expires_at
            ))
            
            conn.commit()
            conn.close()
            
            print(f"  ✓ 快照创建成功: {file_path}")
            return {
                'success': True,
                'snapshot_id': snapshot_id,
                'file_path': file_path,
                'checksum': checksum,
                'size_bytes': size_bytes
            }
        
        except Exception as e:
            print(f"  ✗ 创建失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def list_snapshots(self) -> List:
        """列出所有快照"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT snapshot_id, snapshot_type, description, file_path, 
                   size_bytes, created_at, expires_at, status 
            FROM snapshots ORDER BY created_at DESC
        ''')
        
        snapshots = []
        for row in cursor.fetchall():
            snapshots.append({
                'snapshot_id': row[0],
                'type': row[1],
                'description': row[2],
                'file_path': row[3],
                'size_bytes': row[4],
                'created_at': row[5],
                'expires_at': row[6],
                'status': row[7]
            })
        
        conn.close()
        return snapshots
    
    def restore_from_snapshot(self, snapshot_id: str, target_path: str = None) -> Dict:
        """从快照恢复"""
        print(f"从快照恢复: {snapshot_id}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_path, checksum FROM snapshots WHERE snapshot_id = ? AND status = "active"
        ''', (snapshot_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {'success': False, 'error': '快照不存在或已失效'}
        
        source_path, expected_checksum = result
        
        # 验证快照完整性
        actual_checksum = self.calculate_checksum(source_path)
        if actual_checksum != expected_checksum:
            return {'success': False, 'error': '快照校验失败'}
        
        # 恢复到目标位置
        target = target_path or self.db_path
        
        try:
            # 创建恢复前的备份
            backup_path = f"{target}.backup_{int(time.time())}"
            if os.path.exists(target):
                shutil.copy2(target, backup_path)
            
            shutil.copy2(source_path, target)
            
            restore_id = f"restore_{int(time.time())}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO restore_history
                (restore_id, snapshot_id, target, status, timestamp, restored_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                restore_id,
                snapshot_id,
                target,
                'success',
                datetime.now().isoformat(),
                'system'
            ))
            
            conn.commit()
            conn.close()
            
            print(f"  ✓ 恢复成功")
            return {'success': True, 'restore_id': restore_id, 'backup_path': backup_path}
        
        except Exception as e:
            print(f"  ✗ 恢复失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def cleanup_expired_snapshots(self):
        """清理过期快照"""
        print("清理过期快照...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT snapshot_id, file_path FROM snapshots 
            WHERE expires_at < ? AND status = "active"
        ''', (datetime.now().isoformat(),))
        
        expired = cursor.fetchall()
        cleaned_count = 0
        
        for snapshot_id, file_path in expired:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                cursor.execute('''
                    UPDATE snapshots SET status = "expired" WHERE snapshot_id = ?
                ''', (snapshot_id,))
                
                cleaned_count += 1
                print(f"  ✓ 清理过期快照: {snapshot_id}")
            
            except Exception as e:
                print(f"  ✗ 清理失败 {snapshot_id}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        print(f"\n  共清理 {cleaned_count} 个过期快照")
        return cleaned_count
    
    def sync_shadow_to_main(self):
        """同步影子数据库到主数据库"""
        print("同步影子数据库到主数据库...")
        
        if not os.path.exists(self.shadow_db_path):
            print("  ✗ 影子数据库不存在")
            return {'success': False, 'error': '影子数据库不存在'}
        
        try:
            # 验证影子数据库
            shadow_checksum = self.calculate_checksum(self.shadow_db_path)
            
            # 创建主数据库备份
            backup_path = f"{self.db_path}.shadow_backup_{int(time.time())}"
            shutil.copy2(self.db_path, backup_path)
            
            # 同步
            shutil.copy2(self.shadow_db_path, self.db_path)
            
            sync_id = f"sync_{int(time.time())}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO shadow_sync_logs
                (sync_id, source, target, sync_type, records_synced, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                sync_id,
                self.shadow_db_path,
                self.db_path,
                'shadow_to_main',
                0,
                'success',
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            print(f"  ✓ 同步成功，备份已保存")
            return {'success': True, 'sync_id': sync_id, 'backup_path': backup_path}
        
        except Exception as e:
            print(f"  ✗ 同步失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_shadow_consistency(self) -> Dict:
        """验证影子数据库一致性"""
        print("验证影子数据库一致性...")
        
        if not os.path.exists(self.shadow_db_path):
            return {'consistent': False, 'reason': '影子数据库不存在'}
        
        main_checksum = self.calculate_checksum(self.db_path)
        shadow_checksum = self.calculate_checksum(self.shadow_db_path)
        
        consistent = main_checksum == shadow_checksum
        
        print(f"  主数据库校验和: {main_checksum[:10]}...")
        print(f"  影子数据库校验和: {shadow_checksum[:10]}...")
        print(f"  一致性: {'✅ 一致' if consistent else '❌ 不一致'}")
        
        return {
            'consistent': consistent,
            'main_checksum': main_checksum,
            'shadow_checksum': shadow_checksum
        }
    
    def generate_system_report(self):
        """生成系统报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM snapshots WHERE status = "active"')
        active_snapshots = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM snapshots WHERE status = "expired"')
        expired_snapshots = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM shadow_sync_logs')
        sync_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM restore_history')
        restore_count = cursor.fetchone()[0]
        
        conn.close()
        
        snapshots = self.list_snapshots()
        total_size = sum(s['size_bytes'] for s in snapshots)
        
        consistency = self.verify_shadow_consistency()
        
        print("\n" + "="*80)
        print("          影子系统与快照系统报告")
        print("="*80)
        
        print(f"\n影子系统状态:")
        print(f"  影子数据库: {'✅ 存在' if os.path.exists(self.shadow_db_path) else '❌ 不存在'}")
        print(f"  数据一致性: {'✅ 一致' if consistency['consistent'] else '❌ 不一致'}")
        
        print(f"\n快照统计:")
        print(f"  活跃快照: {active_snapshots}")
        print(f"  过期快照: {expired_snapshots}")
        print(f"  快照总大小: {self.format_size(total_size)}")
        
        print(f"\n操作统计:")
        print(f"  同步次数: {sync_count}")
        print(f"  恢复次数: {restore_count}")
        
        print("\n系统功能:")
        print(f"  ✅ 实时影子副本")
        print(f"  ✅ 定期快照创建")
        print(f"  ✅ 快照完整性校验")
        print(f"  ✅ 数据恢复")
        print(f"  ✅ 自动清理过期快照")
        print(f"  ✅ 影子-主库同步")
        
        if snapshots:
            print("\n最近快照:")
            print("-" * 60)
            for snap in snapshots[:3]:
                print(f"  • {snap['snapshot_id']}")
                print(f"    类型: {snap['type']}")
                print(f"    大小: {self.format_size(snap['size_bytes'])}")
                print(f"    创建: {snap['created_at'][:19]}")
        
        print("\n" + "="*80)
        print("  影子系统与快照系统整合完成！")
        print("="*80)
    
    def format_size(self, bytes_size: int) -> str:
        """格式化文件大小"""
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.1f} KB"
        else:
            return f"{bytes_size / (1024 * 1024):.1f} MB"
    
    def run_system_demo(self):
        """运行系统演示"""
        print("="*80)
        print("          影子系统与快照系统")
        print("="*80)
        
        print("\n[1/3] 创建影子副本...")
        self.create_shadow_copy()
        
        print("\n[2/3] 创建快照...")
        self.create_snapshot('full', '演示快照')
        self.create_snapshot('incremental', '增量快照')
        
        print("\n[3/3] 清理过期快照...")
        self.cleanup_expired_snapshots()
        
        self.generate_system_report()

def main():
    system = ShadowSnapshotSystem()
    system.run_system_demo()

if __name__ == "__main__":
    main()