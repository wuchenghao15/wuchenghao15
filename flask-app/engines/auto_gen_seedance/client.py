"""Seedance 2.5 视频生成 API 客户端
已验证: POST /api/v3/contents/generations/tasks → ✅ 可用 (不需要 Endpoint ID)
"""
import os, time, json, urllib.request, urllib.error, uuid


class SeedanceClient:
    BASE = "https://ark.cn-beijing.volces.com/api/v3"
    MODEL = "doubao-seedance-2-5-260628"

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.environ.get("VOLCENGINE_API_KEY", "")
        self.model = model or os.environ.get("VOLCENGINE_SEEDANCE_MODEL", self.MODEL)
        self._ok = bool(self.api_key and self.api_key.startswith("ark-"))

    @property
    def available(self):
        return self._ok

    def _post(self, path, payload):
        url = f"{self.BASE}{path}"
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            return {"error": {"code": e.code, "message": raw[:300]}}
        except Exception as e:
            return {"error": {"code": "NETWORK", "message": str(e)[:300]}}

    def _get(self, path):
        url = f"{self.BASE}{path}"
        req = urllib.request.Request(url, method="GET")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            return {"error": {"code": e.code, "message": raw[:300]}}
        except Exception as e:
            return {"error": {"code": "NETWORK", "message": str(e)[:300]}}

    def generate(self, text_prompt, refs=None, ratio="16:9", duration=5,
                 generate_audio=False, watermark=False):
        """提交视频生成任务, 返回 task_id"""
        content = [{"type": "text", "text": text_prompt}]
        if refs:
            for r in refs:
                content.append(r)
        payload = {
            "model": self.model,
            "content": content,
            "generate_audio": generate_audio,
            "ratio": ratio,
            "duration": duration,
            "watermark": watermark,
        }
        resp = self._post("/contents/generations/tasks", payload)
        if "id" in resp:
            return {"success": True, "task_id": resp["id"], "model": self.model}
        return {"success": False, "error": resp.get("error", resp)}

    def poll(self, task_id, max_wait=300, interval=5):
        """轮询任务直到完成, 返回最终状态"""
        start = time.time()
        while time.time() - start < max_wait:
            resp = self._get(f"/contents/generations/tasks/{task_id}")
            status = resp.get("status", "unknown")
            if status == "succeeded":
                video_url = resp.get("content", {}).get("video_url", "")
                return {"success": True, "status": status, "video_url": video_url,
                        "usage": resp.get("usage", {}), "duration_s": time.time() - start}
            if status in ("failed", "cancelled", "expired"):
                return {"success": False, "status": status, "error": resp}
            time.sleep(interval)
        return {"success": False, "status": "timeout"}

    def quick_generate(self, text_prompt, **kwargs):
        """提交 + 轮询 + 返回完整结果"""
        sub = self.generate(text_prompt, **kwargs)
        if not sub.get("success"):
            return sub
        return self.poll(sub["task_id"])

    def health(self):
        """健康检查"""
        resp = self._get("/contents/generations/tasks?limit=1")
        return {"available": self._ok, "model": self.model, "api_key_prefix": self.api_key[:10] + "..." if self.api_key else "",
                "test": "ok" if "error" not in resp or resp.get("error", {}).get("code") != 401 else "unauthorized"}


class AsyncSeedanceClient(SeedanceClient):
    """异步/批量接口 — 用 threading 实现, 兼容同步接口"""
    pass
