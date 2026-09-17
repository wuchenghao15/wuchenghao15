# -*- coding: utf-8 -*-
"""
SZU100 U盘钥匙检测驱动（v2 - ioreg BSD映射版）
==================================================
区分真SZU100钥匙和普通U盘改名伪造：
1. USB硬件VID/PID（硬件级别，无法通过OS改名伪造）
2. CD-ROM仿真检测（真SZU100为CD-ROM设备，普通U盘无法仿真）
3. USB制造商名称（硬件级别）
4. USB序列号
5. U盘根目录 .szu100_auth 认证文件（含预共享密钥SHA256）

检测原理：
- 通过 ioreg 将磁盘BSD名称(disk9)映射到USB设备(VID/PID/制造商/序列号)
- 通过 mount 命令获取挂载点和文件系统类型
- 真SZU100: CD-ROM仿真 + 指定VID/PID + 认证文件
- 假SZU100: 普通U盘改名，非CD-ROM，VID/PID不匹配
"""
import os
import re
import hashlib
import subprocess
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# ===== SZU100 合法性配置 =====
# 预共享密钥（写入U盘 .szu100_auth 文件）
_SZU100_PSK = b'MTSCOS_SZU100_SECURE_KEY_2026_v1'
_SZU100_AUTH_FILENAME = '.szu100_auth'

# 合法SZU100的USB硬件特征（多组兼容）
# 真SZU100: VID=0x0305 PID=0x5030 制造商=CD-ROM（CD-ROM仿真设备）
_SZU100_VALID_VID_PID = [
    (0x0305, 0x5030),   # SZU100 CD-ROM仿真版（实际硬件）
    (0x8817, 0x100F),   # SZU100 标准版（legacy）
    (0x8817, 0x1010),   # SZU100 Pro版（legacy）
]
# 合法制造商（小写匹配）
_SZU100_VALID_MANUFACTURERS = ['cd-rom', 'szu tech', 'mtscos secureusb', 'szu']
# 卷标/挂载点名关键词
_SZU100_VALID_PRODUCT_NAMES = ['szu100', 'szu-100', 'szu_100']
# 合法序列号前缀（真SZU100序列号以SZU开头，兼容2603开头）
_SZU100_SERIAL_PREFIXES = ['SZU', '2603']
# 合法容量范围（MB）：最小64MB，最大8192MB（区分普通大容量U盘）
_SZU100_MIN_SIZE_MB = 64
_SZU100_MAX_SIZE_MB = 8192

# 缓存检测结果（3秒内不重复检测）
_detect_cache = {'ts': 0, 'data': None}
_CACHE_TTL = 3.0


def _run_cmd(cmd, timeout=5):
    """安全执行命令"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else ''
    except Exception:
        return ''


def _run_cmd_bytes(cmd, timeout=5):
    """安全执行命令（返回bytes，用于ioreg含非UTF8字符的情况）"""
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return r.stdout.decode('utf-8', errors='ignore') if r.returncode == 0 else ''
    except Exception:
        return ''


def _parse_ioreg_disk_usb_mapping():
    """
    通过 ioreg 将磁盘BSD名称映射到USB设备信息。
    策略：先找到所有 "BSD Name" = "diskN" 行，再从该行反向搜索最近的USB设备信息。
    返回: {bsd_name: {vid, pid, manufacturer, product_name, serial, ...}}
    """
    raw = _run_cmd_bytes(['ioreg', '-l', '-w', '0'])
    if not raw:
        return {}

    lines = raw.split('\n')
    mapping = {}

    def _extract_usb_field(key, text, cast=str):
        """从 ioreg 行中提取字段值"""
        m = re.search(r'"' + key + r'"\s*=\s*([^,}\n]+)', text)
        if m:
            val = m.group(1).strip().strip('"')
            try:
                return cast(val)
            except Exception:
                return val
        return None

    # 找到所有 "BSD Name" = "diskN" 的行号（只匹配 diskN，不匹配 diskNsM 分区）
    bsd_lines = []
    for i, line in enumerate(lines):
        m = re.search(r'"BSD Name"\s*=\s*"(disk\d+)"', line)
        if m:
            bsd_lines.append((i, m.group(1)))

    # 对每个BSD Name，反向搜索最近的USB设备信息
    for bsd_idx, bsd_name in bsd_lines:
        usb_info = {}
        # 反向搜索最多150行，找到USB Device Info或独立字段
        search_start = max(0, bsd_idx - 150)
        for j in range(bsd_idx, search_start - 1, -1):
            jline = lines[j].strip()

            # 找到 USB Device Info（包含所有字段）
            if '"USB Device Info"' in jline and 'vid' not in usb_info:
                info_str = jline.split('=', 1)[-1].strip()
                vid = _extract_usb_field('idVendor', info_str, int)
                pid = _extract_usb_field('idProduct', info_str, int)
                mfr = _extract_usb_field('kUSBVendorString', info_str)
                prod = _extract_usb_field('kUSBProductString', info_str)
                ser = _extract_usb_field('kUSBSerialNumberString', info_str)
                if vid is not None:
                    usb_info['vid'] = vid
                if pid is not None:
                    usb_info['pid'] = pid
                if mfr:
                    usb_info['manufacturer'] = mfr
                if prod:
                    usb_info['product_name'] = prod
                if ser:
                    usb_info['serial'] = ser
                break  # USB Device Info 包含所有信息，找到即可停止

            # 独立字段提取（备用）
            if '"idVendor"' in jline and 'vid' not in usb_info:
                val = _extract_usb_field('idVendor', jline, int)
                if val is not None:
                    usb_info['vid'] = val
            if '"idProduct"' in jline and 'pid' not in usb_info:
                val = _extract_usb_field('idProduct', jline, int)
                if val is not None:
                    usb_info['pid'] = val
            if '"kUSBVendorString"' in jline and 'manufacturer' not in usb_info:
                val = _extract_usb_field('kUSBVendorString', jline)
                if val:
                    usb_info['manufacturer'] = val
            if '"kUSBProductString"' in jline and 'product_name' not in usb_info:
                val = _extract_usb_field('kUSBProductString', jline)
                if val:
                    usb_info['product_name'] = val
            if '"kUSBSerialNumberString"' in jline and 'serial' not in usb_info:
                val = _extract_usb_field('kUSBSerialNumberString', jline)
                if val:
                    usb_info['serial'] = val

            # 如果已收集到vid，可以停止
            if 'vid' in usb_info and 'pid' in usb_info:
                break

        if usb_info:
            mapping[bsd_name] = usb_info

    return mapping


def _get_mount_info():
    """
    通过 mount 命令获取设备→挂载点映射。
    返回: {device: {mount_point, volume_name, is_cdrom, is_readonly, fs_type}}
    """
    raw = _run_cmd(['mount'])
    if not raw:
        return {}

    mounts = {}
    for line in raw.split('\n'):
        # 格式: /dev/disk9s0 on /Volumes/SZU100 (cd9660, local, nodev, nosuid, read-only, noowners)
        m = re.match(r'^(\/dev\/\S+)\s+on\s+(\/Volumes\/\S+)\s+\((.+)\)', line)
        if not m:
            continue
        dev = m.group(1)
        mount_point = m.group(2)
        fs_info = m.group(3)

        # 从设备名提取父磁盘（disk9s0 → disk9）
        parent_disk = re.match(r'(\/dev\/disk\d+)', dev)
        parent_disk = parent_disk.group(1) if parent_disk else dev

        mounts[dev] = {
            'mount_point': mount_point,
            'volume_name': os.path.basename(mount_point),
            'fs_type': fs_info.split(',')[0].strip() if fs_info else '',
            'is_cdrom': 'cd9660' in fs_info,
            'is_readonly': 'read-only' in fs_info,
            'parent_disk': parent_disk,
        }
    return mounts


def _parse_diskutil_external():
    """通过 diskutil list external 解析外部磁盘（补充信息）"""
    raw = _run_cmd(['diskutil', 'list', 'external'])
    if not raw:
        return []
    disks = []
    current_disk = None
    for line in raw.split('\n'):
        line_stripped = line.strip()
        if line_stripped.startswith('/dev/disk'):
            if current_disk:
                disks.append(current_disk)
            parts = line_stripped.split()
            dev = parts[0] if parts else ''
            size_str = ''
            for p in parts:
                if 'GB' in p or 'MB' in p or 'TB' in p:
                    size_str = p
                    break
            current_disk = {'device': dev, 'size_str': size_str, 'name': '', 'fstype': '', 'partitions': []}
        elif current_disk and line_stripped:
            # 跳过表头
            if line_stripped.startswith('#:'):
                continue
            # 解析分区行: "1: CD_ROM_Mode_1 SZU100 2.4 GB disk9s0"
            # 格式: #: TYPE NAME SIZE IDENTIFIER
            part_match = re.match(r'^\d+:\s+(.+)', line_stripped)
            if part_match:
                rest = part_match.group(1).strip()
                # 从右向左找SIZE（如 "2.4 GB"）和IDENTIFIER（如 disk9s0）
                parts = rest.split()
                if len(parts) >= 2:
                    # IDENTIFIER是最后一个
                    identifier = parts[-1]
                    # SIZE是倒数第二+第三（如 "2.4 GB"）
                    size = ''
                    name = ''
                    fstype = ''
                    if len(parts) >= 3 and (parts[-2] in ('GB', 'MB', 'TB') or parts[-2] == '*'):
                        size = parts[-2]
                        if parts[-2] in ('GB', 'MB', 'TB'):
                            size = parts[-3] + ' ' + parts[-2] if len(parts) >= 4 else parts[-2]
                        # TYPE和NAME在前面
                        type_name_parts = parts[:-3] if len(parts) >= 4 else parts[:-2]
                    else:
                        type_name_parts = parts[:-1]

                    # TYPE可能含空格（如 "Apple_APFS Container"），NAME紧随其后
                    # 简化：如果TYPE是已知类型，NAME是剩下的
                    full_str = ' '.join(type_name_parts)
                    # 尝试匹配已知类型
                    known_types = ['Apple_APFS', 'EFI', 'Microsoft Reserved', 'GUID_partition_scheme',
                                   'CD_partition_scheme', 'CD_ROM_Mode_1', 'Apple_HFS', 'MS-DOS']
                    fstype = ''
                    name = ''
                    for kt in known_types:
                        if full_str.startswith(kt):
                            fstype = kt
                            name = full_str[len(kt):].strip()
                            break
                    if not fstype:
                        # 无法确定，取第一个词为TYPE
                        if type_name_parts:
                            fstype = type_name_parts[0]
                            name = ' '.join(type_name_parts[1:]).strip()

                    current_disk['partitions'].append({
                        'fstype': fstype,
                        'name': name,
                        'size': size,
                        'identifier': identifier,
                    })
                    # 如果分区有名称，更新磁盘名称
                    if name and not current_disk['name']:
                        current_disk['name'] = name
                        current_disk['fstype'] = fstype
    if current_disk:
        disks.append(current_disk)
    return disks


def _get_mount_points():
    """获取所有挂载点 /Volumes/* """
    mounts = []
    try:
        for entry in os.listdir('/Volumes'):
            full = os.path.join('/Volumes', entry)
            if os.path.ismount(full):
                mounts.append(full)
    except Exception:
        pass
    return mounts


def _check_auth_file(mount_path):
    """检查U盘根目录的 .szu100_auth 认证文件"""
    auth_file = os.path.join(mount_path, _SZU100_AUTH_FILENAME)
    if not os.path.exists(auth_file):
        return False, 'auth_file_missing'
    try:
        with open(auth_file, 'rb') as f:
            content = f.read().strip()
        expected_hash = hashlib.sha256(_SZU100_PSK).hexdigest()
        if content.decode('utf-8', errors='ignore').strip() == expected_hash:
            return True, 'auth_ok'
        return False, 'auth_hash_mismatch'
    except Exception as e:
        return False, f'auth_read_error: {e}'


def _parse_size_mb(size_str):
    """解析容量字符串为MB"""
    if not size_str:
        return 0
    try:
        if 'TB' in size_str:
            return float(size_str.replace('TB', '').replace('*', '').strip()) * 1024 * 1024
        elif 'GB' in size_str:
            return float(size_str.replace('GB', '').replace('*', '').strip()) * 1024
        elif 'MB' in size_str:
            return float(size_str.replace('MB', '').replace('*', '').strip())
        return 0
    except Exception:
        return 0


def detect_szu100():
    """
    检测SZU100 U盘钥匙（v2 - ioreg BSD映射版）
    返回: {
        'present': bool,           # 是否检测到SZU100设备
        'is_authentic': bool,      # 是否为合法SZU100（非改名U盘）
        'devices': [...],          # 检测到的设备列表
        'auth_status': str,        # 认证状态
        'details': {...}           # 详细信息
    }
    """
    now = time.time()
    if _detect_cache['data'] and (now - _detect_cache['ts']) < _CACHE_TTL:
        return _detect_cache['data']

    # 1. 获取USB设备→磁盘BSD映射
    disk_usb_map = _parse_ioreg_disk_usb_mapping()

    # 2. 获取挂载点信息
    mount_info = _get_mount_info()

    # 3. 获取外部磁盘信息（补充容量等）
    external_disks = _parse_diskutil_external()
    disk_size_map = {}
    for d in external_disks:
        dev_name = d.get('device', '').replace('/dev/', '')
        disk_size_map[dev_name] = _parse_size_mb(d.get('size_str', ''))

    szu100_devices = []
    authentic_szu100 = None
    all_checked_devices = set()

    # 4. 检查所有USB磁盘设备
    for bsd_name, usb_info in disk_usb_map.items():
        all_checked_devices.add(bsd_name)
        vid = usb_info.get('vid')
        pid = usb_info.get('pid')
        manufacturer = (usb_info.get('manufacturer') or '').lower()
        usb_product = (usb_info.get('product_name') or '').lower()
        serial = usb_info.get('serial') or ''

        # 查找对应的挂载点
        device_mount = None
        for dev, minfo in mount_info.items():
            if bsd_name in dev or dev.startswith(f'/dev/{bsd_name}'):
                device_mount = minfo
                break

        # 获取卷标名
        volume_name = device_mount['volume_name'] if device_mount else ''
        volume_name_lower = volume_name.lower()

        # 也从diskutil获取卷标名（备用）
        if not volume_name:
            for d in external_disks:
                if d.get('device', '').endswith(bsd_name):
                    volume_name = d.get('name', '')
                    volume_name_lower = volume_name.lower()
                    break

        # 检查各项匹配
        name_match = any(kw in volume_name_lower for kw in _SZU100_VALID_PRODUCT_NAMES)

        vid_pid_match = False
        if vid is not None and pid is not None:
            vid_pid_match = (vid, pid) in _SZU100_VALID_VID_PID

        mfr_match = any(mfr in manufacturer for mfr in _SZU100_VALID_MANUFACTURERS)

        serial_match = any(serial.upper().startswith(pfx) for pfx in _SZU100_SERIAL_PREFIXES) if serial else False

        # CD-ROM检测（重要安全特征）
        is_cdrom = device_mount['is_cdrom'] if device_mount else False

        size_mb = disk_size_map.get(bsd_name, 0)
        size_match = _SZU100_MIN_SIZE_MB <= size_mb <= _SZU100_MAX_SIZE_MB

        # 判断合法性
        # 硬件特征匹配（VID/PID + 制造商）：这是无法伪造的
        hardware_authentic = vid_pid_match or mfr_match
        # CD-ROM + 名称匹配 = 可能是真SZU100
        cdrom_name_match = is_cdrom and name_match
        # 卷标名匹配但硬件不匹配 = 伪造
        name_only_match = name_match and not hardware_authentic and not is_cdrom

        device_info = {
            'device': f'/dev/{bsd_name}',
            'bsd_name': bsd_name,
            'volume_name': volume_name,
            'size_mb': round(size_mb, 1),
            'vid': vid,
            'pid': pid,
            'manufacturer': usb_info.get('manufacturer', ''),
            'usb_product_name': usb_info.get('product_name', ''),
            'serial': serial,
            'is_cdrom': is_cdrom,
            'fs_type': device_mount['fs_type'] if device_mount else '',
            'mount_point': device_mount['mount_point'] if device_mount else '',
            'name_match': name_match,
            'vid_pid_match': vid_pid_match,
            'mfr_match': mfr_match,
            'serial_match': serial_match,
            'size_match': size_match,
            'hardware_authentic': hardware_authentic,
            'cdrom_name_match': cdrom_name_match,
            'is_fake': name_only_match,
        }

        # 判断认证状态
        if hardware_authentic or cdrom_name_match:
            # 硬件认证通过
            if is_cdrom:
                # CD-ROM设备（只读，无法写入auth文件）：CD-ROM + 硬件特征 = 认证通过
                # 真SZU100是CD-ROM仿真设备，普通U盘无法仿真CD-ROM，这是强安全特征
                device_info['auth_ok'] = True
                device_info['auth_reason'] = 'cdrom_hardware_verified'
                device_info['is_authentic'] = True
                authentic_szu100 = device_info
            elif device_mount and device_mount.get('mount_point'):
                # 非CD-ROM但硬件匹配：检查认证文件（可写U盘场景）
                auth_ok, auth_reason = _check_auth_file(device_mount['mount_point'])
                device_info['auth_ok'] = auth_ok
                device_info['auth_reason'] = auth_reason
                if auth_ok:
                    device_info['is_authentic'] = True
                    authentic_szu100 = device_info
                else:
                    device_info['is_authentic'] = False
            else:
                device_info['is_authentic'] = False
                device_info['auth_reason'] = 'mount_not_found'
        elif name_only_match:
            # 卷标改名但硬件不匹配且非CD-ROM → 伪造
            device_info['is_authentic'] = False
            device_info['auth_reason'] = 'fake_renamed_usb'
            device_info['is_fake'] = True
        else:
            device_info['is_authentic'] = False
            device_info['auth_reason'] = 'not_szu100'

        szu100_devices.append(device_info)

    # 5. 构建返回结果
    has_any = len(szu100_devices) > 0
    has_authentic = authentic_szu100 is not None
    has_fake = any(d.get('is_fake') for d in szu100_devices)

    result = {
        'present': has_any,
        'is_authentic': has_authentic,
        'has_fake_detected': has_fake,
        'devices': szu100_devices,
        'authentic_device': authentic_szu100,
        'auth_status': 'authentic' if has_authentic else ('fake_detected' if has_fake else 'not_found'),
        'timestamp': datetime.now().isoformat(),
        '_source': 'szu100_driver_v2',
    }

    _detect_cache['ts'] = now
    _detect_cache['data'] = result
    return result


def get_szu100_status_summary():
    """获取SZU100状态摘要（简洁版）"""
    d = detect_szu100()
    return {
        'present': d['present'],
        'authentic': d['is_authentic'],
        'fake_detected': d['has_fake_detected'],
        'status': d['auth_status'],
        'device_count': len(d['devices']),
        'serial': (d.get('authentic_device') or {}).get('serial', ''),
        'manufacturer': (d.get('authentic_device') or {}).get('manufacturer', ''),
        'timestamp': d['timestamp'],
    }


def init_auth_file(mount_path):
    """初始化SZU100认证文件（仅在注册新钥匙时调用）"""
    auth_file = os.path.join(mount_path, _SZU100_AUTH_FILENAME)
    expected_hash = hashlib.sha256(_SZU100_PSK).hexdigest()
    try:
        with open(auth_file, 'w') as f:
            f.write(expected_hash)
        return True, 'auth_file_created'
    except Exception as e:
        return False, str(e)
