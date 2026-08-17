#!/usr/bin/env python3

def get_redirect_url_for_role(role):
    role_map = {
        'super_admin': '/super_admin_dashboard',
        'admin': '/super_admin_dashboard',
        'hardware_admin': '/hardware/dashboard',
        'teacher': '/teacher',
        'student': '/exam_system',
        'student_vip': '/exam_system'
    }
    return role_map.get(role, '/dashboard')