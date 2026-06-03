import React from 'react';
import {Text} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';
import {createStackNavigator} from '@react-navigation/stack';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {useAuth} from '../context/AuthContext';
import PlatformAdapter from '../adapters/PlatformAdapter';

import LoginScreen from '../screens/LoginScreen';
import RegisterScreen from '../screens/RegisterScreen';
import HomeScreen from '../screens/HomeScreen';
import ExamScreen from '../screens/ExamScreen';
import OfflineExamScreen from '../screens/OfflineExamScreen';
import ProfileScreen from '../screens/ProfileScreen';
import SettingsScreen from '../screens/SettingsScreen';

import OfflineSettingsScreen from '../screens/OfflineSettingsScreen';
import VersionHistoryScreen from '../screens/VersionHistoryScreen';
import UpdateSettingsScreen from '../screens/UpdateSettingsScreen';
import AISettingsScreen from '../screens/AISettingsScreen';
import BackupSettingsScreen from '../screens/BackupSettingsScreen';
import QuestionBankSettingsScreen from '../screens/QuestionBankSettingsScreen';
import TeacherSettingsScreen from '../screens/TeacherSettingsScreen';
import StudentSettingsScreen from '../screens/StudentSettingsScreen';
import ExamSettingsScreen from '../screens/ExamSettingsScreen';
import SystemConfigScreen from '../screens/SystemConfigScreen';
import RouterSettingsScreen from '../screens/RouterSettingsScreen';
import SecuritySettingsScreen from '../screens/SecuritySettingsScreen';
import KernelSettingsScreen from '../screens/KernelSettingsScreen';
import FirmwareSettingsScreen from '../screens/FirmwareSettingsScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

const AuthStack = () => (
  <Stack.Navigator
    initialRouteName="Login"
    screenOptions={{
      headerStyle: {
        backgroundColor: PlatformAdapter.getBackgroundColor(),
      },
      headerTintColor: PlatformAdapter.getTextColor(),
      headerTitleStyle: {
        fontFamily: PlatformAdapter.getFontFamily(),
      },
    }}>
    <Stack.Screen
      name="Login"
      component={LoginScreen}
      options={{title: '登录'}}
    />
    <Stack.Screen
      name="Register"
      component={RegisterScreen}
      options={{title: '注册'}}
    />
  </Stack.Navigator>
);

const HomeStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: {backgroundColor: PlatformAdapter.getBackgroundColor()},
      headerTintColor: PlatformAdapter.getTextColor(),
      headerTitleStyle: {fontFamily: PlatformAdapter.getFontFamily()},
    }}>
    <Stack.Screen name="Home" component={HomeScreen} options={{title: '首页'}} />
    <Stack.Screen name="Exam" component={ExamScreen} options={{title: '考试中心'}} />
    <Stack.Screen name="OfflineExam" component={OfflineExamScreen} options={{title: '离线考试'}} />
    <Stack.Screen name="Profile" component={ProfileScreen} options={{title: '个人中心'}} />
  </Stack.Navigator>
);

const ExamStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: {backgroundColor: PlatformAdapter.getBackgroundColor()},
      headerTintColor: PlatformAdapter.getTextColor(),
      headerTitleStyle: {fontFamily: PlatformAdapter.getFontFamily()},
    }}>
    <Stack.Screen name="ExamHome" component={ExamScreen} options={{title: '考试中心'}} />
    <Stack.Screen name="ExamSettings" component={ExamSettingsScreen} options={{title: '考试设置'}} />
    <Stack.Screen name="QuestionBankSettings" component={QuestionBankSettingsScreen} options={{title: '题库管理'}} />
  </Stack.Navigator>
);

const ProfileStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: {backgroundColor: PlatformAdapter.getBackgroundColor()},
      headerTintColor: PlatformAdapter.getTextColor(),
      headerTitleStyle: {fontFamily: PlatformAdapter.getFontFamily()},
    }}>
    <Stack.Screen name="ProfileHome" component={ProfileScreen} options={{title: '个人中心'}} />
    <Stack.Screen name="StudentSettings" component={StudentSettingsScreen} options={{title: '学生信息'}} />
    <Stack.Screen name="TeacherSettings" component={TeacherSettingsScreen} options={{title: '教师系统'}} />
  </Stack.Navigator>
);

const SettingsStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: {backgroundColor: PlatformAdapter.getBackgroundColor()},
      headerTintColor: PlatformAdapter.getTextColor(),
      headerTitleStyle: {fontFamily: PlatformAdapter.getFontFamily()},
    }}>
    <Stack.Screen name="SettingsHome" component={SettingsScreen} options={{title: '系统设置'}} />
    <Stack.Screen name="AISettings" component={AISettingsScreen} options={{title: 'AI设置'}} />
    <Stack.Screen name="UpdateSettings" component={UpdateSettingsScreen} options={{title: '版本更新'}} />
    <Stack.Screen name="VersionHistory" component={VersionHistoryScreen} options={{title: '版本历史'}} />
    <Stack.Screen name="BackupSettings" component={BackupSettingsScreen} options={{title: '备份设置'}} />
    <Stack.Screen name="OfflineSettings" component={OfflineSettingsScreen} options={{title: '离线设置'}} />
    <Stack.Screen name="SecuritySettings" component={SecuritySettingsScreen} options={{title: '数据安全'}} />
    <Stack.Screen name="SystemConfig" component={SystemConfigScreen} options={{title: '系统配置'}} />
    <Stack.Screen name="RouterSettings" component={RouterSettingsScreen} options={{title: '路由系统'}} />
    <Stack.Screen name="KernelSettings" component={KernelSettingsScreen} options={{title: '内核系统'}} />
    <Stack.Screen name="FirmwareSettings" component={FirmwareSettingsScreen} options={{title: '固件设置'}} />
  </Stack.Navigator>
);

const TabNavigator = () => (
  <Tab.Navigator
    screenOptions={{
      tabBarStyle: {
        backgroundColor: PlatformAdapter.isHyperOS() ? '#1a1a2e' : '#ffffff',
        borderTopWidth: 0,
        elevation: 10,
      },
      tabBarActiveTintColor: PlatformAdapter.getPrimaryColor(),
      tabBarInactiveTintColor: PlatformAdapter.isHyperOS() ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.5)',
      headerStyle: {
        backgroundColor: PlatformAdapter.getBackgroundColor(),
      },
      headerTintColor: PlatformAdapter.getTextColor(),
      headerTitleStyle: {
        fontFamily: PlatformAdapter.getFontFamily(),
      },
    }}>
    <Tab.Screen
      name="Home"
      component={HomeStack}
      options={{
        title: '首页',
        tabBarIcon: ({color}) => <Text style={{fontSize: 24, color}}>🏠</Text>,
      }}
    />
    <Tab.Screen
      name="Exam"
      component={ExamStack}
      options={{
        title: '考试',
        tabBarIcon: ({color}) => <Text style={{fontSize: 24, color}}>📝</Text>,
      }}
    />
    <Tab.Screen
      name="Profile"
      component={ProfileStack}
      options={{
        title: '我的',
        tabBarIcon: ({color}) => <Text style={{fontSize: 24, color}}>👤</Text>,
      }}
    />
    <Tab.Screen
      name="Settings"
      component={SettingsStack}
      options={{
        title: '设置',
        tabBarIcon: ({color}) => <Text style={{fontSize: 24, color}}>⚙️</Text>,
      }}
    />
  </Tab.Navigator>
);

const Navigation = () => {
  const {isAuthenticated, loading} = useAuth();

  if (loading) {
    return null;
  }

  return (
    <NavigationContainer>
      {isAuthenticated ? <TabNavigator /> : <AuthStack />}
    </NavigationContainer>
  );
};

export default Navigation;