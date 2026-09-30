# MicroPython 玩法: 仙女座反馈桥接器
# 刷入方式: https://ai-passport.folotoy.cn/tools/web-flasher/
# 
# 功能:
#   1. BLE 可连接, 暴露 TRAECARD Service
#   2. 接收仙女座/冰山的 BLE 写入 (音频配置帧 + PCM 数据)
#   3. 直接送到 machine.I2S → ES8311 → 扬声器
#
# 官方 BSP I2S: ES8311 已初始化, I2S0 STD, 引脚 SCK/WS/SD

import time
import ustruct
import machine
import bluetooth
from machine import I2S, Pin

# ═══════════════════════════════════════════
# 硬件定义 (从官方 bsp_audio.c + demo_audio.c 逆向)
# ═══════════════════════════════════════════
SAMPLE_RATE = 16000
BITS = 16
CHANNELS = 1  # MONO! 官方 play_tone 用 MONO

# I2S 引脚 (ES8311 初始化在 bootloader, 这里复用)
# machine.I2S 直接指定 I2S0 STD mode
I2S_ID = 0

# ES8311 DAC 通过 I2C (400kHz) 控制音量
i2c_ctrl = machine.I2C(1, freq=400000)  # SDA=GPIO8, SCL=GPIO9 (假设)

# ═══════════════════════════════════════════
# BLE 定义 (TRAECARD Service, 和 trae_card 固件完全一致!)
# ═══════════════════════════════════════════
SVC_UUID     = bluetooth.UUID("54524145-4341-5244-0000-000000000000")
CHAR_WRITE   = bluetooth.UUID("54524145-4341-5244-0000-000000000010")  # 0x10 WRITE → 我们的入口
CHAR_ACK     = bluetooth.UUID("54524145-4341-5244-0000-000000000011")  # 0x11 NOTIFY → 回 ACK
CHAR_IDENT   = bluetooth.UUID("54524145-4341-5244-0000-000000000012")  # 0x12 READ
CHAR_STATE   = bluetooth.UUID("54524145-4341-5244-0000-000000000013")  # 0x13 READ
CHAR_MIC     = bluetooth.UUID("54524145-4341-5244-0000-000000000014")  # 0x14 NOTIFY

# ACK 码 (和 trae_card 固件一致)
ACK_OK         = b'\x00\x10'
ACK_ERR        = b'\x00\x11'
ACK_AUDIO_RDY  = b'\x00\x15'

# ═══════════════════════════════════════════
# 状态
# ═══════════════════════════════════════════
ble = None
i2s_out = None
audio_open = False

# ═══════════════════════════════════════════
# I2S 音频接口 (ES8311 已初始化, 我们只管送数据)
# ═══════════════════════════════════════════
def audio_open(rate=16000, bits=16, channels=1):
    """打开 I2S DMA 输出通道"""
    global i2s_out, audio_open
    if audio_open:
        audio_close()
    
    # machine.I2S 初始化 — 使用默认 I2S0 STD mode (和 ES8311 一致)
    i2s_out = I2S(
        I2S_ID,
        I2S.TX,
        ws=Pin(6),      # BSP_LCD 旁的 I2S WS (从 bsp_pins.h)
        sck=Pin(7),     # I2S SCK
        sd=Pin(5),      # I2S SD (数据)
        mclk=Pin(4),    # ES8311 MCLK
        bits=bits,
        rate=rate,
        channel=I2S.ONLY_LEFT if channels == 1 else I2S.STEREO,
        dma_buf=4096
    )
    audio_open = True
    print(f"🎵 I2S open: rate={rate} bits={bits} ch={channels}")

def audio_write(data):
    """写 PCM 数据到 ES8311"""
    global i2s_out, audio_open
    if not audio_open:
        audio_open()
    try:
        written = i2s_out.write(data)
        return written
    except Exception as e:
        print(f"audio_write err: {e}")
        return -1

def audio_close():
    global i2s_out, audio_open
    if i2s_out:
        try:
            i2s_out.deinit()
        except:
            pass
        i2s_out = None
    audio_open = False

def set_volume(vol):
    """ES8311 音量控制 (I2C 写寄存器)"""
    # ES8311 0x0C 寄存器 = DAC 音量 (0~100)
    # 简化: 直接通过 AT 命令不行 (MicroPython 玩法), 用 I2C
    try:
        i2c_ctrl.writeto(0x18, ustruct.pack('BB', 0x0C, vol))
        print(f"🔊 volume={vol}")
    except Exception as e:
        print(f"volume set err: {e}")

# ═══════════════════════════════════════════
# BLE GATT 回调 — 这就是我们要的!
# ═══════════════════════════════════════════
def on_write(char, data):
    """核心入口: 仙女座的 BLE 写入全部进来这里"""
    global audio_open
    
    print(f"📥 BLE write ({len(data)}B): {data.hex()}")
    
    # 发 ACK 先 (模仿 trae_card 固件)
    ble.gatts_notify(0, ACK_OK)
    
    # 判断数据类型
    if len(data) >= 2 and data[0] == 0x01:
        # ── I2S 配置帧 (type=0x01) ──
        # 格式: [0x01, len, rate_hi, rate_lo, bits, channels]
        payload_len = data[1]
        if len(data) >= 2 + payload_len:
            rate = (data[2] << 8) | data[3]
            bits = data[4]
            ch   = data[5] if len(data) > 5 else 1
            print(f"🎛 I2S cfg: rate={rate} bits={bits} ch={ch}")
            
            # 先 close 再 reopen (格式切换必须这样)
            audio_close()
            audio_open(rate, bits, ch)
            
            # 回 AUDIO_READY
            ble.gatts_notify(0, ACK_AUDIO_RDY)
    
    elif len(data) >= 1 and data[0] >= 0x61 and data[0] <= 0x7A:
        # ── 文本命令 (a-z 开头) ──
        text = data.decode('ascii', errors='replace').strip()
        print(f"📝 Text cmd: {text}")
        
        if text.startswith('beep'):
            # 播放 1kHz 蜂鸣 (用 I2S 直接生成)
            audio_beep()
        elif text.startswith('volume,'):
            try:
                v = int(text.split(',')[1].split('\r')[0])
                set_volume(v)
            except:
                pass
    
    else:
        # ── PCM 数据 (裸 bytes) ──
        if audio_open:
            audio_write(bytes(data))

def audio_beep(freq=1000, dur_ms=200, vol=0.5):
    """生成并播放蜂鸣声 (方波)"""
    global audio_open, i2s_out
    if not audio_open:
        audio_open(16000, 16, 1)
    
    period = SAMPLE_RATE // freq
    total = SAMPLE_RATE * dur_ms // 1000
    
    buf = bytearray(total * 2)  # 16bit = 2B/sample
    phase = 0
    for i in range(total):
        sample = int(6000 * vol) if phase < period // 2 else int(-6000 * vol)
        ustruct.pack_into('<h', buf, i * 2, sample)
        phase = (phase + 1) % period
    
    audio_write(bytes(buf))

def on_read(char):
    """读请求 — 返回身份/状态"""
    if char == CHAR_IDENT:
        return b'98c377f490f8WzoOV4GUVsOav1.0.0\r\n'
    elif char == CHAR_STATE:
        return b'\x01\x01\x01'
    return b''

# ═══════════════════════════════════════════
# BLE 初始化
# ═══════════════════════════════════════════
def ble_init():
    global ble
    
    ble = bluetooth.BLE()
    ble.active(True)
    
    # 注册 GATT Service — 和 trae_card 固件完全一致!
    service = (
        SVC_UUID,
        (
            (CHAR_WRITE, bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESP),
            (CHAR_ACK,   bluetooth.FLAG_NOTIFY),
            (CHAR_IDENT, bluetooth.FLAG_READ),
            (CHAR_STATE, bluetooth.FLAG_READ),
            (CHAR_MIC,   bluetooth.FLAG_NOTIFY),
        ),
    )
    
    # 注册 + 拿 handle
    handles = ble.gatts_register_services([service])
    print(f"✅ GATT registered, handles: {handles}")
    
    # 设置回调
    ble.gatts_set_buffer(handles[0][0], 512, True)  # 0x10 WRITE 缓冲
    ble.gatt_callbacks(
        conn_cb=lambda conn, event: print(f"BLE conn: {event}") if event else print("BLE disconnect"),
        write_cb=lambda conn, char, data: on_write(char, data),
        read_cb=lambda conn, char: on_read(char),
    )
    
    # 开始广播
    ble_adv = bluetooth.Advertising(
        ble=ble,
        name="98c377f490f8",
        services=[SVC_UUID],
        timeout=0,
    )
    ble_adv.start()
    print(f"📡 BLE advertising '98c377f490f8' — 仙女座可以连接了!")

# ═══════════════════════════════════════════
# 主循环
# ═══════════════════════════════════════════
def main():
    print("=" * 50)
    print("🌟 仙女座反馈桥接器 v1.0")
    print("   FoloToy AI Passport · MicroPython")
    print("=" * 50)
    
    ble_init()
    set_volume(80)
    
    # 开机蜂鸣 (1kHz 200ms) — 验证 OK
    time.sleep(0.5)
    audio_beep(1000, 200)
    print("🔊 开机蜂鸣 OK, 等待仙女座连接...")
    
    # 主循环 — 保持活着
    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()
