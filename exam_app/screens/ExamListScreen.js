import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  SafeAreaView,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { examService } from '../services/api';

export default function ExamListScreen({ navigation }) {
  const [exams, setExams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadExams();
  }, []);

  const loadExams = async () => {
    try {
      const data = await examService.getExamList();
      setExams(data);
    } catch (error) {
      setExams([
        {
          id: 1,
          title: '日语N1词汇测试',
          description: '测试N1级别词汇掌握程度',
          questionCount: 20,
          duration: 30,
          difficulty: '困难',
        },
        {
          id: 2,
          title: '英语四级模拟',
          description: '英语四级考试模拟卷',
          questionCount: 50,
          duration: 60,
          difficulty: '中等',
        },
        {
          id: 3,
          title: '数学基础测试',
          description: '高中数学基础知识测试',
          questionCount: 30,
          duration: 45,
          difficulty: '简单',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadExams();
    setRefreshing(false);
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case '简单':
        return '#34C759';
      case '中等':
        return '#FF9500';
      case '困难':
        return '#FF3B30';
      default:
        return '#8E8E93';
    }
  };

  const handleStartExam = (exam) => {
    navigation.navigate('Exam', { exam });
  };

  const renderExamItem = ({ item }) => (
    <TouchableOpacity
      style={styles.examItem}
      onPress={() => handleStartExam(item)}
    >
      <View style={styles.examHeader}>
        <Text style={styles.examTitle}>{item.title}</Text>
        <View style={[styles.difficultyBadge, { backgroundColor: getDifficultyColor(item.difficulty) }]}>
          <Text style={styles.difficultyText}>{item.difficulty}</Text>
        </View>
      </View>
      <Text style={styles.examDescription}>{item.description}</Text>
      <View style={styles.examFooter}>
        <View style={styles.examInfo}>
          <Text style={styles.examInfoText}>📝 {item.questionCount}题</Text>
          <Text style={styles.examInfoText}>⏱️ {item.duration}分钟</Text>
        </View>
        <View style={styles.startButton}>
          <Text style={styles.startButtonText}>开始考试</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>加载中...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>考试中心</Text>
        <Text style={styles.headerSubtitle}>选择一场考试开始测试</Text>
      </View>
      <FlatList
        data={exams}
        renderItem={renderExamItem}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>暂无考试</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 30,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 5,
  },
  listContent: {
    padding: 20,
  },
  examItem: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 20,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  examHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  examTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  difficultyBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  difficultyText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '600',
  },
  examDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 15,
  },
  examFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  examInfo: {
    flexDirection: 'row',
  },
  examInfoText: {
    fontSize: 14,
    color: '#999',
    marginRight: 15,
  },
  startButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
  },
  startButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
  },
});
