#!/bin/bash

# 数据库配置初始化脚本
echo "=========================================="
echo "  数据库配置初始化"
echo "=========================================="
echo ""

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装，请先安装Node.js"
    exit 1
fi

echo "[1/6] 检查项目结构..."
if [ ! -d "src" ]; then
    echo "❌ 项目结构不正确"
    exit 1
fi
echo "✓ 项目结构正确"

echo ""
echo "[2/6] 创建配置目录..."
mkdir -p src/config
echo "✓ 配置目录创建完成"

echo ""
echo "[3/6] 生成数据库配置文件..."

cat > src/config/database.config.js << 'EOF'
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
EOF

echo "✓ 数据库配置文件已创建"

echo ""
echo "[4/6] 检查SQLite依赖..."
if grep -q "react-native-sqlite-storage" package.json; then
    echo "✓ react-native-sqlite-storage 已安装"
else
    echo "⚠️ react-native-sqlite-storage 未安装"
    echo "建议安装: npm install react-native-sqlite-storage"
fi

echo ""
echo "[5/6] 检查react-native-fs依赖..."
if grep -q "react-native-fs" package.json; then
    echo "✓ react-native-fs 已安装"
else
    echo "⚠️ react-native-fs 未安装"
    echo "建议安装: npm install react-native-fs"
fi

echo ""
echo "[6/6] 生成数据库初始化SQL..."

cat > scripts/init-database.sql << 'EOF'
-- MTSCOS 数据库初始化脚本
-- 创建考试题目表
CREATE TABLE IF NOT EXISTS exam_questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id TEXT UNIQUE,
  subject TEXT,
  content TEXT,
  options TEXT,
  answer TEXT,
  analysis TEXT,
  difficulty INTEGER,
  created_at TEXT,
  updated_at TEXT
);

-- 创建考试记录表
CREATE TABLE IF NOT EXISTS exam_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  record_id TEXT UNIQUE,
  exam_id TEXT,
  subject TEXT,
  questions TEXT,
  answers TEXT,
  score INTEGER,
  total_score INTEGER,
  status TEXT,
  sync_status TEXT DEFAULT 'pending',
  created_at TEXT,
  updated_at TEXT
);

-- 创建用户进度表
CREATE TABLE IF NOT EXISTS user_progress (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT UNIQUE,
  subject TEXT,
  total_questions INTEGER DEFAULT 0,
  correct_questions INTEGER DEFAULT 0,
  last_study_date TEXT,
  study_days INTEGER DEFAULT 0,
  sync_status TEXT DEFAULT 'pending',
  created_at TEXT,
  updated_at TEXT
);

-- 创建离线配置表
CREATE TABLE IF NOT EXISTS offline_config (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT UNIQUE,
  value TEXT,
  updated_at TEXT
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_questions_subject ON exam_questions(subject);
CREATE INDEX IF NOT EXISTS idx_records_subject ON exam_records(subject);
CREATE INDEX IF NOT EXISTS idx_progress_user ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_records_sync ON exam_records(sync_status);
CREATE INDEX IF NOT EXISTS idx_progress_sync ON user_progress(sync_status);

-- 插入初始配置
INSERT OR REPLACE INTO offline_config (key, value, updated_at) VALUES ('db_version', '"1.0"', CURRENT_TIMESTAMP);
INSERT OR REPLACE INTO offline_config (key, value, updated_at) VALUES ('last_sync', '"2026-01-01T00:00:00.000Z"', CURRENT_TIMESTAMP);
EOF

echo "✓ 数据库初始化SQL已创建"

echo ""
echo "=========================================="
echo "  数据库配置初始化完成！"
echo "=========================================="
echo ""
echo "配置文件:"
echo "  - src/config/database.config.js"
echo "  - scripts/init-database.sql"
echo ""
echo "数据库配置:"
echo "  - 类型: SQLite"
echo "  - 名称: mtscos_offline.db"
echo "  - 加密: AES-256-GCM"
echo ""
echo "数据表:"
echo "  - exam_questions (考试题目)"
echo "  - exam_records (考试记录)"
echo "  - user_progress (用户进度)"
echo "  - offline_config (离线配置)"
echo ""
echo "功能特性:"
echo "  ✓ 自动同步"
echo "  ✓ 自动备份"
echo "  ✓ 数据加密"
echo "  ✓ 连接池管理"