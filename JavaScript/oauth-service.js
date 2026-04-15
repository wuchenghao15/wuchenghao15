const axios = require('axios');
const crypto = require('crypto');
const config = require('./config');
const database = require('./database');

class OAuthService {
    constructor() {
        this.providers = {
            github: new GitHubOAuth(),
            google: new GoogleOAuth(),
            wechat: new WeChatOAuth(),
            qq: new QQOAuth(),
            alipay: new AlipayOAuth()
        };
    }

    getAuthorizationUrl(provider, state) {
        const oauthProvider = this.providers[provider];
        if (!oauthProvider) {
            throw new Error(`不支持的OAuth提供商: ${provider}`);
        }
        return oauthProvider.getAuthorizationUrl(state);
    }

    async authenticate(provider, code, state) {
        const oauthProvider = this.providers[provider];
        if (!oauthProvider) {
            throw new Error(`不支持的OAuth提供商: ${provider}`);
        }

        try {
            console.log(`[OAUTH] 开始${provider}认证流程`);
            
            // 1. 获取访问令牌
            const tokenData = await oauthProvider.getAccessToken(code);
            
            // 2. 获取用户信息
            const userInfo = await oauthProvider.getUserInfo(tokenData.access_token);
            
            // 3. 查找或创建用户
            const user = await this.findOrCreateUser(provider, userInfo, tokenData);
            
            console.log(`[OAUTH] ${provider}认证成功: ${user.username} (ID: ${user.id})`);
            
            return {
                user: {
                    id: user.id,
                    username: user.username,
                    email: user.email,
                    fullName: user.full_name,
                    avatarUrl: user.avatar_url,
                    role: user.role
                },
                provider: provider,
                providerUserId: userInfo.id,
                accessToken: tokenData.access_token,
                refreshToken: tokenData.refresh_token,
                tokenExpiresAt: tokenData.expires_at
            };
            
        } catch (error) {
            console.error(`[OAUTH] ${provider}认证失败:`, error);
            throw new Error(`${provider}认证失败: ${error.message}`);
        }
    }

    async findOrCreateUser(provider, userInfo, tokenData) {
        try {
            // 查找现有的第三方认证记录
            const existingAuth = await database.findThirdPartyAuth(provider, userInfo.id);
            
            if (existingAuth) {
                // 更新令牌信息
                await this.updateThirdPartyAuth(existingAuth.id, tokenData, userInfo);
                
                // 获取用户信息
                const user = await database.findUserById(existingAuth.user_id);
                if (!user) {
                    throw new Error('关联用户不存在');
                }
                
                return user;
            }
            
            // 查找是否有相同邮箱的用户
            let user = null;
            if (userInfo.email) {
                user = await database.findUserByEmail(userInfo.email);
            }
            
            if (user) {
                // 绑定到现有用户
                await this.createThirdPartyAuth(user.id, provider, userInfo, tokenData);
                return user;
            }
            
            // 创建新用户
            const userId = await this.createUserFromOAuth(provider, userInfo);
            user = await database.findUserById(userId);
            
            // 创建第三方认证记录
            await this.createThirdPartyAuth(userId, provider, userInfo, tokenData);
            
            return user;
            
        } catch (error) {
            console.error('[OAUTH] 查找或创建用户失败:', error);
            throw error;
        }
    }

    async createUserFromOAuth(provider, userInfo) {
        try {
            // 生成用户名
            let username = userInfo.username || userInfo.name || userInfo.email || `${provider}_${userInfo.id}`;
            
            // 确保用户名唯一
            let originalUsername = username;
            let counter = 1;
            while (await database.findUserByUsername(username)) {
                username = `${originalUsername}_${counter}`;
                counter++;
            }
            
            // 生成随机密码
            const randomPassword = crypto.randomBytes(32).toString('hex');
            
            // 创建用户
            const userId = await database.createUser({
                username: username,
                email: userInfo.email || `${username}@${provider}.local`,
                password: randomPassword,
                fullName: userInfo.name || userInfo.nickname || username,
                phone: null
            });
            
            console.log(`[OAUTH] 从${provider}创建新用户: ${username} (ID: ${userId})`);
            return userId;
            
        } catch (error) {
            console.error('[OAUTH] 创建OAuth用户失败:', error);
            throw error;
        }
    }

    async createThirdPartyAuth(userId, provider, userInfo, tokenData) {
        try {
            await database.createThirdPartyAuth({
                userId: userId,
                provider: provider,
                providerUserId: userInfo.id,
                accessToken: tokenData.access_token,
                refreshToken: tokenData.refresh_token,
                tokenExpiresAt: tokenData.expires_at,
                profileData: userInfo
            });
        } catch (error) {
            console.error('[OAUTH] 创建第三方认证记录失败:', error);
            throw error;
        }
    }

    async updateThirdPartyAuth(authId, tokenData, userInfo) {
        try {
            // 这里应该实现更新逻辑，但为了简化，我们只记录日志
            console.log(`[OAUTH] 更新第三方认证记录: ${authId}`);
        } catch (error) {
            console.error('[OAUTH] 更新第三方认证记录失败:', error);
            throw error;
        }
    }
}

// GitHub OAuth
class GitHubOAuth {
    getAuthorizationUrl(state) {
        const params = new URLSearchParams({
            client_id: config.oauth.github.clientId,
            redirect_uri: config.oauth.github.redirectUri,
            scope: config.oauth.github.scope,
            state: state
        });
        
        return `https://github.com/login/oauth/authorize?${params.toString()}`;
    }

    async getAccessToken(code) {
        try {
            const response = await axios.post('https://github.com/login/oauth/access_token', {
                client_id: config.oauth.github.clientId,
                client_secret: config.oauth.github.clientSecret,
                code: code
            }, {
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            const tokenData = response.data;
            if (tokenData.error) {
                throw new Error(tokenData.error_description || tokenData.error);
            }
            
            return {
                access_token: tokenData.access_token,
                token_type: tokenData.token_type,
                scope: tokenData.scope
            };
        } catch (error) {
            console.error('[GITHUB] 获取访问令牌失败:', error);
            throw error;
        }
    }

    async getUserInfo(accessToken) {
        try {
            const response = await axios.get('https://api.github.com/user', {
                headers: {
                    'Authorization': `token ${accessToken}`,
                    'User-Agent': 'MTSCOS-Login-System'
                }
            });
            
            const userData = response.data;
            
            // 获取用户邮箱（如果公开）
            if (!userData.email) {
                try {
                    const emailResponse = await axios.get('https://api.github.com/user/emails', {
                        headers: {
                            'Authorization': `token ${accessToken}`,
                            'User-Agent': 'MTSCOS-Login-System'
                        }
                    });
                    
                    const primaryEmail = emailResponse.data.find(email => email.primary && email.verified);
                    if (primaryEmail) {
                        userData.email = primaryEmail.email;
                    }
                } catch (emailError) {
                    console.warn('[GITHUB] 获取邮箱失败:', emailError.message);
                }
            }
            
            return {
                id: userData.id.toString(),
                username: userData.login,
                name: userData.name,
                email: userData.email,
                avatar_url: userData.avatar_url,
                bio: userData.bio,
                location: userData.location,
                company: userData.company
            };
        } catch (error) {
            console.error('[GITHUB] 获取用户信息失败:', error);
            throw error;
        }
    }
}

// Google OAuth
class GoogleOAuth {
    getAuthorizationUrl(state) {
        const params = new URLSearchParams({
            client_id: config.oauth.google.clientId,
            redirect_uri: config.oauth.google.redirectUri,
            response_type: 'code',
            scope: config.oauth.google.scope.join(' '),
            state: state,
            access_type: 'offline',
            prompt: 'consent'
        });
        
        return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
    }

    async getAccessToken(code) {
        try {
            const response = await axios.post('https://oauth2.googleapis.com/token', {
                client_id: config.oauth.google.clientId,
                client_secret: config.oauth.google.clientSecret,
                code: code,
                grant_type: 'authorization_code',
                redirect_uri: config.oauth.google.redirectUri
            });
            
            const tokenData = response.data;
            if (tokenData.error) {
                throw new Error(tokenData.error_description || tokenData.error);
            }
            
            return {
                access_token: tokenData.access_token,
                refresh_token: tokenData.refresh_token,
                token_type: tokenData.token_type,
                expires_in: tokenData.expires_in,
                expires_at: new Date(Date.now() + tokenData.expires_in * 1000)
            };
        } catch (error) {
            console.error('[GOOGLE] 获取访问令牌失败:', error);
            throw error;
        }
    }

    async getUserInfo(accessToken) {
        try {
            const response = await axios.get('https://www.googleapis.com/oauth2/v2/userinfo', {
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });
            
            const userData = response.data;
            
            return {
                id: userData.id,
                username: userData.email.split('@')[0],
                name: userData.name,
                email: userData.email,
                avatar_url: userData.picture,
                verified: userData.verified_email
            };
        } catch (error) {
            console.error('[GOOGLE] 获取用户信息失败:', error);
            throw error;
        }
    }
}

// 微信OAuth
class WeChatOAuth {
    getAuthorizationUrl(state) {
        const params = new URLSearchParams({
            appid: config.oauth.wechat.appId,
            redirect_uri: config.oauth.wechat.redirectUri,
            response_type: 'code',
            scope: config.oauth.wechat.scope,
            state: state
        });
        
        return `https://open.weixin.qq.com/connect/qrconnect?${params.toString()}#wechat_redirect`;
    }

    async getAccessToken(code) {
        try {
            const response = await axios.get('https://api.weixin.qq.com/sns/oauth2/access_token', {
                params: {
                    appid: config.oauth.wechat.appId,
                    secret: config.oauth.wechat.appSecret,
                    code: code,
                    grant_type: 'authorization_code'
                }
            });
            
            const tokenData = response.data;
            if (tokenData.errcode) {
                throw new Error(tokenData.errmsg || `错误代码: ${tokenData.errcode}`);
            }
            
            return {
                access_token: tokenData.access_token,
                refresh_token: tokenData.refresh_token,
                expires_in: tokenData.expires_in,
                openid: tokenData.openid,
                scope: tokenData.scope,
                expires_at: new Date(Date.now() + tokenData.expires_in * 1000)
            };
        } catch (error) {
            console.error('[WECHAT] 获取访问令牌失败:', error);
            throw error;
        }
    }

    async getUserInfo(accessToken) {
        try {
            // 首先获取用户信息
            const response = await axios.get('https://api.weixin.qq.com/sns/userinfo', {
                params: {
                    access_token: accessToken,
                    openid: accessToken.openid
                }
            });
            
            const userData = response.data;
            if (userData.errcode) {
                throw new Error(userData.errmsg || `错误代码: ${userData.errcode}`);
            }
            
            return {
                id: userData.openid,
                username: userData.nickname,
                name: userData.nickname,
                avatar_url: userData.headimgurl,
                gender: userData.sex,
                province: userData.province,
                city: userData.city,
                country: userData.country
            };
        } catch (error) {
            console.error('[WECHAT] 获取用户信息失败:', error);
            throw error;
        }
    }
}

// QQ OAuth
class QQOAuth {
    getAuthorizationUrl(state) {
        const params = new URLSearchParams({
            response_type: 'code',
            client_id: config.oauth.qq.appId,
            redirect_uri: config.oauth.qq.redirectUri,
            scope: config.oauth.qq.scope,
            state: state
        });
        
        return `https://graph.qq.com/oauth2.0/authorize?${params.toString()}`;
    }

    async getAccessToken(code) {
        try {
            const response = await axios.get('https://graph.qq.com/oauth2.0/token', {
                params: {
                    grant_type: 'authorization_code',
                    client_id: config.oauth.qq.appId,
                    client_secret: config.oauth.qq.appKey,
                    code: code,
                    redirect_uri: config.oauth.qq.redirectUri
                }
            });
            
            // QQ返回的是query string格式，需要解析
            const tokenData = this.parseQueryString(response.data);
            
            return {
                access_token: tokenData.access_token,
                expires_in: tokenData.expires_in,
                refresh_token: tokenData.refresh_token,
                expires_at: new Date(Date.now() + tokenData.expires_in * 1000)
            };
        } catch (error) {
            console.error('[QQ] 获取访问令牌失败:', error);
            throw error;
        }
    }

    async getUserInfo(accessToken) {
        try {
            // 首先获取OpenID
            const openidResponse = await axios.get('https://graph.qq.com/oauth2.0/me', {
                params: {
                    access_token: accessToken.access_token
                }
            });
            
            const openidData = JSON.parse(openidResponse.data.substring(openidResponse.data.indexOf('(') + 1, openidResponse.data.lastIndexOf(')')));
            
            // 然后获取用户信息
            const userResponse = await axios.get('https://graph.qq.com/user/get_user_info', {
                params: {
                    access_token: accessToken.access_token,
                    oauth_consumer_key: config.oauth.qq.appId,
                    openid: openidData.openid
                }
            });
            
            const userData = userResponse.data;
            
            return {
                id: openidData.openid,
                username: userData.nickname,
                name: userData.nickname,
                avatar_url: userData.figureurl_qq_2 || userData.figureurl_qq_1,
                gender: userData.gender,
                province: userData.province,
                city: userData.city,
                year: userData.year
            };
        } catch (error) {
            console.error('[QQ] 获取用户信息失败:', error);
            throw error;
        }
    }

    parseQueryString(queryString) {
        const params = new URLSearchParams(queryString);
        const result = {};
        for (const [key, value] of params) {
            result[key] = value;
        }
        return result;
    }
}

// 支付宝OAuth
class AlipayOAuth {
    getAuthorizationUrl(state) {
        const params = {
            app_id: config.oauth.alipay.appId,
            redirect_uri: config.oauth.alipay.redirectUri,
            response_type: 'code',
            scope: config.oauth.alipay.scope,
            state: state
        };
        
        // 生成签名
        const sign = this.generateSign(params);
        params.sign = sign;
        params.sign_type = 'RSA2';
        
        return `https://openauth.alipay.com/oauth2/publicAppAuthorize.htm?${new URLSearchParams(params).toString()}`;
    }

    async getAccessToken(code) {
        try {
            const params = {
                grant_type: 'authorization_code',
                code: code
            };
            
            const sign = this.generateSign(params);
            params.sign = sign;
            params.sign_type = 'RSA2';
            
            const response = await axios.post('https://openapi.alipay.com/gateway.do', params);
            
            const tokenData = response.data;
            if (tokenData.error_response) {
                throw new Error(tokenData.error_response.msg || tokenData.error_response.sub_msg);
            }
            
            return {
                access_token: tokenData.alipay_system_oauth_token_response.access_token,
                refresh_token: tokenData.alipay_system_oauth_token_response.refresh_token,
                expires_in: tokenData.alipay_system_oauth_token_response.expires_in,
                user_id: tokenData.alipay_system_oauth_token_response.user_id,
                expires_at: new Date(Date.now() + tokenData.alipay_system_oauth_token_response.expires_in * 1000)
            };
        } catch (error) {
            console.error('[ALIPAY] 获取访问令牌失败:', error);
            throw error;
        }
    }

    async getUserInfo(accessToken) {
        try {
            const params = {
                auth_token: accessToken.access_token
            };
            
            const sign = this.generateSign(params);
            params.sign = sign;
            params.sign_type = 'RSA2';
            
            const response = await axios.post('https://openapi.alipay.com/gateway.do', params);
            
            const userData = response.data;
            if (userData.error_response) {
                throw new Error(userData.error_response.msg || userData.error_response.sub_msg);
            }
            
            return {
                id: userData.alipay_user_info_share_response.user_id,
                username: userData.alipay_user_info_share_response.nick_name,
                name: userData.alipay_user_info_share_response.nick_name,
                avatar_url: userData.alipay_user_info_share_response.avatar,
                gender: userData.alipay_user_info_share_response.gender,
                province: userData.alipay_user_info_share_response.province,
                city: userData.alipay_user_info_share_response.city
            };
        } catch (error) {
            console.error('[ALIPAY] 获取用户信息失败:', error);
            throw error;
        }
    }

    generateSign(params) {
        // 这里应该实现RSA2签名算法，为了简化，返回一个模拟签名
        // 实际项目中需要使用支付宝提供的SDK
        return 'mock_signature_' + Date.now();
    }
}

module.exports = new OAuthService();