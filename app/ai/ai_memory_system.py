#!/usr/bin/env python3
import os
import json
import sqlite3
import threading
import hashlib
from datetime import datetime
from collections import defaultdict

class AIMemorySystem:
    MEMORY_TYPES = ['experience', 'knowledge', 'skill', 'decision', 'pattern', 'insight', 'warning', 'feedback']
    MEMORY_PRIORITIES = ['critical', 'high', 'medium', 'low']
    MEMORY_STATUS = ['active', 'archived', 'forgotten']
    
    def __init__(self):
        self.memories = {}
        self.index_cache = {}
        self._lock = threading.Lock()
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('ai_memory.db')
            cursor = conn.cursor()
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS memories ( id INTEGER PRIMARY KEY AUTOINCREMENT, memory_id TEXT NOT NULL UNIQUE, memory_type TEXT NOT NULL, content TEXT NOT NULL, summary TEXT, priority TEXT DEFAULT 'medium', status TEXT DEFAULT 'active', tags TEXT, source TEXT, author TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, accessed_at TEXT, access_count INTEGER DEFAULT 0, relevance_score REAL DEFAULT 0.0, confidence REAL DEFAULT 0.0, metadata TEXT ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS memory_relations ( id INTEGER PRIMARY KEY AUTOINCREMENT, source_memory_id TEXT NOT NULL, target_memory_id TEXT NOT NULL, relation_type TEXT NOT NULL, confidence REAL DEFAULT 0.0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(source_memory_id, target_memory_id, relation_type) ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS memory_tags ( id INTEGER PRIMARY KEY AUTOINCREMENT, tag_name TEXT NOT NULL, memory_id TEXT NOT NULL, tag_weight REAL DEFAULT 1.0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(tag_name, memory_id) ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS memory_access_log ( id INTEGER PRIMARY KEY AUTOINCREMENT, memory_id TEXT NOT NULL, access_type TEXT NOT NULL, access_context TEXT, accessed_by TEXT, accessed_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS memory_clusters ( id INTEGER PRIMARY KEY AUTOINCREMENT, cluster_id TEXT NOT NULL UNIQUE, cluster_name TEXT NOT NULL, cluster_description TEXT, member_count INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            conn.commit()
            conn.close()
            logger.info("[AI Memory System] 数据库表创建完成")
        except Exception as e:
            logger.info(f"[AI Memory System] 创建表失败: {e}")
    
    def add_memory(self, memory_type, content, summary='', tags=None, source='', author='system', metadata=None):
        memory_id = f"MEM{datetime.now().strftime('%Y%m%d%H%M%S')}{hashlib.md5(content[:100].encode()).hexdigest()[:8]}"
        
        try:
            conn = sqlite3.connect('ai_memory.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT INTO memories (memory_id, memory_type, content, summary, tags, source, author, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (
                memory_id,
                memory_type,
                content,
                summary,
                json.dumps(tags or []),
                source,
                author,
                json.dumps(metadata or {})
            ))
            
            if tags:
                for tag in tags:
                    cursor.execute(''' INSERT OR IGNORE INTO memory_tags (tag_name, memory_id) VALUES (?, ?) ''', (tag, memory_id))
            
            conn.commit()
            conn.close()
            
            self.memories[memory_id] = {
                'type': memory_type,
                'content': content,
                'summary': summary,
                'tags': tags or [],
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'access_count': 0
            }
            
            return {
                'success': True,
                'memory_id': memory_id,
                'type': memory_type,
                'summary': summary
            }
        except Exception as e:
            logger.info(f"[AI Memory System] 添加记忆失败: {e}")
            return {'error': str(e)}
    
    def search_memories(self, query, memory_type=None, tags=None, limit=10):
        try:
            conn = sqlite3.connect('ai_memory.db')
            cursor = conn.cursor()
            
            conditions = ['status = "active"']
            params = []
            
            if memory_type:
                conditions.append('memory_type = ?')
                params.append(memory_type)
            
            if tags:
                tag_conditions = ' OR '.join(['tags LIKE ?' for _ in tags])
                conditions.append(f'({tag_conditions})')
                params.extend([f'%{tag}%' for tag in tags])
            
            query_lower = query.lower()
            search_score = f''' (CASE WHEN LOWER(content) LIKE ? THEN 5 ELSE 0 END) + (CASE WHEN LOWER(summary) LIKE ? THEN 3 ELSE 0 END) + (CASE WHEN LOWER(tags) LIKE ? THEN 2 ELSE 0 END) '''
            
            sql = f''' SELECT *, {search_score} as match_score FROM memories WHERE {" AND ".join(conditions)} ORDER BY match_score DESC, access_count DESC, relevance_score DESC LIMIT ? '''
            
            params.extend([f'%{query_lower}%', f'%{query_lower}%', f'%{query_lower}%', limit])
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            results = []
            for row in rows:
                results.append({
                    'memory_id': row[1],
                    'type': row[2],
                    'content': row[3][:200] + '...' if len(row[3]) > 200 else row[3],
                    'summary': row[4],
                    'tags': json.loads(row[6]) if row[6] else [],
                    'priority': row[5],
                    'source': row[7],
                    'author': row[8],
                    'access_count': row[13],
                    'relevance_score': row[14],
                    'match_score': row[-1],
                    'created_at': row[10]
                })
            
            return {'success': True, 'results': results, 'count': len(results)}
        except Exception as e:
            logger.info(f"[AI Memory System] 搜索记忆失败: {e}")
            return {'error': str(e)}
    
    def get_memory(self, memory_id):
        try:
            conn = sqlite3.connect('ai_memory.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM memories WHERE memory_id = ?', (memory_id,))
            row = cursor.fetchone()
            
            if row:
                cursor.execute('UPDATE memories SET access_count = access_count + 1, accessed_at = ? WHERE memory_id = ?',
                              (datetime.now().isoformat(), memory_id))
                conn.commit()
                
                conn.close()
                
                return {
                    'memory_id': row[1],
                    'type': row[2],
                    'content': row[3],
                    'summary': row[4],
                    'priority': row[5],
                    'status': row[6],
                    'tags': json.loads(row[6]) if row[6] else [],
                    'source': row[7],
                    'author': row[8],
                    'created_at': row[10],
                    'updated_at': row[11],
                    'accessed_at': row[12],
                    'access_count': row[13],
                    'relevance_score': row[14],
                    'confidence': row[15],
                    'metadata': json.loads(row[16]) if row[16] else {}
                }
            
            conn.close()
            return None
        except Exception as e:
            logger.info(f"[AI Memory System] 获取记忆失败: {e}")
            return None
    
    def update_memory(self, memory_id, content=None, summary=None, tags=None, priority=None, status=None):
        try:
            conn = sqlite3.connect('ai_memory.db')
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if content:
                updates.append('content = ?')
                params.append(content)
            if summary:
                updates.append('summary = ?')
                params.append(summary)
            if tags:
                updates.append('tags = ?')
                params.append(json.dumps(tags))
            if priority:
                updates.append('priority = ?')
                params.append(priority)
            if status:
                updates.append('status = ?')
                params.append(status)
            
            updates.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(memory_id)
            
            cursor.execute(f'UPDATE memories SET {", ".join(updates)} WHERE memory_id = ?', params)
            conn.commit()
            conn.close()
            
            return {'success': True, 'memory_id': memory_id}
        except Exception as e:
            logger.info(f"[AI Memory System] 更新记忆失败: {e}")
            return {'error': str(e)}
    
    def delete_memory(self, memory_id):
        try:
            conn = sqlite3.connect('ai_memory.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM memories WHERE memory_id = ?', (memory_id,))
            cursor.execute('DELETE FROM memory_relations WHERE source_memory_id = ? OR target_memory_id = ?',
            (memory_id, memory_id))
            cursor.execute('DELETE FROM memory_tags WHERE memory_id = ?', (memory_id,))
            
            conn.commit()
            conn.close()
            
            if memory_id in self.memories:
                del self.memories[memory_id]
            
            return {'success': True, 'memory_id': memory_id}
        except Exception as e:
            logger.info(f"[AI Memory System] 删除记忆失败: {e}")
            return {'error': str(e)}
    
    def add_memory_relation(self, source_memory_id, target_memory_id, relation_type, confidence=0.8):
        try:
            conn = sqlite3.connect('ai_memory.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT OR REPLACE INTO memory_relations (source_memory_id, target_memory_id, relation_type, confidence) VALUES (?, ?, ?, ?) ''', (source_memory_id, target_memory_id, relation_type, confidence))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'relation': {'source': source_memory_id, 'target': target_memory_id,
            'type': relation_type}}
        except Exception as e:
            logger.info(f"[AI Memory System] 添加记忆关系失败: {e}")
            return {'error': str(e)}
    
    def get_memory_relations(self, memory_id):
        try:
            conn = sqlite3.connect('ai_memory.db')
            cursor = conn.cursor()
            
            cursor.execute(''' SELECT * FROM memory_relations WHERE source_memory_id = ? OR target_memory_id = ? ORDER BY confidence DESC ''', (memory_id, memory_id))
            
            rows = cursor.fetchall()
            conn.close()
            
            relations = []
            for row in rows:
                relations.append({
                    'source_memory_id': row[1],
                    'target_memory_id': row[2],
                    'relation_type': row[3],
                    'confidence': row[4],
                    'created_at': row[5]
                })
            
            return relations
        except Exception as e:
            logger.info(f"[AI Memory System] 获取记忆关系失败: {e}")
            return []
    
    def get_memories_by_type(self, memory_type):
        try:
            conn = sqlite3.connect('ai_memory.db')
            cursor = conn.cursor()
            cursor.execute(
            'SELECT * FROM memories WHERE memory_type = ? AND status = "active" ORDER BY created_at DESC', (memory_type,
            ))
            rows = cursor.fetchall()
            conn.close()
            
            memories = []
            for row in rows:
                memories.append({
                    'memory_id': row[1],
                    'type': row[2],
                    'content': row[3][:100] + '...' if len(row[3]) > 100 else row[3],
                    'summary': row[4],
                    'tags': json.loads(row[6]) if row[6] else [],
                    'created_at': row[10],
                    'access_count': row[13]
                })
            
            return memories
        except Exception as e:
            logger.info(f"[AI Memory System] 获取记忆类型失败: {e}")
            return []
    
    def get_memory_summary(self):
        try:
            conn = sqlite3.connect('ai_memory.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM memories')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM memories WHERE status = "active"')
            active = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM memories WHERE status = "archived"')
            archived = cursor.fetchone()[0]
            
            cursor.execute('SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type')
            type_counts = {}
            for row in cursor.fetchall():
                type_counts[row[0]] = row[1]
            
            cursor.execute('SELECT COUNT(*) FROM memory_relations')
            relations = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT tag_name) FROM memory_tags')
            tags = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(access_count) FROM memories')
            avg_access = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_memories': total,
                'active_memories': active,
                'archived_memories': archived,
                'type_distribution': type_counts,
                'total_relations': relations,
                'total_tags': tags,
                'average_access_count': round(avg_access, 1)
            }
        except Exception as e:
            logger.info(f"[AI Memory System] 获取记忆摘要失败: {e}")
            return {}
    
    def auto_cleanup(self):
        try:
            conn = sqlite3.connect('ai_memory.db')
            cursor = conn.cursor()
            
            cursor.execute(''' UPDATE memories SET status = "archived" WHERE status = "active" AND access_count = 0 AND created_at < ? ''', ((datetime.now() - __import__('datetime').timedelta(days=30)).isoformat(),))
            
            cursor.execute(''' UPDATE memories SET status = "forgotten" WHERE status = "archived" AND created_at < ? ''', ((datetime.now() - __import__('datetime').timedelta(days=90)).isoformat(),))
            
            conn.commit()
            conn.close()
            
            return {'success': True}
        except Exception as e:
            logger.info(f"[AI Memory System] 自动清理失败: {e}")
            return {'error': str(e)}
    
    def generate_insight(self, memory_ids):
        try:
            conn = sqlite3.connect('ai_memory.db')
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(memory_ids))
            cursor.execute(f'SELECT * FROM memories WHERE memory_id IN ({placeholders})', memory_ids)
            rows = cursor.fetchall()
            
            conn.close()
            
            contents = [row[3] for row in rows]
            all_tags = []
            for row in rows:
                tags = json.loads(row[6]) if row[6] else []
                all_tags.extend(tags)
            
            tag_freq = defaultdict(int)
            for tag in all_tags:
                tag_freq[tag] += 1
            
            insight = {
                'memory_count': len(rows),
                'common_tags': [{'tag': tag, 'frequency': count} for tag, count in sorted(tag_freq.items(),
                key=lambda x: x[1], reverse=True)[:5]],
                'summary': f"分析了 {len(rows)} 条记忆，发现共同主题: {', '.join([t[0] for t in tag_freq.items()][:3])}",
                'generated_at': datetime.now().isoformat()
            }
            
            return {'success': True, 'insight': insight}
        except Exception as e:
            logger.info(f"[AI Memory System] 生成洞察失败: {e}")
            return {'error': str(e)}

ai_memory_system = AIMemorySystem()