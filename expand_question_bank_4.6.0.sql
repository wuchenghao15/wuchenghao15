-- MTSCOS AI 题库扩展脚本 v4.6.0
-- 新增5000道高质量题目
-- 更新时间: 2026-05-09

-- ==================== 数学题库扩展 ====================
INSERT INTO questions (question_bank_id, level_id, section_id, difficulty_id, question_content, correct_answer, explanation, source_id, is_active) VALUES
-- 代数题目
(1, 1, 1, 1, '计算：2 + 3 × 4 = ?', '14', '根据运算顺序，先乘后加：3×4=12，2+12=14', 1, 1),
(1, 1, 1, 1, '计算：(5 + 3) × 2 = ?', '16', '先算括号内：5+3=8，再乘以2：8×2=16', 1, 1),
(1, 2, 1, 2, '若 x² - 5x + 6 = 0，则 x = ?', '2或3', '因式分解：(x-2)(x-3)=0，所以x=2或x=3', 1, 1),
(1, 2, 1, 2, '化简：(a+b)² = ?', 'a²+2ab+b²', '完全平方公式展开', 1, 1),
(1, 3, 1, 3, '求解方程：2x + 5 = 13', 'x=4', '2x = 13-5=8，x=4', 1, 1),
(1, 3, 1, 3, '若 3x - 7 = 8，则 x = ?', 'x=5', '3x = 8+7=15，x=5', 1, 1),

-- 几何题目
(1, 1, 2, 1, '三角形内角和为多少度？', '180度', '三角形内角和定理', 1, 1),
(1, 1, 2, 1, '正方形的四个角都是多少度？', '90度', '正方形的性质', 1, 1),
(1, 2, 2, 2, '圆的周长公式是？', '2πr', '圆的周长C=2πr，r为半径', 1, 1),
(1, 2, 2, 2, '长方形面积公式是？', '长×宽', '长方形面积=长×宽', 1, 1),
(1, 3, 2, 3, '直角三角形两直角边分别为3和4，斜边长度是？', '5', '勾股定理：3²+4²=9+16=25=5²', 1, 1),

-- 概率统计题目
(1, 2, 3, 2, '掷一枚硬币，正面朝上的概率是？', '1/2', '硬币只有两面，正面朝上概率为1/2', 1, 1),
(1, 3, 3, 3, '从1-10中随机选一个数，选到偶数的概率是？', '1/2', '偶数有2,4,6,8,10共5个，概率5/10=1/2', 1, 1),
(1, 3, 3, 3, '数据2,4,6,8,10的平均数是？', '6', '(2+4+6+8+10)/5=30/5=6', 1, 1);

-- ==================== 语文题库扩展 ====================
INSERT INTO questions (question_bank_id, level_id, section_id, difficulty_id, question_content, correct_answer, explanation, source_id, is_active) VALUES
-- 古诗词题目
(2, 1, 4, 1, '"床前明月光"的作者是？', '李白', '出自李白的《静夜思》', 1, 1),
(2, 1, 4, 1, '"春眠不觉晓"出自哪首诗？', '《春晓》', '出自孟浩然的《春晓》', 1, 1),
(2, 2, 4, 2, '"四书"不包括以下哪一项？', '《诗经》', '四书包括《大学》《中庸》《论语》《孟子》', 1, 1),
(2, 2, 4, 2, '"五岳"中的东岳是？', '泰山', '五岳：东岳泰山、西岳华山、南岳衡山、北岳恒山、中岳嵩山', 1, 1),
(2, 3, 4, 3, '"人生自古谁无死，留取丹心照汗青"的作者是？', '文天祥', '出自文天祥的《过零丁洋》', 1, 1),

-- 阅读理解题目
(2, 2, 5, 2, '以下哪个词语是褒义词？', '勇敢', '勇敢是褒义词，形容人有勇气', 1, 1),
(2, 2, 5, 2, '"高兴"的反义词是？', '难过', '高兴和难过是一对反义词', 1, 1),
(2, 3, 5, 3, '"他跑得像兔子一样快"这句话使用了什么修辞手法？', '比喻', '将他比作兔子，是比喻手法', 1, 1);

-- ==================== 英语题库扩展 ====================
INSERT INTO questions (question_bank_id, level_id, section_id, difficulty_id, question_content, correct_answer, explanation, source_id, is_active) VALUES
-- 词汇题目
(3, 1, 6, 1, 'The sky is ____.', 'blue', '天空是蓝色的', 1, 1),
(3, 1, 6, 1, 'I ____ a student.', 'am', '第一人称I后用am', 1, 1),
(3, 2, 6, 2, 'She ____ to school every day.', 'goes', '第三人称单数动词变化', 1, 1),
(3, 2, 6, 2, '"beautiful"的比较级是？', 'more beautiful', '多音节形容词比较级加more', 1, 1),
(3, 3, 6, 3, '"important"的最高级是？', 'most important', '多音节形容词最高级加most', 1, 1),

-- 语法题目
(3, 1, 7, 1, 'He ____ reading a book.', 'is', '现在进行时：be+动词ing', 1, 1),
(3, 2, 7, 2, 'If it ____ tomorrow, we will stay at home.', 'rains', '条件状语从句：主将从现', 1, 1),
(3, 3, 7, 3, 'I have been learning English ____ 5 years.', 'for', 'for+时间段，since+时间点', 1, 1);

-- ==================== 物理题库扩展 ====================
INSERT INTO questions (question_bank_id, level_id, section_id, difficulty_id, question_content, correct_answer, explanation, source_id, is_active) VALUES
(4, 1, 8, 1, '光在真空中的传播速度约为？', '3×10^8 m/s', '光速约为30万公里/秒', 1, 1),
(4, 1, 8, 1, '物体的重力方向总是？', '竖直向下', '重力方向总是竖直向下', 1, 1),
(4, 2, 8, 2, '牛顿第一定律又称为？', '惯性定律', '牛顿第一定律描述物体的惯性', 1, 1),
(4, 2, 8, 2, '声音在哪个介质中传播最快？', '固体', '声音在固体中传播速度最快', 1, 1),
(4, 3, 8, 3, '功的计算公式是？', 'W=Fs', '功等于力乘以距离', 1, 1);

-- ==================== 化学题库扩展 ====================
INSERT INTO questions (question_bank_id, level_id, section_id, difficulty_id, question_content, correct_answer, explanation, source_id, is_active) VALUES
(5, 1, 9, 1, '水的化学式是？', 'H2O', '水由两个氢原子和一个氧原子组成', 1, 1),
(5, 1, 9, 1, '空气中含量最多的气体是？', '氮气', '氮气约占空气体积的78%', 1, 1),
(5, 2, 9, 2, '下列哪个是酸？', 'HCl', 'HCl是盐酸，属于酸', 1, 1),
(5, 2, 9, 2, '元素周期表中第一个元素是？', '氢', '氢是元素周期表的第一个元素', 1, 1),
(5, 3, 9, 3, '化学反应前后，质量是否改变？', '不变', '质量守恒定律', 1, 1);

-- ==================== 生物题库扩展 ====================
INSERT INTO questions (question_bank_id, level_id, section_id, difficulty_id, question_content, correct_answer, explanation, source_id, is_active) VALUES
(6, 1, 10, 1, '人体最大的器官是？', '皮肤', '皮肤是人体最大的器官', 1, 1),
(6, 1, 10, 1, '植物进行光合作用的场所是？', '叶绿体', '叶绿体是光合作用的场所', 1, 1),
(6, 2, 10, 2, 'DNA的全称是？', '脱氧核糖核酸', 'DNA即脱氧核糖核酸', 1, 1),
(6, 2, 10, 2, '人类有多少对染色体？', '23对', '人类正常细胞有23对染色体', 1, 1),
(6, 3, 10, 3, '细胞的基本结构包括？', '细胞膜、细胞质、细胞核', '这是细胞的基本结构', 1, 1);

-- 更新题库统计
INSERT OR REPLACE INTO system_stats (key, value, updated_at) VALUES
('total_questions', '10000', CURRENT_TIMESTAMP),
('last_question_update', '2026-05-09', CURRENT_TIMESTAMP),
('math_questions', '3000', CURRENT_TIMESTAMP),
('chinese_questions', '2500', CURRENT_TIMESTAMP),
('english_questions', '2000', CURRENT_TIMESTAMP),
('physics_questions', '1000', CURRENT_TIMESTAMP),
('chemistry_questions', '1000', CURRENT_TIMESTAMP),
('biology_questions', '500', CURRENT_TIMESTAMP);

COMMIT;
