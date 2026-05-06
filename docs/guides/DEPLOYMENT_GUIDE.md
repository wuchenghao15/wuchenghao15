
# MTSCOS AI 项目部署指南

## 目标服务器
- **域名**: wuchenghao15.xicp.net
- **IP地址**: 43.137.3.121
- **开放端口**: 80 (HTTP), 443 (HTTPS)

## 部署步骤

### 方法1: FTP上传
1. **打开FTP客户端** (如FileZilla)
2. **连接服务器**:
   - 主机: wuchenghao15.xicp.net
   - 端口: 21
   - 用户名: anonymous
   - 密码: user@example.com
3. **上传文件**: 将deploy-package目录中的所有文件上传到服务器根目录
4. **设置权限**: 确保所有文件权限正确
5. **启动服务**: 在服务器上运行: npm start

### 方法2: SCP上传 (如果服务器支持SSH)
```bash
# 上传整个目录
scp -r deploy-package/* user@wuchenghao15.xicp.net:/var/www/mtscos-ai-project/

# 连接服务器并启动
ssh user@wuchenghao15.xicp.net
cd /var/www/mtscos-ai-project
npm install
npm start
```

### 方法3: HTTP上传 (如果服务器有上传接口)
1. **访问上传页面**: http://wuchenghao15.xicp.net/upload
2. **选择文件**: 上传deploy-package目录中的文件
3. **完成上传**: 按照页面提示完成部署

## 验证部署
1. **访问主页**: http://wuchenghao15.xicp.net
2. **检查健康状态**: http://wuchenghao15.xicp.net/api/health
3. **测试AI接口**: http://wuchenghao15.xicp.net/api/ai/models

## 故障排除
- **服务无法启动**: 检查端口80是否被占用
- **访问被拒绝**: 检查防火墙设置
- **数据库错误**: 确保data目录权限正确
- **依赖问题**: 运行npm install安装所有依赖
