-- 修改user_japanese_levels表结构，允许level和highest_level字段为NULL
ALTER TABLE user_japanese_levels 
    ALTER COLUMN level DROP NOT NULL,
    ALTER COLUMN level DROP DEFAULT,
    ALTER COLUMN highest_level DROP NOT NULL,
    ALTER COLUMN highest_level DROP DEFAULT;