import React, {useState} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, Alert} from 'react-native';
import {useAuth} from '../context/AuthContext';
import PlatformAdapter from '../adapters/PlatformAdapter';

const ProfileScreen = ({navigation}) => {
  const {user, logout} = useAuth();
  const [editMode, setEditMode] = useState(false);

  const userStats = [
    {label: '学习天数', value: '128', icon: '📅'},
    {label: '完成题目', value: '3,456', icon: '✅'},
    {label: '正确率', value: '87%', icon: '📊'},
    {label: '获得成就', value: '24', icon: '🏆'},
  ];

  const menuItems = [
    {id: 'achievements', label: '我的成就', icon: '🏅', action: () => {}},
    {id: 'history', label: '学习记录', icon: '📖', action: () => {}},
    {id: 'collection', label: '我的收藏', icon: '⭐', action: () => {}},
    {id: 'offline', label: '离线设置', icon: '📴', action: () => navigation.navigate('OfflineSettings')},
    {id: 'feedback', label: '意见反馈', icon: '💬', action: () => {}},
    {id: 'help', label: '帮助中心', icon: '❓', action: () => {}},
    {id: 'settings', label: '系统设置', icon: '⚙️', action: () => navigation.navigate('Settings')},
  ];

  const handleLogout = async () => {
    Alert.alert('确认退出', '确定要退出登录吗？', [
      {text: '取消', style: 'cancel'},
      {text: '确定', onPress: async () => await logout()},
    ]);
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: PlatformAdapter.getBackgroundColor(),
    },
    header: {
      padding: 24,
      paddingTop: 32,
      alignItems: 'center',
    },
    avatar: {
      width: 100,
      height: 100,
      borderRadius: 50,
      backgroundColor: PlatformAdapter.getPrimaryColor(),
      justifyContent: 'center',
      alignItems: 'center',
      marginBottom: 16,
      ...PlatformAdapter.getElevation(),
    },
    avatarText: {
      color: '#ffffff',
      fontSize: 40,
      fontWeight: 'bold',
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    userName: {
      fontSize: 24,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 4,
    },
    userEmail: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    editButton: {
      marginTop: 12,
      paddingHorizontal: 20,
      paddingVertical: 8,
      borderColor: PlatformAdapter.getPrimaryColor(),
      borderWidth: 1,
      borderRadius: 20,
    },
    editButtonText: {
      color: PlatformAdapter.getPrimaryColor(),
      fontSize: 14,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    statsSection: {
      paddingHorizontal: 24,
      marginBottom: 24,
    },
    statsCard: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      padding: 20,
      ...PlatformAdapter.getElevation(),
    },
    statsRow: {
      flexDirection: 'row',
      justifyContent: 'space-around',
    },
    statItem: {
      alignItems: 'center',
    },
    statIcon: {
      fontSize: 24,
      marginBottom: 8,
    },
    statValue: {
      fontSize: 20,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    statLabel: {
      fontSize: 12,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
      marginTop: 4,
    },
    menuSection: {
      paddingHorizontal: 24,
    },
    sectionTitle: {
      fontSize: 18,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      marginBottom: 16,
    },
    menuList: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      overflow: 'hidden',
      ...PlatformAdapter.getElevation(),
    },
    menuItem: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: 16,
      borderBottomWidth: 1,
      borderBottomColor: PlatformAdapter.isHyperOS() ? 'rgba(255,255,255,0.05)' : '#f0f0f0',
    },
    menuItemLast: {
      borderBottomWidth: 0,
    },
    menuIcon: {
      fontSize: 24,
      marginRight: 16,
    },
    menuLabel: {
      flex: 1,
      fontSize: 16,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    menuArrow: {
      fontSize: 20,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.4,
    },
    logoutSection: {
      padding: 24,
    },
    logoutButton: {
      backgroundColor: 'rgba(255, 68, 68, 0.1)',
      borderRadius: PlatformAdapter.getCornerRadius(),
      padding: 16,
      alignItems: 'center',
    },
    logoutText: {
      color: '#ff4444',
      fontSize: 16,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
  });

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{user?.username?.charAt(0)?.toUpperCase() || 'U'}</Text>
        </View>
        <Text style={styles.userName}>{user?.username}</Text>
        <Text style={styles.userEmail}>{user?.email}</Text>
        <TouchableOpacity style={styles.editButton} onPress={() => setEditMode(!editMode)}>
          <Text style={styles.editButtonText}>{editMode ? '完成' : '编辑资料'}</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.statsSection}>
        <View style={styles.statsCard}>
          <View style={styles.statsRow}>
            {userStats.map((stat, index) => (
              <View key={index} style={styles.statItem}>
                <Text style={styles.statIcon}>{stat.icon}</Text>
                <Text style={styles.statValue}>{stat.value}</Text>
                <Text style={styles.statLabel}>{stat.label}</Text>
              </View>
            ))}
          </View>
        </View>
      </View>

      <View style={styles.menuSection}>
        <Text style={styles.sectionTitle}>功能菜单</Text>
        <View style={styles.menuList}>
          {menuItems.map((item, index) => (
            <TouchableOpacity
              key={item.id}
              style={[styles.menuItem, index === menuItems.length - 1 && styles.menuItemLast]}
              onPress={item.action}>
              <Text style={styles.menuIcon}>{item.icon}</Text>
              <Text style={styles.menuLabel}>{item.label}</Text>
              <Text style={styles.menuArrow}>›</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.logoutSection}>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutText}>退出登录</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

export default ProfileScreen;