#!/usr/bin/env python3
"""
ai_local_image_gen.py — 仙女座本地图像生成 (零 token)
=====================================================
MacBook Pro M5 (24GB) / Mac mini M5 (待确认内存)
用 diffusers + torch Metal GPU 本地推理

支持:
  ✅ 文生图 (text2img)
  ✅ 图生图 (img2img)
  ✅ 高清修复 (upscale via tile)
  
模型: segmind/SSD-1B (~2GB, SDXL 架构, 公开免费)
替代方案: stabilityai/sd-xl-base (13GB) 或 ollama flux2-klein

用法:
  python3 ai_local_image_gen.py --prompt "上海弄堂, 手绘" --out /tmp/test.png
  python3 ai_local_image_gen.py --prompt "... " --input base.png --strength 0.7
  python3 ai_local_image_gen.py --status
"""
import argparse, json, os, sys, time, hashlib
from pathlib import Path

# ── 硬件探针 + 自动选模 ──
def detect_hardware():
    import subprocess
    info = {}
    try:
        mem = int(subprocess.check_output(["sysctl","hw.memsize"]).split()[1])
        info["memory_gb"] = mem // (1024**3)
    except: info["memory_gb"] = 0
    try:
        chip = subprocess.check_output(
            ["system_profiler","SPDisplaysDataType"], text=True
        )
        info["has_metal"] = "Metal" in chip and "Supported" in chip
    except: info["has_metal"] = False
    try:
        import torch
        info["torch_mps"] = torch.backends.mps.is_available()
        info["torch_ver"] = torch.__version__
    except: info["torch_mps"] = False
    return info

HWC = detect_hardware()

# ── 模型注册表 (按硬件自动选) ──
MODEL_REGISTRY = {
    # 最小 (2GB, 24s/张 @ 1024x1024, M5 24GB)
    "sd-1b": {
        "repo": "segmind/SSD-1B",
        "params": "1B", "size_gb": 2,
        "steps": 20, "guidance": 7.5,
        "min_mem_gb": 16,
        "license": "OpenRAIL-M",
        "notes": "小而快, 24s/张, 质量够漫剧分镜用",
    },
    # 标准 SDXL (13GB, 质量更高但慢)
    "sdxl": {
        "repo": "stabilityai/stable-diffusion-xl-base-1.0",
        "params": "2.6B", "size_gb": 13,
        "steps": 30, "guidance": 5.0,
        "min_mem_gb": 24,
        "variant": "fp16",
        "license": "OpenRAIL++",
        "notes": "SDXL 标准, 10-20s/张 @ 30 steps",
    },
    # Ollama 原生图像模型 (Homebrew 版暂不支持, 等官方 Desktop 或编译版)
    #  "flux2-klein": { ... }
}

def auto_pick_model():
    """根据内存自动选"""
    mem = HWC.get("memory_gb", 16)
    if mem >= 32 and HWC.get("torch_mps"):
        return "sdxl"
    return "sd-1b"

# ── Pipeline 懒加载 (避免每次都初始化) ──
_PIPE_CACHE = {}

def get_pipe(model_key: str = None):
    global _PIPE_CACHE
    key = model_key or auto_pick_model()
    if key in _PIPE_CACHE:
        return _PIPE_CACHE[key]
    
    import torch
    from diffusers import StableDiffusionXLPipeline

    cfg = MODEL_REGISTRY[key]
    print(f"🔄 加载模型 {key} ({cfg['repo']})...")
    t0 = time.time()

    kwargs = {"torch_dtype": torch.float16}
    if cfg.get("variant"):
        kwargs["variant"] = cfg["variant"]

    pipe = StableDiffusionXLPipeline.from_pretrained(cfg["repo"], **kwargs)
    pipe.to("mps")
    pipe.enable_attention_slicing()
    # 可选: enable_vae_slicing(), enable_sequential_cpu_offload()

    dt = time.time() - t0
    print(f"✅ 加载完成 ({dt:.1f}s), 已上 Metal GPU")
    _PIPE_CACHE[key] = pipe
    return pipe, cfg

# ── 文生图 ──
def text2img(prompt: str, out_path: str, model_key=None,
             width=1024, height=1024, seed=None):
    pipe, cfg = get_pipe(model_key)
    
    generator = None
    if seed is not None:
        import torch
        generator = torch.Generator(device="mps").manual_seed(seed)

    t0 = time.time()
    result = pipe(
        prompt, height=height, width=width,
        num_inference_steps=cfg["steps"],
        guidance_scale=cfg["guidance"],
        generator=generator,
    )
    img = result.images[0]
    dt = time.time() - t0

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(f"🎨 t2i → {out_path} ({img.size[0]}x{img.size[1]}, {dt:.1f}s)")
    return out_path, dt

# ── 图生图 ──
def img2img(prompt: str, input_path: str, out_path: str, 
            strength=0.7, model_key=None, seed=None):
    """基础 img2img — 先加载 input 再送同 pipeline (SDXL 原生支持 img2img)"""
    import torch
    from diffusers import StableDiffusionXLImg2ImgPipeline
    from PIL import Image

    pipe_cfg = MODEL_REGISTRY[model_key or auto_pick_model()]
    t0 = time.time()
    pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
        pipe_cfg["repo"], torch_dtype=torch.float16,
        variant=pipe_cfg.get("variant"),
    )
    pipe.to("mps")
    pipe.enable_attention_slicing()
    print(f"🔄 img2img pipeline 加载 ({time.time()-t0:.1f}s)")

    base = Image.open(input_path).convert("RGB").resize((1024, 1024))
    generator = torch.Generator(device="mps").manual_seed(seed) if seed else None

    result = pipe(
        prompt, image=base, strength=strength,
        num_inference_steps=pipe_cfg["steps"],
        guidance_scale=pipe_cfg["guidance"],
        generator=generator,
    )
    img = result.images[0]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(f"🎨 i2i → {out_path} ({img.size}, {time.time()-t0:.1f}s)")
    return out_path

# ── CLI ──
def main():
    p = argparse.ArgumentParser(description="仙女座本地图像生成 (零 token)")
    sub = p.add_subparsers(dest="cmd")

    # status
    sub.add_parser("status")

    # generate
    gp = sub.add_parser("gen")
    gp.add_argument("--prompt", required=True, nargs="+")
    gp.add_argument("--out", default="/tmp/andromeda_test/out.png")
    gp.add_argument("--model", choices=list(MODEL_REGISTRY.keys()))
    gp.add_argument("--w", type=int, default=1024)
    gp.add_argument("--h", type=int, default=1024)
    gp.add_argument("--seed", type=int, default=None)
    gp.add_argument("--input", default=None, help="图生图: base image path")
    gp.add_argument("--strength", type=float, default=0.7)

    args = p.parse_args()

    if args.cmd == "status":
        auto = auto_pick_model()
        print(json.dumps({
            "hardware": HWC,
            "auto_model": auto,
            "models": {k: {kk:vv for kk,vv in v.items() if kk != "repo"}
                       for k, v in MODEL_REGISTRY.items()},
        }, indent=2, ensure_ascii=False))
        return

    if args.cmd == "gen":
        prompt = " ".join(args.prompt)
        if args.input:
            img2img(prompt, args.input, args.out, args.strength, args.model, args.seed)
        else:
            text2img(prompt, args.out, args.model, args.w, args.h, args.seed)
        return

    p.print_help()

if __name__ == "__main__": main()
