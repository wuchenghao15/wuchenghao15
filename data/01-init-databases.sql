-- 创建MyData数据库
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'MyData')
BEGIN
    CREATE DATABASE MyData;
    PRINT 'Created database: MyData';
END;
GO

-- 创建MyCode数据库
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'MyCode')
BEGIN
    CREATE DATABASE MyCode;
    PRINT 'Created database: MyCode';
END;
GO

-- 使用MyData数据库
USE MyData;
GO

-- 创建用户表
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
BEGIN
    CREATE TABLE users (
        id INT IDENTITY(1,1) PRIMARY KEY,
        username NVARCHAR(50) NOT NULL UNIQUE,
        password_hash NVARCHAR(100) NOT NULL,
        role NVARCHAR(20) DEFAULT 'user',
        displayName NVARCHAR(100),
        email NVARCHAR(100),
        phone NVARCHAR(20),
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE()
    );
    PRINT 'Created table: users';
    
    -- 插入默认管理员用户
    INSERT INTO users (username, password_hash, role, displayName)
    VALUES ('admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'admin', '系统管理员');
    PRINT 'Inserted default admin user';
END;
GO

-- 使用MyCode数据库
USE MyCode;
GO

-- 创建验证码表
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='captchas' AND xtype='U')
BEGIN
    CREATE TABLE captchas (
        id INT IDENTITY(1,1) PRIMARY KEY,
        code NVARCHAR(6) NOT NULL,
        verify_id NVARCHAR(100) NOT NULL UNIQUE,
        created_at DATETIME DEFAULT GETDATE(),
        expires_at DATETIME NOT NULL,
        is_used BIT DEFAULT 0
    );
    PRINT 'Created table: captchas';
    
    -- 创建过期索引
    CREATE INDEX IX_captchas_expires_at ON captchas(expires_at);
    PRINT 'Created index on captchas.expires_at';
END;
GO

-- 设置数据库属性
USE MyData;
GO
ALTER DATABASE MyData SET RECOVERY SIMPLE;
GO

USE MyCode;
GO
ALTER DATABASE MyCode SET RECOVERY SIMPLE;
GO

PRINT 'Database initialization completed successfully!';