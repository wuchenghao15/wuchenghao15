# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for
from flask import session
import os

# 获取flask-app根目录
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

main_bp = Blueprint('main', __name__, template_folder=os.path.join(APP_ROOT, 'templates'))

@main_bp.route('/')
def index():
    """首页"""
    return render_template('index.html')

@main_bp.route('/home')
def home():
    """主页"""
    return render_template('home.html')

@main_bp.route('/dashboard')
def dashboard():
    """仪表板 - 重定向到设置页面（仪表盘已整合到设置页面中）"""
    return redirect('/settings')
