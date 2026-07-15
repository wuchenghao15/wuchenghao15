#!/usr/bin/env python3

def get_redirect_url_for_role(role):
    role_map = {
        'super_admin': '/super_admin_dashboard',
        'admin': '/super_admin_dashboard',
        'hardware_admin': '/hardware/dashboard',
        'teacher': '/teacher',
        'student': '/student_portal',
        'student_vip': '/student_portal'
    }
    return role_map.get(role, '/dashboard')