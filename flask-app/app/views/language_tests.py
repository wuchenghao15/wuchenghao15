# -*- coding: utf-8 -*-
from flask import Blueprint, render_template

language_tests_bp = Blueprint('language_tests', __name__)

@language_tests_bp.route('/')
def index():
    return render_template('index.html')

