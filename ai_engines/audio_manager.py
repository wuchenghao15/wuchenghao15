#!/usr/bin/env python3
import os
import random
import hashlib
import time
import json
from datetime import datetime
from app.utils.logging import logger

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False
    logger.warning("gTTS库未安装,将使用浏览器内置语音合成")

try:
    import playsound
    HAS_PLAYSOUND = True
except ImportError:
    HAS_PLAYSOUND = False
    logger.warning("playsound库未安装,无法播放音频")

class AudioManager:
    def __init__(self):
        self.audio_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'html', 'assets', 'audio')
        os.makedirs(self.audio_cache_dir, exist_ok=True)
        
        self.language_map = {
            '日语': 'ja',
            '英语': 'en',
            '中文': 'zh',
            '中文(普通话)': 'zh-CN',
            '中文(粤语)': 'zh-HK',
            '中文(台湾)': 'zh-TW',
            '韩语': 'ko',
            '法语': 'fr',
            '德语': 'de',
            '西班牙语': 'es',
            '葡萄牙语': 'pt',
            '意大利语': 'it',
            '俄语': 'ru',
            '阿拉伯语': 'ar',
            '印地语': 'hi',
            'japanese': 'ja',
            'english': 'en',
            'chinese': 'zh',
            'korean': 'ko',
            'french': 'fr',
            'german': 'de',
            'spanish': 'es',
        }
        
        self.voice_types = {
            '日语': {
                'kansai': {'name': '关西腔', 'lang': 'ja', 'region': 'JP'},
                'kanto': {'name': '关东腔', 'lang': 'ja', 'region': 'JP'},
                'standard': {'name': '标准日语', 'lang': 'ja', 'region': 'JP'},
                'female': {'name': '女声', 'lang': 'ja', 'region': 'JP'},
                'male': {'name': '男声', 'lang': 'ja', 'region': 'JP'}
            },
            '英语': {
                'american': {'name': '美式发音', 'lang': 'en', 'region': 'US'},
                'british': {'name': '英式发音', 'lang': 'en', 'region': 'GB'},
                'australian': {'name': '澳式发音', 'lang': 'en', 'region': 'AU'},
                'canadian': {'name': '加拿大发音', 'lang': 'en', 'region': 'CA'},
                'standard': {'name': '标准英语', 'lang': 'en', 'region': 'US'},
                'female': {'name': '女声', 'lang': 'en', 'region': 'US'},
                'male': {'name': '男声', 'lang': 'en', 'region': 'US'}
            },
            '中文': {
                'mandarin': {'name': '普通话', 'lang': 'zh', 'region': 'CN'},
                'cantonese': {'name': '粤语', 'lang': 'zh', 'region': 'HK'},
                'taiwan': {'name': '台湾口音', 'lang': 'zh', 'region': 'TW'},
                'standard': {'name': '标准中文', 'lang': 'zh', 'region': 'CN'},
                'female': {'name': '女声', 'lang': 'zh', 'region': 'CN'},
                'male': {'name': '男声', 'lang': 'zh', 'region': 'CN'}
            },
            '韩语': {
                'standard': {'name': '标准韩语', 'lang': 'ko', 'region': 'KR'},
                'female': {'name': '女声', 'lang': 'ko', 'region': 'KR'},
                'male': {'name': '男声', 'lang': 'ko', 'region': 'KR'}
            },
            '法语': {
                'standard': {'name': '标准法语', 'lang': 'fr', 'region': 'FR'},
                'female': {'name': '女声', 'lang': 'fr', 'region': 'FR'},
                'male': {'name': '男声', 'lang': 'fr', 'region': 'FR'}
            },
            '德语': {
                'standard': {'name': '标准德语', 'lang': 'de', 'region': 'DE'},
                'female': {'name': '女声', 'lang': 'de', 'region': 'DE'},
                'male': {'name': '男声', 'lang': 'de', 'region': 'DE'}
            },
            '西班牙语': {
                'standard': {'name': '标准西班牙语', 'lang': 'es', 'region': 'ES'},
                'mexican': {'name': '墨西哥口音', 'lang': 'es', 'region': 'MX'},
                'female': {'name': '女声', 'lang': 'es', 'region': 'ES'},
                'male': {'name': '男声', 'lang': 'es', 'region': 'ES'}
            }
        }
        
        self.max_retries = 3
        self.retry_delay = 2
        self.cache_enabled = True
        self.max_cache_size = 1000
        self.cleanup_interval = 3600
        
        logger.info("音频管理器初始化成功")
    
    def generate_audio_url(self, text: str, language: str = '中文', voice_type: str = 'standard', 
                          speed: float = 1.0, volume: float = 1.0, pitch: float = 1.0) -> str:
        try:
            audio_filename = self._generate_audio_file(text, language, voice_type, speed, volume, pitch)
            if audio_filename:
                return f'/assets/audio/{audio_filename}'
            else:
                return None
        except Exception as e:
            logger.error(f"生成音频失败: {str(e)}")
            return None
    
    def _generate_audio_file(self, text: str, language: str, voice_type: str, 
                             speed: float, volume: float, pitch: float) -> str:
        try:
            lang_code = self.language_map.get(language, 'zh')
            
            hash_content = f"{text}_{language}_{voice_type}_{speed}_{volume}_{pitch}"
            file_hash = hashlib.md5(hash_content.encode('utf-8')).hexdigest()
            filename = f"audio_{file_hash}.mp3"
            filepath = os.path.join(self.audio_cache_dir, filename)
            
            if self.cache_enabled and os.path.exists(filepath):
                return filename
            
            if HAS_GTTS:
                for attempt in range(self.max_retries):
                    try:
                        tts = gTTS(text=text, lang=lang_code, slow=(speed < 0.8))
                        tts.save(filepath)
                        logger.debug(f"生成音频文件: {filename}")
                        return filename
                    except Exception as e:
                        logger.warning(f"生成音频第{attempt+1}次失败: {str(e)}")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay * (attempt + 1))
                logger.error(f"生成音频失败，已重试{self.max_retries}次")
                return None
            else:
                logger.warning("gTTS未安装,跳过音频文件生成")
                return None
                
        except Exception as e:
            logger.error(f"生成音频文件失败: {str(e)}")
            return None
    
    def get_voice_options(self, language: str) -> list:
        voices = self.voice_types.get(language, {})
        return [{'id': k, 'name': v['name'], 'lang': v['lang'], 'region': v['region']} 
                for k, v in voices.items()]
    
    def get_supported_languages(self) -> list:
        return [{'id': k, 'code': v} for k, v in self.language_map.items()]
    
    def text_to_speech(self, text: str, language: str = '中文', voice_type: str = 'standard',
                       speed: float = 1.0, volume: float = 1.0, pitch: float = 1.0) -> dict:
        audio_url = self.generate_audio_url(text, language, voice_type, speed, volume, pitch)
        
        return {
            'success': audio_url is not None,
            'audio_url': audio_url,
            'text': text,
            'language': language,
            'voice_type': voice_type,
            'speed': speed,
            'volume': volume,
            'pitch': pitch,
            'timestamp': datetime.now().isoformat()
        }
    
    def batch_text_to_speech(self, texts: list, language: str = '中文', voice_type: str = 'standard',
                             speed: float = 1.0, volume: float = 1.0, pitch: float = 1.0) -> list:
        results = []
        for text in texts:
            result = self.text_to_speech(text, language, voice_type, speed, volume, pitch)
            results.append(result)
        return results
    
    def cleanup_cache(self):
        try:
            files = os.listdir(self.audio_cache_dir)
            if len(files) > self.max_cache_size:
                files_with_mtime = [(f, os.path.getmtime(os.path.join(self.audio_cache_dir, f))) 
                                    for f in files if f.startswith('audio_')]
                files_with_mtime.sort(key=lambda x: x[1])
                files_to_delete = files_with_mtime[:len(files) - self.max_cache_size]
                
                for filename, _ in files_to_delete:
                    os.remove(os.path.join(self.audio_cache_dir, filename))
                    logger.debug(f"清理缓存文件: {filename}")
                
                logger.info(f"清理了{len(files_to_delete)}个缓存文件")
        except Exception as e:
            logger.error(f"清理缓存失败: {str(e)}")
    
    def get_cache_stats(self) -> dict:
        try:
            files = [f for f in os.listdir(self.audio_cache_dir) if f.startswith('audio_')]
            total_size = sum(os.path.getsize(os.path.join(self.audio_cache_dir, f)) for f in files)
            
            return {
                'total_files': len(files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'max_cache_size': self.max_cache_size
            }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {str(e)}")
            return {'error': str(e)}

audio_manager = AudioManager()