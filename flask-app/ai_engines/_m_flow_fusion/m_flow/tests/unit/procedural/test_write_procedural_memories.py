# m_flow/tests/unit/procedural/test_write_procedural_memories.py
"""
Write Procedural Memories 纯逻辑函数单元测试

测试以下公开函数:
- redact_secrets: 敏感信息脱敏
- contains_dangerous_content: 危险内容检测
"""

from m_flow.memory.procedural.write_procedural_memories import (
    redact_secrets,
    contains_dangerous_content,
)


# =============================================================================
# TestRedactSecrets - 测试 redact_secrets 函数
# =============================================================================


class TestRedactSecrets:
    """测试 redact_secrets 函数"""

    # -------------------------------------------------------------------------
    # API Key 模式
    # -------------------------------------------------------------------------

    def test_api_key_pattern(self):
        """应脱敏 API Key"""
        text = 'api_key="sk-1234923090abcdef1234923090"'
        result = redact_secrets(text)
        assert "sk-1234923090" not in result
        assert "REDACTED" in result

    def test_apikey_no_underscore(self):
        """应脱敏无下划线的 apikey"""
        text = 'apikey="abcdefghijklmnop1234"'
        result = redact_secrets(text)
        assert "abcdefghijklmnop" not in result

    # -------------------------------------------------------------------------
    # Token 模式
    # -------------------------------------------------------------------------

    def test_access_token_pattern(self):
        """应脱敏 access_token"""
        text = "access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = redact_secrets(text)
        assert "eyJhbGciOiJIUzI1" not in result
        assert "REDACTED" in result

    def test_auth_token_pattern(self):
        """应脱敏 auth_token"""
        text = 'auth_token: "token_123492309012349230"'
        result = redact_secrets(text)
        assert "token_123492309" not in result

    # -------------------------------------------------------------------------
    # 密码模式
    # -------------------------------------------------------------------------

    def test_password_pattern(self):
        """应脱敏 password"""
        text = 'password="MySecretPassword123!"'
        result = redact_secrets(text)
        assert "MySecretPassword" not in result
        assert "REDACTED" in result

    def test_passwd_pattern(self):
        """应脱敏 passwd"""
        text = "passwd: SuperSecret"
        result = redact_secrets(text)
        assert "SuperSecret" not in result

    # -------------------------------------------------------------------------
    # AWS 凭证模式
    # -------------------------------------------------------------------------

    def test_aws_access_key_id(self):
        """应脱敏 AWS Access Key ID"""
        text = 'aws_access_key_id="AKIAIOSFODNN7EXAMPLE"'
        result = redact_secrets(text)
        assert "AKIAIOSFODNN7" not in result
        assert "REDACTED" in result

    def test_aws_secret_access_key(self):
        """应脱敏 AWS Secret Access Key"""
        text = 'aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"'
        result = redact_secrets(text)
        assert "wJalrXUtnFEMI" not in result
        assert "REDACTED" in result

    # -------------------------------------------------------------------------
    # 私钥模式
    # -------------------------------------------------------------------------

    def test_private_key_pattern(self):
        """应脱敏私钥"""
        text = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7...
-----END PRIVATE KEY-----"""
        result = redact_secrets(text)
        assert "MIIEvgIBADANBg" not in result
        assert "REDACTED" in result

    def test_rsa_private_key(self):
        """应脱敏 RSA 私钥"""
        text = """-----BEGIN RSA PRIVATE KEY-----
MIIBOgIBAAJBALRmn...
-----END RSA PRIVATE KEY-----"""
        result = redact_secrets(text)
        assert "MIIBOgIBAAJBALRmn" not in result

    # -------------------------------------------------------------------------
    # Bearer Token 模式
    # -------------------------------------------------------------------------

    def test_bearer_token_pattern(self):
        """应脱敏 Bearer Token"""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"
        result = redact_secrets(text)
        assert "eyJhbGciOiJIUzI1" not in result
        assert "REDACTED" in result

    # -------------------------------------------------------------------------
    # 连接字符串模式
    # -------------------------------------------------------------------------

    def test_connection_string_pattern(self):
        """应脱敏连接字符串"""
        text = 'connection_string="Server=myserver;Database=mydb;User=admin;Password=secret"'
        result = redact_secrets(text)
        assert "Password=secret" not in result
        assert "REDACTED" in result

    # -------------------------------------------------------------------------
    # 无敏感信息
    # -------------------------------------------------------------------------

    def test_no_sensitive_info_returns_original(self):
        """无敏感信息时应原样返回"""
        text = "这是一段普通的文本，不包含任何敏感信息。"
        result = redact_secrets(text)
        assert result == text

    def test_empty_string(self):
        """空字符串应原样返回"""
        result = redact_secrets("")
        assert result == ""


# =============================================================================
# TestContainsDangerousContent - 测试 contains_dangerous_content 函数
# =============================================================================


class TestContainsDangerousContent:
    """测试 contains_dangerous_content 函数"""

    # -------------------------------------------------------------------------
    # 自残内容检测
    # -------------------------------------------------------------------------

    def test_self_harm_content(self):
        """应检测自残内容"""
        assert contains_dangerous_content("how to self-harm") is True

    def test_suicide_content(self):
        """应检测自杀内容"""
        assert contains_dangerous_content("suicide methods") is True

    # -------------------------------------------------------------------------
    # 武器制造检测
    # -------------------------------------------------------------------------

    def test_bomb_making_content(self):
        """应检测炸弹制造内容"""
        assert contains_dangerous_content("how to make a bomb") is True

    def test_explosive_device_content(self):
        """应检测爆炸装置内容"""
        assert contains_dangerous_content("explosive device instructions") is True

    def test_weapon_manufacturing(self):
        """应检测武器制造内容"""
        assert contains_dangerous_content("weapon manufacturing guide") is True

    # -------------------------------------------------------------------------
    # 非法入侵检测
    # -------------------------------------------------------------------------

    def test_hacking_content(self):
        """应检测黑客入侵内容"""
        assert contains_dangerous_content("hack into someone's computer") is True

    def test_unauthorized_access(self):
        """应检测未授权访问内容"""
        assert contains_dangerous_content("unauthorized access to systems") is True

    def test_bypass_security(self):
        """应检测绕过安全内容"""
        assert contains_dangerous_content("bypass security measures") is True

    # -------------------------------------------------------------------------
    # 正常内容
    # -------------------------------------------------------------------------

    def test_normal_text_returns_false(self):
        """正常文本应返回 False"""
        assert contains_dangerous_content("Python programming tutorial") is False

    def test_technical_security_discussion(self):
        """技术安全讨论应返回 False"""
        assert contains_dangerous_content("security best practices for web apps") is False

    def test_empty_string_returns_false(self):
        """空字符串应返回 False"""
        assert contains_dangerous_content("") is False

    def test_chinese_normal_text(self):
        """中文正常文本应返回 False"""
        assert contains_dangerous_content("如何学习编程") is False
