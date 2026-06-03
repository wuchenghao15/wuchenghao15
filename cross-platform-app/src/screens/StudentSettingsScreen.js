import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Switch, ActivityIndicator, Alert} from 'react-native';
import PlatformAdapter from '../adapters/PlatformAdapter';
import AIService from '../services/AIService';
import StudentStreamSystem from '../services/student_stream_system';
import ClassManager from '../services/class_manager';

const StudentSettingsScreen = ({navigation}) => {
  const [aiStatus, setAiStatus] = useState(null);
  const [studentInfo, setStudentInfo] = useState(null);
  const [stats, setStats] = useState(null);
  const [streamOptions, setStreamOptions] = useState([]);
  const [selectedStream, setSelectedStream] = useState(null);
  const [classes, setClasses] = useState([]);
  const [currentClass, setCurrentClass] = useState(null);
  const [gradeLevel, setGradeLevel] = useState(9);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    checkAIStatus();
    loadStudentInfo();
    loadStats();
    loadStreamOptions();
    loadClasses();
  }, []);

  const checkAIStatus = async () => {
    const status = await AIService.getAIStatus();
    setAiStatus(status);
  };

  const loadStudentInfo = async () => {
    const info = {
      id: 'S2024001',
      name: '张三',
      avatar: '张',
      grade: 9,
      className: '初三(1)班',
      stream: '理科',
      admissionYear: 2021,
    };
    setStudentInfo(info);
    setGradeLevel(info.grade);
    setSelectedStream(info.stream);
  };

  const loadStats = async () => {
    const statsData = {
      totalExams: 24,
      avgScore: 82.5,
      rank: 15,
      totalStudents: 45,
      completedCourses: 18,
      studyDays: 156,
      weeklyHours: 35,
      weakSubjects: ['数学', '物理'],
      strongSubjects: ['语文', '英语'],
    };
    setStats(statsData);
  };

  const loadStreamOptions = async () => {
    const streams = [
      {id: 'science', name: '理科', icon: '🔬', subjects: ['数学', '物理', '化学', '生物']},
      {id: 'arts', name: '文科', icon: '📖', subjects: ['语文', '历史', '地理', '政治']},
      {id: 'comprehensive', name: '综合', icon: '⚖️', subjects: ['语文', '数学', '英语', '自选']},
    ];
    setStreamOptions(streams);
  };

  const loadClasses = async () => {
    const classList = [
      {id: 'class_1', name: '初三(1)班', count: 42, teacher: '李老师'},
      {id: 'class_2', name: '初三(2)班', count: 45, teacher: '王老师'},
      {id: 'class_3', name: '初三(3)班', count: 40, teacher: '张老师'},
      {id: 'class_4', name: '初三(4)班', count: 43, teacher: '刘老师'},
    ];
    setClasses(classList);
    setCurrentClass('class_1');
  };

  const handleStreamChange = async (streamName) => {
    if (gradeLevel < 9) {
      Alert.alert('提示', '只有9年级及以上学生才能分科');
      return;
    }

    try {
      const result = await StudentStreamSystem.selectStream(streamName);
      if (result.success) {
        setSelectedStream(streamName);
        Alert.alert('分科成功', `已选择${streamName}方向`);
      } else {
        Alert.alert('分科失败', result.message);
      }
    } catch (error) {
      Alert.alert('分科失败', error.message);
    }
  };

  const handleClassChange = async (classId) => {
    try {
      const result = await ClassManager.changeClass(classId);
      if (result.success) {
        setCurrentClass(classId);
        const selectedClass = classes.find(c => c.id === classId);
        Alert.alert('调班成功', `已调至${selectedClass?.name}`);
      } else {
        Alert.alert('调班失败', result.message);
      }
    } catch (error) {
      Alert.alert('调班失败', error.message);
    }
  };

  const handleAIAnalysis = async () => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', '无法进行AI分析，请确保AI服务在线');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await AIService.analyzeStudent({
        studentId: studentInfo?.id,
        grade: gradeLevel,
        stream: selectedStream,
        avgScore: stats?.avgScore,
        weakSubjects: stats?.weakSubjects,
        strongSubjects: stats?.strongSubjects,
      });

      if (result.success) {
        Alert.alert('分析完成', `学习建议：\n\n${result.suggestions}\n\n推荐科目：${result.recommendedSubjects.join('、')}`);
      } else {
        Alert.alert('分析失败', result.message);
      }
    } catch (error) {
      Alert.alert('分析失败', error.message);
    }
    setIsProcessing(false);
  };

  const handleAITest = async () => {
    if (!aiStatus?.online) {
      Alert.alert('AI服务离线', '无法进行AI摸底测试');
      return;
    }

    try {
      const result = await AIService.generatePlacementTest({
        grade: gradeLevel,
        stream: selectedStream,
      });

      if (result.success) {
        Alert.alert('测试生成成功', `已生成${result.questionCount}道摸底测试题目`);
        navigation.navigate('ExamScreen', {testId: result.testId});
      } else {
        Alert.alert('测试生成失败', result.message);
      }
    } catch (error) {
      Alert.alert('测试生成失败', error.message);
    }
  };

  const gradeLevels = [7, 8, 9, 10, 11, 12];

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
    studentCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 16,
    },
    studentHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    studentAvatar: {
      width: 64,
      height: 64,
      borderRadius: 32,
      backgroundColor: PlatformAdapter.getPrimaryColor(),
      alignItems: 'center',
      justifyContent: 'center',
      marginRight: 16,
    },
    studentAvatarText: {
      fontSize: 24,
      color: '#ffffff',
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    studentInfo: {
      flex: 1,
    },
    studentName: {
      fontSize: 20,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    studentClass: {
      fontSize: 14,
      color: PlatformAdapter.getPrimaryColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginTop: 4,
    },
    studentMeta: {
      flexDirection: 'row',
      gap: 16,
    },
    studentMetaItem: {
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
    subjectCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      ...PlatformAdapter.getElevation(),
    },
    subjectHeader: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    subjectRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingVertical: 8,
    },
    subjectName: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    subjectBadge: {
      paddingHorizontal: 8,
      paddingVertical: 2,
      borderRadius: 12,
      fontSize: 12,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    badgeWeak: {
      backgroundColor: 'rgba(255, 68, 68, 0.2)',
      color: '#ff4444',
    },
    badgeStrong: {
      backgroundColor: 'rgba(68, 255, 68, 0.2)',
      color: '#44ff44',
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
    streamCard: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      overflow: 'hidden',
      ...PlatformAdapter.getElevation(),
    },
    streamHeader: {
      padding: 16,
      borderBottomWidth: 1,
      borderBottomColor: PlatformAdapter.isHyperOS() ? 'rgba(255,255,255,0.05)' : '#f0f0f0',
    },
    streamTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    streamDesc: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      marginTop: 4,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    streamList: {
      padding: 8,
    },
    streamItem: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 12,
      borderRadius: PlatformAdapter.getCornerRadius(),
      marginBottom: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.02)' : '#f8f8f8',
    },
    streamItemSelected: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderWidth: 1,
      borderColor: PlatformAdapter.getPrimaryColor(),
    },
    streamIcon: {
      fontSize: 20,
      marginRight: 12,
    },
    streamName: {
      flex: 1,
      fontSize: 14,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    streamSubjects: {
      fontSize: 11,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      marginTop: 4,
    },
    gradeSelector: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 8,
    },
    gradeOption: {
      paddingHorizontal: 16,
      paddingVertical: 8,
      borderRadius: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.1)' : '#f0f0f0',
      alignItems: 'center',
      minWidth: 60,
    },
    gradeOptionSelected: {
      backgroundColor: PlatformAdapter.getPrimaryColor(),
    },
    gradeText: {
      fontSize: 14,
      fontFamily: PlatformAdapter.getFontFamily(),
      fontWeight: 'bold',
    },
    gradeTextSelected: {
      color: '#ffffff',
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
        <Text style={styles.title}>学生信息系统</Text>
        <Text style={styles.subtitle}>管理学生信息和学习设置</Text>
      </View>

      <View style={styles.sections}>
        {studentInfo && (
          <View style={styles.studentCard}>
            <View style={styles.studentHeader}>
              <View style={styles.studentAvatar}>
                <Text style={styles.studentAvatarText}>{studentInfo.avatar}</Text>
              </View>
              <View style={styles.studentInfo}>
                <Text style={styles.studentName}>{studentInfo.name}</Text>
                <Text style={styles.studentClass}>{studentInfo.className} · {studentInfo.stream}方向</Text>
                <View style={styles.studentMeta}>
                  <Text style={styles.studentMetaItem}>📚 {studentInfo.grade}年级</Text>
                  <Text style={styles.studentMetaItem}>🆔 {studentInfo.id}</Text>
                </View>
              </View>
            </View>
          </View>
        )}

        {stats && (
          <View style={styles.statsCard}>
            <Text style={styles.statsHeader}>📊 学习统计</Text>
            <View style={styles.statsGrid}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{stats.totalExams}</Text>
                <Text style={styles.statLabel}>考试次数</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{stats.avgScore}</Text>
                <Text style={styles.statLabel}>平均分</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>第{stats.rank}名</Text>
                <Text style={styles.statLabel}>年级排名</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{stats.studyDays}</Text>
                <Text style={styles.statLabel}>学习天数</Text>
              </View>
            </View>
          </View>
        )}

        {stats && (
          <View style={styles.subjectCard}>
            <Text style={styles.subjectHeader}>🎯 科目分析</Text>
            <View style={{marginBottom: 12}}>
              <Text style={{fontSize: 12, color: '#44ff44', marginBottom: 4}}>优势科目</Text>
              <View style={styles.subjectRow}>
                {stats.strongSubjects.map((subject) => (
                  <Text key={subject} style={[styles.subjectBadge, styles.badgeStrong]}>
                    {subject}
                  </Text>
                ))}
              </View>
            </View>
            <View>
              <Text style={{fontSize: 12, color: '#ff4444', marginBottom: 4}}>薄弱科目</Text>
              <View style={styles.subjectRow}>
                {stats.weakSubjects.map((subject) => (
                  <Text key={subject} style={[styles.subjectBadge, styles.badgeWeak]}>
                    {subject}
                  </Text>
                ))}
              </View>
            </View>
          </View>
        )}

        {aiStatus && (
          <View style={styles.aiCard}>
            <View style={styles.aiHeader}>
              <Text style={styles.aiIcon}>🤖</Text>
              <Text style={styles.aiTitle}>AI学习助手</Text>
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
              <Text style={styles.aiStatusValue}>学习分析、智能推荐、摸底测试</Text>
            </View>
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>年级设置</Text>
          <View style={styles.card}>
            <View style={styles.cardItem}>
              <Text style={styles.itemIcon}>📚</Text>
              <Text style={styles.itemLabel}>当前年级</Text>
            </View>
            <View style={[styles.cardItem, styles.cardItemLast]}>
              <View style={styles.gradeSelector}>
                {gradeLevels.map((grade) => (
                  <TouchableOpacity
                    key={grade}
                    style={[styles.gradeOption, gradeLevel === grade && styles.gradeOptionSelected]}
                    onPress={() => setGradeLevel(grade)}>
                    <Text style={[styles.gradeText, gradeLevel === grade && styles.gradeTextSelected]}>
                      {grade}年级
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>分科选择</Text>
          <View style={styles.streamCard}>
            <View style={styles.streamHeader}>
              <Text style={styles.streamTitle}>🎓 学科方向</Text>
              <Text style={styles.streamDesc}>
                {gradeLevel >= 9 ? '9年级及以上学生可选择文理科方向' : '请先升级到9年级'}
              </Text>
            </View>
            <View style={styles.streamList}>
              {streamOptions.map((stream) => (
                <TouchableOpacity
                  key={stream.id}
                  style={[styles.streamItem, selectedStream === stream.name && styles.streamItemSelected]}
                  onPress={() => handleStreamChange(stream.name)}
                  disabled={gradeLevel < 9}>
                  <Text style={styles.streamIcon}>{stream.icon}</Text>
                  <View style={{flex: 1}}>
                    <Text style={styles.streamName}>{stream.name}</Text>
                    <Text style={styles.streamSubjects}>
                      {stream.subjects.join(' · ')}
                    </Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>班级管理</Text>
          <View style={styles.card}>
            {classes.map((cls) => (
              <TouchableOpacity
                key={cls.id}
                style={[styles.cardItem, classes.indexOf(cls) === classes.length - 1 && styles.cardItemLast]}
                onPress={() => handleClassChange(cls.id)}>
                <Text style={styles.itemIcon}>🏫</Text>
                <Text style={styles.itemLabel}>{cls.name}</Text>
                <Text style={styles.itemValue}>{cls.count}人 · {cls.teacher}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={handleAIAnalysis}
          disabled={!aiStatus?.online || isProcessing}>
          {isProcessing ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.actionButtonText}>🤖 AI学习分析</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.actionButtonSecondary} 
          onPress={handleAITest}
          disabled={!aiStatus?.online}>
          <Text style={styles.actionButtonTextSecondary}>📝 AI摸底测试</Text>
        </TouchableOpacity>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default StudentSettingsScreen;