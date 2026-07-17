#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日语听力音频生成专家AI
专门负责日语听力题目的音频文件生成，支持多角色对话、多种口音、语速调节
"""

import logging
import json
import uuid
import os
import sys
import time
import random
import threading
import asyncio
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False

logger = logging.getLogger(__name__)


class JapaneseListeningAudioAI:
    """日语听力音频生成专家AI"""

    JAPANESE_VOICES = {
        'kanto': {
            'female': 'ja-JP-NanamiNeural',
            'male': 'ja-JP-KeitaNeural',
            'name': '关东腔'
        },
        'kansai': {
            'female': 'ja-JP-NanamiNeural',
            'male': 'ja-JP-KeitaNeural',
            'name': '关西腔'
        },
        'standard': {
            'female': 'ja-JP-NanamiNeural',
            'male': 'ja-JP-KeitaNeural',
            'name': '标准日语'
        }
    }

    SPEED_MAPPING = {
        'N5': '-50%',
        'N4': '-30%',
        'N3': '-15%',
        'N2': '0%',
        'N1': '15%',
        'slow': '-50%',
        'normal': '0%',
        'fast': '15%'
    }

    ROLE_MAPPING = {
        'A': {'name': '人物A', 'gender': 'female'},
        'B': {'name': '人物B', 'gender': 'male'},
        'C': {'name': '人物C', 'gender': 'female'},
        'D': {'name': '人物D', 'gender': 'male'},
        '旁白': {'name': '旁白', 'gender': 'female'},
        '男子': {'name': '男子', 'gender': 'male'},
        '女子': {'name': '女子', 'gender': 'female'}
    }

    def __init__(self, employee_id: str = None, name: str = "日语听力音频AI"):
        self.employee_id = employee_id or f"jla_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.type = "japanese_listening_audio"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.performance_score = 85

        self.skills = [
            {"name": "japanese_tts", "level": 6, "experience": 0.0},
            {"name": "dialogue_synthesis", "level": 6, "experience": 0.0},
            {"name": "multi_role_audio", "level": 5, "experience": 0.0},
            {"name": "accent_control", "level": 4, "experience": 0.0},
            {"name": "speed_control", "level": 5, "experience": 0.0},
            {"name": "audio_post_processing", "level": 4, "experience": 0.0},
            {"name": "batch_audio_generation", "level": 5, "experience": 0.0}
        ]

        self._lock = threading.RLock()
        
        self.audio_base_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app', 'static', 'audio', 'japanese'
        )
        os.makedirs(self.audio_base_dir, exist_ok=True)

        self._init_audio_directories()

        logger.info(f"[日语听力音频AI] 创建: {self.name} ({self.employee_id})")

    def _init_audio_directories(self):
        """初始化音频目录结构"""
        for accent in self.JAPANESE_VOICES.keys():
            for gender in ['female', 'male']:
                dir_path = os.path.join(self.audio_base_dir, accent, gender)
                os.makedirs(dir_path, exist_ok=True)

    def get_status(self) -> Dict[str, Any]:
        """获取AI状态"""
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / max(self.task_count, 1) * 100,
            "performance_score": self.performance_score,
            "skills": self.skills,
            "has_edge_tts": HAS_EDGE_TTS,
            "has_pydub": HAS_PYDUB,
            "supported_accents": list(self.JAPANESE_VOICES.keys()),
            "supported_speeds": list(self.SPEED_MAPPING.keys())
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        self.task_count += 1
        start_time = time.time()

        try:
            task_type = task_data.get("task_type", "generate_audio")

            if task_type == "generate_audio":
                result = self.generate_audio_for_question(task_data)
            elif task_type == "generate_dialogue_audio":
                result = self._generate_dialogue_audio(task_data)
            elif task_type == "generate_batch_audio":
                result = self._generate_batch_audio(task_data)
            elif task_type == "generate_audio_for_transcript":
                result = self._generate_audio_for_transcript(task_data)
            elif task_type == "get_available_voices":
                result = self._get_available_voices()
            elif task_type == "get_status":
                result = {"success": True, "data": self.get_status()}
            else:
                result = {"success": False, "error": f"未知任务类型: {task_type}"}

            if result.get("success", False):
                self.success_count += 1
                self._update_performance(True, time.time() - start_time)
            else:
                self.failure_count += 1
                self._update_performance(False, time.time() - start_time)

            result["execution_time"] = time.time() - start_time
            result["employee_id"] = self.employee_id
            result["employee_name"] = self.name

            return result

        except Exception as e:
            self.failure_count += 1
            self._update_performance(False, time.time() - start_time)
            logger.error(f"[日语听力音频AI] 任务执行失败: {self.name}, 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "employee_id": self.employee_id,
                "employee_name": self.name
            }

    def generate_audio_for_question(self, task_data: Dict) -> Dict:
        """为题目生成音频"""
        question_id = task_data.get("question_id")
        transcript = task_data.get("transcript")
        language = task_data.get("language", "japanese")
        accent = task_data.get("accent", "kanto")
        voice = task_data.get("voice", "female")
        speed = task_data.get("speed", "N3")
        question_content = task_data.get("content", "")

        if not question_id:
            return {"success": False, "error": "缺少question_id"}

        if not transcript:
            return {"success": False, "error": "缺少transcript"}

        audio_path = self._generate_audio_file(
            text=transcript,
            language=language,
            accent=accent,
            voice=voice,
            speed=speed,
            question_id=question_id
        )

        if audio_path:
            question_audio_path = None
            if question_content:
                question_audio_path = self._generate_audio_file(
                    text=question_content,
                    language=language,
                    accent=accent,
                    voice=voice,
                    speed=speed,
                    question_id=f"{question_id}_question"
                )

            result = {
                "success": True,
                "message": "音频生成成功",
                "question_id": question_id,
                "audio_path": audio_path,
                "question_audio_path": question_audio_path,
                "transcript": transcript,
                "accent": accent,
                "voice": voice,
                "speed": speed
            }

            self._save_audio_metadata(question_id, audio_path, transcript, accent, voice, speed)

            return result
        else:
            return {"success": False, "error": "音频生成失败"}

    def _generate_dialogue_audio(self, task_data: Dict) -> Dict:
        """生成对话体音频"""
        dialogue_text = task_data.get("dialogue_text")
        question_id = task_data.get("question_id")
        accent = task_data.get("accent", "kanto")
        speed = task_data.get("speed", "N3")
        speakers_config = task_data.get("speakers", {})

        if not dialogue_text:
            return {"success": False, "error": "缺少dialogue_text"}

        segments = self._parse_dialogue(dialogue_text)
        
        if not segments:
            return {"success": False, "error": "无法解析对话文本"}

        audio_files = []
        
        for i, segment in enumerate(segments):
            speaker = segment["speaker"]
            text = segment["text"].strip()
            
            if not text:
                continue

            speaker_info = speakers_config.get(speaker, {})
            gender = speaker_info.get("gender", self.ROLE_MAPPING.get(speaker, {}).get("gender", "female"))
            
            segment_id = f"{question_id}_seg_{i}" if question_id else f"dialogue_seg_{i}"
            
            audio_path = self._generate_audio_file(
                text=text,
                language="japanese",
                accent=accent,
                voice=gender,
                speed=speed,
                question_id=segment_id
            )

            if audio_path:
                audio_files.append({
                    "speaker": speaker,
                    "text": text,
                    "gender": gender,
                    "audio_path": audio_path
                })
            else:
                logger.warning(f"对话片段{i}音频生成失败: {text}")

        if len(audio_files) == 0:
            return {"success": False, "error": "所有对话片段音频生成失败"}

        combined_path = None
        if len(audio_files) > 1 and HAS_PYDUB:
            combined_path = self._combine_audio_files(audio_files, question_id, accent, speed)

        return {
            "success": True,
            "message": f"成功生成 {len(audio_files)} 个对话片段音频",
            "segments": segments,
            "audio_files": audio_files,
            "combined_audio_path": combined_path,
            "accent": accent,
            "speed": speed
        }

    def _generate_audio_for_transcript(self, task_data: Dict) -> Dict:
        """为纯文本转写生成音频"""
        transcript = task_data.get("transcript")
        language = task_data.get("language", "japanese")
        accent = task_data.get("accent", "kanto")
        voice = task_data.get("voice", "female")
        speed = task_data.get("speed", "normal")
        text_id = task_data.get("text_id")

        if not transcript:
            return {"success": False, "error": "缺少transcript"}

        audio_path = self._generate_audio_file(
            text=transcript,
            language=language,
            accent=accent,
            voice=voice,
            speed=speed,
            question_id=text_id
        )

        if audio_path:
            return {
                "success": True,
                "message": "音频生成成功",
                "audio_path": audio_path,
                "transcript": transcript,
                "accent": accent,
                "voice": voice,
                "speed": speed
            }
        else:
            return {"success": False, "error": "音频生成失败"}

    def _generate_batch_audio(self, task_data: Dict) -> Dict:
        """批量生成音频"""
        items = task_data.get("items", [])
        accent = task_data.get("accent", "kanto")
        voice = task_data.get("voice", "female")
        speed = task_data.get("speed", "N3")

        results = []
        success_count = 0
        failure_count = 0

        for item in items:
            try:
                audio_path = self._generate_audio_file(
                    text=item.get("text", ""),
                    language=item.get("language", "japanese"),
                    accent=accent,
                    voice=voice,
                    speed=speed,
                    question_id=item.get("id")
                )

                if audio_path:
                    results.append({
                        "id": item.get("id"),
                        "success": True,
                        "audio_path": audio_path
                    })
                    success_count += 1
                else:
                    results.append({
                        "id": item.get("id"),
                        "success": False,
                        "error": "音频生成失败"
                    })
                    failure_count += 1
            except Exception as e:
                results.append({
                    "id": item.get("id"),
                    "success": False,
                    "error": str(e)
                })
                failure_count += 1

        return {
            "success": success_count > 0,
            "message": f"批量生成完成: 成功{success_count}个, 失败{failure_count}个",
            "success_count": success_count,
            "failure_count": failure_count,
            "results": results
        }

    def _generate_audio_file(self, text: str, language: str, accent: str, 
                            voice: str, speed: str, question_id: str = None) -> Optional[str]:
        """生成单个音频文件"""
        if not HAS_EDGE_TTS:
            logger.warning("edge-tts未安装,无法生成音频")
            return None

        try:
            voice_name = self.JAPANESE_VOICES.get(accent, {}).get(voice, 'ja-JP-NanamiNeural')
            rate = self.SPEED_MAPPING.get(speed, '0%')

            hash_content = f"{text}_{accent}_{voice}_{speed}"
            file_hash = hashlib.md5(hash_content.encode('utf-8')).hexdigest()[:12]
            
            filename = f"{question_id}_{file_hash}.mp3" if question_id else f"audio_{file_hash}.mp3"
            filepath = os.path.join(self.audio_base_dir, accent, voice, filename)

            if os.path.exists(filepath):
                return f"/static/audio/japanese/{accent}/{voice}/{filename}"

            async def generate():
                communicate = edge_tts.Communicate(text, voice_name, rate=rate)
                await communicate.save(filepath)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(generate())
            loop.close()

            logger.info(f"[日语听力音频AI] 生成音频: {filename}")
            return f"/static/audio/japanese/{accent}/{voice}/{filename}"

        except Exception as e:
            logger.error(f"[日语听力音频AI] 生成音频失败: {e}")
            return None

    def _combine_audio_files(self, audio_files: List[Dict], question_id: str, 
                             accent: str, speed: str) -> Optional[str]:
        """拼接多个音频文件"""
        if not HAS_PYDUB:
            logger.warning("pydub未安装,无法拼接音频")
            return None

        try:
            combined = AudioSegment.empty()
            
            for i, af in enumerate(audio_files):
                full_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'app', af['audio_path'].lstrip('/')
                )
                
                if os.path.exists(full_path):
                    segment = AudioSegment.from_mp3(full_path)
                    combined += segment
                    
                    if i < len(audio_files) - 1:
                        silence = AudioSegment.silent(duration=500)
                        combined += silence

            hash_content = f"{question_id}_{accent}_{speed}_combined"
            file_hash = hashlib.md5(hash_content.encode('utf-8')).hexdigest()[:12]
            filename = f"{question_id}_combined_{file_hash}.mp3"
            filepath = os.path.join(self.audio_base_dir, accent, audio_files[0]['gender'], filename)

            combined.export(filepath, format='mp3')

            return f"/static/audio/japanese/{accent}/{audio_files[0]['gender']}/{filename}"

        except Exception as e:
            logger.error(f"[日语听力音频AI] 音频拼接失败: {e}")
            return None

    def _parse_dialogue(self, dialogue_text: str) -> List[Dict]:
        """解析对话文本"""
        import re

        segments = []
        
        lines = dialogue_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            speaker_match = re.match(r'^([Ａ-ＺA-Za-z]|[\u4e00-\u9fa5])\s*[：:]\s*(.+)$', line)
            if speaker_match:
                speaker = speaker_match.group(1).strip()
                text = speaker_match.group(2).strip()
                if text:
                    segments.append({"speaker": speaker, "text": text})
            else:
                speaker_match2 = re.match(r'^(.+?)\s*[：:]\s*(.+)$', line)
                if speaker_match2:
                    speaker = speaker_match2.group(1).strip()
                    text = speaker_match2.group(2).strip()
                    if text and len(speaker) <= 5:
                        segments.append({"speaker": speaker, "text": text})

        if len(segments) == 0:
            segments.append({"speaker": "旁白", "text": dialogue_text.strip()})

        return segments

    def _save_audio_metadata(self, question_id: str, audio_path: str, transcript: str,
                             accent: str, voice: str, speed: str):
        """保存音频元数据"""
        try:
            from app.services.audio_manager import get_audio_manager
            audio_manager = get_audio_manager()
            
            duration = 0
            if HAS_PYDUB:
                full_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'app', audio_path.lstrip('/')
                )
                if os.path.exists(full_path):
                    audio = AudioSegment.from_mp3(full_path)
                    duration = len(audio) / 1000

            audio_manager.add_audio_for_question(
                question_id=question_id,
                language="japanese",
                accent=accent,
                voice=voice,
                file_path=audio_path,
                transcript=transcript,
                duration=duration
            )
        except Exception as e:
            logger.warning(f"保存音频元数据失败: {e}")

    def _get_available_voices(self) -> Dict:
        """获取可用语音选项"""
        return {
            "success": True,
            "voices": self.JAPANESE_VOICES,
            "speeds": self.SPEED_MAPPING,
            "roles": self.ROLE_MAPPING
        }

    def _update_performance(self, success: bool, duration: float):
        """更新绩效"""
        if success:
            self.performance_score = min(100, self.performance_score + 0.5)
            for skill in self.skills:
                skill["experience"] += 0.1
        else:
            self.performance_score = max(60, self.performance_score - 0.3)


def create_japanese_listening_audio_ai(employee_id: str = None,
                                        name: str = "日语听力音频AI") -> JapaneseListeningAudioAI:
    """创建日语听力音频AI"""
    if not employee_id:
        employee_id = f"jla_{uuid.uuid4().hex[:8]}"
    return JapaneseListeningAudioAI(employee_id, name)


_japanese_listening_audio_ai = None


def get_japanese_listening_audio_ai() -> JapaneseListeningAudioAI:
    """获取日语听力音频AI单例"""
    global _japanese_listening_audio_ai
    if _japanese_listening_audio_ai is None:
        _japanese_listening_audio_ai = create_japanese_listening_audio_ai()
    return _japanese_listening_audio_ai
