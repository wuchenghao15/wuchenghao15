# 考试系统移动端APP

基于React Native (Expo) 构建的移动端考试系统APP，支持iOS和Android平台。

## 功能特性

### 核心功能
- **用户认证**：登录、注册功能
- **考试中心**：浏览和参加考试
- **考试答题**：单选/多选题型，计时器，答题进度跟踪
- **成绩查看**：详细的考试成绩分析
- **错题本**：错题复习和巩固

### AI功能
- **个性化推荐**：基于学习记录智能推荐学习内容
- **学习分析**：分析学习优势和薄弱环节
- **学习计划**：AI生成个性化学习计划
- **智能建议**：提供学习方向和建议

## 技术栈

- **框架**：React Native + Expo
- **导航**：React Navigation
- **状态管理**：React hooks
- **网络请求**：Axios
- **样式**：React Native StyleSheet

## 项目结构

```
exam_app/
├── App.js                 # 主应用入口
├── index.js              # Expo入口文件
├── package.json          # 项目配置
├── app.json             # Expo配置
├── screens/             # 页面组件
│   ├── LoginScreen.js           # 登录页面
│   ├── HomeScreen.js           # 首页
│   ├── ExamListScreen.js       # 考试列表
│   ├── ExamScreen.js           # 答题页面
│   ├── ResultScreen.js         # 成绩页面
│   ├── ErrorQuestionScreen.js  # 错题页面
│   ├── ProfileScreen.js        # 个人中心
│   └── AIRecommendationScreen.js # AI推荐页面
├── services/            # API服务
│   └── api.js          # API接口封装
├── components/          # 通用组件
└── assets/              # 静态资源
```

## 安装和运行

### 前置要求
- Node.js >= 16.0.0
- npm 或 yarn
- Expo CLI
- iOS Simulator (Mac) 或 Android Studio (Windows/Mac)

### 安装步骤

1. 进入项目目录
```bash
cd exam_app
```

2. 安装依赖
```bash
npm install
```

3. 启动开发服务器
```bash
npm start
```

4. 运行iOS版本
```bash
npm run ios
```

5. 运行Android版本
```bash
npm run android
```

## API配置

APP默认连接本地服务器 `http://localhost:5000/api`。

如需修改API地址，编辑 `services/api.js` 文件：

```javascript
const API_BASE_URL = 'http://your-server:5000/api';
```

## 页面说明

### 登录页面 (LoginScreen)
- 用户名密码输入
- 登录按钮
- 注册入口

### 首页 (HomeScreen)
- 用户问候信息
- 学习统计概览
- 快捷操作入口
- 最近考试记录
- AI学习助手推荐

### 考试列表 (ExamListScreen)
- 考试项目列表
- 难度标签
- 题目数量和时长
- 开始考试按钮

### 答题页面 (ExamScreen)
- 题目展示区域
- 选项列表
- 上一题/下一题导航
- 答题进度条
- 计时器
- 提交试卷按钮

### 成绩页面 (ResultScreen)
- 成绩分数展示
- 答题统计
- AI分析和建议
- 返回和复习入口

### 错题页面 (ErrorQuestionScreen)
- 错题列表
- 错误次数统计
- 正确答案展示
- 立即复习按钮

### 个人中心 (ProfileScreen)
- 用户信息展示
- 学习统计数据
- 功能菜单
- 退出登录

### AI推荐页面 (AIRecommendationScreen)
- 个性化推荐内容
- 今日/本周学习计划
- 学习优势和薄弱分析
- AI建议

## 后端API接口

APP需要以下后端API支持：

### 认证接口
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册

### 考试接口
- `GET /api/exams` - 获取考试列表
- `GET /api/exams/:id` - 获取考试详情
- `POST /api/exams/:id/start` - 开始考试
- `POST /api/exams/:id/answer` - 提交答案
- `POST /api/exams/:id/finish` - 结束考试
- `GET /api/exams/:id/result` - 获取成绩

### 错题接口
- `GET /api/error-questions/:userId` - 获取用户错题列表
- `GET /api/error-questions/detail/:id` - 获取错题详情
- `POST /api/error-questions/:id/review` - 标记已复习

### AI接口
- `GET /api/ai/recommendations/:userId` - 获取个性化推荐
- `GET /api/ai/analysis/:userId` - 获取学习分析
- `GET /api/ai/study-plan/:userId` - 获取学习计划

## 打包发布

### iOS
```bash
expo build:ios
```

### Android
```bash
expo build:android
```

或使用EAS Build：
```bash
eas build -p ios
eas build -p android
```

## License

MIT License
