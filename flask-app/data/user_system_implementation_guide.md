# 用户系统增强实现指南

## 1. 登录重定向功能

### 实现步骤
1. 修改登录处理函数，根据用户角色进行重定向
2. 学生用户登录后直接重定向到考试系统
3. 管理员用户登录后重定向到管理仪表盘
4. 教师用户登录后重定向到教师仪表盘

### 代码示例
```python
@app.route('/login', methods=['POST'])
def login():
    # 登录验证逻辑
    user_role = get_user_role(user_id)
    
    if user_role == 'student':
        # 检查用户等级
        if not check_user_levels(user_id):
            # 重定向到摸底测试
            return redirect('/placement-test')
        return redirect('/exam-system')
    elif user_role == 'admin':
        return redirect('/admin/dashboard')
    elif user_role == 'teacher':
        return redirect('/teacher/dashboard')
```

## 2. 等级检测功能

### 实现步骤
1. 创建用户等级检查函数
2. 检查用户的语言等级和各学科等级
3. 如果等级为空或未检测到，触发摸底测试

### 代码示例
```python
def check_user_levels(user_id):
    # 检查用户等级
    levels = get_user_levels(user_id)
    
    # 检查语言等级
    if not levels.get('language_level'):
        return False
    
    # 检查其他学科等级
    subjects = ['math', 'science', 'history']
    for subject in subjects:
        if not levels.get(f'{subject}_level'):
            return False
    
    return True
```

## 3. 管理员权限管理

### 实现步骤
1. 创建管理员权限检查函数
2. 为不同等级的管理员分配不同权限
3. 低权限管理员的敏感操作需要高权限管理员审批

### 代码示例
```python
def check_admin_permission(admin_id, operation):
    # 获取管理员权限等级
    permission_level = get_admin_permission_level(admin_id)
    
    # 检查是否为敏感操作
    if operation in sensitive_operations:
        if permission_level < 2:
            # 需要审批
            create_approval_request(admin_id, operation)
            return False
    
    return True
```

## 4. 操作审批流程

### 实现步骤
1. 创建审批请求函数
2. 创建审批处理函数
3. 实现审批通知机制

### 代码示例
```python
def create_approval_request(requester_id, operation, details):
    # 创建审批请求
    operation_id = generate_operation_id()
    
    # 保存到数据库
    save_approval_request(operation_id, requester_id, operation, details)
    
    # 通知高权限管理员
    notify_admin(operation_id)

@app.route('/approve-operation', methods=['POST'])
def approve_operation():
    # 处理审批请求
    operation_id = request.form.get('operation_id')
    decision = request.form.get('decision')
    
    if decision == 'approve':
        # 执行操作
        execute_operation(operation_id)
    
    # 更新审批状态
    update_approval_status(operation_id, decision)
```

## 5. 操作日志和备份

### 实现步骤
1. 创建操作日志记录函数
2. 实现数据库备份功能
3. 定期清理旧日志

### 代码示例
```python
def log_operation(user_id, operation_type, details, ip_address):
    # 记录操作日志
    log_entry = {
        'user_id': user_id,
        'operation_type': operation_type,
        'operation_details': details,
        'ip_address': ip_address,
        'timestamp': datetime.now().isoformat()
    }
    
    # 保存到数据库
    save_operation_log(log_entry)

 def backup_database():
    # 备份数据库
    backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(db_path, backup_path)
    
    # 记录备份日志
    log_operation(admin_id, 'database_backup', f'备份到 {backup_path}', request.remote_addr)
```

## 6. 权限检查中间件

### 实现步骤
1. 创建权限检查中间件
2. 对敏感路由进行权限控制

### 代码示例
```python
@app.before_request
def check_permissions():
    # 获取当前用户
    user_id = get_current_user_id()
    
    # 检查是否为管理员路由
    if request.path.startswith('/admin'):
        # 检查管理员权限
        if not check_admin_access(user_id):
            return redirect('/unauthorized')
    
    # 检查是否为敏感操作
    if request.endpoint in sensitive_endpoints:
        if not check_operation_permission(user_id, request.endpoint):
            return redirect('/unauthorized')
```
