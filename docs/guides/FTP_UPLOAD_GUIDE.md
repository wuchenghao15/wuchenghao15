
# MTSCOS AI 项目FTP上传指南

## FTP服务器配置
- **主机**: wuchenghao15.xicp.net
- **端口**: 21
- **用户名**: wuchenghao15
- **密码**: LoginMe.1988
- **远程路径**: /

## 上传方法

### 方法1: 使用FileZilla
1. **下载FileZilla**: https://filezilla-project.org/
2. **打开FileZilla**
3. **输入连接信息**:
   - 主机: wuchenghao15.xicp.net
   - 端口: 21
   - 用户名: wuchenghao15
   - 密码: LoginMe.1988
4. **点击连接**
5. **上传文件**:
   - 左侧: 找到 /Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/deploy-package
   - 右侧: 导航到 /
   - 选择所有文件，拖拽到右侧

### 方法2: 使用命令行
```bash
# 使用ftp命令
ftp -n -v -s:ftp-upload.txt

# 或使用curl
curl -T /Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/deploy-package ftp://wuchenghao15:LoginMe.1988@wuchenghao15.xicp.net:21/
```

### 方法3: 使用其他FTP客户端
1. **打开FTP客户端**
2. **输入连接信息**
3. **连接服务器**
4. **上传 /Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/deploy-package 中的所有文件**

## 部署后操作
1. **连接服务器**: 使用SSH或远程桌面
2. **导航到项目目录**: cd /
3. **安装依赖**: npm install
4. **启动服务**: npm start
5. **验证服务**: http://wuchenghao15.xicp.net/api/health

## 故障排除
- **连接失败**: 检查网络连接和FTP凭据
- **上传失败**: 检查文件权限和磁盘空间
- **启动失败**: 检查端口占用和依赖安装
- **访问失败**: 检查防火墙设置
