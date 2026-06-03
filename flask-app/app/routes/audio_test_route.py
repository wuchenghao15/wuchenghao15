# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
音频测试页面路由
"""
from flask import render_template

def add_audio_test_route(app):
    @app.route('/test/audio')
    def audio_test():
        return render_template('audio_test.html')
