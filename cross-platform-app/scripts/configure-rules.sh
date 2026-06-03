#!/bin/bash

# 系统规则配置初始化脚本
echo "=========================================="
echo "  系统规则配置初始化"
echo "=========================================="
echo ""

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装，请先安装Node.js"
    exit 1
fi

echo "[1/4] 检查项目结构..."
if [ ! -d "src" ]; then
    echo "❌ 项目结构不正确"
    exit 1
fi
echo "✓ 项目结构正确"

echo ""
echo "[2/4] 创建配置目录..."
mkdir -p src/config
echo "✓ 配置目录创建完成"

echo ""
echo "[3/4] 生成系统规则配置文件..."

cat > src/config/rules.config.js << 'EOF'
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
EOF

echo "✓ 系统规则配置文件已创建"

echo ""
echo "[4/4] 创建规则服务..."

cat > src/services/RuleService.js << 'EOF'
import { SYSTEM_RULES, hasPermission, calculateGrade, validatePassword } from '../config/rules.config';

class RuleService {
  constructor() {
    this.rules = SYSTEM_RULES;
  }

  getRule(rulePath) {
    const pathParts = rulePath.split('.');
    let result = this.rules;
    for (const part of pathParts) {
      result = result?.[part];
      if (!result) return null;
    }
    return result;
  }

  checkPermission(role, permission) {
    return hasPermission(role, permission);
  }

  validateExamDuration(duration) {
    const { minDuration, maxDuration } = this.rules.exam;
    return duration >= minDuration && duration <= maxDuration;
  }

  validateUserAnswer(answer, correctAnswer) {
    return answer === correctAnswer;
  }

  calculateExamGrade(score) {
    return calculateGrade(score);
  }

  validatePassword(password) {
    return validatePassword(password);
  }

  validateUsername(username) {
    const { min, max } = this.rules.user.usernameLength;
    return username.length >= min && username.length <= max;
  }

  isGradePromotable(score) {
    return score >= this.rules.promotion.requiredScore;
  }

  canRetryExam(attemptCount) {
    return attemptCount < this.rules.exam.maxRetries;
  }

  getTrackSubjects(trackId) {
    const track = this.rules.promotion.tracks.find(t => t.id === trackId);
    return track?.subjects || [];
  }

  getExamCategories() {
    return this.rules.exam.categories;
  }

  getDifficultyLevels() {
    return this.rules.exam.difficultyLevels;
  }

  getTeacherTitleLevel(experienceYears) {
    const levels = [...this.rules.teacherTitle.levels].sort((a, b) => b.minExperience - a.minExperience);
    return levels.find(l => experienceYears >= l.minExperience) || levels[levels.length - 1];
  }

  calculateClassCount(studentCount) {
    return Math.ceil(studentCount / this.rules.promotion.classSize);
  }

  getNotificationTypes() {
    return this.rules.system.notificationTypes;
  }

  isMaintenanceTime() {
    const now = new Date();
    const hour = now.getHours();
    const { start, end } = this.rules.system.maintenanceWindow;
    const startHour = parseInt(start.split(':')[0]);
    const endHour = parseInt(end.split(':')[0]);
    
    if (startHour < endHour) {
      return hour >= startHour && hour < endHour;
    } else {
      return hour >= startHour || hour < endHour;
    }
  }
}

export default new RuleService();
EOF

echo "✓ 规则服务已创建"

echo ""
echo "=========================================="
echo "  系统规则配置初始化完成！"
echo "=========================================="
echo ""
echo "配置文件:"
echo "  - src/config/rules.config.js"
echo "  - src/services/RuleService.js"
echo ""
echo "规则配置包含:"
echo "  ✓ 用户角色规则 (5种角色)"
echo "  ✓ 考试规则 (10个科目, 4种难度)"
echo "  ✓ 用户规则 (密码策略, 会话管理)"
echo "  ✓ 学习规则 (目标设定, 奖励机制)"
echo "  ✓ 升级规则 (年级划分, 分科规则)"
echo "  ✓ 教师职称规则 (4级职称)"
echo "  ✓ 安全规则 (密码策略)"
echo ""
echo "规则服务功能:"
echo "  ✓ 权限检查"
echo "  ✓ 数据验证"
echo "  ✓ 成绩计算"
echo "  ✓ 业务规则校验"