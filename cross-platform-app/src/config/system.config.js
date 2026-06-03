export const SYSTEM_CONFIG = {
  app: {
    name: 'MTSCOS',
    nameZh: '智能学习系统',
    version: '2.0.0',
    buildNumber: '20260511',
    description: '智能学习与考试系统',
    author: 'MTSCOS AI Project Team',
    license: 'MIT',
  },
  environment: {
    development: { apiUrl: 'http://localhost:8890', debug: true, logLevel: 'debug' },
    staging: { apiUrl: 'https://staging.api.mtscos.com', debug: true, logLevel: 'info' },
    production: { apiUrl: 'https://api.mtscos.com', debug: false, logLevel: 'warn' },
  },
  network: { timeout: 30000, retryCount: 3, retryDelay: 1000 },
  cache: { enabled: true, maxSize: 100 * 1024 * 1024, ttl: 3600 },
  storage: { encryption: { enabled: true, algorithm: 'AES-256' } },
  security: { tokenExpiry: 86400, refreshTokenExpiry: 604800 },
  notifications: { enabled: true, pushEnabled: true },
  theme: { default: 'system', availableThemes: ['light', 'dark', 'system'] },
  language: { default: 'zh-CN', availableLanguages: ['zh-CN', 'en-US', 'ja-JP'] },
  features: { aiEnabled: true, offlineMode: true, examMode: true },
  exam: { maxDuration: 3600, autoSubmit: true, autoSave: true },
  sync: { enabled: true, autoSync: true, syncInterval: 300 },
  logging: { enabled: true, consoleEnabled: true },
};

export default SYSTEM_CONFIG;
export const getEnvironmentConfig = (env = 'development') => SYSTEM_CONFIG.environment[env] || SYSTEM_CONFIG.environment.development;
export const getApiUrl = (env = 'development') => getEnvironmentConfig(env).apiUrl;
