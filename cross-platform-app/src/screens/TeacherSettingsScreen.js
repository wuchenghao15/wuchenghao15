import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, ActivityIndicator, Alert} from 'react-native';
import PlatformAdapter from '../adapters/PlatformAdapter';
import AIService from '../services/AIService';
import ProfessorSystem from '../services/professor_system';

const TeacherSettingsScreen = ({navigation}) => {
  const [aiStatus, setAiStatus] = useState(null);
  const [aiEnabled, setAiEnabled] = useState(true);
  const [teacherInfo, setTeacherInfo] = useState(null);
  const [titleLevels, setTitleLevels] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [assignedSubjects, setAssignedSubjects] = useState([]);
  const [stats, setStats] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    checkAIStatus();
    loadTeacherInfo();
    loadTitleLevels();
    loadSubjects();
    loadStats();
  }, []);

  const checkAIStatus = async () => {
    const status = await AIService.getAIStatus();
    setAiStatus(status);
  };

  const loadTeacherInfo = async () => {
    try {
      const info = await ProfessorSystem.getTeacherInfo();
      setTeacherInfo(info);
    } catch (error) {
      console.warn('获取教师信息失败:', error);
    }
  };

  const loadTitleLevels = async () => {
    const levels = [
      {id: 'assistant', name: '助教', icon: '🎓', requiredExp: 0, description: '基础培训合格'},
      {id: 'lecturer', name: '讲师', icon: '📖', requiredExp: 2, description: '取得教师资格证，2年教学经验'},
      {id: 'associate_professor', name: '副教授', icon: '🏆', requiredExp: 5, description: '硕士学位，发表论文5篇以上'},
      {id: 'professor', name: '教授', icon: '👑', requiredExp: 10, description: '博士学位，重要发表，5年领导经验'},
    ];
    setTitleLevels(levels);
  };

  const loadSubjects = async () => {
    const subs = [
      {id: 'chinese', name: '语文', icon: '📖', hours: 6},
      {id: 'math', name: '数学', icon: '📐', hours: 6},
      {id: 'english', name: '英语', icon: '🔤', hours: 5},
      {id: 'physics', name: '物理', icon: '⚛️', hours: 4},
      {id: 'chemistry', name: '化学', icon: '🧪', hours: 4},
      {id: 'biology', name: '生物', icon: '🧬', hours: 3},
      {id: 'history', name: '历史', icon: '📜', hours: 3},
      {id: 'geography', name: '地理', icon: '🌍', hours: 3},
      {id: 'politics', name: '政治', icon: '📖', hours: 2},
      {id: 'japanese', name: '日语', icon: '🌸', hours: 3},
    ];
    setSubjects(subs);
    setAssignedSubjects(['chinese', 'english']);
  };

  const loadStats = async () => {
    const statsData = {
      totalStudents: 156,
      avgScore: 85.5,
      classesTaught: 12,
      papersPublished: 3,
      yearsOfExperience: 8,
      currentTitle: '副教授',
      nextTitle: '教授',
      progressToNext: 80,
    };
    setStats(statsData);
  };

  const handleTitleAssessment = async () => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', '无法进行职称测评，请确保AI服务在线');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await AIService.assessTeacherTitle({
        teacherId: teacherInfo?.id,
        experience: stats?.yearsOfExperience,
        papers: stats?.papersPublished,
        students: stats?.totalStudents,
        avgScore: stats?.avgScore,
      });

      if (result.success) {
        Alert.alert('测评完成', `测评结果：${result.title建议}\n综合评分：${result.score}/100\n${result.recommendations}`);
      } else {
        Alert.alert('测评失败', result.message);
      }
    } catch (error) {
      Alert.alert('测评失败', error.message);
    }
    setIsProcessing(false);
  };

  const handleAssignSubject = (subjectId) => {
    if (assignedSubjects.includes(subjectId)) {
      setAssignedSubjects(prev => prev.filter(id => id !== subjectId));
    } else {
      if (assignedSubjects.length >= 3) {
        Alert.alert('提示', '最多只能负责3个科目');
        return;
      }
      setAssignedSubjects(prev => [...prev, subjectId]);
    }
  };

  const handleSaveAssignments = async () => {
    try {
      const result = await ProfessorSystem.assignSubjects(assignedSubjects);
      if (result.success) {
        Alert.alert('保存成功', '科目委派已保存');
      } else {
        Alert.alert('保存失败', result.message);
      }
    } catch (error) {
      Alert.alert('保存失败', error.message);
    }
  };

  const handleAIEnhance = async () => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', '无法使用AI增强功能');
      return;
    }

    try {
      const result = await AIService.enhanceTeaching({
        subject: assignedSubjects[0],
        studentCount: stats?.totalStudents,
        avgScore: stats?.avgScore,
      });

      if (result.success) {
        Alert.alert('AI增强完成', `教学建议已生成：\n\n${result.suggestions}`);
      } else {
        Alert.alert('增强失败', result.message);
      }
    } catch (error) {
      Alert.alert('增强失败', error.message);
    }
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: PlatformAdapter.getBackgroundColor(),
    },
    header: {
      padding: 24,
      paddingTop: 32,
    },
    title: {
      fontSize: 28,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    subtitle: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      marginTop: 8,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    sections: {
      paddingHorizontal: 24,
    },
    section: {
      marginBottom: 24,
    },
    sectionTitle: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.5,
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
      paddingLeft: 8,
    },
    card: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      overflow: 'hidden',
      ...PlatformAdapter.getElevation(),
    },
    cardItem: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 16,
      borderBottomWidth: 1,
      borderBottomColor: PlatformAdapter.isHyperOS() ? 'rgba(255,255,255,0.05)' : '#f0f0f0',
    },
    cardItemLast: {
      borderBottomWidth: 0,
    },
    itemLabel: {
      flex: 1,
      fontSize: 16,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    itemValue: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    itemIcon: {
      fontSize: 18,
      marginRight: 12,
    },
    itemBadge: {
      paddingHorizontal: 8,
      paddingVertical: 2,
      borderRadius: 12,
      fontSize: 12,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    badgeOnline: {
      backgroundColor: 'rgba(68, 255, 68, 0.2)',
      color: '#44ff44',
    },
    badgeOffline: {
      backgroundColor: 'rgba(255, 68, 68, 0.2)',
      color: '#ff4444',
    },
    teacherCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 16,
    },
    teacherHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    teacherAvatar: {
      width: 64,
      height: 64,
      borderRadius: 32,
      backgroundColor: PlatformAdapter.getPrimaryColor(),
      alignItems: 'center',
      justifyContent: 'center',
      marginRight: 16,
    },
    teacherAvatarText: {
      fontSize: 24,
      color: '#ffffff',
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    teacherInfo: {
      flex: 1,
    },
    teacherName: {
      fontSize: 20,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    teacherTitle: {
      fontSize: 14,
      color: PlatformAdapter.getPrimaryColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginTop: 4,
    },
    teacherMeta: {
      flexDirection: 'row',
      gap: 16,
    },
    teacherMetaItem: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.7,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    statsCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      ...PlatformAdapter.getElevation(),
    },
    statsHeader: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    statsGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 16,
    },
    statItem: {
      flex: 1,
      minWidth: 100,
      alignItems: 'center',
    },
    statValue: {
      fontSize: 20,
      fontWeight: 'bold',
      color: PlatformAdapter.getPrimaryColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    statLabel: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      marginTop: 4,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    progressCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      ...PlatformAdapter.getElevation(),
      marginBottom: 16,
    },
    progressHeader: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    progressRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: 8,
    },
    progressLabel: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    progressBar: {
      height: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.1)' : '#e0e0e0',
      borderRadius: 4,
      overflow: 'hidden',
    },
    progressFill: {
      height: '100%',
      backgroundColor: PlatformAdapter.getPrimaryColor(),
      borderRadius: 4,
    },
    aiCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 16,
    },
    aiHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    aiIcon: {
      fontSize: 24,
      marginRight: 12,
    },
    aiTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    aiStatusRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingVertical: 4,
    },
    aiStatusLabel: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.7,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    aiStatusValue: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    aiStatusIndicator: {
      width: 8,
      height: 8,
      borderRadius: 4,
      marginRight: 6,
    },
    aiOnline: {
      backgroundColor: '#44ff44',
    },
    aiOffline: {
      backgroundColor: '#ff4444',
    },
    titleCard: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      overflow: 'hidden',
      ...PlatformAdapter.getElevation(),
    },
    titleHeader: {
      padding: 16,
      borderBottomWidth: 1,
      borderBottomColor: PlatformAdapter.isHyperOS() ? 'rgba(255,255,255,0.05)' : '#f0f0f0',
    },
    titleTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    titleList: {
      padding: 8,
    },
    titleItem: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.02)' : '#f8f8f8',
    },
    titleItemActive: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderWidth: 1,
      borderColor: PlatformAdapter.getPrimaryColor(),
    },
    titleIcon: {
      fontSize: 20,
      marginRight: 12,
    },
    titleName: {
      flex: 1,
      fontSize: 14,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    titleExp: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    subjectCard: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      overflow: 'hidden',
      ...PlatformAdapter.getElevation(),
    },
    subjectHeader: {
      padding: 16,
      borderBottomWidth: 1,
      borderBottomColor: PlatformAdapter.isHyperOS() ? 'rgba(255,255,255,0.05)' : '#f0f0f0',
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    subjectTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    subjectAction: {
      fontSize: 14,
      color: PlatformAdapter.getPrimaryColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    subjectList: {
      padding: 8,
    },
    subjectItem: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.02)' : '#f8f8f8',
    },
    subjectItemSelected: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderWidth: 1,
      borderColor: PlatformAdapter.getPrimaryColor(),
    },
    subjectIcon: {
      fontSize: 20,
      marginRight: 12,
    },
    subjectName: {
      flex: 1,
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    subjectHours: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    actionButton: {
      ...PlatformAdapter.getButtonStyle('primary'),
      alignItems: 'center',
      padding: 16,
      marginTop: 16,
    },
    actionButtonText: {
      color: '#ffffff',
      fontSize: 16,
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    actionButtonSecondary: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.1)' : '#f0f0f0',
      alignItems: 'center',
      padding: 16,
      marginTop: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
    },
    actionButtonTextSecondary: {
      color: PlatformAdapter.getTextColor(),
      fontSize: 16,
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    actionButtonDisabled: {
      opacity: 0.5,
    },
  });

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>教师系统</Text>
        <Text style={styles.subtitle}>管理教师信息和教学设置</Text>
      </View>

      <View style={styles.sections}>
        {teacherInfo && (
          <View style={styles.teacherCard}>
            <View style={styles.teacherHeader}>
              <View style={styles.teacherAvatar}>
                <Text style={styles.teacherAvatarText}>
                  {teacherInfo.name?.charAt(0) || '教'}
                </Text>
              </View>
              <View style={styles.teacherInfo}>
                <Text style={styles.teacherName}>{teacherInfo.name || '教师姓名'}</Text>
                <Text style={styles.teacherTitle}>{stats?.currentTitle || '职称'}</Text>
                <View style={styles.teacherMeta}>
                  <Text style={styles.teacherMetaItem}>📚 {stats?.yearsOfExperience || 0}年教龄</Text>
                  <Text style={styles.teacherMetaItem}>👥 {stats?.totalStudents || 0}名学生</Text>
                </View>
              </View>
            </View>
          </View>
        )}

        {stats && (
          <View style={styles.statsCard}>
            <Text style={styles.statsHeader}>📊 教学统计</Text>
            <View style={styles.statsGrid}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{stats.totalStudents}</Text>
                <Text style={styles.statLabel}>学生总数</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{stats.avgScore}</Text>
                <Text style={styles.statLabel}>平均分</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{stats.classesTaught}</Text>
                <Text style={styles.statLabel}>授课班级</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{stats.papersPublished}</Text>
                <Text style={styles.statLabel}>发表论文</Text>
              </View>
            </View>
          </View>
        )}

        {stats && (
          <View style={styles.progressCard}>
            <Text style={styles.progressHeader}>🎯 职称晋升进度</Text>
            <View style={styles.progressRow}>
              <Text style={styles.progressLabel}>{stats.currentTitle}</Text>
              <Text style={styles.progressLabel}>{stats.nextTitle}</Text>
            </View>
            <View style={styles.progressBar}>
              <View style={[styles.progressFill, {width: `${stats.progressToNext}%`}]} />
            </View>
            <View style={styles.progressRow}>
              <Text style={{...styles.progressLabel, fontSize: 12, opacity: 0.6}}>
                晋升进度: {stats.progressToNext}%
              </Text>
            </View>
          </View>
        )}

        {aiStatus && (
          <View style={styles.aiCard}>
            <View style={styles.aiHeader}>
              <Text style={styles.aiIcon}>🤖</Text>
              <Text style={styles.aiTitle}>AI教学助手</Text>
            </View>
            <View style={styles.aiStatusRow}>
              <Text style={styles.aiStatusLabel}>AI服务</Text>
              <View style={{flexDirection: 'row', alignItems: 'center'}}>
                <View style={[styles.aiStatusIndicator, aiStatus.online ? styles.aiOnline : styles.aiOffline]} />
                <Text style={styles.aiStatusValue}>{aiStatus.online ? '在线' : '离线'}</Text>
              </View>
            </View>
            <View style={styles.aiStatusRow}>
              <Text style={styles.aiStatusLabel}>可用功能</Text>
              <Text style={styles.aiStatusValue}>职称测评、智能出题、教学建议</Text>
            </View>
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>职称等级</Text>
          <View style={styles.titleCard}>
            <View style={styles.titleHeader}>
              <Text style={styles.titleTitle}>📜 教师职称体系</Text>
            </View>
            <View style={styles.titleList}>
              {titleLevels.map((level) => (
                <View 
                  key={level.id} 
                  style={[styles.titleItem, stats?.currentTitle === level.name && styles.titleItemActive]}>
                  <Text style={styles.titleIcon}>{level.icon}</Text>
                  <View style={{flex: 1}}>
                    <Text style={styles.titleName}>{level.name}</Text>
                    <Text style={{...styles.titleExp, fontSize: 11}}>{level.description}</Text>
                  </View>
                  <Text style={styles.titleExp}>{level.requiredExp}年</Text>
                </View>
              ))}
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>科目委派</Text>
          <View style={styles.subjectCard}>
            <View style={styles.subjectHeader}>
              <Text style={styles.subjectTitle}>📚 选择授课科目</Text>
              <TouchableOpacity onPress={handleSaveAssignments}>
                <Text style={styles.subjectAction}>保存</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.subjectList}>
              {subjects.map((subject) => (
                <TouchableOpacity
                  key={subject.id}
                  style={[styles.subjectItem, assignedSubjects.includes(subject.id) && styles.subjectItemSelected]}
                  onPress={() => handleAssignSubject(subject.id)}>
                  <Text style={styles.subjectIcon}>{subject.icon}</Text>
                  <Text style={styles.subjectName}>{subject.name}</Text>
                  <Text style={styles.subjectHours}>{subject.hours}课时/周</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </View>

        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={handleTitleAssessment}
          disabled={!aiStatus?.online || isProcessing}>
          {isProcessing ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.actionButtonText}>🤖 AI职称测评</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.actionButtonSecondary} 
          onPress={handleAIEnhance}
          disabled={!aiStatus?.online}>
          <Text style={styles.actionButtonTextSecondary}>✨ AI教学增强</Text>
        </TouchableOpacity>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default TeacherSettingsScreen;