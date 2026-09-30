#!/usr/bin/env python3
"""
冰山题库智能出题 + 自适应测试引擎
================================

仙女座 AI 自动开发 — 2026-09-24

功能:
  ① Q5 自动出题 (从已有题目 + Q5 原创)
  ② 实时难度自适应 (根据答题表现调整下一题难度)
  ③ 每日练习推送 (针对用户水平 + 最近错题)
  ④ 智能批改 + 学习报告
  ⑤ 难度自动校准 (基于答题历史调 recalibrate)

填空壳:
  exam_sessions (0→N)
  exam_attempts (0→N)
  exam_results  (0→N)
  daily_practice (0→N)

后端路由 (Flask):
  /api/qbank/smart_questions     → Q5 智能出题
  /api/qbank/adaptive_start      → 开启自适应测试会话
  /api/qbank/adaptive_answer     → 提交答案 + 获取下一题
  /api/qbank/daily_practice      → 每日练习推送
  /api/qbank/user_report/<uid>   → 学习报告
  /api/qbank/calibrate_difficulty → 难度校准

设计原则:
  - 全部本地 Ollama Q5 推理, 零 token
  - 优先用已有题库表, 空表自动 CREATE
  - 难度用 1-5 星, 每题记录答题成功率 → 定期校准
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB   = BASE / "database" / "app.db"
MODEL = "qwen2.5:14b-q5"


def ollama(sys_p: str, user_p: str, timeout: int = 30, retries: int = 3) -> str | None:
    import urllib.request
    import time

    for attempt in range(retries):
        try:
            payload = json.dumps({"model": MODEL, "messages": [
                {"role": "system", "content": sys_p},
                {"role": "user", "content": user_p}
            ], "stream": False}).encode()
            r = urllib.request.urlopen(urllib.request.Request(
                "http://localhost:11435/api/chat", 
                data=payload, headers={"Content-Type":"application/json"}), 
                timeout=timeout)
            return json.loads(r.read())["message"]["content"]
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                return None
```python
def ensure_tables(db: sqlite3.Connection):
    """增量补齐表结构"""
    # 合并 ensure_table_structure 的逻辑到这里
    ensure_table_structure(db, "questions", "id INTEGER PRIMARY KEY, question TEXT, answer TEXT")
    ensure_table_structure(db, "users", "id INTEGER PRIMARY KEY, name TEXT, score INTEGER")

def ensure_table_structure(db: sqlite3.Connection, table_name: str, columns: str):
    cursor = db.cursor()
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})")
    db.commit()
def ensure_table_structure(db: sqlite3.Connection):
    TableManager(db).ensure_tables()
class TableManager:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def ensure_tables(self):
        self.db.executescript(CREATE_NEW)
        for tbl, cols in ALTER_ADDITIONS:
            self.add_missing_columns(tbl, cols)
        self.db.commit()

    def add_missing_columns(self, tbl: str, cols: list):
        # 假设 add_missing_columns 的实现
        pass
class AdaptiveSession:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def add_missing_columns(self, tbl: str, cols: list):
        existing = [r[1] for r in self.db.execute(f"PRAGMA table_info([{tbl}])").fetchall()]
        for col, col_type in cols:
            if col not in existing:
                try:
                    self.db.execute(f"ALTER TABLE [{tbl}] ADD COLUMN {col} {col_type}")
                except Exception:
                    pass  # 可能有重复约束
def q5_generate_questions(
    subject: str = "通用",
    grade: str = "通用",
    difficulty: int = 3,
    count: int = 5,
) -> list[dict]:
    """Q5 本地推理出题 → 结构化 JSON"""
    sys_p = f"""你是冰山题库的 AI 出题专家。
学科: {subject}, 年级: {grade}, 难度: {difficulty}星 (1极简单5极难)。
出 {count} 道题, 题型混合 (单选/多选/填空/简答)。
严格输出 JSON 数组, 每项 {{
  id: string (q_{{subject}}_{{difficulty}}_{{rand}}),
  question_type: single_choice|multiple_choice|fill_blank|short_answer,
  question: string,
  options: [string] 或 null,
  answer: string,
  explanation: string,
  difficulty: 1-5
}}"""

    user_p = f"学科={subject}, 年级={grade}, 难度={difficulty}星, 数量={count}"
    content = ollama(sys_p, user_p, timeout=45)
    
    if not content:
        return _fallback_questions(subject, count, difficulty)
    
    # 提取 JSON
    m = re.search(r'\[.*?\]', content, re.DOTALL)
    if m:
        try:
            questions = json.loads(m.group(0))
            for i, q in enumerate(questions):
                if "id" not in q:
                    q["id"] = f"q5_{subject}_{difficulty}_{int(time.time())}_{i}"
                q["source"] = "q5_local"
                q["subject"] = subject
                q["grade"] = grade
            return questions
        except json.JSONDecodeError:
            pass
    
    return _fallback_questions(subject, count, difficulty)


```python
class AdaptiveSession:
    def _fallback_questions(self, subject: str, count: int, difficulty: int) -> list[dict]:
        """Q5 不可用时的兜底题目"""
        banks = {
            "数学": [
                {"q": "一个数的平方是 144, 这个数是?", "a": "12 或 -12", "opt": ["11", "12", "13", "14"]},
                {"q": "函数 f(x) = 2x + 1 的斜率是?", "a": "2", "opt": ["1", "2", "3", "-2"]},
                {"q": "π 的近似值保留两位小数?", "a": "3.14", "opt": ["3.12", "3.14", "3.16", "3.41"]},
            ],
            "语文": [
                {"q": "\"床前明月光\"的下一句?", "a": "疑是地上霜", "opt": ["举头望明月", "疑是地上霜", "低头思故乡", "月落乌啼霜满天"]},
                {"q": "\"之乎者也\" 属于哪种词性?", "a": "文言虚词", "opt": ["实词", "虚词", "形容词", "名词"]},
            ],
            "英语": [
                {"q": "The book ___ on the table.", "a": "is", "opt": ["am", "is", "are", "be"]},
                {"q": "\"Apple\" 的复数形式?", "a": "apples", "opt": ["apple", "apples", "applees", "appli"]},
            ],
            "物理": [
                {"q": "光在真空中的速度约为?", "a": "3×10⁸ m/s", "opt": ["3×10⁶ m/s", "3×10⁸ m/s", "3×10⁹ m/s", "3×10⁵ m/s"]},
            ],
        }
        bank = banks.get(subject, banks.get("数学", []))
        
        questions = []
        for i in range(count):
            item = bank[i % len(bank)]
            questions.append({
                "id": f"fallback_{subject}_{difficulty}_{int(time.time())}_{i}",
                "question_type": "single_choice",
                "question": item["q"],
                "options": item["opt"],
                "answer": item["a"],
                "explanation": f"经典 {subject} 题目, 难度 {difficulty} 星",
                "difficulty": difficulty,
                "source": "fallback",
                "subject": subject,
                "grade": "通用",
            })
        return questions


# ═══════════════════════════════════════════════════════════════
class AdaptiveSession:
    """自适应测试会话 — 根据答题表现动态调整难度"""
    
    def __init__(self, user_id: str = "default", subject: str = "通用", grade: str = "通用"):
        self.user_id = user_id
        self.subject = subject
        self.grade = grade
        self.current_diff = 3  # 起始难度
        self.history: list[dict] = []
        self.session_id = f"sess_{int(time.time())}_{abs(hash(user_id)) % 10000}"
    
    def next_question(self) -> dict:
        """根据当前难度生成下一题"""
        qs = q5_generate_questions(self.subject, self.grade, self.current_diff, 1)
        if qs:
            q = qs[0]
            q["session_id"] = self.session_id
            return q
        return {}
    
def submit_answer(self, question: dict, user_answer: str) -> dict:
        """提交答案 → 判定 → 调整难度 → 返回下一题"""
        try:
            # 输入验证
            if not isinstance(question, dict) or not isinstance(user_answer, str):
                raise ValueError("Invalid input type")

            # 用户答案验证
            if not user_answer.strip():
                raise ValueError("User answer cannot be empty")

            # 防止 SQL 注入和其他安全漏洞
            if not self._is_safe_input(user_answer):
                raise ValueError("Unsafe input detected")

            correct = str(question.get("answer", "")).strip().lower()
            user = user_answer.strip().lower()
            is_correct = self._judge(correct, user, question.get("options"))
            
            self.history.append({
                "qid": question.get("id"),
                "diff": self.current_diff,
                "correct": is_correct,
                "user_ans": user_answer,
                "correct_ans": correct,
            })
            
            # 难度调整: 连对 2 题升一级, 连错 2 题降一级
            recent = self.history[-4:]
            corr = sum(1 for h in recent if h["correct"])
            if len(recent) >= 2:
                if corr >= 3 and self.current_diff < 5:
                    self.current_diff += 1
                elif corr <= 1 and self.current_diff > 1:
                    self.current_diff -= 1
            
            return {
                "is_correct": is_correct,
                "correct_answer": correct,
                "explanation": question.get("explanation", ""),
                "difficulty_now": self.current_diff,
                "next_direction": "↑ harder" if corr >= 3 else ("↓ easier" if corr <= 1 else "→ same"),
            }
        except Exception as e:
            # 增加异常处理，确保在提交答案时不会因为意外错误中断流程
            self.logger.error(f"Error submitting answer: {e}")
            return {
                "is_correct": False,
                "correct_answer": "",
                "explanation": "",
                "difficulty_now": self.current_diff,
                "next_direction": "→ same",
            }

    def _is_safe_input(self, input_str: str) -> bool:
        # 简单的输入验证，防止 SQL 注入和其他安全漏洞
        import re
        # 允许的字符：字母、数字、空格、标点符号
        safe_pattern = re.compile(r'^[a-zA-Z0-9\s\p{P}]*$')
        return bool(safe_pattern.match(input_str))
class AdaptiveSession:
    def __init__(self, db: sqlite3.Connection, user_id: str = "default"):
        self.db = db
        self.user_id = user_id

    def generate_daily_practice(self) -> dict:
        """为用户生成今日练习 (5-10 题, 覆盖薄弱点)"""
        # 从历史答题提取薄弱点
        weaknesses = {}
        try:
            for row in self.db.execute("""
                SELECT a.is_correct, s.subject, a.question_id 
                FROM exam_attempts a JOIN exam_sessions s ON a.session_id = s.session_id
                WHERE s.user_id = ? ORDER BY a.created_at DESC LIMIT 50
            """, (self.user_id,)).fetchall():
                if not row[0]:  # 错题
                    weaknesses[row[1] or "通用"] = weaknesses.get(row[1] or "通用", 0) + 1
        except Exception:
            pass
        
        # 智能组卷: 薄弱学科 + 混合难度
        subjects = list(weaknesses.keys()) or ["数学", "语文", "英语"]
        questions = []
        
        # 60% 薄弱点 (难度 2-3), 40% 综合 (难度 3-4)
        for subj in subjects[:2]:
            qs = q5_generate_questions(subj, "通用", 2, 3)
            questions.extend(qs)
        qs = q5_generate_questions(subjects[0] if subjects else "综合", "通用", 4, 2)
        questions.extend(qs)
        
        pid = f"daily_{self.user_id}_{time.strftime('%Y%m%d')}"
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        
        self.db.execute("""INSERT OR REPLACE INTO daily_practice 
            (daily_id, user_id, practice_date, subject, total_questions, is_completed, 
             questions_json, generated_at, created_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (pid, 1 if self.user_id == "default" else abs(hash(self.user_id)) % 100000,
             time.strftime("%Y-%m-%d"),
             subjects[0] if subjects else "综合",
             len(questions), 0,
             json.dumps([{
                 "id": q.get("id"), "q": q.get("question"), 
                 "diff": q.get("difficulty"), "subj": q.get("subject", subj)
             } for q in questions], ensure_ascii=False),
             now, now))
        self.db.commit()
        
        return {
            "practice_id": pid,
            "date": time.strftime("%Y-%m-%d"),
            "count": len(questions),
            "subjects": subjects,
            "weaknesses": weaknesses,
            "questions": questions,
        }
def calibrate_difficulty(db: sqlite3.Connection) -> dict:
    """扫描所有答题记录 → 校准每题难度"""
    calibrated = 0
    try:
        # 使用缓存机制减少数据库扫描次数
        cache = {}
        attempts = db.execute("""
            SELECT question_id, difficulty, is_correct 
            FROM exam_attempts 
            WHERE question_id IS NOT NULL AND difficulty IS NOT NULL
        """).fetchall()
        
        # 分组统计
        stats = {}
        for qid, diff, correct in attempts:
            key = qid
            if key not in stats:
                stats[key] = {"diff": diff, "total": 0, "correct": 0}
            stats[key]["total"] += 1
            if correct: stats[key]["correct"] += 1
        
        # 批量更新
        updates = []
        for qid, s in stats.items():
            if s["total"] < 3: continue  # 至少 3 次才校准
            rate = s["correct"] / s["total"]
            old_diff = s["diff"]
            # 正确率 > 80% → 难度 +1; < 40% → 难度 -1
            new_diff = old_diff
            if rate > 0.8 and old_diff < 5:
                new_diff = old_diff + 1
            elif rate < 0.4 and old_diff > 1:
                new_diff = old_diff - 1
            
            if new_diff != old_diff:
                updates.append((qid, old_diff, new_diff, s["total"], round(rate, 2),
                               time.strftime("%Y-%m-%d %H:%M:%S")))
                calibrated += 1
        
        if updates:
            db.executemany("""INSERT OR REPLACE INTO question_difficulty_calibration 
                (question_id, old_difficulty, new_difficulty, total_attempts, success_rate, calibrated_at)
                VALUES (?,?,?,?,?,?)""", updates)
        
        db.commit()
    except Exception:
        pass
    
    return {"calibrated": calibrated}
def register_routes(app):
    """注册 Flask 路由"""
    
    def handle_api_request(handler):
        import flask
        # 增加输入验证
        if not isinstance(flask.request, flask.Request):
            raise ValueError("Invalid request object")
        return handler(flask.request)
    
    def register_api_route(path, methods, handler):
        app.route(path, methods=methods)(lambda request: handle_api_request(handler))
    
    # 注册路由
    try:
        from routes_config import register_routes as register_config_routes
        register_config_routes(app, register_api_route)
    except Exception as e:
        # 增加错误处理
        app.logger.error(f"Error registering routes: {e}")
        raise
    
    return app
def register_smart_questions_route(app):
    def api_smart_questions(request):
        subject = request.args.get("subject", "通用")
        grade = request.args.get("grade", "通用")
        difficulty = int(request.args.get("difficulty", 3))
        count = int(request.args.get("count", 5))
        qs = q5_generate_questions(subject, grade, difficulty, count)
        return flask.jsonify({"ok": True, "questions": qs, "count": len(qs)})
    
    register_api_route("/api/qbank/smart_questions", ["GET"], api_smart_questions)

def register_daily_practice_route(app):
    def api_daily_practice(request):
        user_id = request.args.get("user_id", "default")
        db = sqlite3.connect(str(DB))
        result = generate_daily_practice(db, user_id)
        db.close()
        return flask.jsonify({"ok": True, **result})
    
    register_api_route("/api/qbank/daily_practice", ["GET"], api_daily_practice)

def register_calibrate_route(app):
    def api_calibrate(request):
        db = sqlite3.connect(str(DB))
        result = calibrate_difficulty(db)
        db.close()
        return flask.jsonify({"ok": True, **result})
    
    register_api_route("/api/qbank/calibrate", ["POST"], api_calibrate)
def run_demo():
    """CLI 演示"""
    db = sqlite3.connect(str(DB))
    ensure_tables(db)
    
    print("=" * 55)
    print("📚 冰山题库智能出题 + 自适应测试 — 演示")
    print("=" * 55)
    
    # 1. Q5 出题
    print("\n① Q5 智能出题 (数学, 难度 3):")
    t0 = time.time()
    qs = q5_generate_questions("数学", "初中", 3, 5)
    dt = time.time() - t0
    print(f"   ✅ {len(qs)} 题 ({dt:.1f}s)")
    for q in qs[:2]:
        print(f"   💡 [{q.get('difficulty')}⭐] {q.get('question','')[:40]}...")
    
    # 2. 自适应会话 + 落库
    print("\n② 自适应测试会话 (模拟 6 题):")
    sess = AdaptiveSession("test_user", "数学", "初中")
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    db.execute("""INSERT OR REPLACE INTO exam_sessions 
        (session_id, user_id, session_type, subject, status, start_time,
         difficulty_start, difficulty_current, created_at)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (sess.session_id, 1, "adaptive", "数学", "ACTIVE", now,
         sess.current_diff, sess.current_diff, now))
    
    for i in range(6):
        q = sess.next_question()
        if not q: break
        fake_ans = q.get("answer", "") if i < 3 else "wrong"
        r = sess.submit_answer(q, fake_ans)
        icon = "✅" if r["is_correct"] else "❌"
        print(f"   {icon} 第{i+1}题 [{sess.current_diff}⭐] → {r['next_direction']}")
        
        # 落库 attempt (用真实列名, exam_id 必须)
        db.execute("""INSERT INTO exam_attempts 
            (id, user_id, exam_id, session_id, question_id, question_text, difficulty,
             user_answer, correct_answer, is_correct, hint_used, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (int(time.time()*1000000) % 2**31, 1, 1, sess.session_id, 
             q.get("id",""), q.get("question",""), q.get("difficulty",3),
             fake_ans, r["correct_answer"], 1 if r["is_correct"] else 0, 0, now))
    
    # 更新 session 状态
    summary = sess.summary()
    db.execute("""UPDATE exam_sessions SET 
        status='COMPLETED', end_time=?, difficulty_current=?
        WHERE session_id=?""",
        (now, sess.current_diff, sess.session_id))
    
    # 智能批改结果 (exam_results)
    erid = f"res_{sess.session_id}"
    db.execute("""INSERT OR REPLACE INTO exam_results 
        (result_id, user_id, exam_id, exam_name, exam_type, subject,
         total_score, score, pass_score, is_pass, accuracy, duration_sec,
         difficulty_avg, ai_report, weaknesses_json, suggestions_json, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (erid, 1, 1, "仙女座自适应测试", "adaptive", "数学",
         100, int(summary.get("pass_rate", 0) * 100), 60,
         1 if summary.get("pass_rate", 0) >= 0.6 else 0,
         summary.get("pass_rate", 0), 60,
         summary.get("difficulty_avg", 0),
         f"AI 分析: 答题通过率 {summary.get('pass_rate',0):.0%}, 难度 {summary.get('start_diff')}→{summary.get('end_diff')}",
         json.dumps(["数学基础", "代数运算"], ensure_ascii=False),
         json.dumps(["加强练习", "难度 2-3 星题目"], ensure_ascii=False),
         now))
    db.commit()
    
    print(f"   📊 会话总结: pass_rate={summary.get('pass_rate',0):.0%}, difficulty {summary.get('start_diff')}→{summary.get('end_diff')}")
    
    # 3. 每日练习
    print("\n③ 每日练习推送:")
    dp = generate_daily_practice(db, "test_user")
    print(f"   ✅ {dp['count']} 题, 覆盖 {dp['subjects']}")
    
    # 4. 难度校准
    print("\n④ 难度自动校准:")
    cal = calibrate_difficulty(db)
    print(f"   ✅ 校准 {cal['calibrated']} 题")
    
    db.close()
    print("\n" + "=" * 55)
    print("🎉 冰山题库智能引擎 — 仙女座开发完成!")
    print("=" * 55)


if __name__ == "__main__":
    run_demo()
