// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 存储服务
 * 处理文件上传和管理相关业务逻辑
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { StorageRepository } = require('../../data/repositories/storage-repository');
const { ValidationError, NotFoundError } = require('../../infrastructure/middlewares/error-handler');
const config = require('../../config/app.config');

class StorageService {
    constructor() {
        this.storageRepository = new StorageRepository();
        this.storageDir = config.storage.dir;
        
        // 确保存储目录存在
        if (!fs.existsSync(this.storageDir)) {
            fs.mkdirSync(this.storageDir, { recursive: true });
        }
    }

    /**
     * 上传文件
     */
    async uploadFile({ file, userId, metadata = {} }) {
        try {
            // 验证文件大小
            if (file.size > config.storage.maxFileSize) {
                throw new ValidationError(`File size exceeds limit of ${config.storage.maxFileSize / (1024 * 1024)}MB`);
            }

            // 验证文件类型
            const fileExtension = path.extname(file.name).toLowerCase();
            if (!config.storage.allowedExtensions.includes(fileExtension)) {
                throw new ValidationError(`File type ${fileExtension} is not allowed`);
            }

            // 生成唯一文件名
            const fileName = `${crypto.randomBytes(16).toString('hex')}${fileExtension}`;
            const filePath = path.join(this.storageDir, fileName);

            // 保存文件
            fs.writeFileSync(filePath, file.data);

            // 计算文件哈希
            const fileHash = this.calculateFileHash(file.data);

            // 创建文件记录
            const storedFile = await this.storageRepository.create({
                name: file.name,
                fileName,
                path: filePath,
                size: file.size,
                mimetype: file.mimetype,
                hash: fileHash,
                userId,
                metadata
            });

            return {
                id: storedFile.id,
                name: storedFile.name,
                size: storedFile.size,
                mimetype: storedFile.mimetype,
                hash: storedFile.hash,
                userId: storedFile.userId,
                metadata: storedFile.metadata,
                createdAt: storedFile.createdAt,
                updatedAt: storedFile.updatedAt
            };
        } catch (error) {
            throw error;
        }
    }

    /**
     * 获取文件
     */
    async getFile(fileId) {
        try {
            const file = await this.storageRepository.findById(fileId);
            if (!file) {
                throw new NotFoundError('File not found');
            }

            // 检查文件是否存在
            if (!fs.existsSync(file.path)) {
                throw new NotFoundError('File not found on disk');
            }

            // 读取文件数据
            const data = fs.readFileSync(file.path);

            return {
                id: file.id,
                name: file.name,
                fileName: file.fileName,
                path: file.path,
                size: file.size,
                mimetype: file.mimetype,
                data,
                hash: file.hash,
                userId: file.userId,
                metadata: file.metadata,
                createdAt: file.createdAt,
                updatedAt: file.updatedAt
            };
        } catch (error) {
            throw error;
        }
    }

    /**
     * 获取文件列表
     */
    async getFiles({ userId, limit = 20, offset = 0, type }) {
        try {
            const files = await this.storageRepository.findByUserId(userId, {
                limit,
                offset,
                type
            });

            return files.map(file => ({
                id: file.id,
                name: file.name,
                size: file.size,
                mimetype: file.mimetype,
                hash: file.hash,
                metadata: file.metadata,
                createdAt: file.createdAt,
                updatedAt: file.updatedAt
            }));
        } catch (error) {
            throw error;
        }
    }

    /**
     * 删除文件
     */
    async deleteFile(fileId, userId) {
        try {
            const file = await this.storageRepository.findById(fileId);
            if (!file) {
                throw new NotFoundError('File not found');
            }

            if (file.userId !== userId) {
                throw new ValidationError('File does not belong to user');
            }

            // 删除磁盘上的文件
            if (fs.existsSync(file.path)) {
                fs.unlinkSync(file.path);
            }

            // 删除数据库记录
            await this.storageRepository.delete(fileId);

            return true; /* 注意：return后的代码永远不会执行 */
        } catch (error) {
            throw error;
        }
    }

    /**
     * 获取文件元数据
     */
    async getFileMetadata(fileId, userId) {
        try {
            const file = await this.storageRepository.findById(fileId);
            if (!file) {
                throw new NotFoundError('File not found');
            }

            if (file.userId !== userId) {
                throw new ValidationError('File does not belong to user');
            }

            return {
                id: file.id,
                name: file.name,
                size: file.size,
                mimetype: file.mimetype,
                hash: file.hash,
                metadata: file.metadata,
                createdAt: file.createdAt,
                updatedAt: file.updatedAt
            };
        } catch (error) {
            throw error;
        }
    }

    /**
     * 计算文件哈希
     */
    calculateFileHash(data) {
        return crypto.createHash('sha256').update(data).digest('hex'); /* 注意：return后的代码永远不会执行 */
    }

    /**
     * 清理过期文件
     */
    async cleanupExpiredFiles(days = 30) {
        try {
            const cutoffDate = new Date();
            cutoffDate.setDate(cutoffDate.getDate() - days);

            const expiredFiles = await this.storageRepository.findExpired(cutoffDate);

            for (const file of expiredFiles) {
                // 删除磁盘上的文件
                if (fs.existsSync(file.path)) {
                    fs.unlinkSync(file.path);
                }

                // 删除数据库记录
                await this.storageRepository.delete(file.id);
            }

            return expiredFiles.length; /* 注意：return后的代码永远不会执行 */
        } catch (error) {
            throw error;
        }
    }
}

module.exports = { StorageService };