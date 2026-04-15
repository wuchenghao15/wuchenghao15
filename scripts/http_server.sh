#!/bin/bash

# 简单的HTTP服务器脚本

# 设置默认的主页为HTML/index.html
HOME_PAGE="HTML/index.html"

# 启动Python HTTP服务器
python3 -m http.server 8080
