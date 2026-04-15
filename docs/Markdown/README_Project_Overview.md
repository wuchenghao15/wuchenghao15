# MTSCOS_AI_Project 项目概述

## 项目简介
MTSCOS_AI_Project是一个综合性的AI项目管理系统，提供了完整的开发、测试、部署和监控解决方案。

## 项目结构

```
MTSCOS_AI_Project/
├── Build/                   # 构建相关文件
│   └── Output/              # 构建输出目录
│       └── dist/            # 发布文件
├── Configuration/           # 配置文件目录
├── Data/                    # 数据存储目录
│   ├── MyData/              # 项目数据
│   └── Users/               # 用户数据
│       └── users_data/      # 用户详细数据
├── Database/                # 数据库相关
│   └── Init/                # 数据库初始化脚本
├── Documentation/           # 项目文档
│   ├── Markdown/            # Markdown格式文档
│   ├── Reports/             # 报告文档
│   └── Text/                # 文本格式文档
├── Logs/                    # 日志文件统一管理目录
│   ├── JavaScript监控/      # JavaScript相关日志
│   ├── Python脚本/          # Python脚本日志
│   ├── 备份工具/            # 备份工具日志
│   ├── 错误日志/            # 错误日志
│   ├── 日志监控/            # 日志监控记录
│   └── 系统监控/            # 系统监控日志
├── Media/                   # 媒体资源
│   └── Images/              # 图片资源
├── Others/                  # 其他文件
├── Scripts/                 # 脚本文件
└── SourceCode/              # 源代码目录
    ├── CSS/                 # CSS样式文件
    ├── HTML/                # HTML页面
    ├── JavaScript/          # JavaScript代码
    ├── Python/              # Python代码
    └── Others/              # 其他源代码
```

## 最新更新
- 更新日期：2025-10-20
- 版本号：测试版本 1.1.10202025
- 更新内容：
  1. 优化了日志管理系统
  2. 实现了日志文件的智能分类和转存
  3. 清理了非一级日志文件夹
  4. 提高了系统稳定性和性能
  5. 更新了项目打包和部署脚本
  6. 优化了项目结构和文档说明

## 使用说明
1. 项目启动：在项目根目录执行相应的启动脚本
2. 配置管理：所有配置文件位于Configuration目录
3. 日志查看：统一在Logs目录下查看各类日志
4. 版本信息：版本号保存在Others/VERSION文件中

## 开发指南
1. 源代码开发请在SourceCode目录下进行
2. 新功能开发前请先更新版本号
3. 定期执行日志整理以保持系统整洁

## 注意事项
- 请勿直接修改构建输出目录的文件
- 所有日志文件请通过日志管理工具进行管理
- 重要数据请及时备份