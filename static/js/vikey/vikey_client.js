/**
 * MTSCOS Vikey USBKey 前端二次开发 SDK (v2.0.0)
 * ==================================================
 * 调用：
 *   <script src="/static/js/vikey/vikey_client.js"></script>
 *   const vk = new VikeyClient({ baseUrl: '/api/vikey' });
 *   await vk.detect();
 *   const tok = await vk.login(serial, pin);
 *   const sig = await vk.sign(tok.session_token, 'SM2_SIG_01', data_b64);
 *
 * 本 SDK 对接后端 /api/vikey Blueprint。
 * 浏览器端如果需要直接操作真实 USBKey，可扩展注入 navigator.smartcard / 浏览器插件 / 本地桥接。
 * 当前版本优先走"后端驱动"模式——浏览器把 PIN（通过 HTTPS）传到服务端，由服务端与硬件交互。
 */
(function (global, factory) {
    if (typeof module === 'object' && typeof module.exports === 'object') {
        module.exports = factory();
    } else {
        global.VikeyClient = factory();
    }
})(typeof window !== 'undefined' ? window : this, function () {
    'use strict';

    const _VERSION = '2.0.0';

    function _b64url_encode(bytesOrStr) {
        let bin;
        if (typeof bytesOrStr === 'string') {
            bin = new TextEncoder().encode(bytesOrStr);
        } else if (bytesOrStr instanceof Uint8Array) {
            bin = bytesOrStr;
        } else {
            throw new Error('b64url_encode: need string or Uint8Array');
        }
        let b64 = btoa(String.fromCharCode.apply(null, Array.from(bin)));
        return b64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }

    function _b64url_decode(s) {
        const pad = '='.repeat((4 - (s.length % 4)) % 4);
        const b64 = (s + pad).replace(/-/g, '+').replace(/_/g, '/');
        const bin = atob(b64);
        const out = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
        return out;
    }

    function _getCookie(name) {
        const m = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        return m ? decodeURIComponent(m[2]) : '';
    }

    class VikeyClient {
        constructor(opts) {
            opts = opts || {};
            this.baseUrl = (opts.baseUrl || '/api/vikey').replace(/\/+$/, '');
            this.timeoutMs = opts.timeoutMs || 30000;
            this._token = opts.sessionToken || '';
            this._onTokenChange = opts.onTokenChange || null;
        }

        get version() { return _VERSION; }
        get token() { return this._token; }
        setToken(t) {
            this._token = t || '';
            if (typeof this._onTokenChange === 'function') {
                try { this._onTokenChange(this._token); } catch (e) {}
            }
        }

        // ---------- low level http ----------
        async _request(method, path, data, opts) {
            opts = opts || {};
            const url = this.baseUrl + path;
            const headers = {
                'Accept': 'application/json',
            };
            if (this._token) {
                headers['X-Vikey-Token'] = this._token;
            }
            let body = null;
            if (method === 'GET' || method === 'HEAD') {
                const qs = data ? ('?' + Object.keys(data).map(k => encodeURIComponent(k) + '=' + encodeURIComponent(data[k] || '')).join('&')) : '';
                const finalUrl = qs ? (url + qs) : url;
                return this._doFetch(finalUrl, { method, headers, credentials: 'include' }, opts);
            }
            if (data instanceof FormData) {
                body = data;
            } else if (data !== undefined && data !== null) {
                headers['Content-Type'] = 'application/json';
                body = JSON.stringify(data);
            }
            return this._doFetch(url, { method, headers, body, credentials: 'include' }, opts);
        }

        async _doFetch(url, init, opts) {
            const ctrl = new AbortController();
            const tm = setTimeout(() => ctrl.abort(), this.timeoutMs);
            let resp;
            try {
                init.signal = ctrl.signal;
                resp = await fetch(url, init);
            } finally {
                clearTimeout(tm);
            }
            let payload;
            const ct = (resp.headers.get('Content-Type') || '').toLowerCase();
            if (ct.indexOf('application/json') >= 0) {
                payload = await resp.json();
            } else {
                try { payload = await resp.json(); }
                catch (e) { payload = { success: resp.ok, raw: await resp.text() }; }
            }
            if (!resp.ok || (payload && payload.success === false)) {
                const err = new Error((payload && payload.message) || ('HTTP ' + resp.status));
                err.status = resp.status;
                err.payload = payload;
                throw err;
            }
            return payload;
        }

        // ---------- meta ----------
        async versionInfo() { return this._request('GET', '/version'); }

        async detect() { return this._request('GET', '/detect'); }

        async challenge() { return this._request('GET', '/challenge'); }

        // ---------- session ----------
        async login(serial, pin, userType) {
            const res = await this._request('POST', '/login', {
                serial: serial,
                pin: pin,
                user_type: userType || 'user'
            });
            if (res && res.data && res.data.session_token) {
                this.setToken(res.data.session_token);
            }
            return res;
        }

        async sessionStatus(token) {
            const t = token || this._token;
            return this._request('GET', '/session', { token: t });
        }

        async logout(token) {
            const t = token || this._token;
            const res = await this._request('POST', '/logout', { token: t });
            if (t && t === this._token) this.setToken('');
            return res;
        }

        // ---------- crypto ----------
        async sign(params) {
            const p = params || {};
            const tok = p.token || this._token;
            const body = {
                token: tok,
                key_id: p.key_id || 'SM2_SIG_01',
                data_b64: p.data_b64 || (p.data ? _b64url_encode(p.data) : ''),
                hash_algo: p.hash_algo || 'SM3'
            };
            if (!body.token) throw new Error('请先调用 login() 获取会话 token');
            if (!body.data_b64) throw new Error('缺少签名原文 data / data_b64');
            return this._request('POST', '/sign', body);
        }

        async verify(params) {
            const p = params || {};
            const body = {
                token: p.token || this._token,
                key_id: p.key_id || 'SM2_SIG_01',
                data_b64: p.data_b64 || (p.data ? _b64url_encode(p.data) : ''),
                signature_b64: p.signature_b64 || p.signature || '',
                hash_algo: p.hash_algo || 'SM3'
            };
            if (!body.data_b64 || !body.signature_b64) throw new Error('缺少原文/签名');
            return this._request('POST', '/verify', body);
        }

        async encrypt(params) {
            const p = params || {};
            const body = {
                token: p.token || this._token,
                key_id: p.key_id || 'SM4_SES_01',
                plaintext_b64: p.plaintext_b64 || (p.plaintext ? _b64url_encode(p.plaintext) : '')
            };
            if (!body.token) throw new Error('请先登录');
            return this._request('POST', '/encrypt', body);
        }

        async decrypt(params) {
            const p = params || {};
            const body = {
                token: p.token || this._token,
                key_id: p.key_id || 'SM4_SES_01',
                nonce_b64: p.nonce_b64 || '',
                ciphertext_b64: p.ciphertext_b64 || ''
            };
            if (!body.token) throw new Error('请先登录');
            return this._request('POST', '/decrypt', body);
        }

        async hmac(params) {
            const p = params || {};
            const body = {
                token: p.token || this._token,
                key_id: p.key_id || 'HMAC_KEY_01',
                data_b64: p.data_b64 || (p.data ? _b64url_encode(p.data) : ''),
                hash_algo: p.hash_algo || 'SHA256'
            };
            return this._request('POST', '/hmac', body);
        }

        async hash(dataOrB64, algo) {
            const data_b64 = (typeof dataOrB64 === 'string' && dataOrB64.match(/^[A-Za-z0-9_\-]+$/))
                ? dataOrB64
                : _b64url_encode(dataOrB64);
            return this._request('POST', '/hash', { data_b64, algo: algo || 'SM3' });
        }

        async random(length, serial) {
            return this._request('GET', '/random', { length: length || 32, serial: serial || '' });
        }

        // ---------- keys / certs ----------
        async listKeys(serial) {
            if (!serial) throw new Error('缺少 serial');
            return this._request('GET', '/keys', { serial });
        }

        async listCerts(serial) {
            if (!serial) throw new Error('缺少 serial');
            return this._request('GET', '/certs', { serial });
        }

        async exportCert(serial, certId) {
            return this._request('POST', '/certs/export', {
                serial: serial,
                cert_id: certId || 'CERT_01'
            });
        }

        // ---------- bindings (admin) ----------
        async listBindings() { return this._request('GET', '/bindings'); }

        async getBinding(serial) { return this._request('GET', '/bindings/' + encodeURIComponent(serial)); }

        async upsertBinding(binding) {
            const b = binding || {};
            if (!b.serial) throw new Error('缺少 serial');
            return this._request('POST', '/bindings', b);
        }

        async unbind(serial) {
            return this._request('POST', '/bindings/' + encodeURIComponent(serial) + '/unbind', {});
        }

        // ---------- hardware verify (mechanism_ai integration) ----------
        async verifyHardware(info) {
            const i = info || {};
            return this._request('POST', '/verify_hardware', {
                hardwareId: i.hardwareId || i.serial || '',
                session_token: i.session_token || this._token,
                signature: i.signature || '',
                challenge: i.challenge || ''
            });
        }

        // ---------- audit (admin) ----------
        async logs(opts) {
            opts = opts || {};
            return this._request('GET', '/logs', {
                limit: opts.limit || 100,
                serial: opts.serial || '',
                operation: opts.operation || ''
            });
        }

        async stats() { return this._request('GET', '/stats'); }

        // ---------- utils ----------
        static b64urlEncode(s) { return _b64url_encode(s); }
        static b64urlDecode(s) { return _b64url_decode(s); }
    }

    VikeyClient.VERSION = _VERSION;
    return VikeyClient;
});
