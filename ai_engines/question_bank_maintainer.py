# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
题库维护系统 - 检测重复题目、验证题目质量、清理不符合要求的题目
"""

import logging
import os
import json
import hashlib
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('question_bank_maintainer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class QuestionValidator:
    """题目验证器"""
    
    def __init__(self):
        self.required_fields = ['id', 'subject', 'question', 'options', 'answer', 'difficulty']
        self.valid_difficulties = ['简单', '中等', '困难']
        self.valid_subjects = ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治']
        self.min_question_length = 10
        self.max_question_length = 1000
        self.min_option_count = 2
        self.max_option_count = 6
        
    def validate_question(self, question: Dict) -> Tuple[bool, List[str]]:
        """验证单个题目"""
        errors = []
        
        for field in self.required_fields:
            if field not in question:
                errors.append(f'缺少必填字段: {field}')
            elif not question[field]:
                errors.append(f'字段值为空: {field}')
                
        if 'difficulty' in question and question['difficulty'] not in self.valid_difficulties:
            errors.append(f'难度值无效: {question["difficulty"]}，有效值: {", ".join(self.valid_difficulties)}')
            
        if 'subject' in question and question['subject'] not in self.valid_subjects:
            errors.append(f'科目无效: {question["subject"]}，有效值: {", ".join(self.valid_subjects)}')
            
        if 'question' in question:
            q_len = len(question['question'].strip())
            if q_len < self.min_question_length:
                errors.append(f'题目内容过短，最少需要 {self.min_question_length} 个字符，当前 {q_len} 个')
            if q_len > self.max_question_length:
                errors.append(f'题目内容过长，最多允许 {self.max_question_length} 个字符，当前 {q_len} 个')
                
        if 'options' in question:
            if not isinstance(question['options'], list):
                errors.append('选项必须是列表格式')
            else:
                option_count = len(question['options'])
                if option_count < self.min_option_count:
                    errors.append(f'选项数量不足，最少需要 {self.min_option_count} 个，当前 {option_count} 个')
                if option_count > self.max_option_count:
                    errors.append(f'选项数量过多，最多允许 {self.max_option_count} 个，当前 {option_count} 个')
                    
                for i, option in enumerate(question['options']):
                    if not option or not isinstance(option, str) or len(option.strip()) == 0:
                        errors.append(f'第 {i+1} 个选项为空或无效')
                        
        if 'answer' in question:
            answer = question['answer']
            if 'options' in question and isinstance(question['options'], list):
                if isinstance(answer, int):
                    if answer < 0 or answer >= len(question['options']):
                        errors.append(f'答案索引超出范围: {answer}，选项数量: {len(question["options"])}')
                elif isinstance(answer, str):
                    if answer not in question['options']:
                        errors.append(f'答案不在选项中: {answer}')
                        
        if 'analysis' in question and question['analysis']:
            if len(question['analysis'].strip()) < 5:
                errors.append('解析内容过短，最少需要5个字符')
                
        return (len(errors) == 0, errors)
    
    def is_valid(self, question: Dict) -> bool:
        """判断题目是否有效"""
        valid, _ = self.validate_question(question)
        return valid

class DuplicateDetector:
    """重复题检测器"""
    
    def __init__(self):
        self.question_hashes = {}
        
    def generate_question_hash(self, question: Dict) -> str:
        """生成题目的唯一哈希值"""
        key_parts = []
        
        if 'question' in question:
            key_parts.append(question['question'].strip())
        if 'subject' in question:
            key_parts.append(question['subject'])
        if 'answer' in question:
            key_parts.append(str(question['answer']))
            
        return hashlib.md5('||'.join(key_parts).encode('utf-8')).hexdigest()
    
    def detect_duplicates(self, questions: List[Dict]) -> List[Tuple[int, int]]:
        """检测重复题目，返回重复对索引"""
        duplicates = []
        seen_hashes = {}
        
        for idx, question in enumerate(questions):
            q_hash = self.generate_question_hash(question)
            
            if q_hash in seen_hashes:
                duplicates.append((seen_hashes[q_hash], idx))
            else:
                seen_hashes[q_hash] = idx
                
        return duplicates
    
    def find_duplicate_groups(self, questions: List[Dict]) -> List[List[int]]:
        """找出所有重复题目组"""
        hash_groups = {}
        
        for idx, question in enumerate(questions):
            q_hash = self.generate_question_hash(question)
            if q_hash not in hash_groups:
                hash_groups[q_hash] = []
            hash_groups[q_hash].append(idx)
            
        return [group for group in hash_groups.values() if len(group) > 1]

class QuestionBankMaintainer:
    """题库维护器"""
    
    def __init__(self, db_path='question_bank.db'):
        self.db_path = db_path
        self.validator = QuestionValidator()
        self.detector = DuplicateDetector()
        self._init_db()
        
        self.maintenance_stats = {
            'total_questions': 0,
            'valid_questions': 0,
            'invalid_questions': 0,
            'duplicate_groups': 0,
            'duplicate_questions': 0,
            'cleaned_questions': 0,
            'last_maintenance': None
        }
        
    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT UNIQUE,
            subject TEXT NOT NULL,
            question TEXT NOT NULL,
            options TEXT,
            answer TEXT NOT NULL,
            difficulty TEXT,
            analysis TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            valid BOOLEAN DEFAULT TRUE,
            duplicate_of TEXT,
            status TEXT DEFAULT 'active'
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL,
            question_id TEXT,
            reason TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS duplicate_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT NOT NULL,
            duplicate_id TEXT NOT NULL,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions(subject)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_valid ON questions(valid)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_status ON questions(status)')
            
            conn.commit()
            
    def load_questions_from_file(self, file_path: str) -> List[Dict]:
        """从文件加载题目"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            logger.info(f'从文件加载 {len(questions)} 道题目')
            return questions
        except Exception as e:
            logger.error(f'加载题目文件失败: {str(e)}')
            return []
            
    def save_questions_to_file(self, questions: List[Dict], file_path: str):
        """保存题目到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            logger.info(f'保存 {len(questions)} 道题目到文件')
        except Exception as e:
            logger.error(f'保存题目文件失败: {str(e)}')
            
    def import_questions(self, questions: List[Dict]) -> Dict:
        """导入题目到数据库"""
        imported = 0
        skipped = 0
        errors = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for question in questions:
                try:
                    valid, validation_errors = self.validator.validate_question(question)
                    
                    if not valid:
                        skipped += 1
                        self._log_maintenance('validate_failed', question.get('id', 'unknown'), 
                                           '题目验证失败', json.dumps(validation_errors))
                        errors.append({'question_id': question.get('id'), 'errors': validation_errors})
                        continue
                        
                    q_hash = self.detector.generate_question_hash(question)
                    
                    cursor.execute('SELECT question_id FROM questions WHERE question_id = ?', 
                                 (question.get('id'),))
                    if cursor.fetchone():
                        skipped += 1
                        self._log_maintenance('duplicate_id', question.get('id', 'unknown'),
                                           '题目ID已存在', '')
                        continue
                        
                    options_json = json.dumps(question.get('options', []))
                    
                    cursor.execute('''
                        INSERT INTO questions
                        (question_id, subject, question, options, answer, difficulty, analysis, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        question.get('id'),
                        question.get('subject'),
                        question.get('question'),
                        options_json,
                        str(question.get('answer')),
                        question.get('difficulty'),
                        question.get('analysis', ''),
                        question.get('category', '')
                    ))
                    
                    imported += 1
                    
                except Exception as e:
                    skipped += 1
                    logger.error(f'导入题目失败: {str(e)}')
                    self._log_maintenance('import_failed', question.get('id', 'unknown'),
                                       str(e), '')
                    
            conn.commit()
            
        return {
            'imported': imported,
            'skipped': skipped,
            'errors': errors
        }
        
    def _log_maintenance(self, operation: str, question_id: str, reason: str, details: str):
        """记录维护日志"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO maintenance_logs
                (operation, question_id, reason, details)
                VALUES (?, ?, ?, ?)
            ''', (operation, question_id, reason, details))
            conn.commit()
            
    def validate_all_questions(self) -> Dict:
        """验证所有题目"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, question_id, subject, question, options, answer, difficulty FROM questions WHERE valid = TRUE')
            
            valid_count = 0
            invalid_count = 0
            invalid_details = []
            
            for row in cursor.fetchall():
                q_id, question_id, subject, question, options, answer, difficulty = row
                
                try:
                    options_list = json.loads(options) if options else []
                except Exception:
                    options_list = []
                    
                question_data = {
                    'id': question_id,
                    'subject': subject,
                    'question': question,
                    'options': options_list,
                    'answer': answer,
                    'difficulty': difficulty
                }
                
                valid, errors = self.validator.validate_question(question_data)
                
                if not valid:
                    invalid_count += 1
                    invalid_details.append({
                        'question_id': question_id,
                        'errors': errors
                    })
                    
                    cursor.execute('''
                        UPDATE questions SET valid = FALSE, status = 'invalid' WHERE id = ?
                    ''', (q_id,))
                    
                    self._log_maintenance('mark_invalid', question_id, 
                                       '题目验证失败', json.dumps(errors))
                else:
                    valid_count += 1
                    
            conn.commit()
            
        self.maintenance_stats['valid_questions'] = valid_count
        self.maintenance_stats['invalid_questions'] = invalid_count
        
        return {
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'invalid_details': invalid_details
        }
        
    def detect_and_mark_duplicates(self) -> Dict:
        """检测并标记重复题目"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, question_id, subject, question, options, answer FROM questions WHERE valid = TRUE AND status = "active"')
            
            questions = []
            question_map = {}
            
            for row in cursor.fetchall():
                q_id, question_id, subject, question, options, answer = row
                
                try:
                    options_list = json.loads(options) if options else []
                except Exception:
                    options_list = []
                    
                question_data = {
                    'id': q_id,
                    'question_id': question_id,
                    'subject': subject,
                    'question': question,
                    'options': options_list,
                    'answer': answer
                }
                
                questions.append(question_data)
                question_map[q_id] = question_id
                
            duplicate_groups = self.detector.find_duplicate_groups(questions)
            
            total_duplicates = sum(len(group) - 1 for group in duplicate_groups)
            marked_count = 0
            
            for group in duplicate_groups:
                main_idx = group[0]
                main_q_id = questions[main_idx]['id']
                main_question_id = questions[main_idx]['question_id']
                
                for idx in group[1:]:
                    dup_q_id = questions[idx]['id']
                    dup_question_id = questions[idx]['question_id']
                    
                    cursor.execute('''
                        UPDATE questions 
                        SET status = 'duplicate', duplicate_of = ?, valid = FALSE 
                        WHERE id = ?
                    ''', (main_question_id, dup_q_id))
                    
                    cursor.execute('''
                        INSERT INTO duplicate_records
                        (question_id, duplicate_id)
                        VALUES (?, ?)
                    ''', (dup_question_id, main_question_id))
                    
                    self._log_maintenance('mark_duplicate', dup_question_id,
                                       f'重复题目，主题目: {main_question_id}', '')
                    
                    marked_count += 1
                    
            conn.commit()
            
        self.maintenance_stats['duplicate_groups'] = len(duplicate_groups)
        self.maintenance_stats['duplicate_questions'] = total_duplicates
        
        return {
            'duplicate_groups': len(duplicate_groups),
            'total_duplicates': total_duplicates,
            'marked_count': marked_count
        }
        
    def clean_invalid_questions(self) -> Dict:
        """清理无效题目"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, question_id FROM questions WHERE valid = FALSE OR status = "invalid"')
            invalid_questions = cursor.fetchall()
            
            deleted_count = 0
            
            for q_id, question_id in invalid_questions:
                cursor.execute('DELETE FROM questions WHERE id = ?', (q_id,))
                self._log_maintenance('delete_invalid', question_id, '删除无效题目', '')
                deleted_count += 1
                
            conn.commit()
            
        self.maintenance_stats['cleaned_questions'] += deleted_count
        
        return {
            'deleted_count': deleted_count
        }
        
    def clean_duplicate_questions(self) -> Dict:
        """清理重复题目"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, question_id FROM questions WHERE status = "duplicate"')
            duplicate_questions = cursor.fetchall()
            
            deleted_count = 0
            
            for q_id, question_id in duplicate_questions:
                cursor.execute('DELETE FROM questions WHERE id = ?', (q_id,))
                self._log_maintenance('delete_duplicate', question_id, '删除重复题目', '')
                deleted_count += 1
                
            conn.commit()
            
        self.maintenance_stats['cleaned_questions'] += deleted_count
        
        return {
            'deleted_count': deleted_count
        }
        
    def get_maintenance_summary(self) -> Dict:
        """获取维护摘要"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM questions')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM questions WHERE valid = TRUE AND status = "active"')
            active = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM questions WHERE valid = FALSE')
            invalid = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM questions WHERE status = "duplicate"')
            duplicates = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT operation, COUNT(*) as count 
                FROM maintenance_logs 
                GROUP BY operation
            ''')
            operation_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
        self.maintenance_stats['total_questions'] = total
        
        return {
            'total_questions': total,
            'active_questions': active,
            'invalid_questions': invalid,
            'duplicate_questions': duplicates,
            'maintenance_stats': self.maintenance_stats,
            'operation_summary': operation_counts
        }
        
    def export_clean_questions(self, file_path: str) -> Dict:
        """导出有效题目"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT question_id, subject, question, options, answer, difficulty, analysis, category
                FROM questions
                WHERE valid = TRUE AND status = "active"
            ''')
            
            questions = []
            for row in cursor.fetchall():
                q_id, subject, question, options, answer, difficulty, analysis, category = row
                
                try:
                    options_list = json.loads(options) if options else []
                except Exception:
                    options_list = []
                    
                questions.append({
                    'id': q_id,
                    'subject': subject,
                    'question': question,
                    'options': options_list,
                    'answer': answer,
                    'difficulty': difficulty,
                    'analysis': analysis,
                    'category': category
                })
                
        self.save_questions_to_file(questions, file_path)
        
        return {
            'exported_count': len(questions),
            'file_path': file_path
        }
        
    def run_maintenance(self, input_file: Optional[str] = None, output_file: Optional[str] = None) -> Dict:
        """执行完整的维护流程"""
        logger.info("=== 题库维护开始 ===")
        
        results = {}
        
        if input_file:
            logger.info("1. 加载题目文件...")
            questions = self.load_questions_from_file(input_file)
            if questions:
                import_result = self.import_questions(questions)
                results['import_result'] = import_result
                logger.info(f"   导入完成: {import_result['imported']} 成功, {import_result['skipped']} 跳过")
                
        logger.info("2. 验证所有题目...")
        validate_result = self.validate_all_questions()
        results['validate_result'] = validate_result
        logger.info(f"   验证完成: {validate_result['valid_count']} 有效, {validate_result['invalid_count']} 无效")
        
        logger.info("3. 检测重复题目...")
        duplicate_result = self.detect_and_mark_duplicates()
        results['duplicate_result'] = duplicate_result
        logger.info(f"   检测完成: {duplicate_result['duplicate_groups']} 组重复, {duplicate_result['total_duplicates']} 道重复题目")
        
        logger.info("4. 清理无效题目...")
        clean_invalid_result = self.clean_invalid_questions()
        results['clean_invalid_result'] = clean_invalid_result
        logger.info(f"   清理完成: 删除 {clean_invalid_result['deleted_count']} 道无效题目")
        
        logger.info("5. 清理重复题目...")
        clean_duplicate_result = self.clean_duplicate_questions()
        results['clean_duplicate_result'] = clean_duplicate_result
        logger.info(f"   清理完成: 删除 {clean_duplicate_result['deleted_count']} 道重复题目")
        
        if output_file:
            logger.info("6. 导出清理后的题目...")
            export_result = self.export_clean_questions(output_file)
            results['export_result'] = export_result
            logger.info(f"   导出完成: {export_result['exported_count']} 道题目")
            
        logger.info("=== 题库维护完成 ===")
        
        self.maintenance_stats['last_maintenance'] = datetime.now().isoformat()
        
        results['summary'] = self.get_maintenance_summary()
        
        return results
    
    def get_invalid_questions(self) -> List[Dict]:
        """获取无效题目列表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT question_id, subject, question, difficulty FROM questions WHERE valid = FALSE')
            
            questions = []
            for row in cursor.fetchall():
                questions.append({
                    'question_id': row[0],
                    'subject': row[1],
                    'question': row[2][:50] + '...' if len(row[2]) > 50 else row[2],
                    'difficulty': row[3]
                })
                
        return questions
    
    def get_maintenance_logs(self, limit: int = 50) -> List[Dict]:
        """获取维护日志"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT operation, question_id, reason, details, created_at
                FROM maintenance_logs
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'operation': row[0],
                    'question_id': row[1],
                    'reason': row[2],
                    'details': row[3],
                    'created_at': row[4]
                })
                
        return logs


if __name__ == "__main__":
    maintainer = QuestionBankMaintainer()
    
    print("=== 题库维护系统测试 ===")
    
    test_questions = [
        {
            'id': 'q001',
            'subject': '数学',
            'question': '已知函数 f(x) = x^2 + 2x + 1，求 f(2) 的值。',
            'options': ['A. 5', 'B. 7', 'C. 9', 'D. 11'],
            'answer': 2,
            'difficulty': '简单',
            'analysis': '将 x = 2 代入函数，f(2) = 4 + 4 + 1 = 9'
        },
        {
            'id': 'q002',
            'subject': '数学',
            'question': '已知函数 f(x) = x^2 + 2x + 1，求 f(2) 的值。',
            'options': ['A. 5', 'B. 7', 'C. 9', 'D. 11'],
            'answer': 2,
            'difficulty': '简单',
            'analysis': '将 x = 2 代入函数，f(2) = 4 + 4 + 1 = 9'
        },
        {
            'id': 'q003',
            'subject': '英语',
            'question': 'Choose the correct answer: He ___ to school every day.',
            'options': ['go', 'goes', 'going', 'went'],
            'answer': 1,
            'difficulty': '简单'
        },
        {
            'id': 'q004',
            'subject': '物理',
            'question': '一个物体从高处自由落下，',
            'options': ['A. 速度越来越快', 'B. 速度保持不变'],
            'answer': 0,
            'difficulty': '困难'
        },
        {
            'id': 'q005',
            'subject': '化学',
            'question': '',
            'options': ['A', 'B'],
            'answer': 0,
            'difficulty': '中等'
        }
    ]
    
    print("\n1. 导入测试题目...")
    import_result = maintainer.import_questions(test_questions)
    print(f"   导入: {import_result['imported']} 成功, {import_result['skipped']} 跳过")
    
    print("\n2. 验证题目...")
    validate_result = maintainer.validate_all_questions()
    print(f"   有效: {validate_result['valid_count']}, 无效: {validate_result['invalid_count']}")
    if validate_result['invalid_details']:
        print("   无效详情:")
        for item in validate_result['invalid_details']:
            print(f"     - {item['question_id']}: {', '.join(item['errors'])}")
    
    print("\n3. 检测重复...")
    duplicate_result = maintainer.detect_and_mark_duplicates()
    print(f"   重复组: {duplicate_result['duplicate_groups']}, 重复题目: {duplicate_result['total_duplicates']}")
    
    print("\n4. 清理无效题目...")
    clean_invalid_result = maintainer.clean_invalid_questions()
    print(f"   删除: {clean_invalid_result['deleted_count']} 道")
    
    print("\n5. 清理重复题目...")
    clean_duplicate_result = maintainer.clean_duplicate_questions()
    print(f"   删除: {clean_duplicate_result['deleted_count']} 道")
    
    print("\n6. 维护摘要:")
    summary = maintainer.get_maintenance_summary()
    print(f"   总题目数: {summary['total_questions']}")
    print(f"   有效题目: {summary['active_questions']}")
    print(f"   无效题目: {summary['invalid_questions']}")
    print(f"   重复题目: {summary['duplicate_questions']}")
    
    print("\n7. 导出清理后的题目...")
    export_result = maintainer.export_clean_questions('cleaned_questions.json')
    print(f"   导出: {export_result['exported_count']} 道到 {export_result['file_path']}")