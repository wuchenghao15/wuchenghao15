#!/usr/bin/env python3
"""
auto_quant_adapter.py — 仙女座自动量化择优适配器
================================================
根据本机硬件 (CPU/GPU/内存/磁盘) 自动选择最优 GGUF 量化级别,
下载 (hf-mirror) + ollama create + 验证推理, 零积分.

用法:
  python3 auto_quant_adapter.py status              # 硬件探针 + 推荐
  python3 auto_quant_adapter.py adapt               # 自动适配 + 下载 + create
  python3 auto_quant_adapter.py adapt --force-q5     # 强制 Q5_K_M (忽略内存警告)
  python3 auto_quant_adapter.py adapt --mini         # Mac mini 同步 (SSH 通时)
  python3 auto_quant_adapter.py benchmark            # 所有已装模型跑分
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path

# ═══════════════════════════════════════════════
# 硬件探针
# ═══════════════════════════════════════════════
def hw_probe():
    import platform, re
    info = {}
    # unified memory
    try:
        mem = int(subprocess.check_output(["sysctl","hw.memsize"], text=True).split()[1])
        info["memory_gb"] = mem // (1024**3)
    except: info["memory_gb"] = 0
    # chip
    try:
        chip = subprocess.check_output(
            ["system_profiler","SPDisplaysDataType"], text=True, timeout=5
        )
        info["metal"] = "Metal" in chip
        m = re.search(r"Chipset Model:\s+(\S+)", chip)
        info["chip"] = m.group(1) if m else "unknown"
    except: info["metal"] = False; info["chip"] = "unknown"
    # CPU cores
    try:
        info["cpu_cores"] = int(subprocess.check_output(
            ["sysctl","hw.ncpu"], text=True
        ).split()[1])
    except: info["cpu_cores"] = 0
    # disk free
    try:
        df = subprocess.check_output(["df","-k","/"], text=True).splitlines()[-1]
        info["disk_free_gb"] = int(df.split()[3]) // (1024**2)
    except: info["disk_free_gb"] = 0
    # Ollama version
    try:
        v = subprocess.check_output(["ollama","--version"], text=True, stderr=subprocess.STDOUT)
        info["ollama_ver"] = v.strip().split()[-1]
    except: info["ollama_ver"] = "unknown"
    # Ollama models
    try:
        out = subprocess.check_output(["ollama","list"], text=True)
        models = {}
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 3:
                name = parts[0]
                size = parts[2]
                models[name] = size
        info["ollama_models"] = models
    except: info["ollama_models"] = {}
    return info

# ═══════════════════════════════════════════════
# 模型注册表 (Bartowski GGUF, Ollama 社区推荐)
# ═══════════════════════════════════════════════
GGUF_REGISTRY = {
    "qwen2.5:14b": {
        "repo": "bartowski/Qwen2.5-14B-Instruct-GGUF",
        "filename_prefix": "Qwen2.5-14B-Instruct",
        "template": "chatml",
        "params": "14.8B",
        "license": "Apache 2.0",
        "quants": {
            # quant_tag:  {file_suffix, size_gb, quality_vs_fp16, min_mem_gb}
            "IQ2_M":    {"file": "-IQ2_M.gguf",    "size": 6.0, "q": 0.75, "min": 12},
            "Q2_K":     {"file": "-Q2_K.gguf",     "size": 6.3, "q": 0.78, "min": 12},
            "IQ4_NL":   {"file": "-IQ4_NL.gguf",   "size": 9.0, "q": 0.86, "min": 16},
            "Q4_K_S":   {"file": "-Q4_K_S.gguf",   "size": 8.6, "q": 0.88, "min": 16},
            "Q4_K_M":   {"file": "-Q4_K_M.gguf",   "size": 9.0, "q": 0.89, "min": 16},  # Ollama 默认
            "Q5_K_S":   {"file": "-Q5_K_S.gguf",   "size": 10.3,"q": 0.91, "min": 20},
            "Q5_K_M":   {"file": "-Q5_K_M.gguf",   "size": 10.5,"q": 0.92, "min": 20},  # 推荐
            "Q6_K":     {"file": "-Q6_K.gguf",     "size": 12.1,"q": 0.97, "min": 24},
            "Q8_0":     {"file": "-Q8_0.gguf",     "size": 15.7,"q": 0.99, "min": 28},
            "f16":      {"file": "-f16.gguf",      "size": 30.2,"q": 1.00, "min": 36},
        },
    },
    "qwen2.5-coder:14b": {
        "repo": "bartowski/Qwen2.5-Coder-14B-Instruct-GGUF",
        "filename_prefix": "Qwen2.5-Coder-14B-Instruct",
        "template": "chatml_coder",
        "params": "14.8B",
        "license": "Apache 2.0",
        "quants": None,  # 同 qwen2.5:14b 量化表
    },
}
GGUF_REGISTRY["qwen2.5-coder:14b"]["quants"] = GGUF_REGISTRY["qwen2.5:14b"]["quants"]

# ═══════════════════════════════════════════════
# 择优算法
# ═══════════════════════════════════════════════
def pick_best_quant(model_key: str, hw: dict, purpose: str = "general",
                    force_q5: bool = False, min_speed_priority: bool = False):
    """
    根据硬件 + 用途选量化级别
    
    purpose: "general"(对话推理) | "code"(代码生成, 建议 Q5) | "fast"(极限速度, 建议 Q4)
    """
    entry = GGUF_REGISTRY[model_key]
    mem = hw["memory_gb"]
    disk = hw["disk_free_gb"]
    
    # 可用量化 (按质量降序)
    available = sorted(entry["quants"].items(), 
                      key=lambda x: -x[1]["q"])
    
    # 优先级 (从高到低)
    if force_q5:
        preferred = ["Q5_K_M", "Q5_K_S", "Q6_K", "Q4_K_M"]
    elif purpose == "code":
        preferred = ["Q5_K_M", "Q5_K_S", "Q4_K_M"]  # 代码对质量敏感
    elif purpose == "fast":
        preferred = ["Q4_K_M", "Q4_K_S", "Q5_K_M"]   # 速度优先
    else:  # general
        if mem >= 32:
            preferred = ["Q5_K_M", "Q6_K", "Q4_K_M"]
        else:
            preferred = ["Q5_K_M", "Q4_K_M", "Q4_K_S"]
    
    # 选第一个 fit 的
    for q in preferred:
        if q not in entry["quants"]: continue
        cfg = entry["quants"][q]
        min_mem = cfg.get("min_mem_gb", cfg.get("min", 16))
        if mem >= min_mem and disk >= cfg["size"] + 2:  # +2GB 留 Ollama 开销
            return q, cfg
    
    # fallback: 最后一个 (最小)
    q, cfg = available[-1]
    return q, cfg

def recommend(hw: dict, force_q5: bool = False):
    """仙女座给每台机器的推荐组合"""
    mem = hw["memory_gb"]
    print(f"\n🧠 仙女座择优 ({mem}GB RAM, {hw['chip']}, {hw['disk_free_gb']}GB 可用)")
    print("─" * 50)
    
    recs = {}
    for key in ["qwen2.5:14b", "qwen2.5-coder:14b"]:
        purpose = "general" if ":14b" in key and "coder" not in key else "code"
        q, cfg = pick_best_quant(key, hw, purpose, force_q5)
        tag = f"{key.split(':')[0]}:14b-{q.lower()}"
        score = cfg["q"]
        print(f"  {key:25s} → {q:8s} ({cfg['size']:.1f}GB, quality={score:.0%})  tag={tag}")
        recs[key] = {"quant": q, "tag": tag, "file_suffix": cfg["file"], "size_gb": cfg["size"]}
    return recs

# ═══════════════════════════════════════════════
# 下载 + create
# ═══════════════════════════════════════════════
GGUF_DIR = Path("/tmp/andromeda_gguf")

def download_gguf(model_key: str, quant: str):
    entry = GGUF_REGISTRY[model_key]
    suffix = entry["quants"][quant]["file"]
    fn = f"{entry['filename_prefix']}{suffix}"
    out = GGUF_DIR / fn
    if out.exists() and out.stat().st_size > 10**9:
        print(f"  ✅ 已有: {out}")
        return str(out)
    
    print(f"  🚀 下载 {fn} (hf-mirror)...")
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    from huggingface_hub import hf_hub_download
    GGUF_DIR.mkdir(parents=True, exist_ok=True)
    path = hf_hub_download(repo_id=entry["repo"], filename=fn, local_dir=str(GGUF_DIR))
    sz = os.path.getsize(path)/1024**3
    print(f"  ✅ 下载完成 {sz:.1f}GB")
    return path

def make_modelfile(gguf_path: str, model_key: str) -> str:
    """写 Modelfile → 用于 ollama create"""
    entry = GGUF_REGISTRY[model_key]
    mf_path = GGUF_DIR / f"Modelfile_{model_key.replace(':','_')}"
    
    # ChatML template (Qwen2.5 标准)
    tpl = """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
{{ .Response }}<|im_end|>"""
    
    if "coder" in model_key:
        system = "You are Qwen Coder, created by Alibaba Cloud. You are an expert programmer that writes clean, correct code."
    else:
        system = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."
    
    mf = f"""FROM {gguf_path}

TEMPLATE """ + '"""' + tpl + '"""' + f"""

PARAMETER temperature 0.7
PARAMETER num_ctx 32768
PARAMETER top_p 0.9

SYSTEM {system!r}

LICENSE """ + '"""Apache License, Version 2.0"""'
    
    mf_path.write_text(mf)
    return str(mf_path)

def ollama_create(model_key: str, tag: str, gguf_path: str):
    """ollama create qwen2.5:14b-q5 -f Modelfile"""
    mf = make_modelfile(gguf_path, model_key)
    print(f"  🛠️  ollama create {tag} -f {mf}")
    # 先 rm 旧的同名 tag
    subprocess.run(["ollama","rm",tag], capture_output=True)
    result = subprocess.run(["ollama","create",tag,"-f",mf], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ create 失败: {result.stderr[-300:]}")
        return False
    print(f"  ✅ {tag} 创建成功!")
    return True

def verify_inference(tag: str, prompt: str = "你好, 用一句话介绍自己") -> bool:
    """HTTP API 跑一次推理"""
    import urllib.request as ur
    try:
        payload = json.dumps({"model":tag,"prompt":prompt,"stream":False}).encode()
        t0 = time.time()
        r = ur.urlopen(ur.Request("http://localhost:11435/api/generate",
                                 data=payload, headers={"Content-Type":"application/json"}), timeout=60)
        resp = json.loads(r.read())
        dt = time.time()-t0
        print(f"  ✅ 推理 OK ({dt:.1f}s): {resp['response'][:50]}...")
        return True
    except Exception as e:
        print(f"  ❌ 推理失败: {e}")
        return False

# ═══════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════
def cmd_status(hw: dict):
    print(json.dumps(hw, indent=2, ensure_ascii=False))
    recs = recommend(hw)
    print("\n💡 推荐组合:")
    general = recs.get("qwen2.5:14b", {})
    coder = recs.get("qwen2.5-coder:14b", {})
    combo_mem = general.get("size_gb", 0) + coder.get("size_gb", 0) + 5  # +5GB KV cache
    print(f"   通用 {general.get('quant','?')} ({general.get('size_gb',0):.1f}GB) + "
          f"代码 {coder.get('quant','?')} ({coder.get('size_gb',0):.1f}GB)")
    print(f"   预计内存占用: {combo_mem:.0f}GB / {hw['memory_gb']}GB")
    if combo_mem > hw["memory_gb"]:
        print(f"   ⚠️  警告: 可能 OOM, 建议 coder 保留 Q4_K_M")

def cmd_adapt(hw: dict, force_q5: bool = False):
    recs = recommend(hw, force_q5)
    print("\n" + "="*60)
    print("🚀 仙女座自动适配开始")
    print("="*60)
    
    for key, cfg in recs.items():
        print(f"\n▶ 处理 {key} → {cfg['quant']}")
        gguf = download_gguf(key, cfg["quant"])
        if ollama_create(key, cfg["tag"], gguf):
            verify_inference(cfg["tag"])
    
    print("\n" + "="*60)
    print("✅ 适配完成! ollama list:")
    print("="*60)
    subprocess.run(["ollama","list"])

def cmd_benchmark():
    hw = hw_probe()
    print("\n📊 仙女座 benchmark (每模型 3 次取平均)\n")
    for name, size in hw["ollama_models"].items():
        print(f"▶ {name} ({size})")
        times = []
        for i in range(3):
            try:
                payload = json.dumps({"model":name,"prompt":"1+1等于几?","stream":False}).encode()
                t0 = time.time()
                import urllib.request as ur
                r = ur.urlopen(ur.Request("http://localhost:11435/api/generate",
                                         data=payload, headers={"Content-Type":"application/json"}), timeout=60)
                resp = json.loads(r.read())
                dt = time.time()-t0
                ntokens = resp.get("eval_count", 1)
                speed = ntokens / dt if dt > 0 else 0
                times.append(dt)
                print(f"  第{i+1}次: {dt:.1f}s, {speed:.1f} tok/s")
            except Exception as e:
                print(f"  第{i+1}次: ❌ {e}")
        if times:
            avg = sum(times)/len(times)
            print(f"  ⏱️  平均: {avg:.1f}s")

def main():
    p = argparse.ArgumentParser(description="仙女座自动量化择优适配器")
    p.add_argument("cmd", choices=["status","adapt","benchmark"])
    p.add_argument("--force-q5", action="store_true", help="强制 Q5_K_M (忽略内存警告)")
    p.add_argument("--mini", action="store_true", help="Mac mini SSH 同步")
    args = p.parse_args()
    
    hw = hw_probe()
    
    if args.cmd == "status":
        cmd_status(hw)
    elif args.cmd == "adapt":
        cmd_adapt(hw, args.force_q5)
    elif args.cmd == "benchmark":
        cmd_benchmark()

if __name__ == "__main__": main()
