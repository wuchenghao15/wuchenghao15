export const SYSTEM_RULES = {
  roles: {
    admin: {
      name: '管理员',
      permissions: ['*'],
      description: '系统管理员，拥有所有权限',
    },
    professor: {
      name: '教授',
      permissions: ['manage_users', 'manage_questions', 'manage_exams', 'view_reports', 'delegate_teachers', 'evaluate_teachers'],
      description: '教授级用户，可管理题库、考试和教师',
    },
    teacher: {
      name: '教师',
      permissions: ['view_questions', 'create_exams', 'grade_exams', 'view_students'],
      description: '教师用户，可创建考试和批改作业',
    },
    student: {
      name: '学生',
      permissions: ['take_exams', 'view_progress', 'access_study_materials'],
      description: '学生用户，可参加考试和查看学习进度',
    },
    guest: {
      name: '访客',
      permissions: ['view_public_content'],
      description: '访客用户，仅可查看公开内容',
    },
  },

  exam: {
    maxDuration: 3600,
    minDuration: 300,
    autoSubmit: true,
    autoSaveInterval: 60,
    passingScore: 60,
    categories: [
      { id: 'chinese', name: '语文' },
      { id: 'math', name: '数学' },
      { id: 'english', name: '英语' },
      { id: 'physics', name: '物理' },
      { id: 'chemistry', name: '化学' },
      { id: 'biology', name: '生物' },
      { id: 'history', name: '历史' },
      { id: 'geography', name: '地理' },
      { id: 'politics', name: '政治' },
      { id: 'japanese', name: '日语' },
    ],
    difficultyLevels: [
      { id: 'easy', name: '简单' },
      { id: 'medium', name: '中等' },
      { id: 'hard', name: '困难' },
      { id: 'expert', name: '专家' },
    ],
    gradeScale: {
      A: { min: 90, max: 100, label: '优秀' },
      B: { min: 80, max: 89, label: '良好' },
      C: { min: 70, max: 79, label: '中等' },
      D: { min: 60, max: 69, label: '及格' },
      F: { min: 0, max: 59, label: '不及格' },
    },
  },

  user: {
    usernameLength: { min: 3, max: 20 },
    passwordLength: { min: 6, max: 32 },
    sessionTimeout: 1800,
    maxLoginAttempts: 5,
  },

  learning: {
    dailyGoal: 30,
    weeklyGoal: 210,
    streakBonus: 1.5,
  },

  promotion: {
    requiredScore: 60,
    retriesAllowed: 1,
    gradeLevels: [
      { id: 'g1', name: '一年级' },
      { id: 'g2', name: '二年级' },
      { id: 'g3', name: '三年级' },
      { id: 'g4', name: '四年级' },
      { id: 'g5', name: '五年级' },
      { id: 'g6', name: '六年级' },
      { id: 'g7', name: '七年级' },
      { id: 'g8', name: '八年级' },
      { id: 'g9', name: '九年级', trackRequired: true },
      { id: 'g10', name: '高一' },
      { id: 'g11', name: '高二' },
      { id: 'g12', name: '高三' },
    ],
    tracks: [
      { id: 'arts', name: '文科', subjects: ['chinese', 'history', 'geography', 'politics'] },
      { id: 'science', name: '理科', subjects: ['math', 'physics', 'chemistry', 'biology'] },
    ],
    classSize: 45,
  },

  teacherTitle: {
    levels: [
      { id: 'assistant', name: '助教', minExperience: 0 },
      { id: 'lecturer', name: '讲师', minExperience: 2 },
      { id: 'associate', name: '副教授', minExperience: 5 },
      { id: 'professor', name: '教授', minExperience: 10 },
    ],
    evaluationPeriod: 365,
    minimumScore: 80,
  },

  security: {
    passwordPolicy: {
      requireUppercase: true,
      requireLowercase: true,
      requireNumber: true,
    },
  },
};

export default SYSTEM_RULES;

export const getRolePermissions = (role) => SYSTEM_RULES.roles[role]?.permissions || [];
export const hasPermission = (role, permission) => {
  const permissions = getRolePermissions(role);
  return permissions.includes('*') || permissions.includes(permission);
};
