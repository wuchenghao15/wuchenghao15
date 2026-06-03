# -*- coding: utf-8 -*-
from flask import Blueprint, render_template

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login')
def login():
    """登录页面"""
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """登出页面"""
    return render_template('logout.html')

@auth_bp.route('/register')
def register():
    """注册页面"""
    return render_template('register.html')
