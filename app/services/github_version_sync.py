#!/usr/bin/env python3
import os
import json
import requests
import sqlite3
from datetime import datetime
from flask import Blueprint, jsonify, request

class GitHubVersionSync:
    def __init__(self, db_path):
        self.db_path = db_path
        self.github_token = os.environ.get('GITHUB_TOKEN', '')
        self.repositories = [
            {'owner': 'MTSCOS', 'name': 'MTSCOS_AI_Project'}
        ]
        self.api_base = 'https://api.github.com'
        self._init_sync_table()
    
    def _init_sync_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS github_sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_type TEXT NOT NULL,
                direction TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'running',
                github_ref TEXT,
                local_version TEXT,
                changes_count INTEGER DEFAULT 0,
                start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                end_time TEXT,
                error_message TEXT,
                details TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS github_release_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                release_id INTEGER UNIQUE,
                tag_name TEXT UNIQUE,
                name TEXT,
                body TEXT,
                draft INTEGER DEFAULT 0,
                prerelease INTEGER DEFAULT 0,
                created_at TEXT,
                published_at TEXT,
                synced_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_github_sync_type ON github_sync_log(sync_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_github_sync_status ON github_sync_log(status)')
        
        conn.commit()
        conn.close()
    
    def _make_request(self, method, endpoint, data=None, params=None):
        headers = {
            'Authorization': f'token {self.github_token}' if self.github_token else '',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f'{self.api_base}{endpoint}'
        
        try:
            if method == 'GET':
                resp = requests.get(url, headers=headers, params=params, timeout=15)
            elif method == 'POST':
                resp = requests.post(url, headers=headers, json=data, timeout=15)
            elif method == 'PUT':
                resp = requests.put(url, headers=headers, json=data, timeout=15)
            elif method == 'DELETE':
                resp = requests.delete(url, headers=headers, timeout=15)
            
            resp.raise_for_status()
            return resp.json()
        
        except requests.exceptions.RequestException as e:
            return {'error': str(e), 'status_code': resp.status_code if 'resp' in dir() else 0}
    
    def get_github_releases(self, limit=50, repo_index=0):
        if repo_index >= len(self.repositories):
            return {'error': '仓库索引无效'}
        
        repo = self.repositories[repo_index]
        endpoint = f'/repos/{repo["owner"]}/{repo["name"]}/releases'
        params = {'per_page': limit}
        return self._make_request('GET', endpoint, params=params)
    
    def get_all_github_releases(self, limit=50):
        all_releases = []
        for i, repo in enumerate(self.repositories):
            releases = self.get_github_releases(limit=limit, repo_index=i)
            if 'error' not in releases:
                for r in releases:
                    r['repo_name'] = repo['name']
                all_releases.extend(releases)
        return all_releases
    
    def get_github_tags(self, limit=50, repo_index=0):
        if repo_index >= len(self.repositories):
            return {'error': '仓库索引无效'}
        
        repo = self.repositories[repo_index]
        endpoint = f'/repos/{repo["owner"]}/{repo["name"]}/tags'
        params = {'per_page': limit}
        return self._make_request('GET', endpoint, params=params)
    
    def get_github_commits(self, limit=100, repo_index=0):
        if repo_index >= len(self.repositories):
            return {'error': '仓库索引无效'}
        
        repo = self.repositories[repo_index]
        endpoint = f'/repos/{repo["owner"]}/{repo["name"]}/commits'
        params = {'per_page': limit}
        return self._make_request('GET', endpoint, params=params)
    
    def create_github_release(self, tag_name, name, body, draft=False, prerelease=False, repo_index=0):
        if repo_index >= len(self.repositories):
            return {'error': '仓库索引无效'}
        
        repo = self.repositories[repo_index]
        endpoint = f'/repos/{repo["owner"]}/{repo["name"]}/releases'
        data = {
            'tag_name': tag_name,
            'name': name,
            'body': body,
            'draft': draft,
            'prerelease': prerelease
        }
        return self._make_request('POST', endpoint, data=data)
    
    def update_github_release(self, release_id, name, body):
        endpoint = f'/repos/{self.repo_owner}/{self.repo_name}/releases/{release_id}'
        data = {
            'name': name,
            'body': body
        }
        return self._make_request('PATCH', endpoint, data=data)
    
    def _save_sync_log(self, sync_type, direction, status, github_ref='', 
                       local_version='', changes_count=0, error_message='', details=''):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO github_sync_log 
            (sync_type, direction, status, github_ref, local_version, 
             changes_count, end_time, error_message, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sync_type, direction, status, github_ref, local_version,
              changes_count, datetime.now().isoformat(), error_message, details))
        
        conn.commit()
        conn.close()
    
    def sync_github_to_database(self):
        self._save_sync_log('version', 'github_to_db', 'running')
        
        try:
            all_releases = self.get_all_github_releases()
            
            if not all_releases:
                self._save_sync_log('version', 'github_to_db', 'completed', 
                                   details='GitHub无releases数据')
                return {'success': True, 'message': 'GitHub无releases数据', 'releases': 0, 'commits': 0, 'changes_made': 0}
            
            all_commits = []
            for i in range(len(self.repositories)):
                commits = self.get_github_commits(limit=30, repo_index=i)
                if 'error' not in commits:
                    for c in commits:
                        c['repo_name'] = self.repositories[i]['name']
                    all_commits.extend(commits)
            
            from app.services.system_version_db import system_version_db
            
            changes_made = 0
            
            for release in all_releases:
                tag_name = release.get('tag_name', '')
                name = release.get('name', '')
                body = release.get('body', '')
                published_at = release.get('published_at', '')
                repo_name = release.get('repo_name', '')
                
                version_parts = tag_name.lstrip('v').split('.')
                if len(version_parts) >= 3:
                    try:
                        major = int(version_parts[0])
                        minor = int(version_parts[1])
                        patch = int(version_parts[2])
                    except:
                        continue
                else:
                    continue
                
                existing_version = system_version_db.get_version_by_number(tag_name)
                
                if not existing_version:
                    version_data = {
                        'version': tag_name,
                        'major': major,
                        'minor': minor,
                        'patch': patch,
                        'build_number': published_at[:10].replace('-', '') + 'a' if published_at else '',
                        'build_date': published_at[:10] if published_at else '',
                        'codename': name,
                        'status': 'stable',
                        'description': body[:200] if body else '',
                        'upgrade_notes': body,
                        'features': [line.strip() for line in body.split('\n') if line.strip()][:10]
                    }
                    
                    system_version_db.add_version(version_data)
                    changes_made += 1
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for commit in all_commits:
                commit_sha = commit.get('sha', '')[:10]
                commit_message = commit.get('commit', {}).get('message', '')
                committer = commit.get('commit', {}).get('committer', {}).get('name', '')
                committed_at = commit.get('commit', {}).get('committed_date', '')
                repo_name = commit.get('repo_name', '')
                
                if commit_message:
                    cursor.execute('''
                        INSERT OR IGNORE INTO system_history 
                        (event_type, event_category, event_title, event_description, 
                         related_version, operator, timestamp, details)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', ('github_commit', 'github', f'Commit {commit_sha}', 
                          commit_message[:200], '', committer, committed_at,
                          json.dumps({'sha': commit.get('sha', ''), 'repo': repo_name})))
            
            conn.commit()
            conn.close()
            
            self._save_sync_log('version', 'github_to_db', 'success', 
                               changes_count=changes_made,
                               details=json.dumps({'releases': len(all_releases), 'commits': len(all_commits)}))
            
            return {
                'success': True,
                'message': f'同步完成，新增 {changes_made} 个版本',
                'releases': len(all_releases),
                'commits': len(all_commits),
                'changes_made': changes_made
            }
        
        except Exception as e:
            self._save_sync_log('version', 'github_to_db', 'failed', error_message=str(e))
            return {'success': False, 'message': str(e)}
    
    def sync_database_to_github(self):
        self._save_sync_log('version', 'db_to_github', 'running')
        
        try:
            from app.services.system_version_db import system_version_db
            
            versions = system_version_db.get_all_versions()
            
            if not versions:
                self._save_sync_log('version', 'db_to_github', 'completed', 
                                   details='无版本数据可同步')
                return {'success': True, 'message': '无版本数据可同步'}
            
            github_releases = self.get_github_releases()
            
            if 'error' in github_releases:
                self._save_sync_log('version', 'db_to_github', 'failed', 
                                   error_message=github_releases['error'])
                return {'success': False, 'message': f'获取GitHub releases失败: {github_releases["error"]}'}
            
            existing_tags = {r.get('tag_name', '') for r in github_releases}
            
            changes_made = 0
            
            for version in versions:
                tag_name = version['version']
                
                if tag_name not in existing_tags:
                    name = version.get('codename', f'{tag_name} Release')
                    body = self._generate_release_body(version)
                    
                    result = self.create_github_release(tag_name, name, body)
                    
                    if 'error' not in result:
                        changes_made += 1
                        existing_tags.add(tag_name)
                        
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT OR IGNORE INTO github_release_cache 
                            (release_id, tag_name, name, body, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (result.get('id'), tag_name, name, body, datetime.now().isoformat()))
                        conn.commit()
                        conn.close()
            
            self._save_sync_log('version', 'db_to_github', 'success', 
                               changes_count=changes_made,
                               details=json.dumps({'versions': len(versions), 'created_releases': changes_made}))
            
            return {
                'success': True,
                'message': f'同步完成，创建 {changes_made} 个GitHub releases',
                'versions': len(versions),
                'created_releases': changes_made
            }
        
        except Exception as e:
            self._save_sync_log('version', 'db_to_github', 'failed', error_message=str(e))
            return {'success': False, 'message': str(e)}
    
    def _generate_release_body(self, version):
        lines = []
        lines.append(f'## {version["version"]}')
        lines.append(f'**Codename:** {version.get("codename", "")}')
        lines.append(f'**Build Date:** {version.get("build_date", "")}')
        lines.append(f'**Build Number:** {version.get("build_number", "")}')
        lines.append(f'**Status:** {version.get("status", "stable")}')
        lines.append('')
        lines.append('### Description')
        lines.append(version.get('description', ''))
        lines.append('')
        
        features = version.get('features', [])
        if features:
            lines.append('### Features')
            for feature in features[:10]:
                lines.append(f'- {feature}')
            if len(features) > 10:
                lines.append(f'- ... and {len(features) - 10} more features')
            lines.append('')
        
        upgrade_notes = version.get('upgrade_notes', '')
        if upgrade_notes:
            lines.append('### Upgrade Notes')
            lines.append(upgrade_notes)
        
        return '\n'.join(lines)
    
    def get_sync_logs(self, limit=20):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM github_sync_log 
            ORDER BY id DESC 
            LIMIT ?
        ''', (limit,))
        
        logs = []
        for row in cursor.fetchall():
            try:
                details = json.loads(row[10]) if row[10] else {}
            except:
                details = {}
            
            logs.append({
                'id': row[0],
                'sync_type': row[1],
                'direction': row[2],
                'status': row[3],
                'github_ref': row[4],
                'local_version': row[5],
                'changes_count': row[6],
                'start_time': row[7],
                'end_time': row[8],
                'error_message': row[9],
                'details': details
            })
        
        conn.close()
        return logs
    
    def get_release_cache(self, limit=20):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM github_release_cache 
            ORDER BY id DESC 
            LIMIT ?
        ''', (limit,))
        
        releases = []
        for row in cursor.fetchall():
            releases.append({
                'id': row[0],
                'release_id': row[1],
                'tag_name': row[2],
                'name': row[3],
                'body': row[4][:100] + '...' if row[4] and len(row[4]) > 100 else row[4],
                'draft': bool(row[5]),
                'prerelease': bool(row[6]),
                'created_at': row[7],
                'published_at': row[8],
                'synced_at': row[9]
            })
        
        conn.close()
        return releases

github_version_sync = None

def get_github_version_sync():
    global github_version_sync
    if github_version_sync is None:
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        github_version_sync = GitHubVersionSync(db_path)
    return github_version_sync

github_sync_bp = Bluelogger.info('github_sync_api', __name__)

github_sync_bp.config = {
    'EXEMPT_METHODS': {'GET', 'POST', 'PUT', 'DELETE'}
}

@github_sync_bp.route('/api/github/version/sync/github-to-db', methods=['POST'])
def api_sync_github_to_db():
    sync = get_github_version_sync()
    result = sync.sync_github_to_database()
    return jsonify(result)

@github_sync_bp.route('/api/github/version/sync/db-to-github', methods=['POST'])
def api_sync_db_to_github():
    sync = get_github_version_sync()
    result = sync.sync_database_to_github()
    return jsonify(result)

@github_sync_bp.route('/api/github/version/sync/logs', methods=['GET'])
def api_get_sync_logs():
    sync = get_github_version_sync()
    limit = request.args.get('limit', 20, type=int)
    logs = sync.get_sync_logs(limit)
    return jsonify({'success': True, 'logs': logs})

@github_sync_bp.route('/api/github/version/releases', methods=['GET'])
def api_get_github_releases():
    sync = get_github_version_sync()
    releases = sync.get_all_github_releases(limit=30)
    
    if not releases:
        return jsonify({'success': True, 'releases': [], 'message': '暂无releases数据'})
    
    return jsonify({'success': True, 'releases': releases})

@github_sync_bp.route('/api/github/version/cache', methods=['GET'])
def api_get_release_cache():
    sync = get_github_version_sync()
    limit = request.args.get('limit', 20, type=int)
    cache = sync.get_release_cache(limit)
    return jsonify({'success': True, 'releases': cache})

@github_sync_bp.route('/api/github/version/create-release', methods=['POST'])
def api_create_release():
    sync = get_github_version_sync()
    
    data = request.get_json() or {}
    tag_name = data.get('tag_name')
    name = data.get('name')
    body = data.get('body', '')
    draft = data.get('draft', False)
    prerelease = data.get('prerelease', False)
    
    if not tag_name or not name:
        return jsonify({'success': False, 'message': 'tag_name和name是必填项'}), 400
    
    result = sync.create_github_release(tag_name, name, body, draft, prerelease)
    
    if 'error' in result:
        return jsonify({'success': False, 'message': result['error']}), 500
    
    return jsonify({'success': True, 'release': result})

def init_github_version_sync(app):
    global github_version_sync
    
    db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
    github_version_sync = GitHubVersionSync(db_path)
    
    app.register_bluelogger.info(github_sync_bp, url_prefix='')
    
    return github_version_sync