import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Alert,
  BackHandler,
} from 'react-native';
import { examService } from '../services/api';

export default function ExamScreen({ route, navigation }) {
  const { exam } = route.params;
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeLeft, setTimeLeft] = useState(exam.duration * 60);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef(null);

  const questions = [
    {
      id: 1,
      content: '以下哪个单词的意思是"学习"？',
      options: ['Study', 'Play', 'Sleep', 'Eat'],
      type: 'single_choice',
    },
    {
      id: 2,
      content: '请选择正确的语法：',
      options: ['I am go to school.', 'I go to school.', 'I goes to school.', 'I going to school.'],
      type: 'single_choice',
    },
    {
      id: 3,
      content: '"你好"用英语怎么说？',
      options: ['Hello', 'Goodbye', 'Thank you', 'Sorry'],
      type: 'single_choice',
    },
    {
      id: 4,
      content: '以下哪个是"水"的英语单词？',
      options: ['Water', 'Fire', 'Earth', 'Air'],
      type: 'single_choice',
    },
    {
      id: 5,
      content: '"谢谢"用英语怎么说？',
      options: ['Thanks', 'Please', 'Sorry', 'No'],
      type: 'single_choice',
    },
  ];

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current);
          handleSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    const backHandler = BackHandler.addEventListener('hardwareBackPress', () => {
      handleExit();
      return true;
    });

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      backHandler.remove();
    };
  }, []);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSelectAnswer = (optionIndex) => {
    setAnswers((prev) => ({
      ...prev,
      [currentQuestion]: optionIndex,
    }));
  };

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const handleSubmit = async () => {
    Alert.alert(
      '确认提交',
      '你确定要提交试卷吗？',
      [
        { text: '取消', style: 'cancel' },
        {
          text: '提交',
          onPress: async () => {
            setLoading(true);
            try {
              const result = {
                totalQuestions: questions.length,
                answeredQuestions: Object.keys(answers).length,
                answers: answers,
              };
              navigation.replace('Result', { exam, result });
            } catch (error) {
              Alert.alert('错误', '提交失败，请重试');
            } finally {
              setLoading(false);
            }
          },
        },
      ]
    );
  };

  const handleExit = () => {
    Alert.alert(
      '退出考试',
      '确定要退出考试吗？你的进度将不会保存。',
      [
        { text: '取消', style: 'cancel' },
        {
          text: '退出',
          style: 'destructive',
          onPress: () => navigation.goBack(),
        },
      ]
    );
  };

  const question = questions[currentQuestion];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={handleExit}>
          <Text style={styles.exitButton}>✕</Text>
        </TouchableOpacity>
        <View style={styles.progress}>
          <Text style={styles.progressText}>
            {currentQuestion + 1} / {questions.length}
          </Text>
        </View>
        <View style={styles.timer}>
          <Text style={styles.timerText}>⏱️ {formatTime(timeLeft)}</Text>
        </View>
      </View>

      <View style={styles.progressBar}>
        <View
          style={[
            styles.progressFill,
            { width: `${((currentQuestion + 1) / questions.length) * 100}%` },
          ]}
        />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.questionCard}>
          <Text style={styles.questionType}>
            {question.type === 'single_choice' ? '单选题' : '多选题'}
          </Text>
          <Text style={styles.questionContent}>{question.content}</Text>
        </View>

        <View style={styles.options}>
          {question.options.map((option, index) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.optionItem,
                answers[currentQuestion] === index && styles.optionSelected,
              ]}
              onPress={() => handleSelectAnswer(index)}
            >
              <View
                style={[
                  styles.optionCircle,
                  answers[currentQuestion] === index && styles.optionCircleSelected,
                ]}
              >
                {answers[currentQuestion] === index && (
                  <View style={styles.optionDot} />
                )}
              </View>
              <Text
                style={[
                  styles.optionText,
                  answers[currentQuestion] === index && styles.optionTextSelected,
                ]}
              >
                {option}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.navButton}
          onPress={handlePrevious}
          disabled={currentQuestion === 0}
        >
          <Text
            style={[
              styles.navButtonText,
              currentQuestion === 0 && styles.navButtonDisabled,
            ]}
          >
            上一题
          </Text>
        </TouchableOpacity>

        {currentQuestion === questions.length - 1 ? (
          <TouchableOpacity
            style={[styles.navButton, styles.submitButton]}
            onPress={handleSubmit}
            disabled={loading}
          >
            <Text style={styles.submitButtonText}>提交试卷</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={styles.navButton} onPress={handleNext}>
            <Text style={styles.navButtonText}>下一题</Text>
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#fff',
  },
  exitButton: {
    fontSize: 20,
    color: '#666',
    padding: 5,
  },
  progress: {
    flex: 1,
    alignItems: 'center',
  },
  progressText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  timer: {
    backgroundColor: '#FFF3CD',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 15,
  },
  timerText: {
    fontSize: 14,
    color: '#856404',
    fontWeight: '600',
  },
  progressBar: {
    height: 4,
    backgroundColor: '#E9ECEF',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#007AFF',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  questionCard: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  questionType: {
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '600',
    marginBottom: 10,
  },
  questionContent: {
    fontSize: 18,
    color: '#333',
    lineHeight: 28,
  },
  options: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  optionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 15,
    paddingHorizontal: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  optionSelected: {
    backgroundColor: '#E3F2FD',
  },
  optionCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#DDD',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  optionCircleSelected: {
    borderColor: '#007AFF',
  },
  optionDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#007AFF',
  },
  optionText: {
    fontSize: 16,
    color: '#333',
    flex: 1,
  },
  optionTextSelected: {
    color: '#007AFF',
    fontWeight: '500',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 20,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#F0F0F0',
  },
  navButton: {
    paddingHorizontal: 30,
    paddingVertical: 12,
    borderRadius: 25,
    backgroundColor: '#F5F5F5',
  },
  navButtonText: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  navButtonDisabled: {
    color: '#CCC',
  },
  submitButton: {
    backgroundColor: '#007AFF',
  },
  submitButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: 'bold',
  },
});
