/**
 * 用户组别权限配置 - User Roles Permission Configuration
 * MTSCOS AI Project v3.2
 * 
 * 用户组别层级（从高到低）：
 * 硬件管理员 > 超级管理员 > 管理员 > 教授/专家 > 组长 > 教师 > 设计师/架构师 > 学生
 */

// 用户组别定义
const USER_ROLES = {
    hardware_admin: {
        id: 'hardware_admin',
        name: '硬件管理员',
        level: 100,
        category: 'system',
        description: '系统最高权限，管理所有硬件和系统资源',
        permissions: {
            // 页面访问
            pages: {
                dashboard: true,
                settings: true,
                exam: true,
                exercise: true,
                design: true,
                education: true,
                permission_manage: true,
                audit: true,
                data_manage: true,
                system_config: true
            },
            // 功能权限
            features: {
                // 考试相关
                take_exam: true,
                view_exam_results: true,
                export_exam_data: true,
                
                // 习题相关
                do_exercise: true,
                view_exercise_answers: true,
                
                // 学生管理
                manage_students: true,
                assign_subjects: true,
                remove_students: true,
                transfer_students: true,
                
                // 教师管理
                manage_teachers: true,
                assign_subjects_to_teachers: true,
                
                // 审批相关
                approve_all: true,
                approve_subject_change: true,
                approve_class_transfer: true,
                approve_student_removal: true,
                approve_design_proposal: true,
                approve_architecture_proposal: true,
                approve_role_assignment: true,
                
                // 设计相关
                access_design_page: true,
                edit_design: true,
                submit_design_proposal: true,
                
                // 架构相关
                edit_architecture: true,
                submit_architecture_proposal: true,
                
                // 任命相关
                appoint_designer: true,
                appoint_architect: true,
                appoint_teacher: true,
                appoint_professor: true,
                
                // 系统配置
                modify_all_params: true,
                modify_system_config: true,
                modify_exam_config: true,
                modify_education_config: true,
                modify_design_config: true,
                
                // 数据管理
                export_all_data: true,
                import_data: true,
                backup_data: true,
                restore_data: true,
                
                // 设置页面
                access_settings: true,
                modify_personal_info: true,
                change_password: true,
                modify_notifications: true,
                modify_appearance: true
            }
        }
    },
    
    super_admin: {
        id: 'super_admin',
        name: '超级管理员',
        level: 90,
        category: 'system',
        description: '系统管理权限，审批和配置管理',
        permissions: {
            pages: {
                dashboard: true,
                settings: true,
                exam: false,
                exercise: false,
                design: false,
                education: false,
                permission_manage: true,
                audit: true,
                data_manage: true,
                system_config: true
            },
            features: {
                // 考试相关
                take_exam: false,
                view_exam_results: true,
                export_exam_data: true,
                
                // 习题相关
                do_exercise: false,
                view_exercise_answers: true,
                
                // 学生管理
                manage_students: true,
                assign_subjects: true,
                remove_students: true,
                transfer_students: true,
                
                // 教师管理
                manage_teachers: true,
                assign_subjects_to_teachers: true,
                
                // 审批相关
                approve_all: false,
                approve_subject_change: true,
                approve_class_transfer: true,
                approve_student_removal: true,
                approve_design_proposal: true,
                approve_architecture_proposal: true,
                approve_role_assignment: true,
                
                // 设计相关
                access_design_page: false,
                edit_design: false,
                submit_design_proposal: false,
                
                // 架构相关
                edit_architecture: false,
                submit_architecture_proposal: false,
                
                // 任命相关
                appoint_designer: true,
                appoint_architect: true,
                appoint_teacher: true,
                appoint_professor: true,
                
                // 系统配置
                modify_all_params: false,
                modify_system_config: true,
                modify_exam_config: true,
                modify_education_config: true,
                modify_design_config: false,
                
                // 数据管理
                export_all_data: true,
                import_data: true,
                backup_data: true,
                restore_data: true,
                
                // 设置页面
                access_settings: true,
                modify_personal_info: true,
                change_password: true,
                modify_notifications: true,
                modify_appearance: true
            }
        }
    },
    
    admin: {
        id: 'admin',
        name: '管理员',
        level: 80,
        category: 'system',
        description: '系统配置和低权限审批',
        permissions: {
            pages: {
                dashboard: true,
                settings: true,
                exam: false,
                exercise: false,
                design: false,
                education: false,
                permission_manage: false,
                audit: true,
                data_manage: true,
                system_config: true
            },
            features: {
                // 考试相关
                take_exam: false,
                view_exam_results: true,
                export_exam_data: true,
                
                // 习题相关
                do_exercise: false,
                view_exercise_answers: true,
                
                // 学生管理
                manage_students: true,
                assign_subjects: false,
                remove_students: false,
                transfer_students: false,
                
                // 教师管理
                manage_teachers: false,
                assign_subjects_to_teachers: false,
                
                // 审批相关
                approve_all: false,
                approve_subject_change: false,
                approve_class_transfer: false,
                approve_student_removal: true,
                approve_design_proposal: true,
                approve_architecture_proposal: true,
                approve_role_assignment: false,
                
                // 设计相关
                access_design_page: false,
                edit_design: false,
                submit_design_proposal: false,
                
                // 架构相关
                edit_architecture: false,
                submit_architecture_proposal: false,
                
                // 任命相关
                appoint_designer: false,
                appoint_architect: false,
                appoint_teacher: false,
                appoint_professor: false,
                
                // 系统配置
                modify_all_params: false,
                modify_system_config: true,
                modify_exam_config: false,
                modify_education_config: false,
                modify_design_config: false,
                
                // 数据管理
                export_all_data: false,
                import_data: false,
                backup_data: true,
                restore_data: true,
                
                // 设置页面
                access_settings: true,
                modify_personal_info: true,
                change_password: true,
                modify_notifications: true,
                modify_appearance: true
            }
        }
    },
    
    professor: {
        id: 'professor',
        name: '教授',
        level: 70,
        category: 'education',
        description: '教学管理权限，学科分配和教师管理',
        permissions: {
            pages: {
                dashboard: true,
                settings: true,
                exam: false,
                exercise: false,
                design: false,
                education: true,
                permission_manage: false,
                audit: true,
                data_manage: false,
                system_config: false
            },
            features: {
                // 考试相关
                take_exam: false,
                view_exam_results: true,
                export_exam_data: false,
                
                // 习题相关
                do_exercise: false,
                view_exercise_answers: true,
                
                // 学生管理
                manage_students: true,
                assign_subjects: true,
                remove_students: false,
                transfer_students: false,
                
                // 教师管理
                manage_teachers: true,
                assign_subjects_to_teachers: true,
                
                // 审批相关
                approve_all: false,
                approve_subject_change: true,
                approve_class_transfer: false,
                approve_student_removal: false,
                approve_design_proposal: false,
                approve_architecture_proposal: false,
                approve_role_assignment: false,
                
                // 设计相关
                access_design_page: false,
                edit_design: false,
                submit_design_proposal: false,
                
                // 架构相关
                edit_architecture: false,
                submit_architecture_proposal: false,
                
                // 任命相关
                appoint_designer: false,
                appoint_architect: false,
                appoint_teacher: false,
                appoint_professor: false,
                
                // 系统配置
                modify_all_params: false,
                modify_system_config: false,
                modify_exam_config: false,
                modify_education_config: true,
                modify_design_config: false,
                
                // 数据管理
                export_all_data: false,
                import_data: false,
                backup_data: false,
                restore_data: false,
                
                // 设置页面
                access_settings: true,
                modify_personal_info: true,
                change_password: true,
                modify_notifications: true,
                modify_appearance: true
            }
        }
    },
    
    expert: {
        id: 'expert',
        name: '专家',
        level: 70,
        category: 'education',
        description: '专家权限（与教授同级）',
        permissions: {
            pages: {
                dashboard: true,
                settings: true,
                exam: false,
                exercise: false,
                design: false,
                education: true,
                permission_manage: false,
                audit: true,
                data_manage: false,
                system_config: false
            },
            features: {
                take_exam: false,
                view_exam_results: true,
                export_exam_data: false,
                do_exercise: false,
                view_exercise_answers: true,
                manage_students: true,
                assign_subjects: true,
                remove_students: false,
                transfer_students: false,
                manage_teachers: true,
                assign_subjects_to_teachers: true,
                approve_all: false,
                approve_subject_change: true,
                approve_class_transfer: false,
                approve_student_removal: false,
                approve_design_proposal: false,
                approve_architecture_proposal: false,
                approve_role_assignment: false,
                access_design_page: false,
                edit_design: false,
                submit_design_proposal: false,
                edit_architecture: false,
                submit_architecture_proposal: false,
                appoint_designer: false,
                appoint_architect: false,
                appoint_teacher: false,
                appoint_professor: false,
                modify_all_params: false,
                modify_system_config: false,
                modify_exam_config: false,
                modify_education_config: true,
                modify_design_config: false,
                export_all_data: false,
                import_data: false,
                backup_data: false,
                restore_data: false,
                access_settings: true,
                modify_personal_info: true,
                change_password: true,
                modify_notifications: true,
                modify_appearance: true
            }
        }
    },
    
    group_leader: {
        id: 'group_leader',
        name: '组长',
        level: 60,
        category: 'system',
        description: '审批设计师和架构师方案，任命设计师和架构师',
        permissions: {
            pages: {
                dashboard: true,
                settings: true,
                exam: false,
                exercise: false,
                design: true,
                education: false,
                permission_manage: false,
                audit: true,
                data_manage: false,
                system_config: false
            },
            features: {
                take_exam: false,
                view_exam_results: false,
                export_exam_data: false,
                do_exercise: false,
                view_exercise_answers: false,
                manage_students: false,
                assign_subjects: false,
                remove_students: false,
                transfer_students: false,
                manage_teachers: false,
                assign_subjects_to_teachers: false,
                approve_all: false,
                approve_subject_change: false,
                approve_class_transfer: false,
                approve_student_removal: false,
                approve_design_proposal: true,
                approve_architecture_proposal: true,
                approve_role_assignment: true,
                access_design_page: true,
                edit_design: false,
                submit_design_proposal: false,
                edit_architecture: false,
                submit_architecture_proposal: false,
                appoint_designer: true,
                appoint_architect: true,
                appoint_teacher: false,
                appoint_professor: false,
                modify_all_params: false,
                modify_system_config: false,
                modify_exam_config: false,
                modify_education_config: false,
                modify_design_config: false,
                export_all_data: false,
                import_data: false,
                backup_data: false,
                restore_data: false,
                access_settings: true,
                modify_personal_info: true,
                change_password: true,
                modify_notifications: true,
                modify_appearance: true
            }
        }
    },
    
    teacher: {
        id: 'teacher',
        name: '教师',
        level: 50,
        category: 'education',
        description: '管理学生信息，接受教授的学科更换申请',
        permissions: {
            pages: {
                dashboard: true,
                settings: true,
                exam: false,
                exercise: false,
                design: false,
                education: true,
                permission_manage: false,
                audit: false,
                data_manage: false,
                system_config: false
            },
            features: {
                take_exam: false,
                view_exam_results: true,
                export_exam_data: false,
                do_exercise: false,
                view_exercise_answers: true,
                manage_students: true,
                assign_subjects: false,
                remove_students: true,
                transfer_students: true,
                manage_teachers: false,
                assign_subjects_to_teachers: false,
                approve_all: false,
                approve_subject_change: true,
                approve_class_transfer: true,
                approve_student_removal: true,
                approve_design_proposal: false,
                approve_architecture_proposal: false,
                approve_role_assignment: false,
                access_design_page: false,
                edit_design: false,
                submit_design_proposal: false,
                edit_architecture: false,
                submit_architecture_proposal: false,
                appoint_designer: false,
                appoint_architect: false,
                appoint_teacher: false,
                appoint_professor: false,
                modify_all_params: false,
                modify_system_config: false,
                modify_exam_config: false,
                modify_education_config: false,
                modify_design_config: false,
                export_all_data: false,
                import_data: false,
                backup_data: false,
                restore_data: false,
                access_settings: true,
                modify_personal_info: true,
                change_password: true,
                modify_notifications: true,
                modify_appearance: true
            }
        }
    },
    
    designer: {
        id: 'designer',
        name: '设计师',
        level: 40,
        category: 'system',
        description: '设计页面访问和方案提交（在组长之下）',
        permissions: {
            pages: {
                dashboard: true,
                settings: true,
                exam: false,
                exercise: false,
                design: true,
                education: false,
                permission_manage: false,
                audit: false,
                data_manage: false,
                system_config: false
            },
            features: {
                take_exam: false,
                view_exam_results: false,
                export_exam_data: false,
                do_exercise: false,
                view_exercise_answers: false,
                manage_students: false,
                assign_subjects: false,
                remove_students: false,
                transfer_students: false,
                manage_teachers: false,
                assign_subjects_to_teachers: false,
                approve_all: false,
                approve_subject_change: false,
                approve_class_transfer: false,
                approve_student_removal: false,
                approve_design_proposal: false,
                approve_architecture_proposal: false,
                approve_role_assignment: false,
                access_design_page: true,
                edit_design: true,
                submit_design_proposal: true,
                edit_architecture: false,
                submit_architecture_proposal: false,
                appoint_designer: false,
                appoint_architect: false,
                appoint_teacher: false,
                appoint_professor: false,
                modify_all_params: false,
                modify_system_config: false,
                modify_exam_config: false,
                modify_education_config: false,
                modify_design_config: false,
                export_all_data: false,
                import_data: false,
                backup_data: false,
                restore_data: false,
                access_settings: true,
                modify_personal_info: true,
                change_password: true,
                modify_notifications: true,
                modify_appearance: true
            }
        }
    },
    
    architect: {
        id: 'architect',
        name: '架构师',
        level: 40,
        category: 'system',
        description: '架构方案提交（在组长之下）',
        permissions: {
            pages: {
                dashboard: true,
                settings: true,
                exam: false,
                exercise: false,
                design: true,
                education: false,
                permission_manage: false,
                audit: false,
                data_manage: false,
                system_config: false
            },
            features: {
                take_exam: false,
                view_exam_results: false,
                export_exam_data: false,
                do_exercise: false,
                view_exercise_answers: false,
                manage_students: false,
                assign_subjects: false,
                remove_students: false,
                transfer_students: false,
                manage_teachers: false,
                assign_subjects_to_teachers: false,
                approve_all: false,
                approve_subject_change: false,
                approve_class_transfer: false,
                approve_student_removal: false,
                approve_design_proposal: false,
                approve_architecture_proposal: false,
                approve_role_assignment: false,
                access_design_page: true,
                edit_design: false,
                submit_design_proposal: false,
                edit_architecture: true,
                submit_architecture_proposal: true,
                appoint_designer: false,
                appoint_architect: false,
                appoint_teacher: false,
                appoint_professor: false,
                modify_all_params: false,
                modify_system_config: false,
                modify_exam_config: false,
                modify_education_config: false,
                modify_design_config: false,
                export_all_data: false,
                import_data: false,
                backup_data: false,
                restore_data: false,
                access_settings: true,
                modify_personal_info: true,
                change_password: true,
                modify_notifications: true,
                modify_appearance: true
            }
        }
    },
    
    student: {
        id: 'student',
        name: '学生',
        level: 10,
        category: 'education',
        description: '最低权限，只能参加考试和做习题',
        permissions: {
            pages: {
                dashboard: true,
                settings: true,
                exam: true,
                exercise: true,
                design: false,
                education: true,
                permission_manage: false,
                audit: false,
                data_manage: false,
                system_config: false
            },
            features: {
                take_exam: true,
                view_exam_results: true,
                export_exam_data: false,
                do_exercise: true,
                view_exercise_answers: false,
                manage_students: false,
                assign_subjects: false,
                remove_students: false,
                transfer_students: false,
                manage_teachers: false,
                assign_subjects_to_teachers: false,
                approve_all: false,
                approve_subject_change: false,
                approve_class_transfer: false,
                approve_student_removal: false,
                approve_design_proposal: false,
                approve_architecture_proposal: false,
                approve_role_assignment: false,
                access_design_page: false,
                edit_design: false,
                submit_design_proposal: false,
                edit_architecture: false,
                submit_architecture_proposal: false,
                appoint_designer: false,
                appoint_architect: false,
                appoint_teacher: false,
                appoint_professor: false,
                modify_all_params: false,
                modify_system_config: false,
                modify_exam_config: false,
                modify_education_config: false,
                modify_design_config: false,
                export_all_data: false,
                import_data: false,
                backup_data: false,
                restore_data: false,
                access_settings: true,
                modify_personal_info: true,
                change_password: true,
                modify_notifications: true,
                modify_appearance: true
            }
        }
    }
};

// 权限检查工具函数
const PermissionChecker = {
    /**
     * 检查用户是否有特定权限
     * @param {string} userRole - 用户角色ID
     * @param {string} permissionType - 权限类型 (pages 或 features)
     * @param {string} permissionKey - 权限键
     * @returns {boolean}
     */
    check: function(userRole, permissionType, permissionKey) {
        const role = USER_ROLES[userRole];
        if (!role) return false;
        
        if (role.permissions[permissionType] && 
            typeof role.permissions[permissionType][permissionKey] === 'boolean') {
            return role.permissions[permissionType][permissionKey];
        }
        
        return false;
    },
    
    /**
     * 检查用户是否可以访问某个页面
     * @param {string} userRole - 用户角色ID
     * @param {string} pageName - 页面名称
     * @returns {boolean}
     */
    canAccessPage: function(userRole, pageName) {
        return this.check(userRole, 'pages', pageName);
    },
    
    /**
     * 检查用户是否有某个功能权限
     * @param {string} userRole - 用户角色ID
     * @param {string} featureName - 功能名称
     * @returns {boolean}
     */
    canUseFeature: function(userRole, featureName) {
        return this.check(userRole, 'features', featureName);
    },
    
    /**
     * 获取用户可以访问的页面列表
     * @param {string} userRole - 用户角色ID
     * @returns {Array}
     */
    getAccessiblePages: function(userRole) {
        const role = USER_ROLES[userRole];
        if (!role) return [];
        
        return Object.keys(role.permissions.pages).filter(page => 
            role.permissions.pages[page] === true
        );
    },
    
    /**
     * 获取角色信息
     * @param {string} userRole - 用户角色ID
     * @returns {Object|null}
     */
    getRoleInfo: function(userRole) {
        return USER_ROLES[userRole] || null;
    },
    
    /**
     * 检查角色等级
     * @param {string} userRole - 用户角色ID
     * @param {string} targetRole - 目标角色ID
     * @returns {boolean}
     */
    isHigherThan: function(userRole, targetRole) {
        const userLevel = USER_ROLES[userRole]?.level || 0;
        const targetLevel = USER_ROLES[targetRole]?.level || 0;
        return userLevel > targetLevel;
    }
};

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { USER_ROLES, PermissionChecker };
}
