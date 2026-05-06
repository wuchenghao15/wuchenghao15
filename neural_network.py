#!/usr/bin/env python3
"""
简单的神经网络实现
基于NumPy构建，用于AI学习和自动知识库扩充

import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('neural_network.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('neural_network')

class NeuralNetwork:
    """简单的前馈神经网络实现"""

    def __init__(self, input_size: int, hidden_sizes: List[int], output_size: int):
        """初始化神经网络

        Args:
            input_size: 输入层大小
            hidden_sizes: 隐藏层大小列表（可以是多层）
            output_size: 输出层大小
        self.input_size = input_size
        self.hidden_sizes = hidden_sizes
        self.output_size = output_size

        # 网络层配置
        self.layer_sizes = [input_size] + hidden_sizes + [output_size]
        self.num_layers = len(self.layer_sizes) - 1

        # 初始化权重和偏置
        self.weights = []
        self.biases = []

        for i in range(self.num_layers):
            # 使用He初始化权重
            weight = np.random.randn(self.layer_sizes[i], self.layer_sizes[i+1]) * np.sqrt(2.0 / self.layer_sizes[i])
            bias = np.zeros((1, self.layer_sizes[i+1]))
            self.weights.append(weight)
            self.biases.append(bias)

        # 激活函数（使用ReLU和Softmax）
        self.activation = self._relu
        self.activation_derivative = self._relu_derivative
        self.output_activation = self._softmax

        # 损失函数（交叉熵）
        self.loss = self._cross_entropy
        self.loss_derivative = self._cross_entropy_derivative

        # 训练参数
        self.learning_rate = 0.001
        self.batch_size = 32
        self.epochs = 100

        logger.info(f"初始化神经网络: {self.layer_sizes}")

    def _relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU激活函数"""
        return np.maximum(0, x)

    def _relu_derivative(self, x: np.ndarray) -> np.ndarray:
        """ReLU导数"""
        return (x > 0).astype(float)

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax激活函数"""
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)

    def _cross_entropy(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """交叉熵损失函数"""
        m = y_true.shape[0]
        return -np.sum(y_true * np.log(y_pred + 1e-10)) / m

    def _cross_entropy_derivative(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """交叉熵导数"""
        return y_pred - y_true

    def forward(self, X: np.ndarray) -> List[np.ndarray]:
        """前向传播

        Args:
            X: 输入数据，形状为 (样本数, 输入层大小)
        Returns:
            各层的输出列表
        activations = [X]
        current_activation = X

        # 前向传播到隐藏层
        for i in range(self.num_layers - 1):
            z = np.dot(current_activation, self.weights[i]) + self.biases[i]
            current_activation = self.activation(z)
            activations.append(current_activation)

        # 输出层
        z = np.dot(current_activation, self.weights[-1]) + self.biases[-1]
        current_activation = self.output_activation(z)
        activations.append(current_activation)

        return activations

        """反向传播

        Args:
            X: 输入数据
            y: 真实标签
        # 计算输出层误差
        error = self.loss_derivative(y, activations[-1])
        delta = error

        # 反向传播更新权重和偏置
        for i in range(self.num_layers - 1, -1, -1):
            if i == self.num_layers - 1:
                # 输出层
                weight_gradient = np.dot(activations[i].T, delta)
                bias_gradient = np.sum(delta, axis=0, keepdims=True)
            else:
                # 隐藏层
                delta = np.dot(delta, self.weights[i+1].T) * self.activation_derivative(activations[i+1])
                weight_gradient = np.dot(activations[i].T, delta)

            # 更新权重和偏置
            self.weights[i] -= self.learning_rate * weight_gradient
            self.biases[i] -= self.learning_rate * bias_gradient

    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = None, learning_rate: float = None) -> Dict[str, Any]:

            X: 输入数据
            y: 真实标签
            epochs: 训练轮数

        Returns:
            训练结果
        if epochs is not None:
            self.epochs = epochs
            self.learning_rate = learning_rate
        history = {
            'loss': [],
            'accuracy': []
        }

        logger.info(f"开始训练，样本数: {m}, 轮数: {self.epochs}, 学习率: {self.learning_rate}")

        for epoch in range(self.epochs):
            # 打乱数据
            permutation = np.random.permutation(m)
            X_shuffled = X[permutation]
            y_shuffled = y[permutation]

            epoch_loss = 0
            correct = 0

            # 分批训练
            for i in range(0, m, self.batch_size):
                X_batch = X_shuffled[i:i+self.batch_size]
                y_batch = y_shuffled[i:i+self.batch_size]

                # 前向传播
                activations = self.forward(X_batch)
                y_pred = activations[-1]

                # 计算损失
                batch_loss = self.loss(y_batch, y_pred)
                epoch_loss += batch_loss * X_batch.shape[0]

                # 计算准确率
                correct += np.sum(np.argmax(y_batch, axis=1) == np.argmax(y_pred, axis=1))

                # 反向传播
                self.backward(X_batch, y_batch, activations)

            # 计算平均损失和准确率
            epoch_loss /= m
            accuracy = correct / m

            # 保存历史记录
            history['loss'].append(epoch_loss)
            history['accuracy'].append(accuracy)

            # 每10轮打印一次
            if (epoch + 1) % 10 == 0 or epoch == 0:
                logger.info(f"轮次 {epoch+1}/{self.epochs} - 损失: {epoch_loss:.4f}, 准确率: {accuracy:.4f}")

        logger.info(f"训练完成，最终准确率: {history['accuracy'][-1]:.4f}")
        return history

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测

        Args:
            X: 输入数据

        Returns:
            预测结果
        return np.argmax(activations[-1], axis=1)

    def save(self, filename: str) -> None:
        """保存模型

        Args:
        model_data = {
            'hidden_sizes': self.hidden_sizes,
            'output_size': self.output_size,
            'biases': [b.tolist() for b in self.biases],
            'learning_rate': self.learning_rate,
            'batch_size': self.batch_size,
            'epochs': self.epochs
        }

        # JSON import removed - using database
with open(filename, 'w') as f:
            json.dump(model_data, f)

        logger.info(f"模型已保存到 {filename}")

    @classmethod
    def load(cls, filename: str) -> 'NeuralNetwork':
        """加载模型

        Args:
            filename: 模型路径

        Returns:
            加载的神经网络
        # JSON import removed - using database
with open(filename, 'r') as f:

        # 创建神经网络实例
            model_data['input_size'],
            model_data['hidden_sizes'],
            model_data['output_size']
        )

        model.weights = [np.array(w) for w in model_data['weights']]
        model.biases = [np.array(b) for b in model_data['biases']]

        # 加载训练参数
        model.learning_rate = model_data['learning_rate']
        model.epochs = model_data['epochs']

        logger.info(f"模型已从 {filename} 加载")
        return model

class SimpleQuestionClassifier(NeuralNetwork):
    """简单的问题分类器，用于知识库内容分类"""

        """初始化问题分类器"""
        # 输入大小设为100（假设使用100维词向量）
        # 隐藏层设为两层，大小分别为64和32
        # 输出大小设为4（假设分为词汇、语法、阅读和策略四类）
        super().__init__(input_size=100, hidden_sizes=[64, 32], output_size=4)

        # 类别映射
        self.category_map = {
            0: 'vocabulary',
            1: 'grammar',
            2: 'reading',
            3: 'strategies'
        }

        logger.info("初始化问题分类器")

    def predict_category(self, X: np.ndarray) -> List[str]:
        """预测类别名称

        Args:
            X: 输入数据

        Returns:
            类别名称列表
        predictions = self.predict(X)
        return [self.category_map[pred] for pred in predictions]

# 简单的测试函数
    """测试神经网络"""
    # 创建简单的分类任务（异或问题）
    X = np.array([
        [0, 0],
        [0, 1],
        [1, 0],
        [1, 1]
    ])
    y = np.array([
        [0, 1],  # 1 -> 类别1
        [1, 0]   # 0 -> 类别0

    # 创建神经网络
    model = NeuralNetwork(input_size=2, hidden_sizes=[4], output_size=2)

    # 训练模型
    history = model.train(X, y, epochs=1000, learning_rate=0.01)

    # 测试模型
    predictions = model.predict(X)
    print(f"预测结果: {predictions}")
    print(f"真实结果: {np.argmax(y, axis=1)}")

    # 保存模型
    model.save('test_model.json')

    # 加载模型
    loaded_model = NeuralNetwork.load('test_model.json')
    loaded_predictions = loaded_model.predict(X)
    print(f"加载模型预测结果: {loaded_predictions}")

if __name__ == "__main__":
    test_neural_network()
