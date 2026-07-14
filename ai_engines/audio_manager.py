#!/usr/bin/env python3
"""
音频管理器 - 使用AI技术生成真实语音音频
支持多种语言和发音类型
"""
import os
import random
import hashlib
from datetime import datetime
from app.utils.logging import logger

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False
    logger.warning("gTTS库未安装,将使用浏览器内置语音合成")

class AudioManager:
    """音频管理器"""
    
    def __init__(self):
        self.audio_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'static', 'audio')
        os.makedirs(self.audio_cache_dir, exist_ok=True)
        
        self.language_map = {
            '日语': 'ja',
            '英语': 'en',
            '中文': 'zh',
            'japanese': 'ja',
            'english': 'en',
            'chinese': 'zh'
        }
        
        self.voice_types = {
            '日语': {
                'kansai': {'name': '关西腔', 'lang': 'ja', 'region': 'JP'},
                'kanto': {'name': '关东腔', 'lang': 'ja', 'region': 'JP'},
                'standard': {'name': '标准日语', 'lang': 'ja', 'region': 'JP'}
            },
            '英语': {
                'american': {'name': '美式发音', 'lang': 'en', 'region': 'US'},
                'british': {'name': '英式发音', 'lang': 'en', 'region': 'GB'},
                'australian': {'name': '澳式发音', 'lang': 'en', 'region': 'AU'},
                'standard': {'name': '标准英语', 'lang': 'en', 'region': 'US'}
            },
            '中文': {
                'mandarin': {'name': '普通话', 'lang': 'zh', 'region': 'CN'},
                'cantonese': {'name': '粤语', 'lang': 'zh', 'region': 'HK'},
                'standard': {'name': '标准中文', 'lang': 'zh', 'region': 'CN'}
            }
        }
        
        logger.info("音频管理器初始化成功")
    
    def generate_audio_url(self, text: str, language: str = '中文', voice_type: str = 'standard') -> str:
        """生成音频URL"""
        try:
            audio_filename = self._generate_audio_file(text, language, voice_type)
            if audio_filename:
                return f'/static/audio/{audio_filename}'
            else:
                return None
        except Exception as e:
            logger.error(f"生成音频失败: {str(e)}")
            return None
    
    def _generate_audio_file(self, text: str, language: str, voice_type: str) -> str:
        """生成音频文件"""
        try:
            lang_code = self.language_map.get(language, 'zh')
            
            hash_content = f"{text}_{language}_{voice_type}"
            file_hash = hashlib.md5(hash_content.encode('utf-8')).hexdigest()
            filename = f"audio_{file_hash}.mp3"
            filepath = os.path.join(self.audio_cache_dir, filename)
            
            if os.path.exists(filepath):
                return filename
            
            if HAS_GTTS:
                tts = gTTS(text=text, lang=lang_code, slow=False)
                tts.save(filepath)
                logger.debug(f"生成音频文件: {filename}")
                return filename
            else:
                logger.warning("gTTS未安装,跳过音频文件生成")
                return None
                
        except Exception as e:
            logger.error(f"生成音频文件失败: {str(e)}")
            return None
    
    def get_voice_options(self, language: str) -> list:
        """获取可用的语音选项"""
        return self.voice_types.get(language, {}).keys()
    
    def get_supported_languages(self) -> list:
        """获取支持的语言列表"""
        return list(self.language_map.keys())
    
    def text_to_speech(self, text: str, language: str = '中文') -> dict:
        """文本转语音"""
        audio_url = self.generate_audio_url(text, language)
        
        return {
            'success': audio_url is not None,
            'audio_url': audio_url,
            'text': text,
            'language': language,
            'timestamp': datetime.now().isoformat()
        }

audio_manager = AudioManager()
