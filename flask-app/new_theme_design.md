# 新主题设计方案

## 1. 配色方案

### 主色调
- **主色**: #3b82f6 (蓝色) - 专业、现代，适合科技类应用
- **辅助色**: #8b5cf6 (紫色) - 与主色搭配和谐，用于次要强调
- **强调色**: #ec4899 (粉色) - 用于重要按钮和强调元素

### 中性色
- **深灰**: #1f2937 - 主要文本颜色
- **中灰**: #6b7280 - 次要文本颜色
- **浅灰**: #9ca3af - 提示文本颜色
- **超浅灰**: #f9fafb - 页面背景色
- **边框灰**: #e5e7eb - 边框和分隔线颜色

### 状态色
- **成功**: #10b981 - 成功消息和按钮
- **警告**: #f59e0b - 警告消息和按钮
- **错误**: #ef4444 - 错误消息和按钮
- **信息**: #3b82f6 - 信息消息和按钮

## 2. 布局改进

### 2.1 统一布局结构
- 所有页面使用相同的布局结构
- 包含导航栏、主内容区和页脚
- 固定宽度的主内容区，居中显示

### 2.2 导航栏设计
- 现代扁平设计
- 清晰的导航项分组
- 响应式设计，移动端折叠为汉堡菜单
- 悬停效果和过渡动画

### 2.3 卡片设计
- 圆角矩形设计，圆角半径统一为 12px
- 轻微阴影效果，增强层次感
- 卡片内边距统一为 24px
- 卡片之间间距统一为 24px
- 悬停时轻微放大和阴影增强效果

### 2.4 表单设计
- 统一的表单元素样式
- 清晰的标签和输入框关系
- 输入框获得焦点时的动画效果
- 统一的按钮样式
- 表单验证反馈

### 2.5 按钮设计
- 圆角按钮，圆角半径统一为 8px
- 主要按钮使用渐变背景
- 次要按钮使用描边样式
- 悬停效果和过渡动画
- 统一的按钮尺寸

### 2.6 排版优化
- 统一的字体层级
- 清晰的标题和正文区分
- 合适的行高和字间距
- 响应式字体大小

## 3. 动画效果

### 3.1 过渡动画
- 导航项悬停效果
- 按钮状态变化
- 卡片悬停效果
- 表单元素状态变化

### 3.2 加载动画
- 统一的加载指示器设计
- 页面加载动画
- 按钮加载状态

### 3.3 页面过渡
- 平滑的页面切换效果
- 元素出现动画

## 4. 响应式设计

### 4.1 断点设置
- 移动端: < 640px
- 平板: 640px - 1024px
- 桌面: > 1024px

### 4.2 移动端优化
- 汉堡菜单
- 单列布局
- 优化的触摸目标大小
- 简化的导航

## 5. 实现计划

1. 更新 CSS 变量，定义新的配色方案
2. 改进全局样式，统一布局结构
3. 更新导航栏设计
4. 改进卡片和表单样式
5. 添加动画效果
6. 优化响应式设计
7. 测试所有页面

## 6. 技术实现

### 6.1 CSS 变量
```css
:root {
  /* 主色调 */
  --primary: #3b82f6;
  --primary-dark: #2563eb;
  --secondary: #8b5cf6;
  --secondary-dark: #7c3aed;
  --accent: #ec4899;
  --accent-dark: #db2777;
  
  /* 中性色 */
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --text-tertiary: #9ca3af;
  --bg-primary: #ffffff;
  --bg-secondary: #f9fafb;
  --bg-tertiary: #f3f4f6;
  --border: #e5e7eb;
  
  /* 状态色 */
  --success: #10b981;
  --success-dark: #059669;
  --warning: #f59e0b;
  --warning-dark: #d97706;
  --error: #ef4444;
  --error-dark: #dc2626;
  --info: #3b82f6;
  --info-dark: #2563eb;
  
  /* 间距 */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;
  
  /* 圆角 */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  
  /* 阴影 */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  
  /* 过渡 */
  --transition-fast: 0.15s ease;
  --transition-base: 0.2s ease;
  --transition-slow: 0.3s ease;
}
```

### 6.2 全局样式
```css
/* 重置样式 */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

/* 基础样式 */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  color: var(--text-primary);
  background-color: var(--bg-secondary);
  transition: all var(--transition-base);
}

/* 标题样式 */
h1, h2, h3, h4, h5, h6 {
  font-weight: 600;
  line-height: 1.3;
  margin-bottom: var(--spacing-md);
  color: var(--text-primary);
}

h1 {
  font-size: 2.5rem;
}

h2 {
  font-size: 2rem;
}

h3 {
  font-size: 1.75rem;
}

h4 {
  font-size: 1.5rem;
}

h5 {
  font-size: 1.25rem;
}

h6 {
  font-size: 1rem;
}

/* 段落样式 */
p {
  margin-bottom: var(--spacing-md);
  color: var(--text-secondary);
}

/* 链接样式 */
a {
  color: var(--primary);
  text-decoration: none;
  transition: all var(--transition-base);
}

a:hover {
  color: var(--primary-dark);
  text-decoration: underline;
}

/* 容器样式 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
}

/* 卡片样式 */
.card {
  background-color: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: var(--spacing-lg);
  transition: all var(--transition-base);
  margin-bottom: var(--spacing-lg);
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-weight: 500;
  font-size: 0.95rem;
  line-height: 1.5;
  border: none;
  cursor: pointer;
  transition: all var(--transition-base);
  text-decoration: none;
  white-space: nowrap;
}

.btn-primary {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  text-decoration: none;
}

.btn-secondary {
  background: linear-gradient(135deg, var(--secondary) 0%, var(--secondary-dark) 100%);
  color: white;
}

.btn-secondary:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  text-decoration: none;
}

.btn-accent {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%);
  color: white;
}

.btn-accent:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  text-decoration: none;
}

.btn-outline {
  background-color: transparent;
  color: var(--primary);
  border: 2px solid var(--primary);
}

.btn-outline:hover {
  background-color: var(--primary);
  color: white;
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  text-decoration: none;
}

/* 表单样式 */
.form-group {
  margin-bottom: var(--spacing-lg);
}

.form-label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.form-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  transition: all var(--transition-base);
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  transform: translateY(-1px);
}

/* 导航栏样式 */
.navbar {
  background-color: var(--bg-primary);
  box-shadow: var(--shadow-sm);
  padding: var(--spacing-md) 0;
  position: sticky;
  top: 0;
  z-index: 1000;
  transition: all var(--transition-base);
}

.navbar-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.navbar-logo {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary);
  text-decoration: none;
  transition: all var(--transition-base);
}

.navbar-logo:hover {
  color: var(--primary-dark);
  text-decoration: none;
}

.navbar-nav {
  display: flex;
  list-style: none;
  gap: var(--spacing-lg);
  align-items: center;
}

.navbar-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 500;
  transition: all var(--transition-base);
  padding: var(--spacing-xs) 0;
  position: relative;
}

.navbar-link:hover {
  color: var(--primary);
  text-decoration: none;
}

.navbar-link::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background-color: var(--primary);
  transition: width var(--transition-base);
}

.navbar-link:hover::after {
  width: 100%;
}

/* 页脚样式 */
.footer {
  background-color: var(--bg-primary);
  border-top: 1px solid var(--border);
  padding: var(--spacing-xl) 0;
  margin-top: var(--spacing-2xl);
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
}

.footer-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
}

.footer-section h3 {
  font-size: 1.25rem;
  margin-bottom: var(--spacing-lg);
  color: var(--text-primary);
}

.footer-section ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.footer-section ul li {
  margin-bottom: var(--spacing-md);
}

.footer-section ul li a {
  color: var(--text-secondary);
  text-decoration: none;
  transition: all var(--transition-base);
}

.footer-section ul li a:hover {
  color: var(--primary);
  text-decoration: none;
}

.footer-bottom {
  text-align: center;
  padding-top: var(--spacing-xl);
  border-top: 1px solid var(--border);
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  h1 {
    font-size: 2rem;
  }
  
  h2 {
    font-size: 1.75rem;
  }
  
  h3 {
    font-size: 1.5rem;
  }
  
  .container {
    padding: 0 var(--spacing-md);
  }
  
  .navbar-nav {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .footer-content {
    grid-template-columns: 1fr;
    gap: var(--spacing-lg);
  }
}
