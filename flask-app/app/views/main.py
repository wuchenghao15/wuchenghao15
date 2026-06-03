# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for
from flask import session

main_bp = Blueprint('main', __name__)

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
    """仪表板"""
    username = session.get('username', 'Guest')
    return render_template('dashboard.html', username=username)
