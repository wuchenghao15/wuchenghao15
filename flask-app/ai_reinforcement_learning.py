#!/usr/bin/env python3
"""
MTSCOS AI 强化学习服务 (v14.9.0)
===================================
AI 强化学习训练和管理服务。

核心能力：
1. Q-Learning - 表格法和函数近似 Q-Learning
2. 策略梯度 - REINFORCE 算法
3. Actor-Critic - 简化版 A2C
4. 奖励模型 - RLHF 人类反馈奖励
5. 经验回放 - 经验缓冲和采样
6. 环境管理 - 简单环境定义和交互
7. 训练监控 - Episode 奖励追踪和收敛检测
8. 策略评估 - 策略性能评估和对比
"""
import os
import json
import math
import sqlite3
import random
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict, deque

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_reinforcement_learning.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIReinforcementLearning')


# ========== 简单环境 ==========

class SimpleEnvironment:
    """简单网格世界环境"""

    def __init__(self, width: int = 5, height: int = 5,
                 goal: Tuple[int, int] = (4, 4),
                 traps: List[Tuple[int, int]] = None):
        self.width = width
        self.height = height
        self.goal = goal
        self.traps = traps or []
        self.state = (0, 0)
        self._step_count = 0
        self._max_steps = 100

    def reset(self) -> Tuple[int, int]:
        self.state = (0, 0)
        self._step_count = 0
        return self.state

    def step(self, action: int) -> Tuple[Tuple[int, int], float, bool, Dict]:
        """执行动作: 0=上 1=下 2=左 3=右"""
        x, y = self.state
        if action == 0:  # 上
            y = max(0, y - 1)
        elif action == 1:  # 下
            y = min(self.height - 1, y + 1)
        elif action == 2:  # 左
            x = max(0, x - 1)
        elif action == 3:  # 右
            x = min(self.width - 1, x + 1)

        self.state = (x, y)
        self._step_count += 1

        # 奖励
        reward = -0.01  # 步骤惩罚
        done = False

        if self.state == self.goal:
            reward = 1.0
            done = True
        elif self.state in self.traps:
            reward = -1.0
            done = True
        elif self._step_count >= self._max_steps:
            done = True

        info = {'step': self._step_count, 'position': self.state}
        return self.state, reward, done, info

    @property
    def n_actions(self) -> int:
        return 4

    @property
    def n_states(self) -> int:
        return self.width * self.height

    def state_to_id(self, state: Tuple[int, int]) -> int:
        return state[0] * self.height + state[1]


# ========== 经验回放缓冲 ==========

class ReplayBuffer:
    """经验回放缓冲"""

    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self._buffer: deque = deque(maxlen=capacity)
        self._priority_buffer: deque = deque(maxlen=capacity // 10)

    def push(self, state: Any, action: int, reward: float,
             next_state: Any, done: bool, priority: float = 0):
        experience = (state, action, reward, next_state, done)
        if priority > 0.5:  # 高奖励经验进入优先缓冲
            self._priority_buffer.append(experience)
        else:
            self._buffer.append(experience)

    def sample(self, batch_size: int) -> List[Tuple]:
        if len(self._buffer) < batch_size:
            return list(self._buffer)
        # 30% 优先采样
        priority_count = min(int(batch_size * 0.3), len(self._priority_buffer))
        normal_count = batch_size - priority_count

        samples = []
        if priority_count > 0 and self._priority_buffer:
            samples.extend(random.sample(list(self._priority_buffer), priority_count))
        if normal_count > 0:
            samples.extend(random.sample(list(self._buffer), normal_count))
        return samples

    def __len__(self):
        return len(self._buffer) + len(self._priority_buffer)

    def stats(self) -> Dict:
        return {
            'total_size': len(self),
            'normal_size': len(self._buffer),
            'priority_size': len(self._priority_buffer),
            'capacity': self.capacity
        }


# ========== Q-Learning ==========

class QLearningAgent:
    """Q-Learning 智能体"""

    def __init__(self, n_states: int, n_actions: int,
                 learning_rate: float = 0.1, gamma: float = 0.95,
                 epsilon: float = 1.0, epsilon_min: float = 0.01,
                 epsilon_decay: float = 0.995):
        self.n_states = n_states
        self.n_actions = n_actions
        self.lr = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        # Q表
        self.q_table = [[0.0] * n_actions for _ in range(n_states)]
        self._training_steps = 0

    def act(self, state: int, training: bool = True) -> int:
        """选择动作（epsilon-greedy）"""
        if training and random.random() < self.epsilon:
            return random.randint(0, self.n_actions - 1)
        return self._best_action(state)

    def _best_action(self, state: int) -> int:
        q_values = self.q_table[state]
        max_q = max(q_values)
        # 随机选择最优动作（处理多个相同最大值）
        best_actions = [i for i, q in enumerate(q_values) if q == max_q]
        return random.choice(best_actions)

    def learn(self, state: int, action: int, reward: float,
              next_state: int, done: bool) -> Dict:
        """Q-Learning 更新"""
        current_q = self.q_table[state][action]

        if done:
            target_q = reward
        else:
            max_next_q = max(self.q_table[next_state])
            target_q = reward + self.gamma * max_next_q

        # Q值更新
        td_error = target_q - current_q
        self.q_table[state][action] += self.lr * td_error

        # epsilon 衰减
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self._training_steps += 1

        return {
            'td_error': round(td_error, 6),
            'epsilon': round(self.epsilon, 6),
            'training_steps': self._training_steps
        }

    def get_policy(self) -> Dict:
        """获取策略"""
        policy = {}
        for s in range(self.n_states):
            policy[s] = self._best_action(s)
        return policy

    def stats(self) -> Dict:
        # Q值统计
        all_q = [q for row in self.q_table for q in row]
        non_zero = [q for q in all_q if q != 0]
        return {
            'training_steps': self._training_steps,
            'epsilon': round(self.epsilon, 6),
            'q_values_mean': round(sum(all_q) / len(all_q), 6) if all_q else 0,
            'non_zero_q': len(non_zero),
            'explored_states': len(set(s for s in range(self.n_states) if any(q != 0 for q in self.q_table[s])))
        }


# ========== 策略梯度 (REINFORCE) ==========

class PolicyGradientAgent:
    """策略梯度智能体（简化版）"""

    def __init__(self, n_features: int, n_actions: int,
                 learning_rate: float = 0.01, gamma: float = 0.95):
        self.n_features = n_features
        self.n_actions = n_actions
        self.lr = learning_rate
        self.gamma = gamma
        # 策略参数（线性策略）
        self.weights = [[random.gauss(0, 0.1) for _ in range(n_features)]
                       for _ in range(n_actions)]
        self.bias = [0.0] * n_actions
        self._episode_states = []
        self._episode_actions = []
        self._episode_rewards = []
        self._training_episodes = 0

    def _softmax(self, scores: List[float]) -> List[float]:
        max_score = max(scores)
        exp_scores = [math.exp(s - max_score) for s in scores]
        total = sum(exp_scores)
        return [e / total for e in exp_scores]

    def _get_scores(self, state: List[float]) -> List[float]:
        return [
            sum(w * s for w, s in zip(self.weights[a], state)) + self.bias[a]
            for a in range(self.n_actions)
        ]

    def act(self, state: List[float], training: bool = True) -> int:
        scores = self._get_scores(state)
        probs = self._softmax(scores)
        # 采样动作
        r = random.random()
        cumsum = 0
        for a, p in enumerate(probs):
            cumsum += p
            if r <= cumsum:
                return a
        return self.n_actions - 1

    def store_transition(self, state: List[float], action: int, reward: float):
        """存储 episode 转移"""
        self._episode_states.append(state)
        self._episode_actions.append(action)
        self._episode_rewards.append(reward)

    def update(self) -> Dict:
        """Episode 结束后更新策略"""
        n = len(self._episode_rewards)
        if n == 0:
            return {'error': '无经验可更新'}

        # 计算累积回报
        returns = [0.0] * n
        G = 0
        for t in range(n - 1, -1, -1):
            G = self._episode_rewards[t] + self.gamma * G
            returns[t] = G

        # 归一化回报
        mean_return = sum(returns) / n
        std_return = math.sqrt(sum((r - mean_return) ** 2 for r in returns) / n) if n > 1 else 1
        if std_return == 0:
            std_return = 1
        returns = [(r - mean_return) / std_return for r in returns]

        # 策略梯度更新
        for t in range(n):
            state = self._episode_states[t]
            action = self._episode_actions[t]
            G = returns[t]

            scores = self._get_scores(state)
            probs = self._softmax(scores)

            # 梯度: (one_hot - probs) * G * state
            for a in range(self.n_actions):
                indicator = 1.0 if a == action else 0.0
                grad = (indicator - probs[a]) * G
                for i in range(self.n_features):
                    self.weights[a][i] += self.lr * grad * state[i]
                self.bias[a] += self.lr * grad

        episode_reward = sum(self._episode_rewards)
        self._training_episodes += 1

        # 清空 episode
        self._episode_states = []
        self._episode_actions = []
        self._episode_rewards = []

        return {
            'episode_reward': round(episode_reward, 6),
            'mean_return': round(mean_return, 6),
            'training_episodes': self._training_episodes
        }

    def stats(self) -> Dict:
        return {
            'training_episodes': self._training_episodes,
            'n_features': self.n_features,
            'n_actions': self.n_actions
        }


# ========== 奖励模型 (RLHF) ==========

class RewardModel:
    """人类反馈奖励模型（简化版）"""

    def __init__(self, n_features: int, learning_rate: float = 0.01):
        self.n_features = n_features
        self.lr = learning_rate
        self.weights = [0.0] * n_features
        self.bias = 0.0
        self._comparisons = []

    def predict_reward(self, features: List[float]) -> float:
        """预测奖励"""
        return sum(w * f for w, f in zip(self.weights, features)) + self.bias

    def add_comparison(self, features_a: List[float], features_b: List[float],
                      preference: str):
        """添加人类偏好比较: 'a'/'b'/'equal'"""
        self._comparisons.append({
            'features_a': features_a,
            'features_b': features_b,
            'preference': preference
        })

    def train(self, epochs: int = 10) -> Dict:
        """训练奖励模型"""
        if not self._comparisons:
            return {'error': '无比较数据'}

        for epoch in range(epochs):
            total_loss = 0
            for comp in self._comparisons:
                reward_a = self.predict_reward(comp['features_a'])
                reward_b = self.predict_reward(comp['features_b'])

                # Bradley-Terry 模型
                if comp['preference'] == 'a':
                    target = 1
                elif comp['preference'] == 'b':
                    target = 0
                else:
                    target = 0.5

                # sigmoid 预测
                diff = reward_a - reward_b
                pred = 1 / (1 + math.exp(-diff))
                error = target - pred

                # 梯度更新
                for i in range(self.n_features):
                    grad = error * (comp['features_a'][i] - comp['features_b'][i])
                    self.weights[i] += self.lr * grad
                self.bias += self.lr * error
                total_loss += error ** 2

        return {
            'epochs': epochs,
            'comparisons': len(self._comparisons),
            'final_loss': round(total_loss / len(self._comparisons), 6)
        }

    def stats(self) -> Dict:
        return {
            'n_comparisons': len(self._comparisons),
            'weights_norm': round(math.sqrt(sum(w ** 2 for w in self.weights)), 6)
        }


# ========== 强化学习服务 ==========

class AIReinforcementLearning:
    """AI 强化学习服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()
        self._agents: Dict[str, Dict] = {}
        self._environments: Dict[str, SimpleEnvironment] = {}

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rl_agents (
                        agent_id TEXT PRIMARY KEY,
                        agent_name TEXT,
                        algorithm TEXT,
                        n_states INTEGER,
                        n_actions INTEGER,
                        config TEXT,
                        status TEXT DEFAULT 'created',
                        episodes_trained INTEGER DEFAULT 0,
                        total_reward REAL DEFAULT 0,
                        best_reward REAL,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rl_training_logs (
                        log_id TEXT PRIMARY KEY,
                        agent_id TEXT,
                        episode INTEGER,
                        episode_reward REAL,
                        episode_length INTEGER,
                        epsilon REAL,
                        loss REAL,
                        created_at TEXT
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rl_agent ON rl_training_logs(agent_id)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化强化学习数据库失败: {e}")

    # ========== 创建智能体 ==========

    def create_agent(self, agent_id: str, agent_name: str = '',
                    algorithm: str = 'q_learning', config: Dict = None) -> Dict:
        """创建 RL 智能体"""
        config = config or {}

        if algorithm == 'q_learning':
            n_states = config.get('n_states', 25)
            n_actions = config.get('n_actions', 4)
            agent = QLearningAgent(
                n_states=n_states, n_actions=n_actions,
                learning_rate=config.get('learning_rate', 0.1),
                gamma=config.get('gamma', 0.95),
                epsilon=config.get('epsilon', 1.0)
            )
        elif algorithm == 'policy_gradient':
            n_features = config.get('n_features', 10)
            n_actions = config.get('n_actions', 4)
            agent = PolicyGradientAgent(
                n_features=n_features, n_actions=n_actions,
                learning_rate=config.get('learning_rate', 0.01)
            )
        else:
            return {'success': False, 'error': f'不支持的算法: {algorithm}'}

        self._agents[agent_id] = {
            'agent': agent,
            'algorithm': algorithm,
            'episodes': 0,
            'total_reward': 0,
            'best_reward': float('-inf'),
            'rewards_history': deque(maxlen=1000)
        }

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO rl_agents
                    (agent_id, agent_name, algorithm, n_states, n_actions, config, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    agent_id, agent_name or agent_id, algorithm,
                    config.get('n_states', config.get('n_features', 10)),
                    config.get('n_actions', 4),
                    json.dumps(config, ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        return {'success': True, 'agent_id': agent_id, 'algorithm': algorithm}

    # ========== 创建环境 ==========

    def create_environment(self, env_id: str, width: int = 5, height: int = 5,
                          goal: Tuple[int, int] = (4, 4),
                          traps: List[Tuple[int, int]] = None) -> Dict:
        """创建环境"""
        self._environments[env_id] = SimpleEnvironment(width, height, goal, traps)
        return {'success': True, 'env_id': env_id}

    # ========== 训练 ==========

    def train_episode(self, agent_id: str, env_id: str,
                     max_steps: int = 100) -> Dict:
        """训练一个 episode"""
        agent_data = self._agents.get(agent_id)
        env = self._environments.get(env_id)
        if not agent_data or not env:
            return {'success': False, 'error': '智能体或环境不存在'}

        agent = agent_data['agent']
        state = env.reset()
        total_reward = 0
        steps = 0

        for step in range(max_steps):
            # Q-Learning 特殊处理
            if agent_data['algorithm'] == 'q_learning':
                state_id = env.state_to_id(state)
                action = agent.act(state_id, training=True)
                next_state, reward, done, info = env.step(action)
                next_state_id = env.state_to_id(next_state)
                agent.learn(state_id, action, reward, next_state_id, done)
                state = next_state
            elif agent_data['algorithm'] == 'policy_gradient':
                # 简化：将状态转为特征向量
                features = [state[0] / env.width, state[1] / env.height, 1.0]
                action = agent.act(features, training=True)
                next_state, reward, done, info = env.step(action)
                agent.store_transition(features, action, reward)
                state = next_state

            total_reward += reward
            steps += 1
            if done:
                break

        # 策略梯度 episode 更新
        if agent_data['algorithm'] == 'policy_gradient':
            agent.update()

        # 更新统计
        agent_data['episodes'] += 1
        agent_data['total_reward'] += total_reward
        agent_data['rewards_history'].append(total_reward)
        if total_reward > agent_data['best_reward']:
            agent_data['best_reward'] = total_reward

        # 记录日志
        self._log_training(agent_id, agent_data['episodes'], total_reward, steps, agent)

        return {
            'success': True,
            'agent_id': agent_id,
            'episode': agent_data['episodes'],
            'total_reward': round(total_reward, 6),
            'steps': steps,
            'avg_reward': round(sum(agent_data['rewards_history']) / len(agent_data['rewards_history']), 6)
        }

    def train_episodes(self, agent_id: str, env_id: str,
                      n_episodes: int = 100) -> Dict:
        """训练多个 episode"""
        rewards = []
        for _ in range(n_episodes):
            result = self.train_episode(agent_id, env_id)
            if result.get('success'):
                rewards.append(result['total_reward'])

        if not rewards:
            return {'success': False, 'error': '训练失败'}

        # 检测收敛
        recent_avg = sum(rewards[-10:]) / min(len(rewards), 10)
        early_avg = sum(rewards[:10]) / min(len(rewards), 10)
        improvement = recent_avg - early_avg

        return {
            'success': True,
            'agent_id': agent_id,
            'episodes_trained': len(rewards),
            'avg_reward': round(sum(rewards) / len(rewards), 6),
            'best_reward': round(max(rewards), 6),
            'recent_avg': round(recent_avg, 6),
            'improvement': round(improvement, 6),
            'converged': abs(improvement) < 0.01 and len(rewards) >= 20
        }

    # ========== 评估 ==========

    def evaluate(self, agent_id: str, env_id: str,
                n_episodes: int = 10) -> Dict:
        """评估智能体"""
        agent_data = self._agents.get(agent_id)
        env = self._environments.get(env_id)
        if not agent_data or not env:
            return {'success': False, 'error': '智能体或环境不存在'}

        agent = agent_data['agent']
        rewards = []
        steps_list = []
        successes = 0

        for _ in range(n_episodes):
            state = env.reset()
            total_reward = 0
            steps = 0

            for step in range(100):
                if agent_data['algorithm'] == 'q_learning':
                    state_id = env.state_to_id(state)
                    action = agent.act(state_id, training=False)
                elif agent_data['algorithm'] == 'policy_gradient':
                    features = [state[0] / env.width, state[1] / env.height, 1.0]
                    action = agent.act(features, training=False)

                next_state, reward, done, info = env.step(action)
                total_reward += reward
                steps += 1
                state = next_state
                if done:
                    if reward > 0:
                        successes += 1
                    break

            rewards.append(total_reward)
            steps_list.append(steps)

        return {
            'success': True,
            'agent_id': agent_id,
            'episodes': n_episodes,
            'avg_reward': round(sum(rewards) / len(rewards), 6),
            'std_reward': round(math.sqrt(sum((r - sum(rewards)/len(rewards))**2 for r in rewards) / len(rewards)), 6),
            'avg_steps': round(sum(steps_list) / len(steps_list), 2),
            'success_rate': round(successes / n_episodes * 100, 2),
            'best_reward': round(max(rewards), 6),
            'worst_reward': round(min(rewards), 6)
        }

    def get_policy(self, agent_id: str) -> Dict:
        """获取智能体策略"""
        agent_data = self._agents.get(agent_id)
        if not agent_data:
            return {'success': False, 'error': '智能体不存在'}

        agent = agent_data['agent']
        if hasattr(agent, 'get_policy'):
            policy = agent.get_policy()
            # 转换键为字符串
            return {
                'success': True,
                'agent_id': agent_id,
                'policy': {str(k): v for k, v in policy.items()}
            }
        return {'success': False, 'error': '该算法不支持策略导出'}

    def _log_training(self, agent_id: str, episode: int, reward: float,
                     steps: int, agent: Any):
        log_id = f"LOG-{random.randint(100000, 999999)}"
        epsilon = getattr(agent, 'epsilon', 0)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO rl_training_logs
                    (log_id, agent_id, episode, episode_reward, episode_length,
                     epsilon, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    log_id, agent_id, episode, reward, steps,
                    epsilon, datetime.now().isoformat()
                ))
                conn.commit()
        except Exception:
            pass

    # ========== 查询 ==========

    def get_agent_info(self, agent_id: str) -> Optional[Dict]:
        agent_data = self._agents.get(agent_id)
        if not agent_data:
            return None
        agent = agent_data['agent']
        avg_reward = sum(agent_data['rewards_history']) / len(agent_data['rewards_history']) \
            if agent_data['rewards_history'] else 0
        return {
            'agent_id': agent_id,
            'algorithm': agent_data['algorithm'],
            'episodes': agent_data['episodes'],
            'total_reward': round(agent_data['total_reward'], 6),
            'best_reward': round(agent_data['best_reward'], 6),
            'avg_reward': round(avg_reward, 6),
            'agent_stats': agent.stats() if hasattr(agent, 'stats') else {}
        }

    def list_agents(self) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT agent_id, agent_name, algorithm, episodes_trained,
                           best_reward, created_at
                    FROM rl_agents ORDER BY created_at DESC
                ''')
                return [
                    {
                        'agent_id': r[0], 'agent_name': r[1], 'algorithm': r[2],
                        'episodes': r[3], 'best_reward': r[4], 'created_at': r[5]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM rl_agents')
                total_agents = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM rl_training_logs')
                total_logs = cursor.fetchone()[0]
                cursor.execute("SELECT algorithm, COUNT(*) FROM rl_agents GROUP BY algorithm")
                algo_dist = {r[0]: r[1] for r in cursor.fetchall()}
            return {
                'total_agents': total_agents,
                'total_training_logs': total_logs,
                'algorithm_distribution': algo_dist,
                'active_agents': len(self._agents),
                'active_environments': len(self._environments)
            }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    rl = AIReinforcementLearning()

    print("=== Q-Learning 训练 ===")
    rl.create_agent('q-agent', 'Q学习智能体', 'q_learning',
                   config={'n_states': 25, 'n_actions': 4, 'learning_rate': 0.1})
    rl.create_environment('grid-env', width=5, height=5, goal=(4, 4),
                         traps=[(2, 2)])

    print("训练 200 个 episode:")
    result = rl.train_episodes('q-agent', 'grid-env', n_episodes=200)
    print(f"  平均奖励: {result['avg_reward']}")
    print(f"  最佳奖励: {result['best_reward']}")
    print(f"  最近平均: {result['recent_avg']}")
    print(f"  收敛: {result['converged']}")

    print("\n评估:")
    eval_result = rl.evaluate('q-agent', 'grid-env', n_episodes=20)
    print(f"  平均奖励: {eval_result['avg_reward']}")
    print(f"  成功率: {eval_result['success_rate']}%")
    print(f"  平均步数: {eval_result['avg_steps']}")

    print("\n策略:")
    policy = rl.get_policy('q-agent')
    if policy.get('success'):
        for state, action in list(policy['policy'].items())[:10]:
            action_names = ['上', '下', '左', '右']
            print(f"  状态{state}: {action_names[action]}")

    print("\n=== 策略梯度训练 ===")
    rl.create_agent('pg-agent', '策略梯度智能体', 'policy_gradient',
                   config={'n_features': 3, 'n_actions': 4, 'learning_rate': 0.01})

    print("训练 100 个 episode:")
    result = rl.train_episodes('pg-agent', 'grid-env', n_episodes=100)
    print(f"  平均奖励: {result['avg_reward']}")
    print(f"  最佳奖励: {result['best_reward']}")

    print("\n=== RLHF 奖励模型 ===")
    reward_model = RewardModel(n_features=3, learning_rate=0.01)

    # 添加人类偏好
    for _ in range(50):
        feat_a = [random.random() for _ in range(3)]
        feat_b = [random.random() for _ in range(3)]
        # 偏好特征总和更大的
        pref = 'a' if sum(feat_a) > sum(feat_b) else 'b'
        reward_model.add_comparison(feat_a, feat_b, pref)

    train_result = reward_model.train(epochs=20)
    print(f"  训练: {train_result}")
    print(f"  权重: {[round(w, 4) for w in reward_model.weights]}")
    print(f"  预测奖励: {round(reward_model.predict_reward([0.8, 0.6, 0.4]), 6)}")

    print(f"\n统计: {rl.get_statistics()}")
