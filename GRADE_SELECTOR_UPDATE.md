# 年级选择器权限控制修改说明

## 问题描述
原系统中`settings-v3.html`的年级选择器仅显示1-3年级，需要根据用户权限显示不同范围的年级选项，最高权限应显示全部年级包括成人年级。

## 修改内容

### 1. 修改的文件
- [settings-v3.html](../../frontend/pages/settings-v3.html)

### 2. 具体修改

#### 2.1 年级选项配置 (第1155-1167行)
添加了根据用户组权限的年级选项配置：

```javascript
const gradeOptions = {
    // 普通权限：仅显示1-3年级
    default: ['一年级', '二年级', '三年级'],
    // 教师权限：显示1-6年级
    teacher: ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级'],
    // 教授/专家权限：显示1-9年级
    professor: ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级', '七年级', '八年级', '九年级'],
    // 超级管理员/硬件管理员：显示全部年级，包括成人年级
    super_admin: ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级', '七年级', '八年级', '九年级', '成人初级', '成人中级', '成人高级', '雅思预备', '托福预备', '商务英语初级', '商务英语中级', '商务英语高级', '日语N5', '日语N4', '日语N3', '日语N2', '日语N1', '新概念第一册', '新概念第二册', '新概念第三册', '新概念第四册', 'AMC8预备', 'AMC8进阶', '华罗庚竞赛初级', '华罗庚竞赛中级', '华罗庚竞赛高级']
};
gradeOptions.hardware_admin = gradeOptions.super_admin;
gradeOptions.expert = gradeOptions.professor;
```

#### 2.2 年级选项更新函数 (第1189-1208行)
添加了`updateGradeOptions()`函数：

```javascript
function updateGradeOptions() {
    const gradeSelect = document.getElementById('education-grade');
    if (!gradeSelect) return;

    // 根据当前用户组选择年级选项
    let options = gradeOptions[currentGroup] || gradeOptions.default;

    // 清空现有选项
    gradeSelect.innerHTML = '';

    // 添加新选项
    options.forEach(grade => {
        const option = document.createElement('option');
        option.value = grade;
        option.textContent = grade;
        gradeSelect.appendChild(option);
    });

    console.log(`已为 ${groupNames[currentGroup]} 加载 ${options.length} 个年级选项`);
}
```

#### 2.3 集成到可见性更新
在`updateVisibleSections()`函数中添加了对`updateGradeOptions()`的调用，确保切换用户组时也更新年级选项。

#### 2.4 修改年级选择器HTML (第945-950行)
将静态的年级选项改为动态加载的占位符：

```html
<div class="form-group">
    <label class="form-label">教授年级</label>
    <select class="form-input" id="education-grade">
        <!-- 根据权限动态加载年级选项 -->
    </select>
</div>
```

## 权限级别说明

| 用户组 | 可见年级范围 | 年级数量 |
|--------|-------------|---------|
| 学生/普通用户 | 一年级-三年级 | 3 |
| 教师 | 一年级-六年级 | 6 |
| 教授/专家 | 一年级-九年级 | 9 |
| 超级管理员/硬件管理员 | 全部年级（包括成人年级） | 31 |

## 成人年级列表
1. 成人初级
2. 成人中级
3. 成人高级
4. 雅思预备
5. 托福预备
6. 商务英语初级
7. 商务英语中级
8. 商务英语高级
9. 日语N5
10. 日语N4
11. 日语N3
12. 日语N2
13. 日语N1
14. 新概念第一册
15. 新概念第二册
16. 新概念第三册
17. 新概念第四册
18. AMC8预备
19. AMC8进阶
20. 华罗庚竞赛初级
21. 华罗庚竞赛中级
22. 华罗庚竞赛高级

## 使用方法

1. 访问 `http://localhost:8888/frontend/pages/settings-v3.html`
2. 在页面底部的"测试模式"中选择不同的用户组
3. 点击左侧导航的"教育设置"
4. 在"教授年级"下拉框中查看对应权限的年级选项

## 技术特点

- ✅ 根据用户权限动态显示年级选项
- ✅ 权限切换时自动更新选项
- ✅ 模块化设计，易于扩展
- ✅ 控制台日志便于调试
- ✅ 向下兼容旧用户组

## 后续优化建议

1. 将年级选项数据存储在配置文件或数据库中
2. 添加年级分组（如"义务教育"、"成人教育"、"竞赛培训"等）
3. 添加年级图标增强用户体验
4. 考虑为不同年级添加更多描述信息
5. 添加年级搜索和筛选功能

## 修改日期
2026-05-31
