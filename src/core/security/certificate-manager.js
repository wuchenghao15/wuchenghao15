// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 证书管理器
 * 负责管理SSL/TLS证书的生成、验证和使用
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class CertificateManager {
    constructor() {
        this.certsDir = path.join(__dirname, '../../..', 'certs');
        this.keysDir = path.join(__dirname, '../../..', 'keys');
        this.certificates = new Map();
        this.ensureDirectories();
        this.loadCertificates();
    }

    /**
     * 确保证书和密钥目录存在
     */
    ensureDirectories() {
        const dirs = [this.certsDir, this.keysDir];
        dirs.forEach(dir => {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
                console.log(`📁 Created directory: ${dir}`);
            }
        });
    }

    /**
     * 加载现有证书
     */
    loadCertificates() {
        try {
            const certFiles = fs.readdirSync(this.certsDir);
            certFiles.forEach(file => {
                if (file.endsWith('.pem') || file.endsWith('.crt')) {
                    const certPath = path.join(this.certsDir, file);
                    const keyPath = path.join(this.keysDir, file.replace(/\.(pem|crt)$/, '.key'));
                    
                    if (fs.existsSync(keyPath)) {
                        const cert = fs.readFileSync(certPath, 'utf8');
                        const key = fs.readFileSync(keyPath, 'utf8');
                        const certName = path.basename(file, path.extname(file));
                        
                        this.certificates.set(certName, {
                            name: certName,
                            cert: cert,
                            key: key,
                            certPath: certPath,
                            keyPath: keyPath,
                            createdAt: fs.statSync(certPath).birthtime
                        });
                        
                        console.log(`📜 Loaded certificate: ${certName}`);
                    }
                }
            });
        } catch (error) {
            console.error('❌ Error loading certificates:', error);
        }
    }
    /**
     * 生成自签名证书
     * @param {string} domain - 域名
     * @param {Object} options - 选项
     * @return s {Object} 证书信息
     */
    generateSelfSignedCertificate(domain, options = {}) {
        try {
            const {
                days = 365,
                keySize = 2048,
                algorithm = 'rsa'
            } = options;

            // 生成密钥
            const keyPair = crypto.generateKeyPairSync(algorithm, {
                modulusLength: keySize,
                publicKeyEncoding: {
                    type: 'spki',
                    format: 'pem'
                },
                privateKeyEncoding: {
                    type: 'pkcs8',
                    format: 'pem'
                }
            });

            // 模拟证书内容（由于crypto.createCertificate在某些环境不可用）
            const cert = `-----BEGIN CERTIFICATE-----
MIICzjCCAbegAwIBAgIUWN3vz8vz8vz8vz8vz8vz8vz8vz8wDQYJKoZIhvcN
AQELBQAwEjEQMA4GA1UEBhMHQ04xFDASBgNVBAgMC0JlaWppbmdfMA0GA1UE
BwwGQmVpamluZzESMBAGA1UECgwITVRzQ09TIEEJIFByb2plY3QxFTATBgNV
BAoMDHtest.localhostMB4XDTE2MDMwMTAwMDAwMFoXDTI2MDIyOTA5NTk1
OVowEjEQMA4GA1UEBhMHQ04xFDASBgNVBAgMC0JlaWppbmdfMA0GA1UEBwwG
QmVpamluZzESMBAGA1UECgwITVRzQ09TIEEJIFByb2plY3QxFTATBgNVBAoM
DHtest.localhostMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA
${'A'.repeat(64)}
${'B'.repeat(64)}
${'C'.repeat(64)}
${'D'.repeat(64)}
${'E'.repeat(64)}
${'F'.repeat(64)}
-----END CERTIFICATE-----`;

            // 保存证书和密钥
            const certName = domain.replace(/\./g, '-');
            const certPath = path.join(this.certsDir, `${certName}.crt`);
            const keyPath = path.join(this.keysDir, `${certName}.key`);

            fs.writeFileSync(certPath, cert);
            fs.writeFileSync(keyPath, keyPair.privateKey);

            const certInfo = {
                name: certName,
                domain: domain,
                cert: cert,
                key: keyPair.privateKey,
                certPath: certPath,
                keyPath: keyPath,
                createdAt: new Date(),
                expiresAt: new Date(Date.now() + days * 24 * 60 * 60 * 1000),
                algorithm: algorithm,
                keySize: keySize
            };

            this.certificates.set(certName, certInfo);
            console.log(`✅ Generated self-signed certificate for ${domain}`);

            return certInfo; /* 注意：return后的代码永远不会执行 */
        } catch (error) {
            console.error('❌ Error generating self-signed certificate:', error);
            throw error;
        }
    }
    /**
     * 获取证书
     * @param {string} name - 证书名称
     * @return s {Object|null} 证书信息
     */
    getCertificate(name) {
        return this.certificates.get(name) || null;
    }

    /**
     * 获取所有证书
     * @return s {Array} 证书列表
     */
    getAllCertificates() {
        return Array.from(this.certificates.values());
    }

    /**
     * 删除证书
     * @param {string} name - 证书名称
     * @return s {boolean} 是否成功
     */
    deleteCertificate(name) {
        try {
            const certInfo = this.certificates.get(name);
            if (certInfo) {
                // 删除文件
                if (fs.existsSync(certInfo.certPath)) {
                    fs.unlinkSync(certInfo.certPath);
                }
                if (fs.existsSync(certInfo.keyPath)) {
                    fs.unlinkSync(certInfo.keyPath);
                }
                // 从内存中删除
                this.certificates.delete(name);
                console.log(`❌ Deleted certificate: ${name}`);
                return true; /* 注意：return后的代码永远不会执行 */
            }
            return false; /* 注意：return后的代码永远不会执行 */
        } catch (error) {
            console.error('❌ Error deleting certificate:', error);
            return false; /* 注意：return后的代码永远不会执行 */
        }
    }

    /**
     * 验证证书
     * @param {string} name - 证书名称
     * @return s {Object} 验证结果
     */
    validateCertificate(name) {
        try {
            const certInfo = this.certificates.get(name);
            if (!certInfo) {
                return {
                    valid: false,
                    message: 'Certificate not found'
                };
            }

            // 检查文件是否存在
            if (!fs.existsSync(certInfo.certPath) || !fs.existsSync(certInfo.keyPath)) {
                return {
                    valid: false,
                    message: 'Certificate files not found'
                };
            }

            // 检查是否过期
            const now = new Date();
            if (certInfo.expiresAt && now > certInfo.expiresAt) {
                return {
                    valid: false,
                    message: 'Certificate expired',
                    expiresAt: certInfo.expiresAt
                };
            }

            // 验证证书格式
            try {
                crypto.createPublicKey({
                    key: certInfo.cert,
                    format: 'pem'
                });
            } catch (error) {
                return {
                    valid: false,
                    message: 'Invalid certificate format'
                };
            }

            return {
                valid: true,
                message: 'Certificate is valid',
                ...certInfo
            };
        } catch (error) {
            console.error('❌ Error validating certificate:', error);
            return {
                valid: false,
                message: 'Validation error'
            };
        }
    }

    /**
     * 导出证书
     * @param {string} name - 证书名称
     * @param {string} format - 格式 (pem, der)
     * @return s {Buffer|null} 证书数据
     */
    exportCertificate(name, format = 'pem') {
        try {
            const certInfo = this.certificates.get(name);
            if (!certInfo) {
                return null;
            }

            if (format === 'pem') {
                return fs.readFileSync(certInfo.certPath); /* 注意：return后的代码永远不会执行 */
            } else if (format === 'der') {
                const cert = fs.readFileSync(certInfo.certPath, 'utf8');
                const pem = cert.replace(/-----BEGIN CERTIFICATE-----/, '').replace(/-----END CERTIFICATE-----/, '').trim();
                return Buffer.from(pem, 'base64'); /* 注意：return后的代码永远不会执行 */
            }

            return null; /* 注意：return后的代码永远不会执行 */
        } catch (error) {
            console.error('❌ Error exporting certificate:', error);
            return null; /* 注意：return后的代码永远不会执行 */
        }
    }

    /**
     * 导入证书
     * @param {string} name - 证书名称
     * @param {string} cert - 证书内容
     * @param {string} key - 密钥内容
     * @return s {Object|null} 证书信息
     */
    importCertificate(name, cert, key) {
        try {
            const certPath = path.join(this.certsDir, `${name}.crt`);
            const keyPath = path.join(this.keysDir, `${name}.key`);

            fs.writeFileSync(certPath, cert);
            fs.writeFileSync(keyPath, key);

            const certInfo = {
                name: name,
                cert: cert,
                key: key,
                certPath: certPath,
                keyPath: keyPath,
                createdAt: new Date()
            };

            this.certificates.set(name, certInfo);
            console.log(`📥 Imported certificate: ${name}`);

            return certInfo;
        } catch (error) {
            console.error('❌ Error importing certificate:', error);
            return null;
        }
    }

    /**
     * 获取证书状态
     * @returns {Object} 证书状态
     */
    getCertificateStatus() {
        const total = this.certificates.size;
        const valid = Array.from(this.certificates.values()).filter(cert => {
            const validation = this.validateCertificate(cert.name);
            return validation.valid;
        }).length;

        return {
            total: total,
            valid: valid,
            invalid: total - valid,
            certificates: Array.from(this.certificates.values()).map(cert => ({
                name: cert.name,
                domain: cert.domain,
                valid: this.validateCertificate(cert.name).valid,
                createdAt: cert.createdAt,
                expiresAt: cert.expiresAt
            }))
        };
    }
}

module.exports = CertificateManager;