# 🧪 MTSCOS AI 测试账号指南

本文档提供MTSCOS系统的测试账号信息，供开发者、测试人员和贡献者测试系统功能。

## 📋 测试账号列表

所有测试账号的**统一密码**: `Test@2026`

| 用户名 | 角色 | 角色名称 | 权限等级 | 邮箱 |
|--------|------|---------|---------|------|
| `test_student` | student | 学生 | 1 | student@mtscos.test |
| `test_parent` | parent | 家长 | 1 | parent@mtscos.test |
| `test_designer` | designer | 设计师 | 1 | designer@mtscos.test |
| `test_teacher` | teacher | 教师 | 2 | teacher@mtscos.test |
| `test_proctor` | exam_proctor | 监考员 | 2 | proctor@mtscos.test |
| `test_qm` | question_manager | 题库管理员 | 3 | qm@mtscos.test |
| `test_aim` | ai_manager | AI管理员 | 3 | aim@mtscos.test |
| `test_cm` | cluster_manager | 集群管理员 | 3 | cm@mtscos.test |
| `test_admin` | admin | 系统管理员 | 4 | admin@mtscos.test |
| `test_superadmin` | super_admin | 超级管理员 | 5 | superadmin@mtscos.test |
| `test_hwadmin` | hardware_admin | 硬件管理员 | 6 | hwadmin@mtscos.test |

## 🔐 角色权限说明

### 权限等级说明
- **等级 0 (guest)**: 访客权限，仅可浏览公开内容
- **等级 1 (student/parent/designer)**: 基础用户权限
- **等级 2 (teacher/exam_proctor)**: 中级管理权限
- **等级 3 (question_manager/ai_manager/cluster_manager)**: 高级管理权限
- **等级 4 (admin)**: 系统管理权限
- **等级 5 (super_admin)**: 超级管理权限（完整系统控制）
- **等级 6 (hardware_admin)**: 最高权限（需硬件加密狗）

### 各角色功能范围

#### 👨‍🎓 学生 (student)
- ✅ 查看个人资料
- ✅ 参加考试
- ✅ 查看考试结果
- ✅ 查看学习记录
- ✅ 使用AI聊天
- ✅ 查看学习资料（K12和成人教育）

#### 👨‍👩‍👧 家长 (parent)
- ✅ 查看个人资料
- ✅ 查看孩子考试信息
- ✅ 查看孩子学习记录和成绩
- ✅ 使用AI聊天

#### 🎨 设计师 (designer)
- ✅ 查看个人资料
- ✅ 设计试题
- ✅ 使用AI聊天
- ✅ 管理设计模板

#### 👨‍🏫 教师 (teacher)
- ✅ 学生权限全部功能
- ✅ 管理学生
- ✅ 管理作业和考试
- ✅ 管理题库
- ✅ 查看成绩报表
- ✅ AI聊天高级功能

#### 🕵️ 监考员 (exam_proctor)
- ✅ 监控考试过程
- ✅ 查看考试状态
- ✅ 管理考试会话
- ✅ 查看考试结果

#### 📚 题库管理员 (question_manager)
- ✅ 管理题库
- ✅ 管理题目分类
- ✅ 导入/导出题目
- ✅ 查看题目统计
- ✅ AI聊天高级功能

#### 🤖 AI管理员 (ai_manager)
- ✅ 管理AI模型
- ✅ 管理AI集群
- ✅ 查看AI状态和性能
- ✅ 管理AI配置
- ✅ AI聊天管理员功能

#### ☁️ 集群管理员 (cluster_manager)
- ✅ 管理集群节点
- ✅ 管理端口
- ✅ 查看集群状态
- ✅ 管理负载均衡
- ✅ 资源监控

#### 🔧 系统管理员 (admin)
- ✅ 教师+题库管理员功能
- ✅ 管理用户
- ✅ 管理系统设置
- ✅ 查看系统日志
- ✅ 管理权限
- ✅ 数据库备份

#### 👑 超级管理员 (super_admin)
- ✅ **所有功能权限**
- ✅ 完整系统控制
- ✅ 用户审批
- ✅ 系统升级管理

#### 🔒 硬件管理员 (hardware_admin)
- ✅ **最高权限**
- ✅ 硬件级管理
- ✅ 需硬件加密狗验证

## 🌐 测试访问地址

### 管理后台
```
http://localhost:8888/admin_app/login
```

### 用户前端
```
http://localhost:8888/login
```

### API文档
```
http://localhost:8888/api/system/docs
```

## 🧪 测试场景建议

### 基础功能测试
1. **学生考试流程**: 使用 `test_student` 登录，参加考试，查看结果
2. **教师管理**: 使用 `test_teacher` 登录，管理学生和考试
3. **题库管理**: 使用 `test_qm` 登录，管理题目

### AI功能测试
1. **AI题目生成**: 使用 `test_superadmin` 或 `test_admin` 访问 `/admin/ai-question-generator`
2. **AI学习路径**: 使用 `test_superadmin` 访问 `/admin/ai-study-path`
3. **AI试卷组卷**: 使用 `test_superadmin` 访问 `/admin/ai-exam-composer`
4. **学生成绩分析**: 使用 `test_superadmin` 访问 `/admin/student-analytics`

### 权限测试
1. 尝试用低权限用户访问高权限页面
2. 验证各角色的功能边界
3. 测试权限继承关系

### 集群管理测试
1. 使用 `test_cm` 查看集群状态
2. 使用 `test_aim` 管理AI模型

## 🚀 快速测试流程

```bash
# 1. 启动服务
python app.py --port 8888

# 2. 打开浏览器访问管理后台
open http://localhost:8888/admin_app/login

# 3. 使用超级管理员登录
用户名: test_superadmin
密码: Test@2026

# 4. 测试各功能模块
# - AI题目生成器
# - AI学习路径推荐
# - AI试卷组卷
# - 学生成绩分析仪表盘
```

## 📝 使用注意事项

1. **测试环境**: 这些账号仅用于本地测试环境
2. **数据安全**: 测试账号密码公开，请不要在生产环境使用
3. **权限验证**: 各角色权限已预设，可以验证权限控制是否正常
4. **数据隔离**: 测试数据不会影响正式数据

## 🎯 测试清单

### 用户认证
- [ ] 用户登录/登出功能
- [ ] 密码验证
- [ ] 会话管理

### 权限系统
- [ ] 角色权限控制
- [ ] 页面访问权限
- [ ] API访问权限

### 考试系统
- [ ] 创建考试
- [ ] 参加考试
- [ ] 查看结果
- [ ] 成绩统计

### AI功能
- [ ] AI题目生成
- [ ] AI学习路径推荐
- [ ] AI试卷组卷
- [ ] 学生成绩分析

### 管理功能
- [ ] 用户管理
- [ ] 题库管理
- [ ] 系统设置
- [ ] 日志查看

## 📞 问题反馈

如发现任何问题，请在GitHub上创建Issue：
- [创建Bug报告](../../issues/new?template=bug_report.md)
- [提出功能建议](../../issues/new?template=feature_request.md)

---

**MTSCOS AI** - 让考试更智能，让学习更高效 🚀