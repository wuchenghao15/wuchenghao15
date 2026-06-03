import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Alert, ActivityIndicator} from 'react-native';
import OfflineStorageService from '../services/OfflineStorageService';
import PlatformAdapter from '../adapters/PlatformAdapter';

const OfflineExamScreen = ({navigation}) => {
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [isExamStarted, setIsExamStarted] = useState(false);
  const [isFinished, setIsFinished] = useState(false);
  const [score, setScore] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSubjects();
  }, []);

  const loadSubjects = async () => {
    const subjectList = [
      {id: 'chinese', name: '语文', icon: '📖'},
      {id: 'math', name: '数学', icon: '🧮'},
      {id: 'english', name: '英语', icon: '🔤'},
      {id: 'physics', name: '物理', icon: '⚛️'},
      {id: 'chemistry', name: '化学', icon: '🧪'},
      {id: 'biology', name: '生物', icon: '🧬'},
      {id: 'history', name: '历史', icon: '📜'},
      {id: 'geography', name: '地理', icon: '🌍'},
      {id: 'politics', name: '政治', icon: '⚖️'},
      {id: 'japanese', name: '日语', icon: '🇯🇵'},
    ];
    setSubjects(subjectList);
  };

  const loadQuestions = async (subjectId) => {
    setLoading(true);
    try {
      const subjectQuestions = await OfflineStorageService.getQuestionsBySubject(subjectId);
      
      if (subjectQuestions.length === 0) {
        Alert.alert('提示', '该科目暂无离线题目，请先下载题库');
        setLoading(false);
        return;
      }

      const shuffled = [...subjectQuestions].sort(() => Math.random() - 0.5).slice(0, 10);
      setQuestions(shuffled);
      setSelectedSubject(subjectId);
      setIsExamStarted(true);
      setCurrentIndex(0);
      setAnswers({});
      setIsFinished(false);
      setScore(0);
    } catch (error) {
      Alert.alert('错误', '加载题目失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = (questionId, answer) => {
    setAnswers(prev => ({...prev, [questionId]: answer}));
  };

  const goToNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const goToPrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const finishExam = () => {
    let correctCount = 0;
    questions.forEach(q => {
      if (answers[q.id] === q.answer) {
        correctCount++;
      }
    });
    
    const examScore = Math.round((correctCount / questions.length) * 100);
    setScore(examScore);
    setIsFinished(true);

    saveExamRecord(correctCount, questions.length, examScore);
  };

  const saveExamRecord = async (correctCount, totalCount, examScore) => {
    try {
      const record = {
        record_id: `exam_${Date.now()}`,
        exam_id: `offline_${selectedSubject}_${Date.now()}`,
        subject: selectedSubject,
        questions: questions.map(q => q.id),
        answers: Object.entries(answers).map(([k, v]) => ({question_id: k, answer: v})),
        score: examScore,
        total_score: 100,
        status: 'completed',
      };
      await OfflineStorageService.saveExamRecord(record);
      
      const userId = 'local_user';
      await OfflineStorageService.updateUserProgress(userId, selectedSubject, correctCount, totalCount);
    } catch (error) {
      console.error('保存考试记录失败:', error);
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
      marginBottom: 8,
    },
    subtitle: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.7,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    subjectsSection: {
      paddingHorizontal: 24,
      marginBottom: 24,
    },
    subjectsGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 12,
    },
    subjectCard: {
      width: '31%',
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      padding: 16,
      alignItems: 'center',
      ...PlatformAdapter.getElevation(),
    },
    subjectIcon: {
      fontSize: 28,
      marginBottom: 8,
    },
    subjectName: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      textAlign: 'center',
    },
    examContainer: {
      flex: 1,
      padding: 24,
    },
    questionHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 24,
    },
    questionNumber: {
      fontSize: 16,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    progressBar: {
      flex: 1,
      height: 8,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.1)' : '#e0e0e0',
      borderRadius: 4,
      overflow: 'hidden',
      marginHorizontal: 16,
    },
    progressFill: {
      height: '100%',
      backgroundColor: PlatformAdapter.getPrimaryColor(),
      borderRadius: 4,
    },
    questionCard: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      padding: 20,
      marginBottom: 20,
      ...PlatformAdapter.getElevation(),
    },
    questionContent: {
      fontSize: 18,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 20,
    },
    optionsList: {
      gap: 12,
    },
    optionButton: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#f5f5f5',
      borderRadius: PlatformAdapter.getCornerRadius(),
      borderWidth: 2,
      borderColor: 'transparent',
    },
    optionButtonSelected: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.2)' : 'rgba(98, 0, 238, 0.1)',
      borderColor: PlatformAdapter.getPrimaryColor(),
    },
    optionLetter: {
      width: 32,
      height: 32,
      borderRadius: 16,
      backgroundColor: PlatformAdapter.getPrimaryColor(),
      justifyContent: 'center',
      alignItems: 'center',
      marginRight: 12,
    },
    optionLetterText: {
      color: '#ffffff',
      fontSize: 14,
      fontWeight: 'bold',
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    optionText: {
      flex: 1,
      fontSize: 16,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    navigationButtons: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginTop: 24,
    },
    navButton: {
      ...PlatformAdapter.getButtonStyle('secondary'),
      flex: 1,
      marginHorizontal: 8,
    },
    navButtonText: {
      color: PlatformAdapter.getPrimaryColor(),
      fontSize: 16,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    finishButton: {
      ...PlatformAdapter.getButtonStyle('primary'),
      flex: 1,
      marginHorizontal: 8,
    },
    finishButtonText: {
      color: '#ffffff',
      fontSize: 16,
      fontWeight: 'bold',
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    resultCard: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      padding: 32,
      alignItems: 'center',
      ...PlatformAdapter.getElevation(),
    },
    resultScore: {
      fontSize: 64,
      fontWeight: 'bold',
      color: score >= 60 ? '#44ff44' : '#ff4444',
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 16,
    },
    resultText: {
      fontSize: 18,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 8,
    },
    resultSubtext: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.7,
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 24,
    },
    resultButtons: {
      flexDirection: 'row',
      gap: 12,
      width: '100%',
    },
    resultButton: {
      ...PlatformAdapter.getButtonStyle('primary'),
      flex: 1,
    },
    resultButtonText: {
      color: '#ffffff',
      fontSize: 14,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    backButton: {
      ...PlatformAdapter.getButtonStyle('outline'),
      flex: 1,
    },
    backButtonText: {
      color: PlatformAdapter.getTextColor(),
      fontSize: 14,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    offlineBadge: {
      position: 'absolute',
      top: 100,
      right: 24,
      backgroundColor: '#ffaa00',
      paddingHorizontal: 12,
      paddingVertical: 4,
      borderRadius: 12,
    },
    offlineBadgeText: {
      color: '#ffffff',
      fontSize: 12,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
  });

  if (!isExamStarted) {
    return (
      <ScrollView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>离线考试</Text>
          <Text style={styles.subtitle}>无需网络，随时随地进行测试</Text>
        </View>

        <View style={styles.offlineBadge}>
          <Text style={styles.offlineBadgeText}>📴 离线模式</Text>
        </View>

        <View style={styles.subjectsSection}>
          <Text style={styles.sectionTitle}>选择科目开始测试</Text>
          <View style={styles.subjectsGrid}>
            {subjects.map((subject) => (
              <TouchableOpacity
                key={subject.id}
                style={styles.subjectCard}
                onPress={() => loadQuestions(subject.id)}
                disabled={loading}>
                <Text style={styles.subjectIcon}>{subject.icon}</Text>
                <Text style={styles.subjectName}>{subject.name}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={{height: 32}} />
      </ScrollView>
    );
  }

  if (isFinished) {
    return (
      <ScrollView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>考试完成</Text>
        </View>

        <View style={styles.examContainer}>
          <View style={styles.resultCard}>
            <Text style={styles.resultScore}>{score}</Text>
            <Text style={styles.resultText}>{score >= 60 ? '恭喜通过！' : '继续努力！'}</Text>
            <Text style={styles.resultSubtext}>
              答对 {Object.values(answers).filter((a, i) => a === questions[i]?.answer).length} 题，共 {questions.length} 题
            </Text>
            <View style={styles.resultButtons}>
              <TouchableOpacity style={styles.resultButton} onPress={() => loadQuestions(selectedSubject)}>
                <Text style={styles.resultButtonText}>再考一次</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.backButton} onPress={() => setIsExamStarted(false)}>
                <Text style={styles.backButtonText}>返回</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </ScrollView>
    );
  }

  const currentQuestion = questions[currentIndex];
  const progress = ((currentIndex + 1) / questions.length) * 100;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>离线考试</Text>
        <Text style={styles.subtitle}>{subjects.find(s => s.id === selectedSubject)?.name || '测试'}</Text>
      </View>

      <View style={styles.offlineBadge}>
        <Text style={styles.offlineBadgeText}>📴 离线模式</Text>
      </View>

      <View style={styles.examContainer}>
        <View style={styles.questionHeader}>
          <Text style={styles.questionNumber}>第 {currentIndex + 1} / {questions.length} 题</Text>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, {width: `${progress}%`}]} />
          </View>
        </View>

        <View style={styles.questionCard}>
          <Text style={styles.questionContent}>{currentQuestion?.content}</Text>
          
          <View style={styles.optionsList}>
            {currentQuestion?.options.map((option, index) => {
              const letter = String.fromCharCode(65 + index);
              const isSelected = answers[currentQuestion.id] === letter;
              return (
                <TouchableOpacity
                  key={letter}
                  style={[styles.optionButton, isSelected && styles.optionButtonSelected]}
                  onPress={() => handleAnswer(currentQuestion.id, letter)}>
                  <View style={styles.optionLetter}>
                    <Text style={styles.optionLetterText}>{letter}</Text>
                  </View>
                  <Text style={styles.optionText}>{option}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        <View style={styles.navigationButtons}>
          <TouchableOpacity 
            style={styles.navButton} 
            onPress={goToPrev}
            disabled={currentIndex === 0}>
            <Text style={styles.navButtonText}>上一题</Text>
          </TouchableOpacity>
          
          {currentIndex === questions.length - 1 ? (
            <TouchableOpacity style={styles.finishButton} onPress={finishExam}>
              <Text style={styles.finishButtonText}>完成考试</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity style={styles.navButton} onPress={goToNext}>
              <Text style={styles.navButtonText}>下一题</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </ScrollView>
  );
};

export default OfflineExamScreen;