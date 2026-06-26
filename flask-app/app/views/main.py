# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for
from flask import session
import os

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
    """仪表板 - 根据角色重定向到对应页面"""
    role = session.get('role', 'guest')
    
    role_redirect_map = {
        'student': '/exam_system',
        'designer': '/arduino',
        'teacher': '/teacher',
        'researcher': '/researcher',
        'admin': '/settings',
        'super_admin': '/settings',
        'hardware_admin': '/settings',
        'hardware_vikey_admin': '/settings',
        'guest': '/'
    }
    
    redirect_path = role_redirect_map.get(role, '/')
    return redirect(redirect_path)
