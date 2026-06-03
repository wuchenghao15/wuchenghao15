import React, {useEffect, useState} from 'react';
import {Platform, StatusBar, SafeAreaView, StyleSheet} from 'react-native';
import Navigation from './src/navigation/Navigation';
import PlatformAdapter from './src/adapters/PlatformAdapter';
import {AuthProvider} from './src/context/AuthContext';
import {ThemeProvider} from './src/context/ThemeContext';

const App = () => {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const initApp = async () => {
      await PlatformAdapter.init();
      setIsReady(true);
    };
    initApp();
  }, []);

  if (!isReady) {
    return null;
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar
        barStyle={PlatformAdapter.getStatusBarStyle()}
        backgroundColor={PlatformAdapter.getStatusBarColor()}
      />
      <ThemeProvider>
        <AuthProvider>
          <Navigation />
        </AuthProvider>
      </ThemeProvider>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: PlatformAdapter.getBackgroundColor(),
  },
});

export default App;