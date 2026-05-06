import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';
import { authService } from '../services/api';

export default function HomeScreen({ navigation }) {
  const user = authService.getCurrentUser();

  const quickActions = [
    { name: '开始考试', icon: '📝', color: '#007AFF', route: 'Main' },
    { name: '错题复习', icon: '❌', color: '#FF3B30', route: 'Main' },
    { name: 'AI推荐', icon: '🤖', color: '#5856D6', route: 'Main' },
    { name: '学习报告', icon: '📊', color: '#34C759', route: 'Main' },
  ];

  const recentExams = [
    { id: 1, name: '日语N1模拟测试', date: '2024-04-10', score: 85 },
    { id: 2, name: '英语四级模拟', date: '2024-04-08', score: 78 },
    { id: 3, name: '数学期末模拟', date: '2024-04-05', score: 92 },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>你好，{user?.username || '学生'}</Text>
            <Text style={styles.date}>{new Date().toLocaleDateString('zh-CN')}</Text>
          </View>
          <TouchableOpacity style={styles.avatar}>
            <Text style={styles.avatarText}>{user?.username?.[0]?.toUpperCase() || 'S'}</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.statsContainer}>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>12</Text>
            <Text style={styles.statLabel}>已完成考试</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>85%</Text>
            <Text style={styles.statLabel}>平均正确率</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>28</Text>
            <Text style={styles.statLabel}>错题数量</Text>
          </View>
        </View>

        <Text style={styles.sectionTitle}>快捷操作</Text>
        <View style={styles.quickActions}>
          {quickActions.map((action, index) => (
            <TouchableOpacity
              key={index}
              style={[styles.actionItem, { backgroundColor: action.color }]}
              onPress={() => navigation.navigate(action.route)}
            >
              <Text style={styles.actionIcon}>{action.icon}</Text>
              <Text style={styles.actionText}>{action.name}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.sectionTitle}>最近考试</Text>
        <View style={styles.recentExams}>
          {recentExams.map((exam) => (
            <TouchableOpacity key={exam.id} style={styles.examItem}>
              <View style={styles.examInfo}>
                <Text style={styles.examName}>{exam.name}</Text>
                <Text style={styles.examDate}>{exam.date}</Text>
              </View>
              <View style={styles.examScore}>
                <Text style={styles.scoreText}>{exam.score}</Text>
                <Text style={styles.scoreLabel}>分</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.aiBanner}>
          <Text style={styles.aiBannerTitle}>AI学习助手</Text>
          <Text style={styles.aiBannerText}>根据你的学习情况，AI为你推荐个性化学习计划</Text>
          <TouchableOpacity
            style={styles.aiBannerButton}
            onPress={() => navigation.navigate('Main', { screen: 'AI助手' })}
          >
            <Text style={styles.aiBannerButtonText}>查看推荐</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
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
    padding: 20,
    backgroundColor: '#007AFF',
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  date: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 5,
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(255,255,255,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  statsContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginTop: -20,
    borderRadius: 15,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 5,
  },
  statDivider: {
    width: 1,
    backgroundColor: '#eee',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginHorizontal: 20,
    marginTop: 25,
    marginBottom: 15,
  },
  quickActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 15,
  },
  actionItem: {
    width: '45%',
    marginHorizontal: '2.5%',
    marginBottom: 10,
    borderRadius: 12,
    padding: 15,
    alignItems: 'center',
  },
  actionIcon: {
    fontSize: 30,
    marginBottom: 8,
  },
  actionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
  recentExams: {
    paddingHorizontal: 20,
  },
  examItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
  },
  examInfo: {
    flex: 1,
  },
  examName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  examDate: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  examScore: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  scoreText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#34C759',
  },
  scoreLabel: {
    fontSize: 14,
    color: '#999',
    marginLeft: 2,
  },
  aiBanner: {
    backgroundColor: '#5856D6',
    marginHorizontal: 20,
    marginTop: 10,
    marginBottom: 30,
    borderRadius: 15,
    padding: 20,
  },
  aiBannerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  aiBannerText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 8,
  },
  aiBannerButton: {
    backgroundColor: '#fff',
    borderRadius: 20,
    paddingVertical: 10,
    paddingHorizontal: 25,
    alignSelf: 'flex-start',
    marginTop: 15,
  },
  aiBannerButtonText: {
    color: '#5856D6',
    fontWeight: '600',
  },
});
