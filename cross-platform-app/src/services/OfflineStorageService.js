import ReactNativeFS from 'react-native-fs';
import {Platform} from 'react-native';

class OfflineStorageService {
  constructor() {
    this.dbPath = this._getDbPath();
    this.cachePath = this._getCachePath();
    this.init();
  }

  _getDbPath() {
    if (Platform.OS === 'ios') {
      return `${ReactNativeFS.DocumentDirectoryPath}/mtscos_offline.db`;
    }
    return `${ReactNativeFS.DocumentDirectoryPath}/databases/mtscos_offline.db`;
  }

  _getCachePath() {
    return `${ReactNativeFS.CachesDirectoryPath}/mtscos_cache`;
  }

  async init() {
    try {
      await ReactNativeFS.mkdir(`${ReactNativeFS.DocumentDirectoryPath}/databases`);
    } catch (e) {
      // Directory may already exist
    }
    try {
      await ReactNativeFS.mkdir(this.cachePath);
    } catch (e) {
      // Directory may already exist
    }
    await this._createTables();
  }

  async _createTables() {
    const db = await this._openDatabase();
    await db.transaction((tx) => {
      tx.executeSql(`
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
        )
      `);

      tx.executeSql(`
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
        )
      `);

      tx.executeSql(`
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
        )
      `);

      tx.executeSql(`
        CREATE TABLE IF NOT EXISTS offline_config (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          key TEXT UNIQUE,
          value TEXT,
          updated_at TEXT
        )
      `);
    });
    await db.close();
  }

  async _openDatabase() {
    return new Promise((resolve, reject) => {
      const sqlite = require('react-native-sqlite-storage');
      const db = sqlite.openDatabase(
        {name: 'mtscos_offline.db', location: 'default'},
        () => resolve(db),
        (error) => reject(error)
      );
    });
  }

  async saveQuestions(questions) {
    const db = await this._openDatabase();
    return new Promise((resolve, reject) => {
      db.transaction((tx) => {
        questions.forEach((question) => {
          tx.executeSql(
            `INSERT OR REPLACE INTO exam_questions 
             (question_id, subject, content, options, answer, analysis, difficulty, created_at, updated_at)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            [
              question.id,
              question.subject,
              question.content,
              JSON.stringify(question.options),
              question.answer,
              question.analysis,
              question.difficulty,
              new Date().toISOString(),
              new Date().toISOString(),
            ]
          );
        });
      }, (error) => reject(error), () => {
        db.close();
        resolve();
      });
    });
  }

  async getQuestionsBySubject(subject) {
    const db = await this._openDatabase();
    return new Promise((resolve, reject) => {
      db.transaction((tx) => {
        tx.executeSql(
          'SELECT * FROM exam_questions WHERE subject = ? ORDER BY difficulty ASC',
          [subject],
          (_, results) => {
            const questions = [];
            for (let i = 0; i < results.rows.length; i++) {
              const row = results.rows.item(i);
              questions.push({
                id: row.question_id,
                subject: row.subject,
                content: row.content,
                options: JSON.parse(row.options),
                answer: row.answer,
                analysis: row.analysis,
                difficulty: row.difficulty,
              });
            }
            db.close();
            resolve(questions);
          }
        );
      }, (error) => {
        db.close();
        reject(error);
      });
    });
  }

  async saveExamRecord(record) {
    const db = await this._openDatabase();
    return new Promise((resolve, reject) => {
      db.transaction((tx) => {
        tx.executeSql(
          `INSERT INTO exam_records 
           (record_id, exam_id, subject, questions, answers, score, total_score, status, sync_status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
          [
            record.record_id,
            record.exam_id,
            record.subject,
            JSON.stringify(record.questions),
            JSON.stringify(record.answers),
            record.score,
            record.total_score,
            record.status,
            'pending',
            new Date().toISOString(),
            new Date().toISOString(),
          ]
        );
      }, (error) => reject(error), () => {
        db.close();
        resolve();
      });
    });
  }

  async getUnsyncedRecords() {
    const db = await this._openDatabase();
    return new Promise((resolve, reject) => {
      db.transaction((tx) => {
        tx.executeSql(
          'SELECT * FROM exam_records WHERE sync_status = ?',
          ['pending'],
          (_, results) => {
            const records = [];
            for (let i = 0; i < results.rows.length; i++) {
              const row = results.rows.item(i);
              records.push({
                id: row.id,
                record_id: row.record_id,
                exam_id: row.exam_id,
                subject: row.subject,
                questions: JSON.parse(row.questions),
                answers: JSON.parse(row.answers),
                score: row.score,
                total_score: row.total_score,
                status: row.status,
                sync_status: row.sync_status,
              });
            }
            db.close();
            resolve(records);
          }
        );
      }, (error) => {
        db.close();
        reject(error);
      });
    });
  }

  async markRecordsAsSynced(recordIds) {
    const db = await this._openDatabase();
    return new Promise((resolve, reject) => {
      db.transaction((tx) => {
        recordIds.forEach((id) => {
          tx.executeSql(
            'UPDATE exam_records SET sync_status = ?, updated_at = ? WHERE record_id = ?',
            ['synced', new Date().toISOString(), id]
          );
        });
      }, (error) => reject(error), () => {
        db.close();
        resolve();
      });
    });
  }

  async updateUserProgress(userId, subject, correctCount, totalCount) {
    const db = await this._openDatabase();
    return new Promise((resolve, reject) => {
      db.transaction((tx) => {
        tx.executeSql(
          `INSERT OR REPLACE INTO user_progress 
           (user_id, subject, total_questions, correct_questions, last_study_date, study_days, sync_status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
          [
            userId,
            subject,
            totalCount,
            correctCount,
            new Date().toISOString(),
            1,
            'pending',
            new Date().toISOString(),
            new Date().toISOString(),
          ]
        );
      }, (error) => reject(error), () => {
        db.close();
        resolve();
      });
    });
  }

  async getUnsyncedProgress() {
    const db = await this._openDatabase();
    return new Promise((resolve, reject) => {
      db.transaction((tx) => {
        tx.executeSql(
          'SELECT * FROM user_progress WHERE sync_status = ?',
          ['pending'],
          (_, results) => {
            const progressList = [];
            for (let i = 0; i < results.rows.length; i++) {
              const row = results.rows.item(i);
              progressList.push({
                id: row.id,
                user_id: row.user_id,
                subject: row.subject,
                total_questions: row.total_questions,
                correct_questions: row.correct_questions,
                last_study_date: row.last_study_date,
                study_days: row.study_days,
              });
            }
            db.close();
            resolve(progressList);
          }
        );
      }, (error) => {
        db.close();
        reject(error);
      });
    });
  }

  async markProgressAsSynced(userId) {
    const db = await this._openDatabase();
    return new Promise((resolve, reject) => {
      db.transaction((tx) => {
        tx.executeSql(
          'UPDATE user_progress SET sync_status = ?, updated_at = ? WHERE user_id = ?',
          ['synced', new Date().toISOString(), userId]
        );
      }, (error) => reject(error), () => {
        db.close();
        resolve();
      });
    });
  }

  async saveConfig(key, value) {
    const db = await this._openDatabase();
    return new Promise((resolve, reject) => {
      db.transaction((tx) => {
        tx.executeSql(
          'INSERT OR REPLACE INTO offline_config (key, value, updated_at) VALUES (?, ?, ?)',
          [key, JSON.stringify(value), new Date().toISOString()]
        );
      }, (error) => reject(error), () => {
        db.close();
        resolve();
      });
    });
  }

  async getConfig(key) {
    const db = await this._openDatabase();
    return new Promise((resolve, reject) => {
      db.transaction((tx) => {
        tx.executeSql(
          'SELECT value FROM offline_config WHERE key = ?',
          [key],
          (_, results) => {
            if (results.rows.length > 0) {
              db.close();
              resolve(JSON.parse(results.rows.item(0).value));
            } else {
              db.close();
              resolve(null);
            }
          }
        );
      }, (error) => {
        db.close();
        reject(error);
      });
    });
  }

  async clearAllData() {
    const db = await this._openDatabase();
    return new Promise((resolve, reject) => {
      db.transaction((tx) => {
        tx.executeSql('DELETE FROM exam_questions');
        tx.executeSql('DELETE FROM exam_records');
        tx.executeSql('DELETE FROM user_progress');
      }, (error) => reject(error), () => {
        db.close();
        resolve();
      });
    });
  }

  async getStorageStats() {
    const db = await this._openDatabase();
    return new Promise((resolve, reject) => {
      db.transaction((tx) => {
        tx.executeSql('SELECT COUNT(*) as count FROM exam_questions', [], (_, qRes) => {
          tx.executeSql('SELECT COUNT(*) as count FROM exam_records', [], (_, rRes) => {
            tx.executeSql('SELECT COUNT(*) as count FROM user_progress', [], (_, pRes) => {
              db.close();
              resolve({
                questions: qRes.rows.item(0).count,
                records: rRes.rows.item(0).count,
                progress: pRes.rows.item(0).count,
              });
            });
          });
        });
      }, (error) => {
        db.close();
        reject(error);
      });
    });
  }
}

export default new OfflineStorageService();