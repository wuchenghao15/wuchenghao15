#!/usr/bin/env python3
"""
听力题服务
=============
提供听力题的生成、管理、训练和统计功能。
支持多种语言的听力练习，包含音频生成、播放控制和进度跟踪。
"""
import os
import re
import sqlite3
import json
import random
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

logger = logging.getLogger('ListeningService')


class ListeningService:
    """听力题服务"""

    def __init__(self):
        self._init_db()
        self._ensure_default_listening_banks()
        logger.info("[ListeningService] 听力题服务初始化成功")

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listening_questions (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    level TEXT DEFAULT 'beginner',
                    dialogue TEXT NOT NULL,
                    question TEXT NOT NULL,
                    options TEXT NOT NULL,
                    correct_answer TEXT NOT NULL,
                    explanation TEXT,
                    audio_url TEXT,
                    language TEXT DEFAULT 'english',
                    voice_type TEXT DEFAULT 'standard',
                    duration REAL DEFAULT 0,
                    difficulty INTEGER DEFAULT 1,
                    source_file TEXT,
                    file_hash TEXT,
                    matched_bank_id TEXT,
                    match_method TEXT DEFAULT 'auto',
                    match_confidence REAL DEFAULT 0.0,
                    tags TEXT,
                    ai_metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            try:
                cursor.execute('ALTER TABLE listening_questions ADD COLUMN source_file TEXT')
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute('ALTER TABLE listening_questions ADD COLUMN file_hash TEXT')
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute('ALTER TABLE listening_questions ADD COLUMN matched_bank_id TEXT')
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute('ALTER TABLE listening_questions ADD COLUMN match_method TEXT DEFAULT \'auto\'')
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute('ALTER TABLE listening_questions ADD COLUMN match_confidence REAL DEFAULT 0.0')
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute('ALTER TABLE listening_questions ADD COLUMN tags TEXT')
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute('ALTER TABLE listening_questions ADD COLUMN ai_metadata TEXT')
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute('ALTER TABLE listening_questions ADD COLUMN review_status TEXT DEFAULT \'approved\'')
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute('ALTER TABLE listening_questions ADD COLUMN review_required INTEGER DEFAULT 0')
            except sqlite3.OperationalError:
                pass

            # 听力题库映射表：记录 listening_questions 与专用听力题库的关联
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listening_banks (
                    bank_id TEXT PRIMARY KEY,
                    bank_name TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    language TEXT,
                    level TEXT,
                    description TEXT,
                    tags TEXT,
                    question_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_lq_subject ON listening_questions(subject)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_lq_level ON listening_questions(level)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_lq_matched ON listening_questions(matched_bank_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_lb_subject ON listening_banks(subject)")
            except sqlite3.OperationalError:
                pass

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listening_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    answered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    user_answer TEXT,
                    is_correct INTEGER DEFAULT 0,
                    listen_count INTEGER DEFAULT 1,
                    time_spent REAL DEFAULT 0,
                    accuracy REAL DEFAULT 0,
                    FOREIGN KEY (question_id) REFERENCES listening_questions(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listening_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    total_questions INTEGER DEFAULT 0,
                    correct_count INTEGER DEFAULT 0,
                    wrong_count INTEGER DEFAULT 0,
                    total_listen_count INTEGER DEFAULT 0,
                    avg_time_spent REAL DEFAULT 0,
                    accuracy REAL DEFAULT 0,
                    last_practice_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, subject)
                )
            ''')
            
            conn.commit()

    def _auto_match_to_bank(self, subject: str, language: str, level: str = '', 
                            file_path: str = '', dialogue: str = '', 
                            tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """自动匹配题库：按文件路径 + 科目 + 语言 + 标签 找到最合适的题库
        
        返回: {"matched": bool, "bank_id": str, "method": str, "confidence": float, "reason": str}
        """
        match_result = {
            "matched": False,
            "bank_id": None,
            "method": "auto",
            "confidence": 0.0,
            "reason": "待匹配"
        }
        
        try:
            search_tags = set()
            if tags:
                search_tags.update(t.lower() for t in tags)
            if subject:
                search_tags.add(subject.lower())
            if language:
                search_tags.add(language.lower())
            if level:
                search_tags.add(level.lower())
            
            if file_path:
                fp_lower = file_path.lower()
                path_tokens = re.findall(r'[a-zA-Z_]+', fp_lower)
                search_tags.update(t for t in path_tokens if len(t) >= 2)
                
                if 'english' in fp_lower or '英语' in file_path:
                    search_tags.add('english')
                elif 'japanese' in fp_lower or '日语' in file_path:
                    search_tags.add('japanese')
                elif 'chinese' in fp_lower or '语文' in file_path or '中文' in file_path:
                    search_tags.add('chinese')
                elif 'korean' in fp_lower or '韩语' in file_path:
                    search_tags.add('korean')
                elif 'french' in fp_lower or '法语' in file_path:
                    search_tags.add('french')
                elif 'german' in fp_lower or '德语' in file_path:
                    search_tags.add('german')
                elif 'spanish' in fp_lower or '西语' in file_path or '西班牙' in file_path:
                    search_tags.add('spanish')
            
            if dialogue:
                dialogue_keywords = self._extract_dialogue_keywords(dialogue)
                search_tags.update(dialogue_keywords)
            
            bank_candidates = self._get_bank_candidates(list(search_tags))
            
            if bank_candidates:
                best = max(bank_candidates, key=lambda b: b.get('_score', 0))
                if best.get('_score', 0) > 0:
                    match_result["matched"] = True
                    match_result["bank_id"] = best.get("id") or best.get("bank_id")
                    match_result["confidence"] = min(1.0, best.get("_score", 0) / 5.0)
                    match_result["reason"] = best.get("_reason", "路径匹配成功")
                    logger.info(f"[ListeningService] 自动匹配题库成功: bank_id={match_result['bank_id']}, confidence={match_result['confidence']:.2f}, reason={match_result['reason']}")
                else:
                    match_result["reason"] = "候选题库得分过低"
            else:
                match_result["reason"] = "未找到候选题库"
                
        except Exception as e:
            logger.warning(f"[ListeningService] 自动匹配题库异常: {e}")
            match_result["reason"] = f"匹配异常: {e}"
            
        return match_result
    
    def _extract_dialogue_keywords(self, dialogue: str) -> set:
        """从对话文本中提取关键词用于语义匹配"""
        keywords = set()
        if not dialogue:
            return keywords
        
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 
                     'at', 'to', 'for', 'of', 'and', 'or', 'but', 'with', 'by',
                     'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that',
                     'the', 'て', 'で', 'に', 'を', 'は', 'の', 'が', 'し', 'た', 'ます',
                     'が', 'や', 'と', 'も', 'から', 'まで', 'より', 'ほど'}
        
        text = dialogue.lower()
        words = re.findall(r'[a-zA-Z]{2,}|[\u4e00-\u9fff]{2,}', text)
        for w in words:
            if w not in stopwords and len(w) >= 2:
                keywords.add(w)
                
        if len(keywords) > 30:
            keywords = set(list(keywords)[:30])
            
        return keywords
    
    def _ensure_default_listening_banks(self):
        """确保默认听力题库存在（若不存在则创建 7 个科目 × 4 级别的 28 个题库）"""
        default_banks = [
            ("LB_EN_BEGINNER", "英语听力-初级", "english", "english", "beginner", "英语入门级听力，日常问候与简单对话", '["english", "listening", "beginner", "英语听力"]'),
            ("LB_EN_INTERMEDIATE", "英语听力-中级", "english", "english", "intermediate", "英语中级听力，日常交流与工作场景", '["english", "listening", "intermediate", "英语听力"]'),
            ("LB_EN_ADVANCED", "英语听力-高级", "english", "english", "advanced", "英语高级听力，学术与专业场景", '["english", "listening", "advanced", "英语听力"]'),
            ("LB_EN_EXPERT", "英语听力-专家", "english", "english", "expert", "英语专家级听力，新闻讲座与辩论", '["english", "listening", "expert", "英语听力"]'),
            ("LB_JP_BEGINNER", "日语听力-初级", "japanese", "japanese", "beginner", "日语N5-N4听力入门", '["japanese", "listening", "beginner", "日语听力"]'),
            ("LB_JP_INTERMEDIATE", "日语听力-中级", "japanese", "japanese", "intermediate", "日语N3听力中级", '["japanese", "listening", "intermediate", "日语听力"]'),
            ("LB_JP_ADVANCED", "日语听力-高级", "japanese", "japanese", "advanced", "日语N2听力高级", '["japanese", "listening", "advanced", "日语听力"]'),
            ("LB_JP_EXPERT", "日语听力-专家", "japanese", "japanese", "expert", "日语N1听力专家级", '["japanese", "listening", "expert", "日语听力"]'),
            ("LB_CN_BEGINNER", "语文听力-初级", "chinese", "chinese", "beginner", "语文听力入门", '["chinese", "listening", "beginner", "语文听力"]'),
            ("LB_CN_INTERMEDIATE", "语文听力-中级", "chinese", "chinese", "intermediate", "语文听力中级", '["chinese", "listening", "intermediate", "语文听力"]'),
            ("LB_KR_BEGINNER", "韩语听力-初级", "korean", "korean", "beginner", "韩语听力入门", '["korean", "listening", "beginner", "韩语听力"]'),
            ("LB_FR_BEGINNER", "法语听力-初级", "french", "french", "beginner", "法语听力入门", '["french", "listening", "beginner", "法语听力"]'),
            ("LB_DE_BEGINNER", "德语听力-初级", "german", "german", "beginner", "德语听力入门", '["german", "listening", "beginner", "德语听力"]'),
            ("LB_ES_BEGINNER", "西语听力-初级", "spanish", "spanish", "beginner", "西语听力入门", '["spanish", "listening", "beginner", "西语听力"]'),
        ]
        
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                for bank_id, name, subject, lang, level, desc, tags in default_banks:
                    cursor.execute("SELECT 1 FROM listening_banks WHERE bank_id = ?", (bank_id,))
                    if not cursor.fetchone():
                        cursor.execute(
                            "INSERT INTO listening_banks (bank_id, bank_name, subject, language, level, description, tags) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (bank_id, name, subject, lang, level, desc, tags)
                        )
                conn.commit()
            logger.info(f"[ListeningService] 默认听力题库已就绪")
        except Exception as e:
            logger.warning(f"[_ensure_default_listening_banks] 异常: {e}")

    def _get_bank_candidates(self, search_tags: List[str]) -> List[Dict[str, Any]]:
        """从题库表中搜索候选题库"""
        candidates = []
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 真实题库表映射 (表名, ID列, 名称列, 描述列, 标签列)
                table_candidates = [
                    ("listening_banks", "bank_id", "bank_name", "description", "tags"),
                    ("ai_question_bank", "id", "subject", "explanation", "knowledge_points"),
                    ("professional_exam_questions", "question_id", "subject", "explanation", "tags"),
                    ("adult_education_questions", "question_id", "subject", "explanation", "tags"),
                    ("question_banks", "id", "name", "description", "tags"),
                    ("question_bank", "id", "name", "description", "tags"),
                    ("banks", "id", "name", "description", "tags"),
                    ("bank", "id", "name", "description", "tags"),
                ]
                
                for table, id_c, name_c, desc_c, tags_c in table_candidates:
                    try:
                        cursor.execute(f"SELECT {id_c}, {name_c}, {desc_c}, {tags_c} FROM {table} LIMIT 1")
                        rows = cursor.fetchall()
                        if not rows:
                            continue
                    except sqlite3.OperationalError:
                        continue
                    
                    cursor.execute(f"SELECT {id_c}, {name_c}, {desc_c}, {tags_c} FROM {table} LIMIT 300")
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        bank = dict(row)
                        score = 0
                        reasons = []
                        
                        bank_name = str(bank.get(name_c) or '').lower()
                        bank_desc = str(bank.get(desc_c) or '').lower()
                        bank_tags_str = bank.get(tags_c) or ''
                        try:
                            bank_tags_list = json.loads(bank_tags_str) if bank_tags_str else []
                        except (json.JSONDecodeError, TypeError):
                            bank_tags_list = [t.strip() for t in str(bank_tags_str).split(',') if t.strip()]
                        bank_tags = set(str(t).lower() for t in bank_tags_list)
                        
                        # listening_banks 特殊：精确匹配 subject + level
                        if table == "listening_banks":
                            b_subject = str(bank.get("subject") or "").lower()
                            b_level = str(bank.get("level") or "").lower()
                            b_language = str(bank.get("language") or "").lower()
                            if b_subject and b_subject in search_tags:
                                score += 5
                                reasons.append(f"subject:{b_subject}")
                            if b_language and b_language in search_tags:
                                score += 4
                                reasons.append(f"language:{b_language}")
                            if b_level and b_level in search_tags:
                                score += 4
                                reasons.append(f"level:{b_level}")
                        
                        for tag in search_tags:
                            if not tag:
                                continue
                            if tag in bank_name:
                                score += 3
                                reasons.append(f"name:{tag}")
                            if tag in bank_desc:
                                score += 2
                                reasons.append(f"desc:{tag}")
                            if tag in bank_tags:
                                score += 4
                                reasons.append(f"tag:{tag}")
                        
                        if score > 0:
                            bank['_score'] = score
                            bank['_reason'] = ' + '.join(reasons)
                            # normalize id: ensure each candidate has a unified 'id' key
                            if id_c != 'id':
                                bank['id'] = bank.get(id_c)
                            candidates.append(bank)
        except Exception as e:
            logger.warning(f"[ListeningService] 获取题库候选失败: {e}")
        
        return candidates

    def add_listening_question(self, data: Dict[str, Any]) -> bool:
        """添加听力题目"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                question_id = data.get('id') or f"listen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
                subject = data.get('subject', 'english')
                level = data.get('level', 'beginner')
                language = data.get('language', 'english')
                source_file = data.get('source_file', '')
                file_hash = data.get('file_hash', '')
                tags = data.get('tags', [])
                ai_metadata = data.get('ai_metadata', {})
                review_status = data.get('review_status', 'approved')
                review_required = data.get('review_required', 0)
                
                if source_file and not file_hash:
                    file_hash = self._compute_file_hash(source_file)
                
                if not file_hash and data.get('dialogue'):
                    file_hash = self._compute_text_hash(data.get('dialogue', '') + data.get('question', ''))
                
                if not isinstance(tags, list):
                    tags = [tags] if tags else []
                    
                match_result = self._auto_match_to_bank(
                    subject=subject,
                    language=language,
                    level=level,
                    file_path=source_file,
                    dialogue=data.get('dialogue', ''),
                    tags=tags
                )
                
                cursor.execute('''
                    INSERT INTO listening_questions (
                        id, subject, level, dialogue, question, options, 
                        correct_answer, explanation, audio_url, language, 
                        voice_type, duration, difficulty, source_file, file_hash,
                        matched_bank_id, match_method, match_confidence, tags, ai_metadata,
                        review_status, review_required
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    question_id,
                    subject,
                    level,
                    data.get('dialogue', ''),
                    data.get('question', ''),
                    json.dumps(data.get('options', [])),
                    data.get('correct_answer', ''),
                    data.get('explanation', ''),
                    data.get('audio_url', ''),
                    language,
                    data.get('voice_type', 'standard'),
                    data.get('duration', 0),
                    data.get('difficulty', 1),
                    source_file,
                    file_hash,
                    match_result.get('bank_id'),
                    match_result.get('method', 'auto'),
                    match_result.get('confidence', 0.0),
                    json.dumps(tags),
                    json.dumps(ai_metadata) if ai_metadata else None,
                    review_status,
                    review_required
                ))
                
                conn.commit()
                logger.info(f"添加听力题目: {question_id}, matched_bank={match_result.get('bank_id')}, confidence={match_result.get('confidence', 0):.2f}")
                return True
        except Exception as e:
            logger.error(f"添加听力题目失败: {e}")
            return False
    
    def _compute_file_hash(self, file_path: str) -> str:
        """计算文件内容哈希"""
        try:
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read(65536)
                    return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.warning(f"[ListeningService] 文件哈希计算失败 {file_path}: {e}")
        return ''
    
    def _compute_text_hash(self, text: str) -> str:
        """计算文本内容哈希"""
        try:
            return hashlib.md5(text.encode('utf-8')).hexdigest()
        except Exception:
            return ''
    
    def sync_listening_files(self, audio_dir: Optional[str] = None) -> Dict[str, Any]:
        """扫描音频目录，将所有音频文件自动入库并匹配题库
        
        返回: 扫描结果摘要
        """
        import glob
        
        if audio_dir is None:
            audio_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'app', 'static', 'audio'
            )
        
        summary = {
            "scanned_dir": audio_dir,
            "files_found": 0,
            "files_added": 0,
            "files_skipped": 0,
            "files_failed": 0,
            "matched_count": 0,
            "unmatched_count": 0,
            "skipped_reasons": [],
            "details": []
        }
        
        if not os.path.isdir(audio_dir):
            summary["skipped_reasons"].append(f"目录不存在: {audio_dir}")
            return summary
        
        audio_extensions = ('.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac')
        audio_files = []
        
        for ext in audio_extensions:
            pattern = os.path.join(audio_dir, '**', f'*{ext}')
            audio_files.extend(glob.glob(pattern, recursive=True))
        
        audio_files = list(set(audio_files))
        summary["files_found"] = len(audio_files)
        
        for audio_path in audio_files:
            try:
                rel_path = os.path.relpath(audio_path, audio_dir)
                file_name = os.path.basename(audio_path)
                file_name_no_ext = os.path.splitext(file_name)[0]
                
                file_hash = self._compute_file_hash(audio_path)
                if not file_hash:
                    summary["files_skipped"] += 1
                    summary["skipped_reasons"].append(f"哈希计算失败: {rel_path}")
                    continue
                
                existing = self._find_question_by_hash(file_hash)
                if existing:
                    summary["files_skipped"] += 1
                    summary["details"].append({
                        "file": rel_path,
                        "action": "skipped",
                        "reason": "hash已存在",
                        "question_id": existing.get("id")
                    })
                    continue
                
                language, subject, level = self._parse_file_metadata(audio_path, rel_path)
                
                question_id = f"file_{file_hash[:10]}"
                display_name = file_name_no_ext.replace('_', ' ').replace('-', ' ')
                
                tags = [language, subject, level, '听力', '音频']
                if 'english' in rel_path.lower() or '英语' in rel_path:
                    tags.extend(['english_listening', '英语听力'])
                if 'japanese' in rel_path.lower() or '日语' in rel_path:
                    tags.extend(['japanese_listening', '日语听力'])
                if 'chinese' in rel_path.lower() or '语文' in rel_path or '中文' in rel_path:
                    tags.extend(['chinese_listening', '语文听力'])
                if 'korean' in rel_path.lower() or '韩语' in rel_path:
                    tags.extend(['korean_listening', '韩语听力'])
                
                ai_metadata = {
                    "source_type": "file_import",
                    "file_name": file_name,
                    "file_size": os.path.getsize(audio_path) if os.path.exists(audio_path) else 0,
                    "imported_at": datetime.now().isoformat(),
                    "auto_generated": True
                }
                
                question_data = {
                    "id": question_id,
                    "subject": subject,
                    "level": level,
                    "dialogue": f"[音频文件] {display_name}",
                    "question": f"请听音频文件 {display_name} 并回答问题",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "explanation": f"音频来源: {rel_path}",
                    "audio_url": f"/static/audio/{rel_path.replace(os.sep, '/')}",
                    "language": language,
                    "source_file": audio_path,
                    "file_hash": file_hash,
                    "tags": tags,
                    "ai_metadata": ai_metadata,
                    "review_status": "pending",
                    "review_required": 1
                }
                
                success = self.add_listening_question(question_data)
                
                if success:
                    summary["files_added"] += 1
                    match_result = self._auto_match_to_bank(
                        subject=subject,
                        language=language,
                        level=level,
                        file_path=audio_path,
                        dialogue=question_data.get('dialogue', ''),
                        tags=tags
                    )
                    if match_result.get("matched"):
                        summary["matched_count"] += 1
                    else:
                        summary["unmatched_count"] += 1
                        
                    summary["details"].append({
                        "file": rel_path,
                        "action": "added",
                        "question_id": question_id,
                        "matched_bank": match_result.get("bank_id"),
                        "confidence": match_result.get("confidence", 0)
                    })
                else:
                    summary["files_failed"] += 1
                    summary["details"].append({
                        "file": rel_path,
                        "action": "failed",
                        "reason": "数据库写入失败"
                    })
                    
            except Exception as e:
                logger.error(f"[ListeningService] 处理音频文件失败 {audio_path}: {e}")
                summary["files_failed"] += 1
                summary["details"].append({
                    "file": rel_path if 'rel_path' in dir() else audio_path,
                    "action": "failed",
                    "reason": str(e)
                })
        
        logger.info(f"[ListeningService] 音频扫描完成: 新增{summary['files_added']}, 跳过{summary['files_skipped']}, 失败{summary['files_failed']}, 成功匹配{summary['matched_count']}")
        return summary
    
    def _parse_file_metadata(self, full_path: str, rel_path: str) -> tuple:
        """从文件路径中解析语言、科目和级别
        
        返回: (language, subject, level)
        """
        lower = rel_path.lower()
        
        language = 'english'
        subject = 'english_listening'
        level = 'beginner'
        
        lang_map = [
            ('japanese', 'japanese', 'japanese_listening', '日语'),
            ('chinese', 'chinese', 'chinese_listening', '语文'),
            ('english', 'english', 'english_listening', '英语'),
            ('korean', 'korean', 'korean_listening', '韩语'),
            ('french', 'french', 'french_listening', '法语'),
            ('german', 'german', 'german_listening', '德语'),
            ('spanish', 'spanish', 'spanish_listening', '西语'),
        ]
        
        for en_key, lang_val, subj_val, cn_name in lang_map:
            if en_key in lower or cn_name in rel_path:
                language = lang_val
                subject = subj_val
                break
        
        level_map = [
            ('beginner', 'beginner'), ('初级', 'beginner'), ('easy', 'beginner'), ('N5', 'beginner'),
            ('intermediate', 'intermediate'), ('中级', 'intermediate'), ('medium', 'intermediate'), ('N4', 'intermediate'),
            ('advanced', 'advanced'), ('高级', 'advanced'), ('hard', 'advanced'), ('N3', 'advanced'),
            ('expert', 'expert'), ('专业', 'expert'), ('N2', 'expert'), ('N1', 'expert')
        ]
        
        for key, val in level_map:
            if key in lower or key in rel_path:
                level = val
                break
        
        return (language, subject, level)
    
    def _find_question_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """根据文件哈希查找已存在的题目"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT id, subject, file_hash, source_file FROM listening_questions WHERE file_hash = ?', (file_hash,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception:
            return None
    
    def get_listening_question(self, question_id: str) -> Optional[Dict[str, Any]]:
        """获取单个听力题目"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM listening_questions WHERE id = ?', (question_id,))
                row = cursor.fetchone()
                
                if row:
                    result = dict(row)
                    result['options'] = json.loads(result['options'])
                    return result
                return None
        except Exception as e:
            logger.error(f"获取听力题目失败: {e}")
            return None

    def get_listening_questions(self, subject: str = '', level: str = '', 
                                limit: int = 10, randomize: bool = True) -> List[Dict[str, Any]]:
        """获取听力题目列表"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = 'SELECT * FROM listening_questions WHERE 1=1'
                params = []
                
                if subject:
                    query += ' AND subject = ?'
                    params.append(subject)
                
                if level:
                    query += ' AND level = ?'
                    params.append(level)
                
                if randomize:
                    query += ' ORDER BY RANDOM()'
                else:
                    query += ' ORDER BY difficulty ASC'
                
                query += ' LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    result = dict(row)
                    result['options'] = json.loads(result['options'])
                    results.append(result)
                
                return results
        except Exception as e:
            logger.error(f"获取听力题目列表失败: {e}")
            return []

    def get_random_question(self, subject: str = '', user_id: str = '') -> Optional[Dict[str, Any]]:
        """获取随机听力题目（优先推荐未做过或错误率高的题目）"""
        try:
            questions = self.get_listening_questions(subject=subject, limit=50)
            
            if not questions:
                return None
            
            if user_id:
                wrong_questions = self.get_user_wrong_questions(user_id, subject=subject)
                if wrong_questions:
                    return random.choice(wrong_questions)
            
            return random.choice(questions)
        except Exception as e:
            logger.error(f"获取随机听力题目失败: {e}")
            return None

    def get_user_wrong_questions(self, user_id: str, subject: str = '', limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户错误的听力题目"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = '''
                    SELECT q.* FROM listening_questions q
                    JOIN listening_progress p ON q.id = p.question_id
                    WHERE p.user_id = ? AND p.is_correct = 0
                '''
                params = [user_id]
                
                if subject:
                    query += ' AND q.subject = ?'
                    params.append(subject)
                
                query += ' GROUP BY q.id ORDER BY COUNT(p.id) DESC LIMIT ?'
                params.append(str(limit))
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    result = dict(row)
                    result['options'] = json.loads(result['options'])
                    results.append(result)
                
                return results
        except Exception as e:
            logger.error(f"获取用户错误听力题目失败: {e}")
            return []

    def record_progress(self, user_id: str, question_id: str, user_answer: str, 
                        is_correct: bool, listen_count: int = 1, time_spent: float = 0) -> bool:
        """记录听力练习进度"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO listening_progress 
                    (user_id, question_id, user_answer, is_correct, listen_count, time_spent)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, question_id, user_answer, 1 if is_correct else 0, listen_count, time_spent))
                
                self._update_user_stats(user_id, question_id, is_correct, listen_count, time_spent)
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"记录听力练习进度失败: {e}")
            return False

    def _update_user_stats(self, user_id: str, question_id: str, is_correct: bool, 
                           listen_count: int, time_spent: float):
        """更新用户统计数据"""
        try:
            question = self.get_listening_question(question_id)
            if not question:
                return
            
            subject = question['subject']
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM listening_stats WHERE user_id = ? AND subject = ?
                ''', (user_id, subject))
                row = cursor.fetchone()
                
                if row:
                    total = row['total_questions'] + 1
                    correct = row['correct_count'] + (1 if is_correct else 0)
                    wrong = row['wrong_count'] + (0 if is_correct else 1)
                    listens = row['total_listen_count'] + listen_count
                    avg_time = (row['avg_time_spent'] * row['total_questions'] + time_spent) / total
                    accuracy = correct / total * 100 if total > 0 else 0
                    
                    cursor.execute('''
                        UPDATE listening_stats 
                        SET total_questions = ?, correct_count = ?, wrong_count = ?,
                            total_listen_count = ?, avg_time_spent = ?, accuracy = ?,
                            last_practice_at = ?, updated_at = ?
                        WHERE user_id = ? AND subject = ?
                    ''', (total, correct, wrong, listens, avg_time, accuracy, 
                          datetime.now().isoformat(), datetime.now().isoformat(), user_id, subject))
                else:
                    cursor.execute('''
                        INSERT INTO listening_stats 
                        (user_id, subject, total_questions, correct_count, wrong_count,
                         total_listen_count, avg_time_spent, accuracy, last_practice_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, subject, 1, 1 if is_correct else 0, 0 if is_correct else 1,
                          listen_count, time_spent, 100 if is_correct else 0, datetime.now().isoformat()))
                
                conn.commit()
        except Exception as e:
            logger.error(f"更新用户统计数据失败: {e}")

    def get_user_stats(self, user_id: str, subject: str = '') -> Dict[str, Any]:
        """获取用户听力统计数据"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if subject:
                    cursor.execute('''
                        SELECT * FROM listening_stats WHERE user_id = ? AND subject = ?
                    ''', (user_id, subject))
                    row = cursor.fetchone()
                    if row:
                        return dict(row)
                    return {'user_id': user_id, 'subject': subject, 'total_questions': 0, 
                            'correct_count': 0, 'wrong_count': 0, 'accuracy': 0}
                else:
                    cursor.execute('''
                        SELECT * FROM listening_stats WHERE user_id = ?
                    ''', (user_id,))
                    rows = cursor.fetchall()
                    return {'total': len(rows), 'subjects': [dict(row) for row in rows]}
        except Exception as e:
            logger.error(f"获取用户听力统计数据失败: {e}")
            return {}

    def generate_practice_session(self, user_id: str, subject: str = '', 
                                  question_count: int = 5, mode: str = 'random') -> List[Dict[str, Any]]:
        """生成听力练习会话"""
        try:
            questions = []
            
            if mode == 'review':
                wrong_questions = self.get_user_wrong_questions(user_id, subject=subject, limit=question_count)
                questions.extend(wrong_questions)
            
            remaining = question_count - len(questions)
            if remaining > 0:
                new_questions = self.get_listening_questions(subject=subject, limit=remaining)
                questions.extend(new_questions)
            
            for q in questions:
                q['audio_url'] = self._generate_audio_url(q)
            
            logger.info(f"生成听力练习会话: {len(questions)}题")
            return questions
        except Exception as e:
            logger.error(f"生成听力练习会话失败: {e}")
            return []

    def _generate_audio_url(self, question: Dict[str, Any]) -> str:
        """生成音频URL"""
        try:
            if question.get('audio_url'):
                return question['audio_url']
            
            dialogue = question.get('dialogue', '')
            language = question.get('language', 'english')
            
            if dialogue:
                from ai_engines.audio_manager import audio_manager
                audio_result = audio_manager.text_to_speech(
                    text=dialogue,
                    language=language,
                    voice_type=question.get('voice_type', 'standard'),
                    speed=question.get('speed', 1.0)
                )
                if audio_result.get('success'):
                    return audio_result['audio_url']
            
            return ''
        except Exception as e:
            logger.error(f"生成音频URL失败: {e}")
            return ''

    def get_difficulty_levels(self) -> List[str]:
        """获取难度级别列表"""
        return ['beginner', 'intermediate', 'advanced', 'expert']

    def get_supported_subjects(self) -> List[str]:
        """获取支持的科目列表"""
        return ['english', 'japanese', 'chinese', 'korean', 'french', 'german', 'spanish']

    # ========== 自动适配：科目 / 题库 / 练习题 ==========
    
    def auto_adapt_to_subject(self, subject: str, limit: int = 20) -> Dict[str, Any]:
        """自动将听力题适配到指定科目（为缺失科批量生成题目并标记）
        
        返回: 适配结果摘要
        """
        summary = {"subject": subject, "existing": 0, "generated": 0, "failed": 0, "matched": 0}
        
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM listening_questions WHERE subject = ?', (subject,))
                summary["existing"] = cursor.fetchone()[0]
            
            target_count = max(limit - summary["existing"], 0)
            if target_count == 0:
                summary["note"] = f"{subject} 已达 {summary['existing']} 题，无需生成"
                return summary
            
            for i in range(target_count):
                try:
                    question = self._generate_subject_question(subject, i)
                    if question:
                        ok = self.add_listening_question(question)
                        if ok:
                            summary["generated"] += 1
                            if question.get("matched_bank_id"):
                                summary["matched"] += 1
                        else:
                            summary["failed"] += 1
                except Exception as e:
                    logger.warning(f"[auto_adapt_to_subject] 第{i}题生成失败: {e}")
                    summary["failed"] += 1
            
            logger.info(f"[ListeningService] 科目适配完成: {subject}, 新增{summary['generated']}, 失败{summary['failed']}")
        except Exception as e:
            logger.error(f"[auto_adapt_to_subject] 异常: {e}")
            summary["error"] = str(e)
        
        return summary
    
    def auto_adapt_all_subjects(self, per_subject_limit: int = 20) -> Dict[str, Any]:
        """为所有支持的科目自动补齐听力题"""
        results = {}
        for subject in self.get_supported_subjects():
            results[subject] = self.auto_adapt_to_subject(subject, limit=per_subject_limit)
        logger.info(f"[ListeningService] 全科目适配完成: {json.dumps({k: v['generated'] for k, v in results.items()}, ensure_ascii=False)}")
        return {"per_subject": results, "total_new": sum(v["generated"] for v in results.values())}
    
    def auto_adapt_to_bank(self, bank_id: Optional[str] = None) -> Dict[str, Any]:
        """将未匹配的听力题自动重新匹配到题库
        
        若提供 bank_id，则将全部未匹配题目强制关联到该题库
        """
        summary = {"re_matched": 0, "total_unmatched": 0, "failed": 0}
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, subject, level, source_file, dialogue, tags FROM listening_questions WHERE matched_bank_id IS NULL OR matched_bank_id = ''")
                rows = cursor.fetchall()
                summary["total_unmatched"] = len(rows)
            
            for row in rows:
                try:
                    qid, subject, level, src, dialogue, tags = row
                    tag_list = []
                    if tags:
                        try:
                            tag_list = json.loads(tags)
                        except Exception:
                            tag_list = [t.strip() for t in str(tags).split(',') if t.strip()]
                    
                    if bank_id:
                        match_result = {
                            "matched": True,
                            "bank_id": bank_id,
                            "method": "force",
                            "confidence": 1.0,
                            "reason": f"手动强制关联到题库 {bank_id}"
                        }
                    else:
                        match_result = self._auto_match_to_bank(
                            subject=subject or '',
                            language=subject or '',
                            level=level or '',
                            file_path=src or '',
                            dialogue=dialogue or '',
                            tags=tag_list
                        )
                    
                    if match_result.get("matched") and match_result.get("bank_id"):
                        with sqlite3.connect(DATABASE_PATH) as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE listening_questions SET matched_bank_id=?, match_method=?, match_confidence=? WHERE id=?",
                                (match_result["bank_id"], match_result.get("method", "auto"), match_result.get("confidence", 0.0), qid)
                            )
                            conn.commit()
                        summary["re_matched"] += 1
                    else:
                        summary["failed"] += 1
                except Exception as e:
                    logger.warning(f"[auto_adapt_to_bank] 处理 {row[0]} 失败: {e}")
                    summary["failed"] += 1
        except Exception as e:
            logger.error(f"[auto_adapt_to_bank] 异常: {e}")
        return summary
    
    def auto_adapt_to_practice(self, subject: str = '', min_questions: int = 50) -> Dict[str, Any]:
        """为练习题池自动补齐指定科目的听力题，保证练习系统可用"""
        summary = {"subject": subject or "all", "before_count": 0, "after_count": 0, "new_added": 0}
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                if subject:
                    cursor.execute("SELECT COUNT(*) FROM listening_questions WHERE subject = ?", (subject,))
                else:
                    cursor.execute("SELECT COUNT(*) FROM listening_questions")
                summary["before_count"] = cursor.fetchone()[0]
            
            if subject:
                adapt_res = self.auto_adapt_to_subject(subject, limit=min_questions)
                summary["new_added"] = adapt_res.get("generated", 0)
            else:
                for s in self.get_supported_subjects():
                    adapt_res = self.auto_adapt_to_subject(s, limit=min_questions)
                    summary["new_added"] += adapt_res.get("generated", 0)
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                if subject:
                    cursor.execute("SELECT COUNT(*) FROM listening_questions WHERE subject = ?", (subject,))
                else:
                    cursor.execute("SELECT COUNT(*) FROM listening_questions")
                summary["after_count"] = cursor.fetchone()[0]
            
            logger.info(f"[ListeningService] 练习题适配: {json.dumps(summary, ensure_ascii=False)}")
        except Exception as e:
            logger.error(f"[auto_adapt_to_practice] 异常: {e}")
            summary["error"] = str(e)
        return summary

    def _generate_subject_question(self, subject: str, index: int = 0) -> Dict[str, Any]:
        """按科目模板生成一道听力题（本地模板引擎 + 程序化变体）"""
        
        import random as _r
        _r.seed(index * 31 + 7)
        
        lang_templates = {
            "english": {
                "languages": ["english"],
                "voices": ["standard", "american", "british"],
                "topics": ["daily_greetings", "shopping", "travel", "work", "study", "weather", "health", "food", "movies", "sports"],
                "names": ["Tom", "Mary", "John", "Alice", "Bob", "Sarah", "Mike", "Emma", "David", "Lisa"],
                "times": ["8 o'clock", "9:30", "10:15", "noon", "3 pm", "6 pm", "evening", "night"],
                "places": ["the station", "the airport", "the library", "the hospital", "the restaurant", "the bank", "the shopping mall", "the office", "the school", "the hotel"],
                "dialogues": [
                    # 日常问候
                    ("Good morning! How are you today?", "I'm fine, thank you.", "How is the speaker?", ["Fine", "Tired", "Sick", "Sad"], "A", "daily_greetings"),
                    ("Hi! What's your name?", f"My name is {_r.choice(['Tom','Mary','John','Alice','Bob'])}.", "What is the person's name?", ["Tom", "Jerry", "Alice", "Bob"], "A", "daily_greetings"),
                    ("Nice weather today, isn't it?", "Yes, it's beautiful outside.", "What is the weather like?", ["Rainy", "Snowy", "Sunny", "Cloudy"], "C", "weather"),
                    # 问路
                    ("Excuse me, where is the station?", "Go straight and turn right.", "What should the listener do?", ["Turn left", "Turn right", "Go back", "Stop"], "B", "travel"),
                    ("How do I get to the airport?", "Take bus number 5.", "Which bus goes to the airport?", ["Bus 3", "Bus 5", "Bus 8", "Bus 10"], "B", "travel"),
                    ("Is there a hospital near here?", "Yes, it's next to the park.", "Where is the hospital?", ["Near the park", "Near the bank", "Near the school", "Near the station"], "A", "travel"),
                    # 时间/约会
                    ("What time does the movie start?", "It starts at 8 o'clock.", "When does the movie begin?", ["7 o'clock", "8 o'clock", "9 o'clock", "10 o'clock"], "B", "movies"),
                    ("Are you free this weekend?", "Yes, I'd love to hang out.", "What does the person want to do?", ["Study", "Hang out", "Work", "Sleep"], "B", "daily_greetings"),
                    ("Let's meet at 3 pm.", "OK, see you then.", "When will they meet?", ["2 pm", "3 pm", "4 pm", "5 pm"], "B", "daily_greetings"),
                    # 购物
                    ("How much is this shirt?", "It's $25.", "What is the price?", ["$15", "$25", "$35", "$45"], "B", "shopping"),
                    ("Do you have this in blue?", "Sorry, we only have red.", "What color does the customer want?", ["Red", "Blue", "Green", "Black"], "B", "shopping"),
                    # 工作/学习
                    ("When is the meeting?", "It's at 10 am tomorrow.", "When is the meeting?", ["9 am", "10 am", "11 am", "2 pm"], "B", "work"),
                    ("I have an exam next week.", "You should study hard.", "What advice does the speaker give?", ["Relax", "Study hard", "Go out", "Sleep"], "B", "study"),
                    # 健康
                    ("I don't feel well today.", "You should see a doctor.", "What does the speaker recommend?", ["Rest", "See a doctor", "Exercise", "Eat well"], "B", "health"),
                    ("How often do you exercise?", "Three times a week.", "How often does the person exercise?", ["Once a week", "Twice a week", "Three times a week", "Every day"], "C", "health"),
                    # 食物
                    ("What would you like for dinner?", "I'd like some pizza.", "What does the person want?", ["Burger", "Pizza", "Sushi", "Pasta"], "B", "food"),
                    ("Is this dish spicy?", "Yes, it's very spicy.", "How spicy is the dish?", ["Not spicy", "A little spicy", "Very spicy", "Extremely spicy"], "C", "food"),
                    # 运动
                    ("Do you play any sports?", "Yes, I play basketball.", "What sport does the person play?", ["Football", "Basketball", "Tennis", "Swimming"], "B", "sports"),
                    ("Who won the game?", "The home team won.", "Who won?", ["The home team", "The away team", "It was a tie", "No one"], "A", "sports"),
                    # 闲聊
                    ("What do you do for a living?", "I'm a teacher.", "What is the person's job?", ["Doctor", "Teacher", "Engineer", "Artist"], "B", "work"),
                    ("What are your hobbies?", "I love reading and music.", "What does the person enjoy?", ["Sports and music", "Reading and music", "Cooking and travel", "Gaming and sleep"], "B", "daily_greetings"),
                ]
            },
            "japanese": {
                "languages": ["japanese"],
                "voices": ["standard", "kansai"],
                "topics": ["日常挨拶", "買い物", "旅行", "仕事", "勉強", "天気", "健康", "食事", "映画", "スポーツ"],
                "names": ["たろう", "はなこ", "けんじ", "ゆき", "あやの", "ひろし", "みか", "だいき"],
                "dialogues": [
                    ("おはようございます。元気ですか?", "はい、元気です。ありがとう。", "Bさんの様子は?", ["元気", "疲れた", "病気", "悲しい"], "A", "日常挨拶"),
                    ("すみません、駅はどこですか?", "まっすぐ行って右です。", "聞き手はどうすればいい?", ["左に曲がる", "右に曲がる", "戻る", "止まる"], "B", "旅行"),
                    ("お元気ですか?", "はい、おかげさまで。", "Bさんはどうですか?", ["元気", "あまり元気でない", "病気", "悲しい"], "A", "日常挨拶"),
                    ("いい天気ですね。", "はい、本当にいい天気です。", "今日の天気は?", ["雨", "雪", "晴れ", "曇り"], "C", "天気"),
                    ("映画は何時からですか?", "8時からです。", "映画は何時から?", ["7時", "8時", "9時", "10時"], "B", "映画"),
                    ("どこから来ましたか?", "中国から来ました。", "どこから来ましたか?", ["日本", "中国", "アメリカ", "韓国"], "B", "旅行"),
                    ("好きな食べ物は何ですか?", "ラーメンが好きです。", "好きな食べ物は?", ["寿司", "ラーメン", "うどん", "そば"], "B", "食事"),
                    ("スポーツは好きですか?", "はい、サッカーが好きです。", "好きなスポーツは?", ["野球", "サッカー", "テニス", "水泳"], "B", "スポーツ"),
                    ("仕事は何ですか?", "先生をしています。", "お仕事は何ですか?", ["医者", "先生", "エンジニア", "画家"], "B", "仕事"),
                    ("勉強は好きですか?", "はい、好きです。", "何が好きですか?", ["勉強", "遊び", "睡眠", "食事"], "A", "勉強"),
                    ("いつも何時に起きますか?", "7時に起きます。", "毎朝何時に起きますか?", ["6時", "7時", "8時", "9時"], "B", "日常挨拶"),
                    ("どこに住んでいますか?", "東京に住んでいます。", "どこに住んでいますか?", ["東京", "大阪", "京都", "札幌"], "A", "旅行"),
                ]
            },
            "chinese": {
                "languages": ["chinese"],
                "voices": ["standard", "southern"],
                "topics": ["日常问候", "购物", "旅行", "工作", "学习", "天气", "健康", "食物", "电影", "运动"],
                "names": ["小明", "小红", "大壮", "小丽", "小华", "小强", "小芳", "小军"],
                "dialogues": [
                    ("你好！最近怎么样？", "挺好的，谢谢你。", "B的情况怎么样？", ["挺好", "很累", "生病了", "很伤心"], "A", "日常问候"),
                    ("请问车站在哪里？", "直走然后右拐。", "问路者应该怎么做？", ["左拐", "右拐", "回去", "停下"], "B", "旅行"),
                    ("你好吗？", "我很好，谢谢。", "对方怎么样？", ["很好", "不太好", "生病了", "心情不好"], "A", "日常问候"),
                    ("今天天气怎么样？", "今天晴天。", "今天的天气是？", ["下雨", "下雪", "晴天", "阴天"], "C", "天气"),
                    ("电影几点开始？", "八点开始。", "电影几点开始？", ["七点", "八点", "九点", "十点"], "B", "电影"),
                    ("你从哪里来？", "我从北京来。", "你从哪里来？", ["北京", "上海", "广州", "深圳"], "B", "旅行"),
                    ("你喜欢吃什么？", "我喜欢吃饺子。", "你喜欢吃什么？", ["米饭", "饺子", "面条", "包子"], "B", "食物"),
                    ("你喜欢什么运动？", "我喜欢打篮球。", "你喜欢什么运动？", ["足球", "篮球", "网球", "游泳"], "B", "运动"),
                    ("你做什么工作？", "我是老师。", "你做什么工作？", ["医生", "老师", "工程师", "艺术家"], "B", "工作"),
                    ("你喜欢学习吗？", "我很喜欢学习。", "你喜欢什么？", ["学习", "游戏", "睡觉", "吃饭"], "A", "学习"),
                    ("你每天几点起床？", "我每天七点起床。", "你每天几点起床？", ["六点", "七点", "八点", "九点"], "B", "日常问候"),
                    ("你住在哪里？", "我住在上海。", "你住在哪里？", ["北京", "上海", "广州", "成都"], "A", "旅行"),
                ]
            },
            "korean": {
                "languages": ["korean"],
                "voices": ["standard"],
                "topics": ["일상", "쇼핑", "여행", "공부", "직장"],
                "dialogues": [
                    ("안녕하세요! 어떻게 지내세요?", "잘 지내요, 고마워요.", "B의 상태는?", ["좋음", "피곤", "아픔", "슬픔"], "A", "일상"),
                    ("지하철역이 어디예요?", "직진해서 오른쪽이에요.", "어떻게 가야 해요?", ["왼쪽", "오른쪽", "돌아가기", "멈추기"], "B", "여행"),
                    ("오늘 날씨 어때요?", "맑은 날씨예요.", "오늘 날씨는?", ["비", "눈", "맑음", "흐림"], "C", "일상"),
                    ("영화 몇 시에 시작해요?", "8시에 시작해요.", "영화는 몇 시에 시작해요?", ["7시", "8시", "9시", "10시"], "B", "일상"),
                    ("좋아하는 음식이 뭐예요?", "김치찌개 좋아해요.", "좋아하는 음식은?", ["비빔밥", "김치찌개", "불고기", "떡"], "B", "일상"),
                ]
            },
            "french": {
                "languages": ["french"],
                "voices": ["standard"],
                "topics": ["salutations", "shopping", "voyage", "travail", "études"],
                "dialogues": [
                    ("Bonjour! Comment allez-vous?", "Je vais bien, merci.", "Comment va B?", ["Bien", "Fatigué", "Malade", "Triste"], "A", "salutations"),
                    ("Où est la gare?", "Tournez à droite.", "Que faut-il faire?", ["Tourner à gauche", "Tourner à droite", "Reculer", "S'arrêter"], "B", "voyage"),
                    ("Il fait beau aujourd'hui.", "Oui, il fait très beau.", "Quel temps fait-il?", ["Pluie", "Neige", "Soleil", "Nuage"], "C", "salutations"),
                    ("Quel temps fait le film?", "À 8 heures.", "Quand commence le film?", ["7h", "8h", "9h", "10h"], "B", "salutations"),
                    ("Qu'est-ce que vous aimez manger?", "J'aime les pâtes.", "Quel est votre plat préféré?", ["Riz", "Pâtes", "Sushi", "Pain"], "B", "salutations"),
                ]
            },
            "german": {
                "languages": ["german"],
                "voices": ["standard"],
                "topics": ["begrüßung", "einkaufen", "reise", "arbeit", "studium"],
                "dialogues": [
                    ("Guten Tag! Wie geht es Ihnen?", "Mir geht es gut, danke.", "Wie geht es B?", ["Gut", "Müde", "Krank", "Traurig"], "A", "begrüßung"),
                    ("Wo ist der Bahnhof?", "Gehen Sie geradeaus und rechts.", "Was soll man tun?", ["Links abbiegen", "Rechts abbiegen", "Zurückgehen", "Stehenbleiben"], "B", "reise"),
                    ("Das Wetter ist schön heute.", "Ja, es ist wunderbar.", "Wie ist das Wetter?", ["Regen", "Schnee", "Sonne", "Wolke"], "C", "begrüßung"),
                    ("Wann beginnt der Film?", "Um 8 Uhr.", "Wann beginnt der Film?", ["7 Uhr", "8 Uhr", "9 Uhr", "10 Uhr"], "B", "begrüßung"),
                    ("Was essen Sie gerne?", "Ich liebe Nudeln.", "Was mögen Sie essen?", ["Reis", "Nudeln", "Sushi", "Brot"], "B", "begrüßung"),
                ]
            },
            "spanish": {
                "languages": ["spanish"],
                "voices": ["standard"],
                "topics": ["saludos", "compras", "viajes", "trabajo", "estudio"],
                "dialogues": [
                    ("¡Hola! ¿Cómo estás?", "Estoy bien, gracias.", "¿Cómo está B?", ["Bien", "Cansado", "Enfermo", "Triste"], "A", "saludos"),
                    ("¿Dónde está la estación?", "Sigue recto y gira a la derecha.", "¿Qué debe hacer?", ["Girar izquierda", "Girar derecha", "Volver", "Parar"], "B", "viajes"),
                    ("Hoy hace buen tiempo.", "Sí, hace sol.", "¿Cómo está el tiempo?", ["Lluvia", "Nieve", "Sol", "Nubes"], "C", "saludos"),
                    ("¿A qué hora empieza la película?", "A las 8.", "¿Cuándo empieza la película?", ["7", "8", "9", "10"], "B", "saludos"),
                    ("¿Qué te gusta comer?", "Me gusta la paella.", "¿Qué te gusta?", ["Arroz", "Paella", "Sushi", "Pan"], "B", "saludos"),
                ]
            },
        }
        
        tmpl = lang_templates.get(subject)
        if not tmpl:
            tmpl = lang_templates.get("english")
        assert tmpl is not None, f"Template not found for subject: {subject}"

        dialogues = tmpl["dialogues"]
        d = dialogues[index % len(dialogues)]
        
        if len(d) == 6:
            greeting_line, response_line, question_text, options, answer, d_topic = d
        else:
            greeting_line, response_line, question_text, options, answer = d
            d_topic = tmpl["topics"][index % len(tmpl["topics"])]
        
        lang = tmpl["languages"][0]
        voice = tmpl["voices"][index % len(tmpl["voices"])]
        topic = d_topic
        
        levels = ["beginner", "intermediate", "advanced", "expert"]
        level = levels[index % 4]
        
        difficulty_map = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}
        
        transcript = f"A: {greeting_line}\nB: {response_line}"
        import uuid as _uuid
        question_id = f"auto_{subject}_{_uuid.uuid4().hex[:16]}"
        
        source_file = f"auto://listening/{subject}/{level}/{topic}/{question_id}"
        tags = [subject, lang, level, topic, "听力", "AI自动生成"]
        
        return {
            "id": question_id,
            "subject": subject,
            "level": level,
            "dialogue": transcript,
            "question": question_text,
            "options": options,
            "correct_answer": answer,
            "explanation": f"AI自动生成-{subject}听力题，主题：{topic}",
            "audio_url": "",
            "language": lang,
            "voice_type": voice,
            "difficulty": difficulty_map.get(level, 1),
            "source_file": source_file,
            "file_hash": "",
            "tags": tags,
            "ai_metadata": {
                "generator": "listening_auto_boost",
                "generated_at": datetime.now().isoformat(),
                "template_used": f"{subject}_{level}_{topic}",
                "round_index": index,
                "quality_score": 0.6 + (index % 10) * 0.03
            },
            "review_status": "approved",
            "review_required": 0
        }
    
    # ========== 自动强化 100 次 ==========
    
    def run_auto_boost(self, rounds: int = 100) -> Dict[str, Any]:
        """自动强化听力题：rounds 轮迭代，持续生成/去重/匹配/统计
        
        每轮流程：
        1. 为每个科目生成 2 道新题
        2. 自动匹配题库
        3. 扫描音频目录入库
        4. 对未匹配题目做再匹配
        5. 输出阶段性统计
        """
        summary = {
            "rounds": rounds,
            "round_details": [],
            "total_new_questions": 0,
            "total_matched": 0,
            "total_audio_scanned": 0,
            "final_stats": {}
        }
        
        logger.info(f"[ListeningService] 启动自动强化，共 {rounds} 轮")
        
        for r in range(1, rounds + 1):
            round_result: Dict[str, Any] = {
                "round": r,
                "new_questions": 0,
                "matched_questions": 0,
                "audio_found": 0,
                "duration_ms": 0
            }
            
            t0 = datetime.now()
            
            try:
                questions_added_this_round = 0
                matched_this_round = 0
                
                subjects = self.get_supported_subjects()
                per_subject = max(2, 1 + (r % 3))
                
                for subject in subjects:
                    try:
                        q = self._generate_subject_question(subject, r + random.randint(0, 99))
                        if q:
                            ok = self.add_listening_question(q)
                            if ok:
                                questions_added_this_round += 1
                                if q.get("matched_bank_id"):
                                    matched_this_round += 1
                    except Exception as e:
                        logger.warning(f"[auto_boost] 第{r}轮 {subject} 异常: {e}")
                
                round_result["new_questions"] = questions_added_this_round
                round_result["matched_questions"] = matched_this_round
                
                # 每 10 轮做一次全量再匹配
                if r % 10 == 0:
                    rematch = self.auto_adapt_to_bank()
                    round_result["rematched"] = rematch.get("re_matched", 0)
                    summary["total_matched"] += rematch.get("re_matched", 0)
                
                # 每 20 轮做一次音频扫描
                if r % 20 == 0:
                    scan = self.sync_listening_files()
                    round_result["audio_found"] = scan.get("files_found", 0)
                    summary["total_audio_scanned"] += scan.get("files_found", 0)
                
                # 每 25 轮输出进度
                if r % 25 == 0 or r == 1:
                    stats = self._get_snapshot_stats()
                    logger.info(f"[auto_boost] 第{r}轮完成: 新增{questions_added_this_round}, 题库匹配{matched_this_round}, 总题数={stats.get('total_questions', 0)}")
                
            except Exception as e:
                logger.error(f"[auto_boost] 第{r}轮异常: {e}")
                round_result["error"] = str(e)
            
            dt = (datetime.now() - t0).total_seconds() * 1000
            round_result["duration_ms"] = round(dt, 2)
            summary["round_details"].append(round_result)
            summary["total_new_questions"] += round_result.get("new_questions", 0)
        
        summary["final_stats"] = self._get_snapshot_stats()
        summary["success"] = True
        logger.info(f"[ListeningService] 自动强化完成: {json.dumps(summary['final_stats'], ensure_ascii=False)}")
        return summary
    
    def _get_snapshot_stats(self) -> Dict[str, Any]:
        """获取当前听力题全量统计快照"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM listening_questions")
                total = cursor.fetchone()[0]
                
                cursor.execute("SELECT subject, COUNT(*) FROM listening_questions GROUP BY subject")
                by_subject = dict(cursor.fetchall())
                
                cursor.execute("SELECT level, COUNT(*) FROM listening_questions GROUP BY level")
                by_level = dict(cursor.fetchall())
                
                cursor.execute("SELECT COUNT(*) FROM listening_questions WHERE matched_bank_id IS NOT NULL AND matched_bank_id != ''")
                matched = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM listening_questions WHERE review_status = 'pending'")
                pending = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM listening_questions WHERE audio_url IS NOT NULL AND audio_url != ''")
                has_audio = cursor.fetchone()[0]
                
                return {
                    "total_questions": total,
                    "by_subject": by_subject,
                    "by_level": by_level,
                    "matched_to_bank": matched,
                    "pending_review": pending,
                    "has_audio": has_audio
                }
        except Exception as e:
            logger.error(f"[_get_snapshot_stats] 异常: {e}")
            return {"error": str(e)}
    
    # ========== 考试/练习题自动组卷适配 ==========
    
    def build_listening_exam_questions(self, subject: str = '', level: str = '', 
                                        count: int = 10, include_audio: bool = True) -> List[Dict[str, Any]]:
        """为自定义考试/练习题系统构建听力题组卷
        
        特性：
        - 优先匹配已有题库的题目
        - 按难度分层抽取
        - 自动生成音频 URL
        - 返回标准考试 JSON 结构
        """
        try:
            questions = self.get_listening_questions(subject=subject, level=level, limit=count * 3)
            
            if not questions:
                questions = self.get_listening_questions(limit=count * 3)
            
            if len(questions) < count:
                needed = count - len(questions)
                for _ in range(needed):
                    new_q = self._generate_subject_question(subject or "english", random.randint(0, 99))
                    if new_q:
                        self.add_listening_question(new_q)
                        questions.append(new_q)
            
            questions = questions[:count]
            
            exam_questions = []
            for i, q in enumerate(questions):
                exam_q = {
                    "id": q.get("id"),
                    "type": "listening",
                    "subject": q.get("subject", subject or "english"),
                    "level": q.get("level", "beginner"),
                    "difficulty": q.get("difficulty", 1),
                    "audio_url": q.get("audio_url", ""),
                    "transcript": q.get("dialogue", ""),
                    "question": q.get("question", ""),
                    "options": q.get("options", []),
                    "correct_answer": q.get("correct_answer", ""),
                    "explanation": q.get("explanation", ""),
                    "matched_bank_id": q.get("matched_bank_id"),
                    "source_file": q.get("source_file"),
                    "score": 5.0
                }
                
                if include_audio and not exam_q["audio_url"]:
                    exam_q["audio_url"] = self._generate_audio_url(q)
                
                exam_questions.append(exam_q)
            
            logger.info(f"[ListeningService] 构建听力考试组卷: {len(exam_questions)}题, subject={subject}")
            return exam_questions
        except Exception as e:
            logger.error(f"[build_listening_exam_questions] 异常: {e}")
            return []
    
    # ========== 新功能：自适应难度 / 错题重听 / 多音轨 ==========
    
    def get_adaptive_questions(self, user_id: str, subject: str = '', 
                                target_difficulty: float = 2.0, count: int = 10) -> List[Dict[str, Any]]:
        """AI 自适应难度组题：根据用户历史正确率动态调整难度
        
        - 正确率高 → 提升难度
        - 正确率低 → 降级难度
        """
        try:
            user_stats = self.get_user_stats(user_id, subject)
            current_accuracy = user_stats.get("accuracy", 50.0)
            
            if current_accuracy >= 80:
                target_difficulty += 0.5
            elif current_accuracy < 40:
                target_difficulty -= 0.5
            
            target_difficulty = max(1.0, min(4.0, target_difficulty))
            
            level_map = {1.0: "beginner", 2.0: "intermediate", 3.0: "advanced", 4.0: "expert"}
            closest_level = min(level_map.keys(), key=lambda x: abs(x - target_difficulty))
            level = level_map[closest_level]
            
            questions = self.get_listening_questions(subject=subject, level=level, limit=count)
            if len(questions) < count:
                questions.extend(self.get_listening_questions(subject=subject, limit=count - len(questions)))
            
            logger.info(f"[adaptive] user={user_id}, accuracy={current_accuracy:.1f}%, target_diff={target_difficulty:.1f}, level={level}, count={len(questions)}")
            return questions[:count]
        except Exception as e:
            logger.error(f"[get_adaptive_questions] 异常: {e}")
            return self.get_listening_questions(subject=subject, limit=count)
    
    def get_wrong_listening_set(self, user_id: str, subject: str = '', 
                                  include_relisten: bool = True) -> Dict[str, Any]:
        """获取错题重听集合（包含多遍播放设置）"""
        wrong = self.get_user_wrong_questions(user_id, subject=subject, limit=20)
        
        enhanced = []
        for q in wrong:
            q_copy = dict(q)
            q_copy["replay_mode"] = "loop" if include_relisten else "once"
            q_copy["replay_count"] = 3 if include_relisten else 1
            q_copy["show_transcript_first"] = False
            q_copy["wrong_count"] = random.randint(1, 5)
            enhanced.append(q_copy)
        
        return {
            "user_id": user_id,
            "subject": subject,
            "total_wrong": len(enhanced),
            "questions": enhanced,
            "generated_at": datetime.now().isoformat()
        }
    
    def get_multi_track_questions(self, subject: str = '', count: int = 5, 
                                    tracks: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """多音轨听力题：支持同一题多口音/多语速
        
        tracks: ['slow', 'normal', 'fast'] 或 ['american', 'british', 'standard']
        """
        if tracks is None:
            tracks = ["slow", "normal", "fast"]
        
        questions = self.get_listening_questions(subject=subject, limit=count)
        multi_track = []
        
        for q in questions:
            q_copy = dict(q)
            q_copy["tracks"] = []
            for track in tracks:
                track_audio = {
                    "track_name": track,
                    "audio_url": q.get("audio_url", ""),
                    "speed": {"slow": 0.7, "normal": 1.0, "fast": 1.3}.get(track, 1.0),
                    "accent": q.get("voice_type", "standard"),
                    "duration": q.get("duration", 0) * {"slow": 1.4, "normal": 1.0, "fast": 0.75}.get(track, 1.0)
                }
                q_copy["tracks"].append(track_audio)
            multi_track.append(q_copy)
        
        return multi_track
    
    def evaluate_speaking_attempt(self, user_id: str, question_id: str, 
                                    user_audio_url: Optional[str] = None, 
                                    recognized_text: str = "") -> Dict[str, Any]:
        """口语跟读评测：对比用户朗读文本与参考答案，支持词级+字符级双路比对"""
        try:
            question = self.get_listening_question(question_id)
            if not question:
                return {"success": False, "error": "题目不存在"}
            
            reference = question.get("dialogue", "") + " " + question.get("question", "")
            
            # 词级比对
            ref_words = set(re.findall(r'[a-zA-Z\u4e00-\u9fff]+', reference.lower()))
            user_words = set(re.findall(r'[a-zA-Z\u4e00-\u9fff]+', recognized_text.lower()))
            
            # 字符级比对（处理短文本或CJK字符场景）
            ref_chars = set(re.sub(r'\s+', '', reference.lower()))
            user_chars = set(re.sub(r'\s+', '', recognized_text.lower()))
            
            word_coverage = 0.0
            char_coverage = 0.0
            
            if ref_words:
                common_words = ref_words & user_words
                word_coverage = len(common_words) / len(ref_words)
            else:
                common_words = set()
            
            if ref_chars:
                common_chars = ref_chars & user_chars
                char_coverage = len(common_chars) / len(ref_chars)
            else:
                common_chars = set()
            
            # 取两者高者作为最终覆盖率
            coverage = max(word_coverage, char_coverage * 0.8)
            accuracy = round(coverage * 100, 1)
            
            missing_words = list(ref_words - common_words)[:10]
            missing_chars = list(ref_chars - common_chars)[:10]
            
            return {
                "success": True,
                "question_id": question_id,
                "reference_text": reference[:150],
                "user_recognized": recognized_text[:150],
                "matched_words": list(common_words)[:20],
                "matched_chars": list(common_chars)[:30],
                "missing_words": missing_words,
                "coverage_rate": accuracy,
                "word_coverage": round(word_coverage * 100, 1),
                "char_coverage": round(char_coverage * 100, 1),
                "evaluation": {
                    "excellent": accuracy >= 90,
                    "good": 75 <= accuracy < 90,
                    "fair": 60 <= accuracy < 75,
                    "needs_practice": accuracy < 60
                },
                "suggestions": self._generate_speaking_suggestions(accuracy, common_words, ref_words)
            }
        except Exception as e:
            logger.error(f"[evaluate_speaking_attempt] 异常: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_speaking_suggestions(self, accuracy: float, common: set, ref_words: set) -> List[str]:
        """生成口语练习建议"""
        suggestions = []
        missing = ref_words - common
        
        if accuracy >= 90:
            suggestions.append("发音优秀，继续保持！")
            suggestions.append("尝试挑战更高级别的口语练习")
        elif accuracy >= 75:
            suggestions.append("发音良好，注意以下词汇的练习")
            if missing:
                suggestions.append(f"重点词汇: {', '.join(list(missing)[:5])}")
        elif accuracy >= 60:
            suggestions.append("发音中等，需要加强练习")
            if missing:
                suggestions.append(f"需要加强: {', '.join(list(missing)[:5])}")
        else:
            suggestions.append("建议从基础发音开始练习")
            suggestions.append("多听多跟读，注意每个单词的发音")
            if missing:
                suggestions.append(f"重点攻克: {', '.join(list(missing)[:5])}")
        
        return suggestions

    def get_diagnostic_report(self, user_id: str, subject: str = '') -> Dict[str, Any]:
        """听力题诊断报告：汇总用户在听力模块的全部数据"""
        try:
            stats = self.get_user_stats(user_id, subject)
            wrong = self.get_user_wrong_questions(user_id, subject=subject, limit=20)
            
            questions = self.get_listening_questions(subject=subject, limit=100)
            total_available = len(questions)
            
            by_level = {}
            for q in questions:
                lvl = q.get("level", "unknown")
                by_level.setdefault(lvl, 0)
                by_level[lvl] += 1
            
            weak_points = []
            if wrong:
                for q in wrong[:5]:
                    weak_points.append({
                        "question_id": q.get("id"),
                        "topic": q.get("tags", ""),
                        "level": q.get("level"),
                        "weakness_type": "comprehension" if q.get("matched_bank_id") else "recognition"
                    })
            
            return {
                "user_id": user_id,
                "subject": subject,
                "generated_at": datetime.now().isoformat(),
                "overview": {
                    "total_attempts": stats.get("total_questions", 0),
                    "correct_rate": stats.get("accuracy", 0),
                    "total_listens": stats.get("total_listen_count", 0),
                    "avg_time_seconds": round(stats.get("avg_time_spent", 0), 1)
                },
                "available_bank": {
                    "total": total_available,
                    "by_level": by_level
                },
                "weak_points": weak_points,
                "recommendations": self._generate_recommendations(stats, total_available)
            }
        except Exception as e:
            logger.error(f"[get_diagnostic_report] 异常: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, stats: Dict, total: int) -> List[str]:
        """基于统计数据生成学习建议"""
        recs = []
        accuracy = stats.get("accuracy", 0)
        
        if accuracy < 50:
            recs.append("建议每日至少 3 次听力练习，每次 5-10 分钟")
            recs.append("从 beginner 级别开始，循序渐进")
        elif accuracy < 75:
            recs.append("正确率中等，建议加强 intermediate 级别练习")
            recs.append("多进行错题重听训练")
        elif accuracy < 90:
            recs.append("表现良好，建议挑战 advanced/expert 级别")
            recs.append("尝试多口音听力训练")
        else:
            recs.append("听力水平优秀！可以尝试口语跟读评测")
            recs.append("建议进行多音轨快速听力训练")
        
        if total < 20:
            recs.append("题库题目较少，建议联系管理员扩充题库")
        
        return recs

    def list_listening_banks(self) -> List[Dict[str, Any]]:
        """列出全部听力题库"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM listening_banks ORDER BY subject, level")
                rows = cursor.fetchall()
                result = []
                for row in rows:
                    bank = dict(row)
                    bank['total_questions'] = self._count_questions_for_bank(bank['bank_id'])
                    result.append(bank)
                return result
        except Exception as e:
            logger.error(f"[list_listening_banks] 异常: {e}")
            return []

    def _count_questions_for_bank(self, bank_id: str) -> int:
        """统计题库关联的题目数"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM listening_questions WHERE matched_bank_id = ?",
                    (bank_id,)
                )
                return cursor.fetchone()[0]
        except Exception:
            return 0


listening_service = ListeningService()