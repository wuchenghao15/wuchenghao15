# -*- coding: utf-8 -*-
# 应用初始化
from flask import Flask
from .config import Config

app = Flask(__name__)
app.config.from_object(Config)

# 导入路由和其他模块

__all__ = ['app']
