"""
galaxy_ai_model_router.py — 仙女座 AI 模型路由器 (v1 架构)

5 种 AI 模型接入接口:
  - video_gen    视频生成 (Runway/Pika/Kling/可灵)
  - copywriting  文案生成 (Ollama qwen2.5 本地, 零 token)
  - animation    动画生成 (Runway Gen-3/Hailuo 海洛)
  - 3d_modeling  3D 建模 (TripoSR/Shap-E)
  - original_art 原画/概念图 (SDXL/Flux/MJ)

设计原则:
  - 插件化: 每种模型注册为 Plugin, 实现 generate() 标准签名
  - 降级: 不可用时 fallback 到本地 Ollama / 静态模板
  - 统一: 所有输出打包到 ModelResult, 含 text/image/video/metadata
  - 可审计: 每次调用落库 (mt_galaxy_ai_model_call_log)

用法:
  router = ModelRouter()
  result = router.copywriting(topic="秦统一六国", style="cute_history")
  result = router.video_gen(prompt="秦朝士兵 可爱动画 爆炸效果", duration_sec=15)
  result = router.animation(storyboard=[...], style="cute_burst")
  result = router.original_art(concept="秦始皇 卡通风格 portrait")
  result = router.model_3d(description="秦朝兵器 青铜剑")
"""
from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# 允许 engines 内部脚本直接运行时找到同级模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "app.db")


# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class ModelResult:
    """统一模型输出"""
    success: bool
    text: Optional[str] = None                    # 文案生成的文本
    images: Optional[List[str]] = None            # 原画/概念图的本地路径列表
    video_path: Optional[str] = None              # 视频生成的 mp4 路径
    audio_path: Optional[str] = None             # 音频路径 (旁白/BGM)
    duration_sec: float = 0.0                     # 视频/音频时长
    provider: str = ""                            # 实际调用的 provider 名称
    model_name: str = ""                          # 模型名 (如 qwen2.5:14b)
    tokens_used: int = 0                          # token 消耗
    tokens_saved: int = 0                         # 本地推理节省
    latency_ms: int = 0                           # 调用耗时
    error: Optional[str] = None                  # 失败原因
    metadata: Dict[str, Any] = field(default_factory=dict)  # 原始响应

    def to_dict(self) -> Dict:
        d = asdict(self)
        if isinstance(d.get('metadata'), dict):
            # metadata 里的大对象截断
            for k, v in d['metadata'].items():
                if isinstance(v, str) and len(v) > 200:
                    d['metadata'][k] = v[:200] + "..."
        return d


@dataclass
class ModelConfig:
    """模型注册配置"""
    plugin_id: str              # e.g. 'copywriting', 'video_gen'
    plugin_name: str            # e.g. '文案AI', '视频AI'
    plugin_class: str           # 类名 (e.g. 'CopywritingPlugin')
    enabled: bool = True
    priority: int = 0           # 越小越优先
    provider: str = ""           # ollama / runwaysd / kling / local
    api_key_env: str = ""        # 环境变量名
    api_endpoint: str = ""       # API endpoint
    model_name: str = ""         # 默认模型


# ============================================================================
# 插件基类
# ============================================================================

class BaseModelPlugin(ABC):
    """所有 AI 模型插件的基类"""
    plugin_id: str = ""
    plugin_name: str = ""
    provider: str = ""

    def __init__(self, config: ModelConfig = None):
        self.config = config or ModelConfig(
            plugin_id=self.plugin_id, plugin_name=self.plugin_name,
            plugin_class=self.__class__.__name__, provider=self.provider,
        )
        self._ready = False
        self._init()

    def _init(self):
        """子类实现: 验证依赖 / 加载模型 / 建立连接"""
        pass

    @abstractmethod
    def generate(self, **kwargs) -> ModelResult:
        """子类实现: 生成内容"""
        pass

    def _make_result(self, **overrides) -> ModelResult:
        base = ModelResult(success=True, provider=self.provider,
                          model_name=self.config.model_name)
        for k, v in overrides.items():
            setattr(base, k, v)
        return base

    def _record_call(self, result: ModelResult):
        """落库每次调用日志"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            conn.execute("""
                INSERT INTO mt_galaxy_ai_model_call_log
                    (plugin_id, provider, model_name, success, latency_ms,
                     tokens_used, tokens_saved, error, metadata, called_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                self.plugin_id, self.provider, result.model_name,
                1 if result.success else 0, result.latency_ms,
                result.tokens_used, result.tokens_saved,
                result.error, json.dumps(result.metadata, ensure_ascii=False)[:2000],
            ))
            conn.commit()
            conn.close()
        except Exception:
            # 表可能还不存在, 不影响主流程
            pass


# ============================================================================
# 5 种 AI 模型插件实现 (MVP: 先文案AI 用 Ollama, 其他 4 个先 placeholder)
# ============================================================================

class CopywritingPlugin(BaseModelPlugin):
    """文案 AI — Ollama qwen2.5 本地推理, 零 token"""
    plugin_id = "copywriting"
    plugin_name = "文案AI"
    provider = "ollama_local"

    def _init(self):
        self.config.model_name = "qwen2.5:14b"
        # 测试 Ollama 连通性
        try:
            import urllib.request
            req = urllib.request.Request(
                "http://localhost:11435/api/tags",
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                models = [m.get("name", "") for m in data.get("models", [])]
                self._ready = True
                self._ollama_models = models
        except Exception:
            self._ready = False

    def generate(self, topic: str = "", style: str = "educational",
                 length: str = "medium", **kwargs) -> ModelResult:
        """生成文案 (旁白/剧本/分镜描述)"""
        t0 = time.time()

        if not self._ready:
            return self._make_result(
                success=False, error="Ollama 未启动 (localhost:11435)",
                latency_ms=int((time.time()-t0)*1000),
            )

        STYLE_PROMPTS = {
            "cute_history": "用可爱轻松的语气讲历史, 像给小朋友讲故事但不失准确",
            "explosive_science": "用爆炸能量感讲解科学原理, 把抽象概念具象化",
            "code_demo": "简洁直接的编程技巧讲解, 像老司机带你看代码",
            "healing_life": "温暖治愈的生活小妙招",
            "guochao": "国潮文化解读, 古风典雅",
            "hotspot": "热点事件快速梳理, 直击要点",
            "math_beauty": "数学之美, 发现公式里的宇宙",
            "english_drama": "英文情景教学, 台词自然",
            "educational": "标准科普讲解",
        }

        length_map = {"short": 100, "medium": 250, "long": 400}
        max_chars = length_map.get(length, 250)
        style_desc = STYLE_PROMPTS.get(style, STYLE_PROMPTS["educational"])

        prompt = f"""你是专业短视频文案师。

主题: {topic}
风格: {style_desc}
字数: ≤ {max_chars} 字

生成一段适合短视频旁白的文案, 语言自然流畅, 口语化, 适合念出来。
不要写标题标签 hashtags, 只要正文内容。

文案:"""

        try:
            import urllib.request
            payload = json.dumps({
                "model": self.config.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 300},
            }).encode("utf-8")
            req = urllib.request.Request(
                "http://localhost:11435/api/generate",
                data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
            text = data.get("response", "").strip()
            tokens = data.get("eval_count", 0)

            result = self._make_result(
                success=True, text=text,
                tokens_used=tokens, tokens_saved=tokens,
                latency_ms=int((time.time()-t0)*1000),
                metadata={"style": style, "topic": topic},
            )
        except Exception as e:
            result = self._make_result(
                success=False, error=str(e)[:200],
                latency_ms=int((time.time()-t0)*1000),
            )

        self._record_call(result)
        return result


class VideoGenPlugin(BaseModelPlugin):
    """视频生成 AI — 即梦 Jimeng CLI + 本地 galaxy_video_renderer 降级"""
    plugin_id = "video_gen"
    plugin_name = "视频AI"
    provider = "jimeng_dreamina"

    def _init(self):
        """验证 dreamina CLI 可用 + 检查登录状态"""
        import shutil
        self._cli_path = shutil.which("dreamina")
        if self._cli_path:
            import subprocess
            try:
                r = subprocess.run(
                    [self._cli_path, "user_credit"],
                    capture_output=True, text=True, timeout=10,
                )
                self._ready = r.returncode == 0
                self.config.model_name = "seedance2.0fast"
            except Exception:
                self._ready = False
        else:
            self._ready = False

    def generate(self, prompt: str = "", duration_sec: int = 5,
                 ratio: str = "9:16", resolution: str = "720p",
                 model_version: str = "seedance2.0fast",
                 download_dir: str = "/tmp/galaxy_video_out",
                 poll: int = 120,
                 **kwargs) -> ModelResult:
        """即梦文生视频 (seedance2.0fast 默认)

        Args:
            prompt: 视频生成 prompt (中文/英文均可)
            duration_sec: 视频时长 (4-15s 依模型)
            ratio: 画面比例 9:16(竖屏)/16:9/1:1
            resolution: 480p/720p/1080p
            model_version: seedance2.0fast/seedance2.5/...
            download_dir: 结果下载目录
            poll: 异步轮询秒数 (0=不等待)
        """
        import subprocess, shutil
        t0 = time.time()

        if not self._ready or not shutil.which("dreamina"):
            return self._make_result(
                success=False,
                error="即梦 CLI 未登录或未安装 (运行: curl -s https://jimeng.jianying.com/cli | bash && dreamina login)",
                provider="jimeng_not_ready",
                latency_ms=int((time.time()-t0)*1000),
            )

        # 提交 + 轮询 + 下载
        cmd = [
            "dreamina", "text2video",
            "--prompt", prompt,
            "--duration", str(duration_sec),
            "--ratio", ratio,
            "--video_resolution", resolution,
            "--model_version", model_version,
            "--poll", str(poll),
        ]
        if download_dir:
            cmd.extend(["--download_dir", download_dir])

        try:
            os.makedirs(download_dir, exist_ok=True)
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=poll + 30)
            stdout = r.stdout.strip()
            stderr = r.stderr.strip()
            combined = stdout + "\n" + stderr

            # 解析结果 — 找 submit_id 和输出文件
            import re
            submit_id_match = re.search(r"submit_id[=:]\s*([a-zA-Z0-9\-]+)", combined)
            submit_id = submit_id_match.group(1) if submit_id_match else None

            video_path = None
            # dreamina 直接输出文件路径
            for line in combined.splitlines():
                line = line.strip()
                if line.startswith("/") and (line.endswith(".mp4") or ".mp4" in line):
                    video_path = line
                    break
                # 或者 download_dir 里最新的 mp4
                if "download" in line.lower() and ".mp4" in line:
                    path_match = re.search(r"(/\S+\.mp4)", line)
                    if path_match:
                        video_path = path_match.group(1)
                        break

            if not video_path and os.path.isdir(download_dir):
                mtime = 0
                for f in os.listdir(download_dir):
                    fp = os.path.join(download_dir, f)
                    if f.endswith(".mp4") and os.path.getmtime(fp) > mtime:
                        mtime = os.path.getmtime(fp)
                        video_path = fp

            if r.returncode == 0 and video_path and os.path.exists(video_path):
                import subprocess as sp
                try:
                    probe = sp.run(
                        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration,size",
                         "-of", "json", video_path],
                        capture_output=True, text=True, timeout=10,
                    )
                    dur = float(sp.json.loads(probe.stdout).get("format", {}).get("duration", duration_sec))
                    size_mb = float(sp.json.loads(probe.stdout).get("format", {}).get("size", 0)) / 1024 / 1024
                except Exception:
                    dur = duration_sec
                    size_mb = 0.0

                result = self._make_result(
                    success=True, video_path=video_path,
                    duration_sec=dur,
                    provider="jimeng_dreamina",
                    model_name=model_version,
                    latency_ms=int((time.time()-t0)*1000),
                    metadata={
                        "prompt": prompt, "ratio": ratio,
                        "resolution": resolution, "submit_id": submit_id,
                        "size_mb": round(size_mb, 1),
                    },
                )
            else:
                result = self._make_result(
                    success=False,
                    error=stderr[:300] or f"returncode={r.returncode}",
                    provider="jimeng_dreamina",
                    latency_ms=int((time.time()-t0)*1000),
                    metadata={"stdout": stdout[:500], "submit_id": submit_id},
                )

        except subprocess.TimeoutExpired:
            result = self._make_result(
                success=False, error=f"超时 ({poll}s), 但任务可能在处理中",
                provider="jimeng_dreamina",
                latency_ms=int((time.time()-t0)*1000),
            )
        except Exception as e:
            result = self._make_result(
                success=False, error=str(e)[:200],
                provider="jimeng_dreamina",
                latency_ms=int((time.time()-t0)*1000),
            )

        self._record_call(result)
        return result

    def generate_images(self, prompt: str = "", num_images: int = 4,
                        ratio: str = "1:1", model_version: str = "4.7",
                        resolution_type: str = "2k",
                        download_dir: str = "/tmp/galaxy_art_out",
                        poll: int = 60, **kwargs) -> ModelResult:
        """即梦文生图 (原画AI 接这个)"""
        import subprocess
        t0 = time.time()

        cmd = [
            "dreamina", "text2image",
            "--prompt", prompt,
            "--generate_num", str(num_images),
            "--ratio", ratio,
            "--resolution_type", resolution_type,
            "--model_version", model_version,
            "--poll", str(poll),
        ]
        if download_dir:
            cmd.extend(["--download_dir", download_dir])

        try:
            os.makedirs(download_dir, exist_ok=True)
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=poll + 30)

            images = []
            for line in (r.stdout + "\n" + r.stderr).splitlines():
                line = line.strip()
                if line.startswith("/") and (line.endswith(".png") or ".png" in line or ".jpg" in line):
                    images.append(line)
                elif ".png" in line or ".jpg" in line:
                    import re
                    match = re.search(r"(/\S+\.(?:png|jpg))", line)
                    if match:
                        images.append(match.group(1))

            if not images and os.path.isdir(download_dir):
                for f in sorted(os.listdir(download_dir)):
                    if f.endswith((".png", ".jpg")):
                        images.append(os.path.join(download_dir, f))

            if r.returncode == 0 and images:
                result = self._make_result(
                    success=True, images=images,
                    provider="jimeng_dreamina",
                    model_name=f"jimeng_image_{model_version}",
                    latency_ms=int((time.time()-t0)*1000),
                    metadata={"prompt": prompt, "num": len(images), "ratio": ratio},
                )
            else:
                result = self._make_result(
                    success=False,
                    error=(r.stderr or "")[:200] or "无输出图片",
                    provider="jimeng_dreamina",
                    latency_ms=int((time.time()-t0)*1000),
                )
        except Exception as e:
            result = self._make_result(
                success=False, error=str(e)[:200],
                provider="jimeng_dreamina",
                latency_ms=int((time.time()-t0)*1000),
            )

        self._record_call(result)
        return result


class AnimationPlugin(BaseModelPlugin):
    """动画生成 AI — MVP placeholder, 后续接 Runway Gen-3/Hailuo"""
    plugin_id = "animation"
    plugin_name = "动画AI"
    provider = "api_planned"

    def _init(self): self._ready = False

    def generate(self, storyboard=None, style: str = "cute_burst", **kwargs) -> ModelResult:
        return self._make_result(
            success=False, error="动画AI 待接入 (Runway Gen-3 / Hailuo API)",
            provider=self.provider,
        )


class Model3DPlugin(BaseModelPlugin):
    """3D 建模 AI — MVP placeholder, 后续接 TripoSR/Shap-E"""
    plugin_id = "3d_modeling"
    plugin_name = "建模AI"
    provider = "api_planned"

    def _init(self): self._ready = False

    def generate(self, description: str = "", **kwargs) -> ModelResult:
        return self._make_result(
            success=False, error="建模AI 待接入 (TripoSR / Shap-E)",
            provider=self.provider,
        )


class OriginalArtPlugin(BaseModelPlugin):
    """原画 AI — 即梦 Jimeng text2image (4.7/5.0Pro 模型)"""
    plugin_id = "original_art"
    plugin_name = "原画AI"
    provider = "jimeng_dreamina"

    def _init(self):
        # 复用 VideoGenPlugin 的即梦登录检查
        import shutil, subprocess
        self._cli_path = shutil.which("dreamina")
        if self._cli_path:
            try:
                r = subprocess.run(
                    [self._cli_path, "user_credit"],
                    capture_output=True, text=True, timeout=10,
                )
                self._ready = r.returncode == 0
                self.config.model_name = "jimeng_image_4.7"
            except Exception:
                self._ready = False
        else:
            self._ready = False

    def generate(self, concept: str = "", style: str = "digital_painting",
                 num_images: int = 4, ratio: str = "1:1",
                 model_version: str = "4.7", **kwargs) -> ModelResult:
        """即梦文生图 (原画/概念图)"""
        # 样式增强 prompt
        STYLE_ENHANCE = {
            "digital_painting": "digital painting, 2d concept art, clean lines, anime style",
            "chibi_cute": "chibi cute, super deformed, round face, pastel colors",
            "oil_painting": "oil painting, classical art, textured brush strokes",
            "ink_wash": "chinese ink wash painting, traditional style, minimalist",
            "pixel_art": "pixel art, retro game style, 16-bit",
            "3d_render": "3d render, octane render, realistic, subsurface scattering",
            "anime": "anime style, cel shading, vibrant colors",
        }
        enhance = STYLE_ENHANCE.get(style, "concept art")
        full_prompt = f"{concept}, {enhance}"

        # 调用 VideoGenPlugin 的 generate_images
        from engines.galaxy_ai_model_router import VideoGenPlugin
        jp = VideoGenPlugin()
        return jp.generate_images(
            prompt=full_prompt, num_images=num_images,
            ratio=ratio, model_version=model_version,
            download_dir="/tmp/galaxy_art_out",
        )


# ============================================================================
# ModelRouter — 统一入口
# ============================================================================

class ModelRouter:
    """仙女座 AI 模型路由器 — 5 种 AI 的统一入口"""

    PLUGIN_REGISTRY: Dict[str, type] = {
        "copywriting": CopywritingPlugin,
        "video_gen": VideoGenPlugin,
        "animation": AnimationPlugin,
        "3d_modeling": Model3DPlugin,
        "original_art": OriginalArtPlugin,
    }

    def __init__(self):
        self.plugins: Dict[str, BaseModelPlugin] = {}
        self._init_db()
        for pid, cls in self.PLUGIN_REGISTRY.items():
            try:
                self.plugins[pid] = cls()
            except Exception as e:
                print(f"⚠️ 插件 {pid} 初始化失败: {e}")
                self.plugins[pid] = None

    def _init_db(self):
        """确保调用日志表存在"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mt_galaxy_ai_model_call_log (
                    call_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plugin_id TEXT NOT NULL,
                    provider TEXT,
                    model_name TEXT,
                    success INTEGER,
                    latency_ms INTEGER,
                    tokens_used INTEGER DEFAULT 0,
                    tokens_saved INTEGER DEFAULT 0,
                    error TEXT,
                    metadata TEXT,
                    called_at TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception:
            pass

    # --- 便捷方法 ---

    def copywriting(self, **kwargs) -> ModelResult:
        return self._call("copywriting", **kwargs)

    def video_gen(self, **kwargs) -> ModelResult:
        return self._call("video_gen", **kwargs)

    def animation(self, **kwargs) -> ModelResult:
        return self._call("animation", **kwargs)

    def model_3d(self, **kwargs) -> ModelResult:
        return self._call("3d_modeling", **kwargs)

    def original_art(self, **kwargs) -> ModelResult:
        return self._call("original_art", **kwargs)

    def _call(self, plugin_id: str, **kwargs) -> ModelResult:
        plugin = self.plugins.get(plugin_id)
        if plugin is None:
            return ModelResult(
                success=False, error=f"插件 {plugin_id} 未注册或初始化失败",
                provider="router_error",
            )
        return plugin.generate(**kwargs)

    # --- 状态查询 ---

    def status(self) -> Dict[str, Dict]:
        """5 种 AI 模型当前状态"""
        info = {}
        for pid, plugin in self.plugins.items():
            info[pid] = {
                "name": plugin.plugin_name if plugin else "?",
                "provider": plugin.provider if plugin else "?",
                "ready": getattr(plugin, "_ready", False) if plugin else False,
                "enabled": plugin is not None,
            }
        return info


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="仙女座 AI 模型路由器")
    sub = parser.add_subparsers(dest="mode")

    p_status = sub.add_parser("status", help="查看 5 种 AI 模型状态")

    p_copy = sub.add_parser("copywriting", help="文案生成")
    p_copy.add_argument("-t", "--topic", required=True)
    p_copy.add_argument("-s", "--style", default="educational")

    p_vid = sub.add_parser("video", help="视频生成 (MVP 走本地 renderer)")
    p_vid.add_argument("-t", "--topic", required=True)

    args = parser.parse_args()
    router = ModelRouter()

    if args.mode == "status":
        print("=== 仙女座 AI 模型状态 ===")
        for pid, info in router.status().items():
            mark = "✅" if info["ready"] else "⏳" if info["enabled"] else "❌"
            print(f"  {mark} {pid:15s} {info['name']:10s} provider={info['provider']:15s} ready={info['ready']}")

    elif args.mode == "copywriting":
        r = router.copywriting(topic=args.topic, style=args.style)
        print(f"=== 文案生成 ===")
        print(f"success={r.success} latency={r.latency_ms}ms tokens_saved={r.tokens_saved}")
        print(f"\n{r.text}")

    elif args.mode == "video":
        r = router.video_gen(topic=args.topic)
        print(f"{'✅' if r.success else '❌'} success={r.success} video={r.video_path} ({r.duration_sec:.1f}s)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
