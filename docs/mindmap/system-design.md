# MTSCOS AI 系统设计思维导图

> 更新日期: 2026-07-11
> 📖 **说明**: 本文件使用Mermaid mindmap语法编写，GitHub原生支持渲染。如遇渲染问题，请查看文档末尾的Flowchart版本。

---

## 🗺️ 1. 系统架构总览

```mermaid
mindmap
  root((MTSCOS AI<br/>智能考试系统))
    🏗️ 架构层
      前端展示层
        管理后台 (Admin UI)
        用户端 (Student/Teacher)
        移动端 (PWA)
        API文档
      服务层
        Flask应用 (API路由)
        业务服务 (Services)
        AI引擎 (AI Engines)
        中间件 (Middlewares)
      数据层
        分布式数据库 (SQLite)
        缓存层 (Redis/Memory)
        文件存储
      基础设施层
        Git自动同步
        自动修复引擎
        系统健康监控
        性能监控
    🧠 AI智能层
      AI员工体系
        41+ AI员工
        6+ AI Agent
        590+ 检索模型
      AI引擎
        自适应学习引擎
        知识图谱引擎
        错题本智能引擎
        学习预测分析引擎
        AI助教答疑引擎
      AI模型库
        GPT-4/Claude-3/Qwen
        Llama-3/Gemini/DeepSeek
    🔐 安全层
      企业级防火墙
        SQL注入防护
        XSS防护
        命令注入防护
        SSRF防护
        API限流
      权限管理
        RBAC权限体系
        50+权限规则
        6级访问控制
        审计日志
    📚 业务层
      题库系统
        37000+题目
        7种题型
        AI题目生成
      考试系统
        智能组卷
        在线考试
        成绩分析
      学习系统
        学习路径推荐
        智能错题本
        学习助手
      管理系统
        集群管理
        端口管理
        数据库管理
```

---

## 🤖 2. AI引擎模块图

```mermaid
mindmap
  root((AI引擎体系))
    🧑‍💼 AI员工体系
      安全类员工
        代码错误修复专家
        数据安全专家
        安全管理专家
      教育类员工
        高考真题扩容专家
        智能出题拟题专家
        AI题目讲解分析专家
        九年制义务教育辅导员
      运维类员工
        系统监控专家
        数据库管理专家
        备份恢复专家
        性能优化Agent
      开发类员工
        代码优化与系统升级专家
        前端优化专家
        CDN和图标修复专家
      诊断类员工
        诊断修复AI员工
        单选题选项修复专家
        音频播放修复专家
    🤖 AI Agent体系
      智能调度器 (SCHEDULER)
      系统监控Agent (MONITOR)
      数据备份Agent (BACKUP)
      日志分析Agent (LOG)
      数据清理Agent (CLEANUP)
      性能优化Agent (OPTIMIZE)
    🧠 AI能力矩阵
      题目生成
        文本转题目
        科目自动检测
        关键点提取
      学习推荐
        错题分析
        薄弱环节识别
        知识图谱
      智能组卷
        难度均衡
        知识覆盖率
        质量评分
      智能答疑
        多科目解答
        会话管理
        知识库搜索
      学习分析
        成绩分析仪表盘
        学习趋势预测
        学习报告生成
```

---

## 🗄️ 3. 数据库分布图

```mermaid
mindmap
  root((分布式数据库架构))
    📊 核心数据库
      auth.db
        users表
        roles表
        permissions表
        sessions表
      exam.db
        exams表
        exam_questions表
        exam_results表
      question.db
        questions表
        ai_generated_questions表
        question_tags表
      learning.db
        learning_records表
        study_paths表
        knowledge_points表
    ⚙️ 系统数据库
      system.db
        configs表
        versions表
        logs表
      admin.db
        admin_users表
        admin_logs表
      log.db
        system_logs表
        audit_logs表
        error_logs表
    🤖 AI引擎数据库
      ai.db
        ai_models表
        ai_clusters表
        ai_results表
      api_management.db
        api_endpoints表
        api_stats表
      routes_management.db
        routes表
        route_stats表
      search_models.db
        search_models表
        model_performance表
    🌐 业务数据库
      proctor.db
        proctor_sessions表
        monitoring_data表
      notification.db
        notifications表
        push_queue表
        user_devices表
      cluster.db
        cluster_nodes表
        node_status表
        load_balancing表
```

---

## 🔐 4. 用户角色权限图

```mermaid
mindmap
  root((RBAC权限体系))
    📊 角色层级
      等级1 - 基础用户
        guest (访客)
        student (学生)
        parent (家长)
        designer (设计师)
      等级2 - 教育用户
        teacher (教师)
        exam_proctor (监考员)
      等级3 - 管理用户
        question_manager (题库管理员)
        ai_manager (AI管理员)
        cluster_manager (集群管理员)
      等级4 - 系统管理员
        admin (系统管理员)
      等级5 - 超级管理员
        super_admin (超级管理员)
      等级6 - 硬件管理员
        hardware_admin (硬件管理员)
    🎯 权限模块
      题库管理权限
        查看题目
        添加题目
        修改题目
        删除题目
        AI生成题目
      考试管理权限
        创建考试
        修改考试
        删除考试
        查看成绩
        批量组卷
      AI引擎权限
        管理AI模型
        监控AI节点
        配置AI参数
        查看AI统计
      系统管理权限
        管理用户
        管理角色
        系统配置
        系统监控
        日志查看
      集群管理权限
        节点管理
        负载均衡
        端口管理
        健康检查
    📋 审计日志
      操作记录
        登录/登出
        数据修改
        权限变更
      实时审计
        异常检测
        安全告警
        行为分析
```

---

## 🏗️ 5. 模块依赖关系图

```mermaid
mindmap
  root((模块依赖关系))
    🚀 启动模块
      db_config_loader
        加载数据库配置
        初始化连接池
      core_init
        初始化Flask应用
        注册中间件
        初始化扩展
      module_loader
        加载API路由
        加载AI引擎
        加载业务服务
    📡 API路由模块
      auth_api
        登录/登出
        权限验证
      exam_api
        考试管理
        成绩查询
      ai_api
        题目生成
        学习推荐
        智能组卷
      enhancement_api
        系统监控
        数据库管理
        集群管理
    🧪 服务模块
      ai_question_generation_service
        题目生成逻辑
        AI调用封装
      ai_study_path_service
        学习路径算法
        知识图谱构建
      ai_exam_composition_service
        组卷算法
        质量评估
      db_performance_service
        性能监控
        索引优化
      cluster_service
        节点管理
        负载均衡
    🛠️ 工具模块
      redis_manager
        Redis连接管理
        内存缓存降级
      db.py
        数据库连接池
        查询封装
      api_response.py
        统一响应格式
        错误处理
      permission.py
        权限装饰器
        角色验证
```

---

## 📊 6. 数据流向图

```mermaid
mindmap
  root((数据流向))
    📥 输入数据流
      用户请求
        HTTP请求
        API调用
        WebSocket连接
      AI输入
        文本内容
        错题数据
        学习记录
      系统输入
        配置文件
        环境变量
        数据库初始化
    🔄 处理流程
      请求处理
        路由分发
        权限验证
        参数校验
      业务处理
        数据查询
        AI调用
        逻辑计算
      响应生成
        数据格式化
        缓存处理
        响应返回
    📤 输出数据流
      用户响应
        HTML页面
        JSON数据
        文件下载
      AI输出
        生成题目
        学习推荐
        分析报告
      系统输出
        日志记录
        审计记录
        监控数据
    💾 数据存储
      数据库写入
        用户数据
        业务数据
        系统数据
      缓存写入
        热点数据
        会话数据
        配置数据
      文件存储
        上传文件
        生成报告
        备份文件
```

---

## 🎨 7. UI设计体系图

```mermaid
mindmap
  root((UI设计体系))
    🎨 设计系统
      颜色系统
        主色调 (Primary)
        语义色 (Success/Warning/Danger/Info)
        背景色 (Page/Card/Dark)
        文字色 (Primary/Secondary/Tertiary)
      字体系统
        字体家族
        字体大小 (XS/SM/BASE/LG/XL)
        字体粗细
      间距系统
        8px基准
        间距变量 (Spacing-1~10)
      圆角系统
        基础圆角 (SM/BASE/ROUND/XL/2XL)
      阴影系统
        阴影变量 (SM/BASE/MD/LG)
    🧩 UI组件
      按钮 (Button)
        主按钮/次按钮/轮廓按钮/文字按钮
        成功/警告/错误按钮
        大小变体 (SM/BASE/LG)
      卡片 (Card)
        基础卡片/阴影卡片/毛玻璃卡片
        卡片头部/主体/底部
      表单 (Form)
        输入框/选择框/文本域
        表单组/表单标签
        表单验证
      图表 (Chart)
        柱状图/折线图/饼图
        统计卡片/图表容器
      导航 (Navigation)
        侧边栏/顶部导航/面包屑
        移动端抽屉菜单
    🎯 主题适配
      浅色主题
        默认主题/紧凑主题/极简主题
      深色主题
        暗色主题/全屏暗色主题
      响应式设计
        桌面端 (1200px+)
        平板端 (768px-1200px)
        移动端 (<768px)
```

---

## 📊 Flowchart兼容版本

```mermaid
graph TD
    A[MTSCOS AI智能考试系统] --> B[架构层]
    A --> C[AI智能层]
    A --> D[安全层]
    A --> E[业务层]
    
    B --> B1[前端展示层]
    B --> B2[服务层]
    B --> B3[数据层]
    B --> B4[基础设施层]
    
    C --> C1[AI员工体系]
    C --> C2[AI引擎]
    C --> C3[AI模型库]
    
    D --> D1[企业级防火墙]
    D --> D2[权限管理]
    
    E --> E1[题库系统]
    E --> E2[考试系统]
    E --> E3[学习系统]
    E --> E4[管理系统]
    
    C1 --> C1a[41+ AI员工]
    C1 --> C1b[6+ AI Agent]
    C1 --> C1c[590+ 检索模型]
    
    C2 --> C2a[自适应学习引擎]
    C2 --> C2b[知识图谱引擎]
    C2 --> C2c[错题本智能引擎]
    C2 --> C2d[学习预测分析引擎]
    C2 --> C2e[AI助教答疑引擎]
    
    C3 --> C3a[GPT-4]
    C3 --> C3b[Claude-3]
    C3 --> C3c[Qwen]
    C3 --> C3d[Llama-3]
    
    style A fill:#8B5CF6,color:#fff
    style B fill:#3B82F6,color:#fff
    style C fill:#10B981,color:#fff
    style D fill:#EF4444,color:#fff
    style E fill:#F59E0B,color:#fff
```

---

> 📖 **提示**: 在GitHub上查看此文档时，Mermaid思维导图会自动渲染为交互式图形。
> 🎨 设计遵循项目《设计规范》中的颜色变量和主题风格。
> ⚠️ **兼容性**: 如果mindmap无法正常渲染，Flowchart版本提供了同等信息的可视化展示。