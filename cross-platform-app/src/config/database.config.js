export const DATABASE_CONFIG = {
  type: 'sqlite',
  name: 'mtscos',
  version: '1.0',
  
  local: {
    dbName: 'mtscos_offline.db',
    location: 'default',
    createFromLocation: 1,
    allowLocationInUri: true,
  },
  
  remote: {
    type: 'mysql',
    host: 'localhost',
    port: 3306,
    database: 'mtscos_db',
    username: 'mtscos_user',
    password: 'mtscos_password',
    charset: 'utf8mb4',
    timezone: '+08:00',
  },
  
  encryption: {
    enabled: true,
    algorithm: 'AES-256-GCM',
    keyLength: 256,
  },
  
  pool: {
    max: 10,
    min: 2,
    acquire: 30000,
    idle: 10000,
  },
  
  sync: {
    enabled: true,
    autoSync: true,
    syncInterval: 300,
    batchSize: 100,
  },
  
  backup: {
    enabled: true,
    autoBackup: true,
    backupInterval: 86400,
    maxBackups: 7,
    backupDir: 'backups',
  },
  
  tables: {
    exam_questions: {
      fields: [
        {name: 'id', type: 'INTEGER', primaryKey: true, autoIncrement: true},
        {name: 'question_id', type: 'TEXT', unique: true},
        {name: 'subject', type: 'TEXT', index: true},
        {name: 'content', type: 'TEXT'},
        {name: 'options', type: 'TEXT'},
        {name: 'answer', type: 'TEXT'},
        {name: 'analysis', type: 'TEXT'},
        {name: 'difficulty', type: 'INTEGER'},
        {name: 'created_at', type: 'TEXT'},
        {name: 'updated_at', type: 'TEXT'},
      ],
    },
    exam_records: {
      fields: [
        {name: 'id', type: 'INTEGER', primaryKey: true, autoIncrement: true},
        {name: 'record_id', type: 'TEXT', unique: true},
        {name: 'subject', type: 'TEXT', index: true},
        {name: 'questions', type: 'TEXT'},
        {name: 'answers', type: 'TEXT'},
        {name: 'score', type: 'INTEGER'},
        {name: 'total_score', type: 'INTEGER'},
        {name: 'status', type: 'TEXT'},
        {name: 'sync_status', type: 'TEXT', defaultValue: 'pending'},
        {name: 'created_at', type: 'TEXT'},
        {name: 'updated_at', type: 'TEXT'},
      ],
    },
    user_progress: {
      fields: [
        {name: 'id', type: 'INTEGER', primaryKey: true, autoIncrement: true},
        {name: 'user_id', type: 'TEXT', unique: true},
        {name: 'subject', type: 'TEXT', index: true},
        {name: 'total_questions', type: 'INTEGER', defaultValue: 0},
        {name: 'correct_questions', type: 'INTEGER', defaultValue: 0},
        {name: 'last_study_date', type: 'TEXT'},
        {name: 'study_days', type: 'INTEGER', defaultValue: 0},
        {name: 'sync_status', type: 'TEXT', defaultValue: 'pending'},
        {name: 'created_at', type: 'TEXT'},
        {name: 'updated_at', type: 'TEXT'},
      ],
    },
    offline_config: {
      fields: [
        {name: 'id', type: 'INTEGER', primaryKey: true, autoIncrement: true},
        {name: 'key', type: 'TEXT', unique: true},
        {name: 'value', type: 'TEXT'},
        {name: 'updated_at', type: 'TEXT'},
      ],
    },
  },
};

export default DATABASE_CONFIG;
