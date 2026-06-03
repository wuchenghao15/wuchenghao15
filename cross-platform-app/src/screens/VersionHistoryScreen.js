import React, {useState, useEffect} from 'react';
import {View, Text, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator} from 'react-native';
import VersionService from '../services/VersionService';
import PlatformAdapter from '../adapters/PlatformAdapter';

const VersionHistoryScreen = ({navigation}) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    const data = await VersionService.getVersionHistory();
    setHistory(data);
    setLoading(false);
  };

  const getTypeColor = (type) => {
    const colors = {
      major: '#ff6b6b',
      minor: '#4ecdc4',
      patch: '#45b7d1',
      initial: '#96ceb4',
      beta: '#ffeaa7',
      dev: '#dfe6e9',
      plc: '#fd79a8',
    };
    return colors[type] || '#95a5a6';
  };

  const getTypeIcon = (type) => {
    const icons = {
      major: '🚀',
      minor: '✨',
      patch: '🔧',
      initial: '🎉',
      beta: '🧪',
      dev: '🔨',
      plc: '⚙️',
    };
    return icons[type] || '📦';
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
    title: {
      fontSize: 28,
      fontWeight: 'bold',
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    refreshButton: {
      padding: 8,
    },
    refreshText: {
      fontSize: 24,
    },
    content: {
      paddingHorizontal: 24,
      paddingBottom: 32,
    },
    loadingContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
    },
    historyCard: {
      backgroundColor: PlatformAdapter.isHyperOS() ? 'rgba(255, 255, 255, 0.05)' : '#ffffff',
      borderRadius: PlatformAdapter.getCornerRadius(),
      padding: 20,
      marginBottom: 16,
      ...PlatformAdapter.getElevation(),
    },
    versionHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    versionBadge: {
      backgroundColor: PlatformAdapter.getPrimaryColor(),
      paddingHorizontal: 12,
      paddingVertical: 4,
      borderRadius: 8,
      marginRight: 12,
    },
    versionText: {
      color: '#ffffff',
      fontSize: 16,
      fontWeight: 'bold',
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    typeBadge: {
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 8,
      flexDirection: 'row',
      alignItems: 'center',
      gap: 4,
    },
    typeText: {
      color: '#ffffff',
      fontSize: 12,
      fontFamily: PlatformAdapter.getFontFamily(),
    },
    dateText: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      opacity: 0.6,
      fontFamily: PlatformAdapter.getFontFamily(),
      marginLeft: 'auto',
    },
    changesList: {
      gap: 8,
    },
    changeItem: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      gap: 8,
    },
    changeBullet: {
      fontSize: 16,
      marginTop: 2,
    },
    changeText: {
      fontSize: 14,
      color: PlatformAdapter.getTextColor(),
      fontFamily: PlatformAdapter.getFontFamily(),
      flex: 1,
    },
    currentVersionBadge: {
      position: 'absolute',
      top: 12,
      right: 12,
      backgroundColor: '#44ff44',
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 8,
    },
    currentVersionText: {
      color: '#ffffff',
      fontSize: 12,
      fontWeight: 'bold',
      fontFamily: PlatformAdapter.getFontFamily(),
    },
  });

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>版本历史</Text>
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator color={PlatformAdapter.getPrimaryColor()} />
        </View>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>版本历史</Text>
        <TouchableOpacity style={styles.refreshButton} onPress={loadHistory}>
          <Text style={styles.refreshText}>🔄</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.content}>
        {history.map((item, index) => (
          <View key={index} style={styles.historyCard}>
            {item.version === VersionService.getCurrentVersion() && (
              <View style={styles.currentVersionBadge}>
                <Text style={styles.currentVersionText}>当前版本</Text>
              </View>
            )}
            
            <View style={styles.versionHeader}>
              <View style={styles.versionBadge}>
                <Text style={styles.versionText}>v{item.version}</Text>
              </View>
              <View style={[styles.typeBadge, {backgroundColor: getTypeColor(item.type)}]}>
                <Text>{getTypeIcon(item.type)}</Text>
                <Text style={styles.typeText}>{VersionService.formatVersion(item.type)}</Text>
              </View>
              <Text style={styles.dateText}>{item.date}</Text>
            </View>

            <View style={styles.changesList}>
              {item.changes.map((change, changeIndex) => (
                <View key={changeIndex} style={styles.changeItem}>
                  <Text style={styles.changeBullet}>•</Text>
                  <Text style={styles.changeText}>{change}</Text>
                </View>
              ))}
            </View>
          </View>
        ))}
      </View>
    </ScrollView>
  );
};

export default VersionHistoryScreen;