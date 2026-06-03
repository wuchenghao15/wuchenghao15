import React from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView} from 'react-native';
import {useAuth} from '../context/AuthContext';
import PlatformAdapter from '../adapters/PlatformAdapter';

const HomeScreen = ({navigation}) => {
  const {user, logout} = useAuth();

  const quickStats = [
    {label: '今日任务', value: '5', color: PlatformAdapter.getPrimaryColor()},
    {label: '待完成', value: '3', color: PlatformAdapter.getAccentColor()},
    {label: '已完成', value: '12', color: '#44ff44'},
    {label: '正确率', value: '85%', color: '#ffaa00'},
  ];

  const quickActions = [
    {id: 'exam', label: '开始考试', icon: '📝', screen: 'Exam', color: '#6366f1'},
    {id: 'offlineExam', label: '离线考试', icon: '📴', screen: 'OfflineExam', color: '#007dff'},
    {id: 'profile', label: '我的学习', icon: '📊', screen: 'Profile', color: '#f472b6'},
  ];

  const handleLogout = async () => {
    await logout();
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: PlatformAdapter.getBackgroundColor(),
    },
    header: {
      padding: 24,
      paddingTop: 32,
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    userInfo: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 12,
    },
    avatar: {
      width: 48,
      height: 48,
      borderRadius: 24,
      backgroundColor: PlatformAdapter.getPrimaryColor(),
      justifyContent: 'center',
      alignItems: 'center',
    },
    avatarText: {
      color: '#ffffff',
      fontSize: 20,
      fontWeight: 'bold',
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    welcomeText: {
      fontSize: 18,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    userName: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.7,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    logoutButton: {
      padding: 8,
      backgroundColor: 'rgba(255, 68, 68, 0.1)',
      borderRadius: 8,
    },
    logoutText: {
      color: '#ff4444',
      fontSize: 14,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    statsSection: {
      paddingHorizontal: 24,
      marginBottom: 24,
    },
    sectionTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 12,
    },
    statsGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 12,
    },
    statCard: {
      width: '47%',
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : 
                      PlatformAdapter.isHarmonyOS() ? 'rgba(0, 125, 255, 0.1)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      padding: 16,
      ...PlatformAdapter.getElevation(),
    },
    statLabel: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    statValue: {
      fontSize: 24,
      fontWeight: 'bold',
      fontFamily: PlatformAdapter.getFontFamily(),
      marginTop: 4,
    },
    actionsSection: {
      paddingHorizontal: 24,
      marginBottom: 24,
    },
    actionsGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 12,
    },
    actionCard: {
      width: '31%',
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      padding: 16,
      alignItems: 'center',
      ...PlatformAdapter.getElevation(),
    },
    actionIcon: {
      fontSize: 32,
      marginBottom: 8,
    },
    actionLabel: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      textAlign: 'center',
    },
    infoCard: {
      marginHorizontal: 24,
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0, 125, 255, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
    },
    infoTitle: {
      fontSize: 16,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 8,
    },
    infoText: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.8,
      fontFamily: PlatformAdapter.getFontFamily(),
      lineHeight: 20,
    },
    tipsSection: {
      paddingHorizontal: 24,
      marginTop: 24,
    },
    tipsCard: {
      padding: 16,
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(68, 255, 68, 0.05)' : 'rgba(68, 255, 68, 0.05)',
      borderRadius: PlatformAdapter.getCornerRadius(),
    },
    tipsTitle: {
      fontSize: 14,
      fontWeight: 'bold',
      color: '#44ff44',
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 8,
    },
    tipsText: {
      fontSize: 13,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.8,
      fontFamily: PlatformAdapter.getFontFamily(),
      lineHeight: 18,
    },
  });

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.userInfo}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{user?.username?.charAt(0).toUpperCase() || '?'}</Text>
          </View>
          <View>
            <Text style={styles.welcomeText}>欢迎回来</Text>
            <Text style={styles.userName}>{user?.username || '用户'}</Text>
          </View>
        </View>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutText}>退出登录</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.statsSection}>
        <Text style={styles.sectionTitle}>📊 学习统计</Text>
        <View style={styles.statsGrid}>
          {quickStats.map((stat, index) => (
            <View key={index} style={styles.statCard}>
              <Text style={styles.statLabel}>{stat.label}</Text>
              <Text style={[styles.statValue, {color: stat.color}]}>{stat.value}</Text>
            </View>
          ))}
        </View>
      </View>

      <View style={styles.actionsSection}>
        <Text style={styles.sectionTitle}>🚀 快捷操作</Text>
        <View style={styles.actionsGrid}>
          {quickActions.map((action) => (
            <TouchableOpacity
              key={action.id}
              style={styles.actionCard}
              onPress={() => navigation.navigate(action.screen)}>
              <Text style={styles.actionIcon}>{action.icon}</Text>
              <Text style={styles.actionLabel}>{action.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>🎯 今日目标</Text>
        <Text style={styles.infoText}>完成3道数学题、2道英语题，保持学习进度。记得完成摸底测试！</Text>
      </View>

      <View style={styles.tipsSection}>
        <View style={styles.tipsCard}>
          <Text style={styles.tipsTitle}>💡 学习小贴士</Text>
          <Text style={styles.tipsText}>每天保持30分钟学习时间，可以有效提升学习效果。建议在安静的环境中进行学习，效果更佳。</Text>
        </View>
      </View>

      <View style={{height: 32}} />
    </ScrollView>
  );
};

export default HomeScreen;