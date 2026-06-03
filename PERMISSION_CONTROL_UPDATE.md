# 用户组切换权限控制功能说明

## 功能概述
为系统添加了用户组切换权限控制功能，防止低权限用户切换到高权限用户组。

## 修改的文件
- [settings-v3.html](../../frontend/pages/settings-v3.html)

## 修改内容

### 1. 权限级别定义 (第1169-1181行)
添加了用户组权限级别定义，数字越大权限越高：

```javascript
const permissionLevel = {
    student: 1,
    designer: 2,
    architect: 3,
    teacher: 4,
    group_leader: 5,
    professor: 6,
    expert: 7,
    admin: 8,
    super_admin: 9,
    hardware_admin: 10
};
```

### 2. 实际用户组记录 (第1183-1185行)
添加了 `actualUserGroup` 变量来记录实际登录用户的权限：

```javascript
let actualUserGroup = localStorage.getItem('mtcos_userGroup') || 'admin';
let currentGroup = actualUserGroup;
```

### 3. 用户组切换权限校验 (第1251-1273行)
修改了用户组点击事件处理，添加了权限校验逻辑：

```javascript
document.querySelectorAll('.group-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        const targetGroup = this.dataset.group;
        
        // 权限校验：检查是否有权限切换到目标用户组
        const actualLevel = permissionLevel[actualUserGroup] || 0;
        const targetLevel = permissionLevel[targetGroup] || 0;
        
        // 只能切换到权限级别不超过自己的用户组
        if (targetLevel > actualLevel) {
            showToast(`您没有权限切换到${groupNames[targetGroup]}！`, 'error');
            return;
        }
        
        // 权限校验通过，执行切换
        document.querySelectorAll('.group-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        currentGroup = targetGroup;
        updateVisibleSections();
        updateTabVisibility();
        showToast(`已切换到${groupNames[currentGroup]}视图`, 'success');
    });
});
```

### 4. 标签可见性更新函数 (第1275-1295行)
添加了 `updateTabVisibility()` 函数，用于禁用或隐藏权限不足的用户组标签：

```javascript
function updateTabVisibility() {
    const actualLevel = permissionLevel[actualUserGroup] || 0;
    
    document.querySelectorAll('.group-tab').forEach(tab => {
        const targetGroup = tab.dataset.group;
        const targetLevel = permissionLevel[targetGroup] || 0;
        
        if (targetLevel > actualLevel) {
            tab.disabled = true;
            tab.style.opacity = '0.4';
            tab.style.cursor = 'not-allowed';
            tab.title = `您没有权限切换到${groupNames[targetGroup]}`;
        } else {
            tab.disabled = false;
            tab.style.opacity = '';
            tab.style.cursor = '';
            tab.title = '';
        }
    });
}
```

### 5. 初始化时调用 (第1375行)
在页面初始化时也调用 `updateTabVisibility()` 来设置初始状态。

## 用户组权限级别

| 用户组 | 权限级别 | 学生能否切换 | 教师能否切换 | 超级管理员能否切换 |
|--------|---------|-------------|-------------|------------------|
| 学生 | 1 | ✅ 能 | ✅ 能 | ✅ 能 |
| 设计师 | 2 | ❌ 不能 | ✅ 能 | ✅ 能 |
| 架构师 | 3 | ❌ 不能 | ✅ 能 | ✅ 能 |
| 教师 | 4 | ❌ 不能 | ✅ 能 | ✅ 能 |
| 组长 | 5 | ❌ 不能 | ❌ 不能 | ✅ 能 |
| 教授 | 6 | ❌ 不能 | ❌ 不能 | ✅ 能 |
| 专家 | 7 | ❌ 不能 | ❌ 不能 | ✅ 能 |
| 管理员 | 8 | ❌ 不能 | ❌ 不能 | ✅ 能 |
| 超级管理员 | 9 | ❌ 不能 | ❌ 不能 | ✅ 能 |
| 硬件管理员 | 10 | ❌ 不能 | ❌ 不能 | ✅ 能 |

## 功能特点

### 1. 双重安全保障
- **视觉提示**：权限不足的标签显示为半透明，鼠标悬停显示提示
- **点击拦截**：即使视觉上没有注意到，点击时也会被拦截并显示错误提示

### 2. 智能提示
- 使用 `showToast()` 显示友好的错误消息
- 提示信息包含具体的用户组名称
- 鼠标悬停在禁用标签上也有提示

### 3. 初始化状态
- 页面加载时自动设置标签可见性
- 根据实际登录用户的权限进行初始化

## 测试方法

### 场景1：学生用户（权限级别1）
1. 在浏览器控制台执行：`localStorage.setItem('mtcos_userGroup', 'student')`
2. 刷新页面：`http://localhost:8888/frontend/pages/settings-v3.html`
3. 预期结果：
   - 只有"学生"标签可用
   - 其余所有标签显示为半透明且不可点击
   - 点击任何高权限标签都会显示错误提示

### 场景2：教师用户（权限级别4）
1. 在浏览器控制台执行：`localStorage.setItem('mtcos_userGroup', 'teacher')`
2. 刷新页面
3. 预期结果：
   - 学生、设计师、架构师、教师标签可用
   - 组长及以上标签禁用

### 场景3：超级管理员用户（权限级别9）
1. 在浏览器控制台执行：`localStorage.setItem('mtcos_userGroup', 'super_admin')`
2. 刷新页面
3. 预期结果：
   - 所有标签可用（除了硬件管理员）
   - 可以自由切换到任何权限级别不超过9的用户组

### 场景4：硬件管理员用户（权限级别10）
1. 在浏览器控制台执行：`localStorage.setItem('mtcos_userGroup', 'hardware_admin')`
2. 刷新页面
3. 预期结果：
   - 所有标签都可用
   - 可以自由切换到任何用户组

## 界面效果

### 可用标签
- 正常显示
- 鼠标悬停有交互效果
- 点击可以切换

### 禁用标签
- 透明度降低至40%
- 鼠标显示为"禁止"光标
- 鼠标悬停显示提示信息："您没有权限切换到XX用户组"
- 点击被拦截并显示错误提示

## 技术实现细节

### 权限校验逻辑
```javascript
// 获取实际用户和目标用户的权限级别
const actualLevel = permissionLevel[actualUserGroup] || 0;
const targetLevel = permissionLevel[targetGroup] || 0;

// 比较级别：目标级别不能超过实际级别
if (targetLevel > actualLevel) {
    // 阻止切换
    showToast(`您没有权限切换到${groupNames[targetGroup]}！`, 'error');
    return;
}
```

### 样式控制
使用内联样式进行样式控制，无需额外的CSS类：
- `opacity: '0.4'` - 半透明效果
- `cursor: 'not-allowed'` - 禁止光标
- `title` - 鼠标悬停提示

## 扩展性

### 添加新用户组
如果需要添加新的用户组，只需：
1. 在 `groupNames` 中添加组名映射
2. 在 `permissionLevel` 中定义权限级别
3. 在 `userGroupSettings` 中添加权限配置
4. 在 `gradeOptions` 中添加年级选项（如需要）

### 调整权限级别
只需修改 `permissionLevel` 对象中的数值即可调整用户组的权限高低关系。

## 修改日期
2026-05-31
