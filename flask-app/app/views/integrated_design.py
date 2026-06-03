# -*- coding: utf-8 -*-
from flask import Blueprint, render_template

integrated_design_bp = Blueprint('integrated_design', __name__)

@integrated_design_bp.route('/')
def index():
    return render_template('index.html')

