# -*- coding: utf-8 -*-
"""
About页面蓝图 - 公司简介、发展历程、团队介绍、新闻动态
"""

from flask import Blueprint, render_template

about_bp = Blueprint('about', __name__)


@about_bp.route('/about/company')
def company():
    """公司简介页面"""
    return render_template('about/company.html',
                           title='公司简介',
                           current_page='about_company')


@about_bp.route('/about/history')
def history():
    """发展历程页面"""
    return render_template('about/history.html',
                           title='发展历程',
                           current_page='about_history')


@about_bp.route('/about/team')
def team():
    """团队介绍页面"""
    return render_template('about/team.html',
                           title='团队介绍',
                           current_page='about_team')


@about_bp.route('/about/news')
def news():
    """新闻动态页面"""
    return render_template('about/news.html',
                           title='新闻动态',
                           current_page='about_news')


@about_bp.route('/products/features')
def products_features():
    """产品功能介绍页面"""
    return render_template('products/features.html',
                           title='产品功能',
                           current_page='products_features')


@about_bp.route('/contact/contact')
def contact():
    """联系我们页面"""
    return render_template('contact/contact.html',
                           title='联系我们',
                           current_page='contact_contact')
