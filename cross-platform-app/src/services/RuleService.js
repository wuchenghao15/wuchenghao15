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
