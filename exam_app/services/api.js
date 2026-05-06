import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = globalThis.localStorage?.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (username, password) => {
    const response = await api.post('/auth/login', { username, password });
    if (response.data.token) {
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },
  
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
  
  getCurrentUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
};

export const examService = {
  getExamList: async () => {
    const response = await api.get('/exams');
    return response.data;
  },
  
  getExamDetail: async (examId) => {
    const response = await api.get(`/exams/${examId}`);
    return response.data;
  },
  
  startExam: async (examId) => {
    const response = await api.post(`/exams/${examId}/start`);
    return response.data;
  },
  
  submitAnswer: async (examId, questionId, answer) => {
    const response = await api.post(`/exams/${examId}/answer`, {
      question_id: questionId,
      answer: answer,
    });
    return response.data;
  },
  
  finishExam: async (examId) => {
    const response = await api.post(`/exams/${examId}/finish`);
    return response.data;
  },
  
  getExamResult: async (examId) => {
    const response = await api.get(`/exams/${examId}/result`);
    return response.data;
  },
};

export const errorQuestionService = {
  getErrorQuestions: async (userId) => {
    const response = await api.get(`/error-questions/${userId}`);
    return response.data;
  },
  
  getErrorQuestionDetail: async (errorQuestionId) => {
    const response = await api.get(`/error-questions/detail/${errorQuestionId}`);
    return response.data;
  },
  
  reviewErrorQuestion: async (errorQuestionId) => {
    const response = await api.post(`/error-questions/${errorQuestionId}/review`);
    return response.data;
  },
};

export const aiService = {
  getPersonalizedRecommendations: async (userId) => {
    const response = await api.get(`/ai/recommendations/${userId}`);
    return response.data;
  },
  
  getLearningAnalysis: async (userId) => {
    const response = await api.get(`/ai/analysis/${userId}`);
    return response.data;
  },
  
  getStudyPlan: async (userId) => {
    const response = await api.get(`/ai/study-plan/${userId}`);
    return response.data;
  },
};

export const databaseService = {
  syncData: async (userId) => {
    const response = await api.post('/database/sync', { user_id: userId });
    return response.data;
  },
  
  backupData: async (userId) => {
    const response = await api.post('/database/backup', { user_id: userId });
    return response.data;
  },
  
  restoreData: async (userId, backupId) => {
    const response = await api.post('/database/restore', {
      user_id: userId,
      backup_id: backupId,
    });
    return response.data;
  },
  
  getBackupList: async (userId) => {
    const response = await api.get(`/database/backups/${userId}`);
    return response.data;
  },
  
  getSyncHistory: async (userId) => {
    const response = await api.get(`/database/sync-history/${userId}`);
    return response.data;
  },
};

export default api;
