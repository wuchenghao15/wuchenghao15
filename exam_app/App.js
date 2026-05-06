import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text, View, ActivityIndicator, StyleSheet } from 'react-native';

import LoginScreen from './screens/LoginScreen';
import HomeScreen from './screens/HomeScreen';
import ExamListScreen from './screens/ExamListScreen';
import ExamScreen from './screens/ExamScreen';
import ResultScreen from './screens/ResultScreen';
import ErrorQuestionScreen from './screens/ErrorQuestionScreen';
import ProfileScreen from './screens/ProfileScreen';
import AIRecommendationScreen from './screens/AIRecommendationScreen';
import DatabaseSyncScreen from './screens/DatabaseSyncScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function AppNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;
          if (route.name === '首页') {
            iconName = focused ? '🏠' : '🏡';
          } else if (route.name === '考试') {
            iconName = focused ? '📝' : '📄';
          } else if (route.name === '错题') {
            iconName = focused ? '❌' : '❎';
          } else if (route.name === 'AI助手') {
            iconName = focused ? '🤖' : '🤖';
          } else if (route.name === '我的') {
            iconName = focused ? '👤' : '👥';
          }
          return <Text style={{ fontSize: size }}>{iconName}</Text>;
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: 'gray',
        headerShown: false,
      })}
    >
      <Tab.Screen name="首页" component={HomeScreen} />
      <Tab.Screen name="考试" component={ExamListScreen} />
      <Tab.Screen name="错题" component={ErrorQuestionScreen} />
      <Tab.Screen name="AI助手" component={AIRecommendationScreen} />
      <Tab.Screen name="我的" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="auto" />
      <Stack.Navigator
        screenOptions={{
          headerShown: false,
        }}
      >
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Main" component={AppNavigator} />
        <Stack.Screen name="Exam" component={ExamScreen} />
        <Stack.Screen name="Result" component={ResultScreen} />
        <Stack.Screen name="DatabaseSync" component={DatabaseSyncScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
