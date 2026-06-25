# MTSCOS AI Project Directory Structure

## 项目目录结构

```
flask-app/                              # 项目根目录
├── app/                                # 应用核心代码
│   ├── ai/                             # AI引擎相关模块
│   │   ├── ai_engine_integrator.py     # AI引擎集成器
│   │   ├── auto_update_manager.py      # AI自动更新管理器
│   │   └── ...
│   ├── blueprints/                      # Flask蓝图模块
│   │   ├── placement_test_api.py       # 摸底测试API
│   │   └── ...
│   ├── routes/                          # 路由模块
│   │   ├── hardware_routes.py          # 硬件管理路由
│   │   ├── settings_routes.py          # 设置路由
│   │   ├── admin_api.py                # 管理员API
│   │   └── ...
│   ├── services/                        # 服务层
│   │   ├── ssl_manager.py              # SSL证书管理
│   │   ├── ssl_db_manager.py           # SSL数据库绑定
│   │   ├── db_encryption_manager.py    # 数据库加密管理
│   │   ├── dual_encryption_manager.py  # 双重加密管理
│   │   ├── json_sync_manager.py        # JSON同步管理
│   │   ├── user_certificate_manager.py # 用户数字证书管理
│   │   ├── placement_test_service.py   # 摸底测试服务
│   │   ├── exam_enhancement_service.py # 考试增强服务
│   │   ├── promotion_exam_service.py   # 升级考试服务
│   │   └── ...
│   ├── utils/                           # 工具模块
│   │   ├── db.py                       # 数据库工具
│   │   ├── permission_manager.py       # 权限管理
│   │   ├── session_manager.py          # 会话管理
│   │   ├── rule_manager.py             # 规则管理
│   │   ├── config_manager.py           # 配置管理
│   │   ├── monitor_manager.py          # 监控管理
│   │   ├── backup_manager.py           # 备份管理
│   │   └── ...
│   ├── middlewares/                     # 中间件
│   │   ├── access_control.py           # 访问控制中间件
│   │   └── ...
│   ├── containers/                     # 依赖注入容器
│   │   ├── user_container.py           # 用户容器
│   │   └── ...
│   ├── __init__.py                     # 应用初始化
│   └── app.py                          # 主应用入口
├── database/                           # 数据库相关
│   ├── backups/                        # 数据库备份
│   ├── migrations/                     # 数据库迁移脚本
│   └── app.db                          # 主数据库文件
├── scripts/                            # 脚本目录
│   ├── init/                           # 初始化脚本
│   │   ├── init_database.py            # 初始化数据库
│   │   ├── init_exam_system.py         # 初始化考试系统
│   │   └── ...
│   ├── maintenance/                     # 维护脚本
│   │   ├── backup_database.py          # 备份数据库
│   │   ├── clean_database.py           # 清理数据库
│   │   └── ...
│   ├── migration/                      # 迁移脚本
│   │   ├── json_to_db_migration.py     # JSON迁移到数据库
│   │   └── ...
│   └── test/                           # 测试脚本
│       ├── test_ai_system.py           # AI系统测试
│       ├── test_exam_system.py         # 考试系统测试
│       └── ...
├── tests/                              # 单元测试目录
│   ├── test_auth.py                    # 认证测试
│   ├── test_exam.py                    # 考试测试
│   └── ...
├── ssl/                                # SSL证书目录
│   ├── cert.pem                        # SSL证书
│   └── key.pem                         # SSL私钥
├── logs/                               # 日志目录
│   ├── server.log                      # 服务器日志
│   ├── system.log                      # 系统日志
│   └── ...
├── static/                             # 静态资源
│   ├── css/                            # 样式文件
│   ├── js/                             # JavaScript文件
│   ├── images/                         # 图片资源
│   └── ...
├── templates/                          # 模板目录
│   ├── admin_center.html               # 管理员中心
│   ├── exam_center.html                # 考试中心
│   ├── login.html                      # 登录页面
│   ├── logout.html                     # 退出页面
│   └── ...
├── start_server.py                     # 服务器启动脚本
├── requirements.txt                    # 依赖清单
└── README.md                           # 项目说明
```

## 目录用途说明

### 核心应用层 (app/)
| 目录 | 用途 |
|------|------|
| ai/ | AI引擎集成、自动更新、AI服务管理 |
| blueprints/ | Flask蓝图，模块化路由管理 |
| routes/ | 应用路由定义 |
| services/ | 业务逻辑服务层 |
| utils/ | 工具类和通用功能 |
| middlewares/ | Flask中间件 |
| containers/ | 依赖注入容器 |

### 数据层 (database/)
| 目录 | 用途 |
|------|------|
| backups/ | 数据库备份文件 |
| migrations/ | 数据库迁移脚本 |

### 脚本层 (scripts/)
| 目录 | 用途 |
|------|------|
| init/ | 系统初始化脚本 |
| maintenance/ | 系统维护脚本 |
| migration/ | 数据迁移脚本 |
| test/ | 测试脚本 |

### 资源层
| 目录 | 用途 |
|------|------|
| ssl/ | SSL证书存储 |
| logs/ | 日志文件存储 |
| static/ | 静态资源文件 |
| templates/ | HTML模板文件 |

## 文件命名规范

### Python文件
- 使用小写字母和下划线命名
- 文件名应描述文件功能
- 示例: `user_certificate_manager.py`, `exam_enhancement_service.py`

### HTML模板
- 使用小写字母和连字符命名
- 示例: `admin_center.html`, `exam_center.html`

### 测试文件
- 使用 `test_` 前缀
- 示例: `test_ai_system.py`, `test_exam_system.py`

## 新增文件管理

当新增文件时，请按照以下规则放置：

1. **核心功能** → `app/` 下对应子目录
2. **一次性脚本** → `scripts/` 下对应子目录
3. **单元测试** → `tests/` 目录
4. **静态资源** → `static/` 或 `templates/` 目录
5. **配置文件** → 项目根目录

## 数据库表结构映射

### 用户相关表
- `users` - 用户信息
- `user_roles` - 用户角色关联
- `user_permissions` - 用户权限
- `user_sessions` - 用户会话
- `user_certificates` - 用户数字证书

### 考试相关表
- `exams` - 考试信息
- `questions` - 题目信息
- `exam_questions` - 考试-题目关联
- `exam_sessions` - 考试会话
- `exam_answers` - 考试答案
- `exam_results` - 考试成绩
- `placement_tests` - 摸底测试
- `placement_reports` - 摸底测试报告

### 系统管理表
- `system_settings` - 系统配置
- `system_logs` - 系统日志
- `ssl_certificates` - SSL证书信息
- `json_data` - JSON数据存储
- `backup_records` - 备份记录

### 学习进度表
- `learning_progress` - 学习进度
- `mistake_notebook` - 错题本
- `exam_rankings` - 考试排名
- `certificates` - 证书颁发

## 注意事项

1. 不要在项目根目录放置过多文件
2. 所有Python模块应放在 `app/` 目录下
3. 数据库文件应放在 `database/` 目录或根目录
4. 日志文件应放在 `logs/` 目录
5. 保持目录结构清晰，便于维护