# 9年制学生升级逻辑系统设计文档

## 📋 系统概述

本文档定义了9年制义务教育系统中学生升级的完整逻辑，包括各种考试情况的处理、年级变化规则和权限控制机制。

---

## 🎯 核心概念

### 1. 年级级别 (Grade Level)
**完整9年制体系（小学1年级至初中3年级）**

**小学阶段（1-6年级）**
- **小学1年级（Grade 1）** - 义务教育入口年级
- **小学2年级（Grade 2）**
- **小学3年级（Grade 3）**
- **小学4年级（Grade 4）**
- **小学5年级（Grade 5）**
- **小学6年级（Grade 6）**

**初中阶段（7-9年级）**
- **初中1年级（Grade 7）**
- **初中2年级（Grade 8）**
- **初中3年级（Grade 9）** - 义务教育终点

### 2. 考试类型 (Exam Type)
- **期中考试** - 4月30日前完成
- **期末考试** - 7月31日前完成
- **补考** - 8月20日前完成（针对不及格学生）
- **平时测试** - 日常练习

### 3. 考试状态 (Exam Status)
- **未开始** - 考试尚未开始
- **进行中** - 正在考试
- **已暂停** - 考试被暂停（需教师审批）
- **已完成** - 考试已完成
- **不及格** - 得分低于60%
- **及格** - 得分≥60%

### 4. 及格标准
- 期中考试：≥60% 及格
- 期末考试：≥60% 及格
- 补考：≥60% 及格

---

## 📊 升级逻辑流程

### 场景1: 正常升级（期中+期末都及格）

```
当前年级学生
    ↓
期中考试及格 ✅
    ↓
期末考试及格 ✅
    ↓
自动升级到下一年级 ✅
```

**条件**:
- 期中考试成绩 ≥ 60%
- 期末考试成绩 ≥ 60%

**结果**:
- ✅ 自动升级到下一年级
- ✅ 获得参加下一年级期中考的资格
- ✅ 记录升级历史

**年级流转示例**:
- 小学1年级 → 小学2年级
- 小学6年级 → 初中1年级
- 初中3年级 → 毕业

---

### 场景2: 考试不及格但补考及格

```
当前年级学生
    ↓
期中考试不及格 ❌
    ↓
或
期末考试不及格 ❌
    ↓
参加补考
    ↓
补考及格 ✅
    ↓
条件性升级到下一年级 ⚠️
```

**条件**:
- 期中考试或期末考试 < 60%
- 补考成绩 ≥ 60%

**结果**:
- ⚠️ 有条件升级（需教师审批）
- ⚠️ 标记为"补考升级"
- ⚠️ 需要额外学习任务

**权限限制**:
- 只能参加基础难度考试
- 不能参加竞赛类活动
- 需完成补修课程

---

### 场景3: 补考不及格

```
当前年级学生
    ↓
期中考试不及格 ❌
    ↓
或
期末考试不及格 ❌
    ↓
参加补考
    ↓
补考仍不及格 ❌❌
    ↓
暂停考试资格 ⏸️
    ↓
留级或特殊处理
```

**条件**:
- 期中考试或期末考试 < 60%
- 补考成绩 < 60%

**结果**:
- ⛔ 暂停考试审批（需教师/管理员审批）
- ⛔ 留级或参加特殊培训
- ⛔ 需要重新参加该年级考试
- ⛔ 限制系统访问权限

**权限限制**:
- 不能参加任何考试
- 不能进入学习系统高级内容
- 只能访问复习材料
- 需要教师一对一辅导

---

### 场景4: 暂停考试审批不通过

```
学生申请暂停考试
    ↓
教师审批
    ↓
审批不通过 ❌
    ↓
强制继续考试
    ↓
考试不及格
    ↓
进入补考流程
```

**条件**:
- 学生因特殊原因申请暂停考试
- 教师认为理由不充分
- 审批未通过

**结果**:
- ⛔ 必须继续参加考试
- ⛔ 不能获得额外时间
- ⛔ 超时视为不及格
- ⛔ 记录违规行为

**权限限制**:
- 不能申请第二次暂停
- 不能申请特殊照顾
- 记录到学生档案

---

### 场景5: 暂停考试审批通过

```
学生申请暂停考试
    ↓
教师审批
    ↓
审批通过 ✅
    ↓
考试暂停
    ↓
特殊情况处理
    ↓
恢复考试
    ↓
继续考试流程
```

**条件**:
- 学生因不可抗力申请暂停考试
- 教师/管理员批准
- 合理理由（如生病、事故）

**结果**:
- ⏸️ 考试暂停
- ⏸️ 延长截止时间
- ⏸️ 记录暂停原因
- ✅ 恢复后可继续考试

**权限变化**:
- 暂停期间不能访问考试
- 需重新申请考试资格
- 可能需要补交证明材料

---

## 🔐 权限层级定义

### 用户权限等级（从高到低）

| 等级 | 角色 | 权限说明 |
|------|------|----------|
| 100 | 超级管理员 | 完全控制，可审批任何操作 |
| 80 | 管理员 | 系统配置管理 |
| 60 | 教师 | 审批考试暂停、管理学生 |
| 40 | 学习监督 | 查看学生状态、提交报告 |
| 20 | 正常学生（所有年级） | 完整学习考试权限 |
| 10 | 受限学生（补考升级） | 受限考试权限 |
| 0 | 留级学生 | 仅复习权限 |

### 权限控制规则

#### 学生权限矩阵

| 状态 | 学习系统 | 考试系统 | 补考资格 | 升级申请 |
|------|----------|----------|----------|----------|
| 正常升级 | ✅ 全部 | ✅ 全部 | ❌ 无需 | ❌ 自动 |
| 补考升级 | ⚠️ 基础 | ⚠️ 基础难度 | ✅ 有 | ❌ 条件 |
| 补考不及格 | ⚠️ 复习 | ❌ 无资格 | ❌ 无 | ❌ 无 |
| 暂停通过 | ⏸️ 暂停 | ⏸️ 暂停 | ✅ 延期 | ⏸️ 待定 |
| 暂停不通过 | ✅ 正常 | ✅ 强制 | ❌ 无 | ❌ 无 |

---

## 🎯 升级判断算法

### 伪代码

```python
def check_upgrade_eligibility(user_id):
    current_grade = get_student_grade(user_id)
    midterm_result = get_exam_result(user_id, 'midterm')
    final_result = get_exam_result(user_id, 'final')
    
    # 情况1: 都及格
    if midterm_result >= 60 and final_result >= 60:
        return {
            'status': 'ELIGIBLE',
            'upgrade_type': 'NORMAL',
            'permissions': FULL_PERMISSIONS
        }
    
    # 情况2: 需要补考
    elif midterm_result < 60 or final_result < 60:
        makeup_result = get_exam_result(user_id, 'makeup')
        
        # 补考及格
        if makeup_result >= 60:
            return {
                'status': 'CONDITIONAL_ELIGIBLE',
                'upgrade_type': 'MAKEUP_PASSED',
                'permissions': LIMITED_PERMISSIONS
            }
        
        # 补考不及格
        else:
            return {
                'status': 'NOT_ELIGIBLE',
                'upgrade_type': 'FAILED',
                'permissions': RESTRICTED_PERMISSIONS
            }
    
    # 情况3: 暂停考试
    elif has_paused_exam(user_id):
        pause_approved = check_pause_approval(user_id)
        
        if pause_approved:
            return {
                'status': 'PAUSED',
                'upgrade_type': 'PAUSE_APPROVED',
                'permissions': SUSPENDED_PERMISSIONS
            }
        else:
            return {
                'status': 'PAUSE_DENIED',
                'upgrade_type': 'FORCE_CONTINUE',
                'permissions': NORMAL_PERMISSIONS
            }
```

---

## 📝 状态转换图

```
[正常状态]
    │
    ├─→ [期中不及格] ─→ [补考] ─→ [补考及格] ─→ [条件升级]
    │                                    │
    │                                    └→ [补考不及格] ─→ [留级]
    │
    ├─→ [期末不及格] ─→ [补考] ─→ [补考及格] ─→ [条件升级]
    │                                    │
    │                                    └→ [补考不及格] ─→ [留级]
    │
    ├─→ [申请暂停] ─→ [审批通过] ─→ [暂停状态] ─→ [恢复] ─→ [继续流程]
    │           │
    │           └→ [审批不通过] ─→ [强制继续] ─→ [超时不及格] ─→ [留级]
    │
    └→ [都及格] ─→ [正常升级]
```

---

## 🎨 路由设计

### 学生路由

| 路由 | 方法 | 权限要求 | 说明 |
|------|------|----------|------|
| /api/grade/status | GET | 学生 | 获取当前年级和状态 |
| /api/grade/upgrade-check | GET | 学生 | 检查升级资格 |
| /api/exam/start | POST | 学生(正常) | 开始考试 |
| /api/exam/pause-request | POST | 学生(正常) | 申请暂停考试 |
| /api/exam/submit | POST | 学生(正常) | 提交考试 |
| /api/learning/access | GET | 学生(受限) | 访问学习内容 |

### 教师路由

| 路由 | 方法 | 权限要求 | 说明 |
|------|------|----------|------|
| /api/teacher/pause-approve | POST | 教师 | 审批暂停申请 |
| /api/teacher/upgrade-review | GET | 教师 | 查看升级学生列表 |
| /api/teacher/override-grade | POST | 教师 | 特殊调整年级 |
| /api/student/status | GET | 教师 | 查看学生状态 |

### 管理员路由

| 路由 | 方法 | 权限要求 | 说明 |
|------|------|----------|------|
| /api/admin/force-upgrade | POST | 管理员 | 强制升级学生 |
| /api/admin/force-repeat | POST | 管理员 | 强制留级学生 |
| /api/admin/permission-override | POST | 超级管理员 | 权限覆盖 |
| /api/admin/grade-history | GET | 管理员 | 查看升级历史 |

---

## 📊 数据库设计

### 主要数据表

#### 1. 学生年级表 (nine_year_grades)
```sql
CREATE TABLE nine_year_grades (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    current_grade VARCHAR(20) NOT NULL,
    grade_status VARCHAR(20) DEFAULT 'normal',
    permission_level INTEGER DEFAULT 20,
    is_confirmed BOOLEAN DEFAULT FALSE,
    confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);
```

#### 2. 考试记录表 (nine_year_exams)
```sql
CREATE TABLE nine_year_exams (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    exam_type VARCHAR(20) NOT NULL,
    subject VARCHAR(20) NOT NULL,
    grade VARCHAR(20) NOT NULL,
    score DECIMAL(5,2),
    max_score DECIMAL(5,2) DEFAULT 100,
    status VARCHAR(20) DEFAULT 'not_started',
    is_paused BOOLEAN DEFAULT FALSE,
    pause_reason TEXT,
    pause_approved BOOLEAN DEFAULT FALSE,
    pause_approved_by TEXT,
    pause_approved_at TIMESTAMP,
    pause_deadline TIMESTAMP,
    deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    UNIQUE(user_id, exam_type, subject, grade)
);
```

#### 3. 升级历史表 (nine_year_upgrade_history)
```sql
CREATE TABLE nine_year_upgrade_history (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    from_grade VARCHAR(20),
    to_grade VARCHAR(20) NOT NULL,
    upgrade_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    reason TEXT,
    approved_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. 暂停申请表 (nine_year_pause_requests)
```sql
CREATE TABLE nine_year_pause_requests (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    exam_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    approved_by TEXT,
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_id) REFERENCES nine_year_exams(id)
);
```

#### 5. 权限记录表 (nine_year_permission_logs)
```sql
CREATE TABLE nine_year_permission_logs (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    action VARCHAR(50) NOT NULL,
    resource VARCHAR(50) NOT NULL,
    old_permission INTEGER,
    new_permission INTEGER,
    reason TEXT,
    operator_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎯 关键业务规则

### 规则1: 自动升级时间
- **时间**: 每年9月1日
- **条件**: 8月20日前完成所有考试
- **执行**: 系统自动执行

### 规则2: 补考时间窗口
- **开始**: 8月1日
- **截止**: 8月20日 23:59:59
- **资格**: 期中或期末不及格

### 规则3: 暂停考试限制
- **申请次数**: 每学期最多1次
- **审批时间**: 24小时内
- **暂停时长**: 最多7天

### 规则4: 权限降级触发
- **触发条件**: 补考不及格
- **降级程度**: 从"正常"降至"受限"
- **恢复条件**: 教师特批或重修通过

### 规则5: 年级锁定
- **锁定时间**: 确认年级后
- **解锁条件**: 学期结束或特殊审批
- **例外**: 教师可临时调整

### 规则6: 科目和分数配置
- **小学1-6年级**: 所有科目满分100分
- **初中7-9年级**:
  - 语文、数学、英语：满分150分
  - 物理、化学：满分100分
  - 其他科目：满分100分

---

## 📈 监控指标

### 升级成功率
- 目标: ≥95%
- 计算: (升级人数 / 应升级人数) × 100%

### 补考通过率
- 目标: ≥80%
- 计算: (补考及格人数 / 补考人数) × 100%

### 暂停申请批准率
- 目标: ≥70%
- 计算: (批准数 / 申请数) × 100%

### 平均升级耗时
- 目标: < 5分钟
- 计算: 系统自动处理

---

## 🔒 安全考虑

### 数据隔离
- 学生只能查看自己的成绩和状态
- 教师只能管理自己的学生
- 管理员可查看全部但不能修改

### 操作审计
- 所有权限变更记录到日志
- 重要操作需要二次确认
- 异常操作自动告警

### 权限验证
- JWT Token验证
- 角色检查中间件
- API访问频率限制

---

## 📝 实施优先级

### 第一阶段（核心功能）
1. ✅ 年级状态管理
2. ✅ 考试状态跟踪
3. ✅ 基础升级逻辑

### 第二阶段（增强功能）
1. 🔄 补考管理
2. 🔄 暂停考试审批
3. 🔄 条件升级处理

### 第三阶段（高级功能）
1. ⏳ 权限动态调整
2. ⏳ 升级预测分析
3. ⏳ 自动化学年处理

---

## 📞 支持与反馈

如有问题或建议，请联系系统管理员。

**最后更新**: 2026年5月30日
**版本**: 1.1
**状态**: 实施中
**更新说明**: 修正为从小学1年级开始的完整9年制体系
