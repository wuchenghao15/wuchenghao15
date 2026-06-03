# 9年制学生升级管理系统 - 使用指南

## 📋 系统概述

本系统为MTSCOS AI教育平台的9年制学生升级管理子系统，包含完整的升级逻辑、考试管理、权限控制功能。

### 🎓 完整9年制体系
- **小学阶段**: 1年级 → 2年级 → 3年级 → 4年级 → 5年级 → 6年级
- **初中阶段**: 7年级 → 8年级 → 9年级
- **入口**: 小学1年级
- **出口**: 初中3年级（毕业）

---

## 🎯 核心功能

### 1. 年级管理
- ✅ 学生年级注册和选择（小学1年级至初中3年级）
- ✅ 年级状态跟踪（正常、条件、限制、暂停、留级、毕业）
- ✅ 权限等级管理（0-100）

### 2. 考试管理
- ✅ 期中考试（4月30日截止）
- ✅ 期末考试（7月31日截止）
- ✅ 补考（8月20日截止）
- ✅ 暂停考试申请和审批

### 3. 升级管理
- ✅ 正常升级（期中和期末都及格）
- ✅ 条件升级（补考及格）
- ✅ 强制升级（管理员操作）
- ✅ 强制留级（管理员操作）
- ✅ 毕业（完成初中3年级）

### 4. 权限控制
- ✅ 基于权限等级的访问控制
- ✅ 角色权限验证
- ✅ 操作审计日志

---

## 🚀 快速启动

### 步骤1: 初始化数据库

```bash
cd /Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project

python3 nine_year_upgrade_system.py
```

**预期输出:**
```
================================================================================
MTSCOS 9年制学生升级管理系统 (v1.1)
================================================================================
✅ 9年制升级系统数据库初始化完成
✅ 完整9年制体系: 小学1年级至初中3年级
✅ 学生注册成功
✅ 年级确认成功
✅ 期中考试创建成功
✅ 成绩提交成功
================================================================================
✅ 测试完成！
================================================================================
```

### 步骤2: 启动API服务

```bash
# 启动9年制升级系统API (端口5002)
python3 nine_year_api.py
```

**API服务将运行在:** `http://localhost:5002`

### 步骤3: 启动前端服务

```bash
# 确保前端服务正在运行 (端口8888)
cd frontend
python3 -m http.server 8888
```

---

## 🎓 学生使用流程

### 场景1: 正常升级（小学/初中通用）

```
学生首次登录
    ↓
选择年级（小学1年级至初中3年级）
    ↓
参加期中考试 → 及格 ✅
    ↓
参加期末考试 → 及格 ✅
    ↓
9月1日自动升级或手动申请升级
    ↓
升级到下一年级 ✅
```

**权限变化:**
- 权限等级: 20 (完整权限)
- 可参加: 所有考试
- 可访问: 全部学习内容

**年级过渡示例:**
- 小学1年级 → 小学2年级
- 小学6年级 → 初中1年级
- 初中3年级 → 毕业

### 场景2: 补考及格升级

```
学生首次登录
    ↓
参加期中考试 → 不及格 ❌
    ↓
或
期末考试 → 不及格 ❌
    ↓
参加补考 → 及格 ✅
    ↓
申请条件升级 ⚠️
    ↓
升级到下一年级（带限制）⚠️
```

**权限变化:**
- 权限等级: 10 (受限权限)
- 可参加: 仅基础难度考试
- 可访问: 仅复习材料
- 限制: 需完成补修课程

### 场景3: 补考不及格

```
学生首次登录
    ↓
参加期中考试 → 不及格 ❌
    ↓
或
期末考试 → 不及格 ❌
    ↓
参加补考 → 仍不及格 ❌❌
    ↓
暂停考试资格 ⏸️
    ↓
教师/管理员审批
    ↓
留级或特殊处理
```

**权限变化:**
- 权限等级: 0 (严格受限)
- 可参加: 无考试资格
- 可访问: 仅复习材料
- 需联系: 教师一对一辅导

### 场景4: 暂停考试审批通过

```
学生因特殊原因无法继续考试
    ↓
申请暂停考试
    ↓
填写暂停原因
    ↓
教师审批 → 通过 ✅
    ↓
考试暂停
    ↓
特殊情况处理
    ↓
恢复考试 → 继续流程
```

**权限变化:**
- 暂停期间: 权限等级0
- 恢复后: 恢复原权限
- 特殊: 可获得延长时间

### 场景5: 暂停考试审批不通过

```
学生因特殊原因申请暂停考试
    ↓
教师审批 → 不通过 ❌
    ↓
强制继续考试
    ↓
考试不及格
    ↓
进入补考流程
```

**权限变化:**
- 权限等级: 保持20
- 后果: 记录违规行为
- 限制: 不能再次申请暂停

### 场景6: 毕业（完成初中3年级）

```
学生在初中3年级
    ↓
参加期中考试 → 及格 ✅
    ↓
参加期末考试 → 及格 ✅
    ↓
毕业评估 → 合格 ✅
    ↓
获得毕业资格 🎓
```

**权限变化:**
- 权限等级: 30 (毕业状态)
- 可访问: 毕业档案
- 可申请: 继续教育

---

## 👨‍🏫 教师操作指南

### 查看待审批暂停申请

**API:** `GET /api/nine-year/teacher/pause-requests`

**响应示例:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "user_id": "student001",
      "exam_id": 5,
      "reason": "突发疾病需要就医",
      "status": "pending",
      "exam_type": "final",
      "subject": "math",
      "grade": "grade3"
    }
  ]
}
```

### 审批暂停申请

**API:** `POST /api/nine-year/exam/pause-approve`

**请求头:**
```
X-User-Level: 60
```

**请求体:**
```json
{
  "request_id": 1,
  "approved": true,
  "teacher_id": "teacher001",
  "comment": "情况属实，批准暂停"
}
```

### 查看学生升级状态

**API:** `GET /api/nine-year/status/{user_id}`

### 获取年级信息

**API:** `GET /api/nine-year/grades/info`

**响应示例:**
```json
{
  "success": true,
  "data": {
    "grade1": "小学1年级",
    "grade2": "小学2年级",
    "grade3": "小学3年级",
    "grade4": "小学4年级",
    "grade5": "小学5年级",
    "grade6": "小学6年级",
    "grade7": "初中1年级",
    "grade8": "初中2年级",
    "grade9": "初中3年级"
  }
}
```

---

## 👑 管理员操作指南

### 查看升级报告

**API:** `GET /api/nine-year/report`

**请求头:**
```
X-User-Level: 80
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "status_distribution": {
      "normal": 45,
      "conditional": 5,
      "restricted": 2,
      "suspended": 1,
      "repeating": 1,
      "graduated": 3
    },
    "monthly_upgrades": 10,
    "pending_pauses": 3,
    "generated_at": "2026-05-30T10:30:00"
  }
}
```

### 强制学生留级

**API:** `POST /api/nine-year/force-repeat`

**请求头:**
```
X-User-Level: 80
```

**请求体:**
```json
{
  "user_id": "student001",
  "operator_id": "admin001",
  "reason": "多次补考不及格，需要重新学习"
}
```

### 查看学生列表

**API:** `GET /api/nine-year/teacher/students`

**请求头:**
```
X-User-Level: 60
```

---

## 📊 权限等级参考

| 等级 | 角色 | 权限说明 |
|------|------|----------|
| 100 | 超级管理员 | 完全控制 |
| 80 | 管理员 | 系统配置、强制留级 |
| 60 | 教师 | 学生管理、审批暂停申请 |
| 40 | 学习监督 | 查看报告 |
| 30 | 毕业学生 | 访问毕业档案 |
| 20 | 正常学生 | 完整权限 |
| 10 | 受限学生 | 条件升级 |
| 0 | 留级学生 | 仅复习 |

---

## 📚 年级体系

### 完整9年制年级顺序

```
小学1年级 (Grade 1)
    ↓
小学2年级 (Grade 2)
    ↓
小学3年级 (Grade 3)
    ↓
小学4年级 (Grade 4)
    ↓
小学5年级 (Grade 5)
    ↓
小学6年级 (Grade 6)
    ↓
初中1年级 (Grade 7)
    ↓
初中2年级 (Grade 8)
    ↓
初中3年级 (Grade 9)
    ↓
毕业 (Graduated)
```

### 科目分数规则

**小学阶段（1-6年级）:**
- 语文、数学、英语: 100分制，60分及格
- 科学、道德与法治: 100分制，60分及格

**初中阶段（7-9年级）:**
- 语文、数学、英语: 150分制，90分及格
- 物理、化学: 100分制，60分及格
- 生物、历史、地理、政治: 100分制，60分及格

---

## 🔐 安全规则

### 数据隔离
- 学生只能查看自己的成绩
- 教师只能管理分配的学生
- 管理员可查看全部数据

### 操作审计
- 所有权限变更记录日志
- 重要操作需要确认
- 异常操作自动告警

### 访问控制
- 基于权限等级的验证
- 角色检查中间件
- API频率限制

---

## 📁 文件结构

```
MTSCOS_AI_Project/
├── nine_year_upgrade_system.py    # 升级系统核心逻辑
├── nine_year_api.py              # API服务
├── frontend/
│   └── assets/
│       └── js/
│           └── nine_year_upgrade_manager.js  # 前端管理模块
├── NINE_YEAR_UPGRADE_SYSTEM_DESIGN.md  # 设计文档
└── NINE_YEAR_USER_GUIDE.md       # 用户指南
```

---

## 🧪 测试用例

### 测试1: 完整小学升级流程

```python
# 初始化
system = NineYearUpgradeSystem()
system.init_database()

# 注册小学1年级学生
system.register_student_grade('primary_student', GradeLevel.GRADE_1)
system.confirm_grade('primary_student')

# 小学1年级 → 小学2年级
exam_id = system.create_exam_record('primary_student', 'midterm', Subject.MATH, GradeLevel.GRADE_1)
system.submit_exam(exam_id, 75)  # 及格
exam_id = system.create_exam_record('primary_student', 'final', Subject.MATH, GradeLevel.GRADE_1)
system.submit_exam(exam_id, 80)  # 及格

result = system.check_upgrade_eligibility('primary_student')
print(result['eligible'])  # True
print(result['next_grade'])  # grade2

system.perform_upgrade('primary_student')
```

### 测试2: 小学升初中过渡

```python
# 小学6年级学生
system.register_student_grade('transition_student', GradeLevel.GRADE_6)
system.confirm_grade('transition_student')

# 完成小学6年级考试
exam_id = system.create_exam_record('transition_student', 'final', Subject.MATH, GradeLevel.GRADE_6)
system.submit_exam(exam_id, 70)  # 及格

result = system.check_upgrade_eligibility('transition_student')
print(result['next_grade'])  # grade7 (初中1年级)
```

### 测试3: 初中毕业流程

```python
# 初中3年级学生
system.register_student_grade('grad_student', GradeLevel.GRADE_9)
system.confirm_grade('grad_student')

# 完成初中3年级考试
exam_id = system.create_exam_record('grad_student', 'final', Subject.MATH, GradeLevel.GRADE_9)
system.submit_exam(exam_id, 120)  # 及格

result = system.check_upgrade_eligibility('grad_student')
print(result['eligible'])  # True
print(result['reason'])  # 完成初中3年级，可以毕业！
```

### 测试4: 补考升级流程

```python
# 期中不及格
exam_id = system.create_exam_record('test_user', 'midterm', Subject.MATH, GradeLevel.GRADE_3)
system.submit_exam(exam_id, 50)  # 不及格

# 补考及格
exam_id = system.create_exam_record('test_user', 'makeup', Subject.MATH, GradeLevel.GRADE_3)
system.submit_exam(exam_id, 70)  # 及格

# 检查升级资格
result = system.check_upgrade_eligibility('test_user')
print(result['eligible'])  # True
print(result['upgrade_type'])  # 'conditional'
```

---

## 📞 技术支持

如遇到问题，请检查:

1. ✅ 数据库是否正确初始化
2. ✅ API服务是否运行在端口5002
3. ✅ 前端JavaScript是否正确引入
4. ✅ 权限等级设置是否正确
5. ✅ 用户权限是否足够

---

## 📝 注意事项

### ⚠️ 重要提醒

1. **数据库初始化**: 首次使用必须运行 `nine_year_upgrade_system.py`
2. **权限验证**: 教师和管理员操作需要设置X-User-Level头信息
3. **截止时间**: 考试必须在截止时间前完成
4. **日志记录**: 所有操作都会被记录到日志
5. **数据备份**: 定期备份数据库
6. **年级顺序**: 严格按照1-9年级顺序升级

### 🔧 故障排除

**问题1: 数据库锁定**
```bash
# 关闭所有连接后重试
python3 nine_year_upgrade_system.py
```

**问题2: API连接失败**
```bash
# 检查端口占用
lsof -i :5002

# 重启API服务
python3 nine_year_api.py
```

**问题3: 权限不足**
```javascript
// 检查请求头中的权限等级
// 教师需要: X-User-Level: 60
// 管理员需要: X-User-Level: 80
```

**问题4: 年级选择错误**
```javascript
// 确保使用正确的年级代码
// grade1-grade9
```

---

## 📈 性能优化建议

1. **数据库索引**: 为常用查询字段添加索引
2. **缓存策略**: 使用Redis缓存学生状态
3. **异步处理**: 升级操作异步执行
4. **负载均衡**: 多实例部署
5. **监控告警**: 实时监控系统状态

---

## 🎯 版本历史

### v1.1 (2026-05-30)
- ✅ 扩展为完整9年制体系
- ✅ 小学1年级至初中3年级
- ✅ 小学升初中过渡逻辑
- ✅ 毕业流程
- ✅ 阶段科目分数规则
- ✅ 更新前端管理模块

### v1.0 (2026-05-30)
- ✅ 初始版本发布
- ✅ 完整的升级逻辑
- ✅ 考试管理功能
- ✅ 权限控制系统
- ✅ API服务
- ✅ 前端管理模块

---

**最后更新**: 2026年5月30日
**版本**: 1.1
**维护团队**: MTSCOS AI Development Team
