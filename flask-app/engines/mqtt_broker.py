#!/usr/bin/env python3
"""
仙女座 MQTT Broker v2 — 带连接日志 + 详细调试
"""
import asyncio, struct, sys, time
from datetime import datetime

HOST, PORT = "0.0.0.0", 1883
subscriptions = {}
connections = 0

def ts():
    return datetime.now().strftime("%H:%M:%S")

def mqtt_read_int(data, off):
    mult = 1; total = 0; i = 0
    while i < 4:
        b = data[off + i]
        total += (b & 0x7F) * mult
        if (b & 0x80) == 0: break
        mult *= 128; i += 1
    return total, off + i + 1

def encode_remaining_length(n):
    out = []
    while True:
        byte = n % 128; n //= 128
        if n > 0: byte |= 0x80
        out.append(byte)
        if n == 0: break
    return bytes(out)

async def handle_client(reader, writer):
    global connections
    connections += 1
    addr = writer.get_extra_info("peername")
    conn_id = connections
    print(f"[{ts()}] 🟢 NEW #{conn_id}  from {addr} (total={connections})")
    
    try:
        while True:
            header = await reader.read(1)
            if not header: break
            ptype = (header[0] >> 4) & 0xF
            
            rl_bytes = bytearray()
            while True:
                b = await reader.read(1)
                if not b: return
                rl_bytes.append(b[0])
                if (b[0] & 0x80) == 0: break
            rl, _ = mqtt_read_int(bytes(rl_bytes), 0)
            
            payload = b''
            if rl > 0:
                payload = await reader.read(rl)
            
            if ptype == 1:  # CONNECT
                # 解析 client_id
                client_id = ""
                if len(payload) > 10:
                    try:
                        id_len = struct.unpack(">H", payload[8:10])[0]
                        client_id = payload[10:10+id_len].decode(errors="replace")
                    except: pass
                print(f"[{ts()}] � #{conn_id} CONNECT client_id='{client_id}'")
                writer.write(b'\x20\x02\x00\x00'); await writer.drain()  # CONNACK 0
            
            elif ptype == 8:  # SUBSCRIBE
                sub_pkt_id = struct.unpack(">H", payload[:2])[0]
                topics = []; i = 2
                while i < len(payload):
                    tl = struct.unpack(">H", payload[i:i+2])[0]
                    topic = payload[i+2:i+2+tl].decode()
                    qos = payload[i+2+tl]
                    topics.append(topic)
                    subscriptions.setdefault(topic, []).append((addr, writer))
                    i += 3 + tl
                print(f"[{ts()}] 📥 #{conn_id} SUBSCRIBE {topics}")
                suback = b'\x90' + encode_remaining_length(len(topics)+2) + struct.pack(">H", sub_pkt_id) + bytes(topics)
                writer.write(suback); await writer.drain()
            
            elif ptype == 3:  # PUBLISH
                off = 2
                tl = struct.unpack(">H", payload[:2])[0]
                topic = payload[2:2+tl].decode()
                content = payload[2+tl:]
                preview = content[:80].decode(errors="replace")
                print(f"[{ts()}] 📤 #{conn_id} PUBLISH [{topic}] {preview}")
                
                for tpat, subs in subscriptions.items():
                    if tpat == topic or (tpat.endswith("/#") and topic.startswith(tpat[:-2])):
                        for a, w in subs:
                            try:
                                pub = b'\x30' + encode_remaining_length(len(payload)) + payload
                                w.write(pub); await w.drain()
                            except Exception: pass
            
            elif ptype == 12:  # PINGREQ
                writer.write(b'\xD0\x00'); await writer.drain()
            
            elif ptype == 14:  # DISCONNECT
                print(f"[{ts()}] 🔴 #{conn_id} DISCONNECT")
                break
            
    except Exception as e:
        print(f"[{ts()}] ❌ #{conn_id} {type(e).__name__}: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    print(f"📡 仙女座 MQTT Broker v2  [{ts()}]")
    print(f"   监听 {HOST}:{PORT} · 带连接日志 · Ctrl+C 退出\n", flush=True)
    
    server = await asyncio.start_server(handle_client, HOST, PORT)
    print(f"   ✅ 已启动, 等待连接...\n", flush=True)
    
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n👋 [{ts()}] 退出")
