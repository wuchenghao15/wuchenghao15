# MTSCOS AI Smart Exam System

[![CI](https://github.com/wuchenghao15/wuchenghao15/actions/workflows/ci.yml/badge.svg)](https://github.com/wuchenghao15/wuchenghao15/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org)
[![Flask](https://img.shields.io/badge/flask-2.0%2B-green.svg)](https://flask.palletsprojects.com)

> Version: v7.2.0 (Comprehensive Enhancement Edition)
> Updated: 2026-07-09

[中文](README.md) | English

MTSCOS AI is a distributed smart exam management platform developed based on Flask framework, providing complete question bank system, exam management, learning analysis, AI smart engine and other functions, supporting adult education and K12 subjects.

## 🌟 Core Features

### 🏗️ Architecture Features
- **Modular Startup System**: 8-phase configuration loading + 6-phase feature module loading
- **Distributed Database Architecture**: 16+ independent databases with smart routing
- **AI Smart Engine Matrix**: 20+ core engines, 60+ AI employees
- **Responsive Frontend Layout**: Supports desktop and mobile devices

### 📚 Question Bank System
- **37,000+ Questions**: Covers adult education and K12 subjects (Chinese, Math, English, Physics, Chemistry, Biology, History, Geography, Politics, Science, Japanese)
- **7 Question Types**: Single choice, Multiple choice, True/False, Fill in the blank, Short answer, Essay, Listening
- **Smart Question Generation**: Batch question generation based on knowledge points/difficulty/types
- **AI Question Generator**: Automatically generate exam questions from text content

### 🔐 Permission Management
- **12 Roles**: guest→student→parent→designer→teacher→exam_proctor→question_manager→ai_manager→cluster_manager→admin→super_admin→hardware_admin
- **Fine-grained Permissions**: Comprehensive system function permission control
- **Audit Logs**: Complete operation records and real-time auditing
- **Permission Matrix**: Supports custom permission rule configuration

### 🤖 AI Cluster & Model Library
- **15+ AI Models**: GPT-4, Claude-3, Qwen, Llama-3, Gemini, DeepSeek, etc.
- **Performance Monitoring**: Latency, throughput, accuracy metrics
- **Dynamic Scaling**: Auto node expansion and load balancing
- **Multi-model Configuration**: Supports model switching and version management

### ✨ AI Smart Features
- **AI Question Generator**: Automatically generate exam questions from text content, supporting 6 question types, 11 subjects, 3 difficulty levels
- **AI Study Path Recommendation**: Analyze student wrong answer data, generate personalized study paths with weakness analysis and knowledge graph
- **AI Exam Composition**: Smart exam paper composition based on subject/difficulty/type, automatic score distribution and duration calculation
- **Student Performance Analytics Dashboard**: Multi-dimensional data visualization with score distribution, study time trends, weakness analysis

### 🌐 Port & Cluster Management
- **21 Port Configurations**: HTTP/HTTPS, API, WebSocket, Database, etc.
- **Port Management**: Scan, allocate, reserve, release, auto repair
- **Load Balancing**: Round-robin, Least connections, Weighted round-robin, IP hash
- **Health Check**: Heartbeat detection, auto failover, node status monitoring

### 📊 System Monitoring
- **Real-time Monitoring**: CPU, Memory, Disk, Network
- **Slow Query Detection**: Auto identify and optimize slow queries
- **Performance Analysis**: Index suggestions, query statistics
- **Performance Monitoring API**: System status and performance metrics

### 🚀 Automated Operations
- **Git Auto Sync**: Change detection, auto commit, push
- **Daily Health Check**: Database cleanup, log cleanup, backup
- **Auto Upgrade**: Version detection, canary release, health check rollback
- **Version Management**: System version history, auto update documentation

## 📁 Project Structure

```
flask-app/
├── app.py                      # Application entry
├── modular_start.py            # Modular startup script
├── VERSION                     # Version file
├── SYSTEM_DOC.md               # System documentation
├── ai_engines/                 # AI engine modules (20+ core engines)
├── app/                        # Application modules
│   ├── api/                    # API interfaces (120+)
│   ├── services/               # Service modules
│   ├── models/                 # Data models (20+)
│   └── ...
├── split_databases/            # Distributed databases (16+)
├── templates/                  # HTML templates (100+)
├── migrations/                 # Database migration scripts
└── startup_modules/            # Modular startup modules
```

## 🚀 Quick Start

### Requirements
- Python 3.8+
- SQLite 3.30+
- Git
- pip 20.0+

### Installation

```bash
# Clone repository
git clone https://github.com/wuchenghao15/wuchenghao15.git
cd wuchenghao15/flask-app

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize databases
python -c "from app.utils.db import init_all_databases; init_all_databases()"

# Run database migrations (optional)
python migrations/migrate_ai_generated_questions.py

# Start service
python app.py --port 8888
```

### Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| --port | Service port | 8888 |
| --host | Bind address | 0.0.0.0 |
| --debug | Debug mode | False |
| --ssl | Enable SSL | False |
| --ssl-port | SSL port | 8443 |

### Access
- Admin Panel: http://localhost:8888/admin_app/login
- API Docs: http://localhost:8888/api/system/docs

## 📡 API Interfaces

### Authentication
| Interface | Method | Description |
|-----------|--------|-------------|
| /api/auth/login | POST | User login |
| /api/auth/logout | POST | User logout |
| /api/auth/check | GET | Check login status |

### AI Question Generation
| Interface | Method | Description |
|-----------|--------|-------------|
| /api/ai/generate-questions | POST | Generate questions from text |
| /api/ai/generate-questions/save | POST | Save generated questions |
| /api/ai/detect-subject | POST | Auto detect subject |

### AI Study Path
| Interface | Method | Description |
|-----------|--------|-------------|
| /api/ai/study-path/generate | POST | Generate study path |
| /api/ai/study-path/analyze | POST | Analyze weaknesses |
| /api/ai/study-path/knowledge-graph | GET | Get knowledge graph |

### AI Exam Composition
| Interface | Method | Description |
|-----------|--------|-------------|
| /api/ai/exam-compose | POST | Auto compose exam |
| /api/ai/exam-compose/preview | POST | Preview exam |
| /api/ai/exam-compose/save | POST | Save exam |

## 📊 Database Architecture

| Database | Purpose | Core Tables |
|----------|---------|-------------|
| auth.db | Authentication & User Management | users, roles, permissions, sessions |
| exam.db | Exam Management | exams, exam_questions, exam_results |
| question.db | Question Bank | questions, ai_generated_questions |
| learning.db | Learning System | learning_records, study_paths |
| system.db | System Configuration | configs, versions, logs |
| ai.db | AI Engine Data | ai_models, ai_clusters |

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

MIT License

## 📞 Contact

- Project: https://github.com/wuchenghao15/wuchenghao15
- Documentation: [SYSTEM_DOC.md](SYSTEM_DOC.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)

---

**MTSCOS AI** - Making exams smarter, making learning more efficient 🚀