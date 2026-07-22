#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_trigger.py —— 并口 TTL Trigger 测试工具

功能: 连续发送几个不同 code 的 TTL 脉冲，验证并口硬件是否正常工作。

使用方法 (以管理员身份运行):
    python test_trigger.py

依赖:
    无需安装任何第三方 Python 包，仅需 InpOut 驱动:
        1. 下载 InpOutBinaries: http://www.highrez.co.uk/downloads/inpout32/
        2. 解压后将 inpout32.dll (32位) 或 inpoutx64.dll (64位) 放到 C:\Windows\System32\

常见并口地址:
    LPT1 = 0x0378 (默认)
    LPT2 = 0x0278
    LPT3 = 0x03BC
    PCI扩展卡常见: 0x3FF8, 0xDF00 等
    在 设备管理器 > 端口(COM和LPT) > LPT端口 > 资源 中确认。

硬件验证:
    有示波器/逻辑分析仪: 连接到并口 D0-D7 数据线 + GND 观察脉冲。
    简易验证: 在并口 D0 和 GND 间接一个 LED + 1kΩ 限流电阻，
              低 codes (1,2,4,8...) 应能看到 LED 闪烁。
"""

import ctypes
import time

# ── 并口初始化 ──────────────────────────────────────────────────
# ★ 根据你的实际硬件修改此地址 ★
LPT_ADDRESS = 0x3FF8

inpout = None
try:
    inpout = ctypes.WinDLL("inpoutx64.dll")
    print(f"[驱动] 加载 inpoutx64.dll (64位)")
except OSError:
    pass

if inpout is None:
    try:
        inpout = ctypes.WinDLL("inpout32.dll")
        print(f"[驱动] 加载 inpout32.dll (32位)")
    except OSError:
        pass

if inpout is None:
    print(f"[FAIL] 驱动未找到!")
    print()
    print("解决方法:")
    print("  1. 下载 InpOutBinaries (http://www.highrez.co.uk/downloads/inpout32/)")
    print("  2. 解压后将 inpout32.dll 或 inpoutx64.dll 放到 C:\\Windows\\System32\\")
    print("  3. 以管理员身份重新运行")
    print()
    print("将以纯日志模式运行（不发送硬件信号）...")
else:
    try:
        # 验证并口可访问
        inpout.Inp32(LPT_ADDRESS)
        print(f"[OK] 并口初始化成功: 地址 0x{LPT_ADDRESS:04X}")
        print(f"     请确认示波器/LED 已连接到并口数据线 D0-D7")
    except Exception as e:
        print(f"[FAIL] 并口访问失败: {e}")
        print("请确认: 1) 以管理员运行  2) 地址正确")
        inpout = None

print()
port_ok = inpout is not None


# ── Trigger 编码表 (与 mario_v3_0_1.py 保持一致) ──────────────
TRIGGER = {
    "EXPERIMENT_END":       1,
    "BLOCK_START":         10,
    "BLOCK_END":           11,
    "REST_BLOCK_START":    12,
    "REST_BLOCK_END":      13,
    "REST_START":          20,
    "REST_END":            21,
    "CUE_START":           30,
    "CUE_END":             31,
    "READY":               40,
    "COUNTDOWN_START":     50,
    "COUNTDOWN_END":       51,
    "MI_START":            60,
    "MI_END":              61,
    "FEEDBACK_START":      70,
    "FEEDBACK_END":        71,
    "COIN_EATEN":          80,
}


def send_trigger(code, duration_ms=5):
    """发送单个 TTL 脉冲: Out32(code) → 保持 duration_ms → Out32(0)"""
    if port_ok:
        try:
            inpout.Out32(LPT_ADDRESS, code)
            time.sleep(duration_ms / 1000.0)
            inpout.Out32(LPT_ADDRESS, 0)
            print(f"  [SENT] code={code:3d} (0x{code:02X}), pulse={duration_ms}ms  ✓")
        except Exception as e:
            print(f"  [ERR]  code={code:3d} → 发送失败: {e}")
    else:
        time.sleep(duration_ms / 1000.0)
        print(f"  [SIM]  code={code:3d} (0x{code:02X}), pulse={duration_ms}ms  (模拟)")


# ── 连续发送测试序列 ──────────────────────────────────────────
print("=" * 60)
print("  TTL Trigger 连续发送测试")
print("=" * 60)
print()

# 测试 1: 逐个发送所有 trigger code
print(">>> 测试1: 遍历所有 Trigger 编码 (间隔 500ms)")
print("-" * 40)
for name, code in sorted(TRIGGER.items(), key=lambda x: x[1]):
    print(f"  {name:20s} → code={code:3d}")
    send_trigger(code, duration_ms=5)
    time.sleep(0.5)
print()

# 测试 2: 快速连续脉冲 (类 trial 序列)
print(">>> 测试2: 模拟一个 Trial 的完整 Trigger 序列")
print("-" * 40)
simulated_sequence = [
    ("REST_START",      TRIGGER["REST_START"]),
    ("REST_END",        TRIGGER["REST_END"]),
    ("CUE_START",       TRIGGER["CUE_START"]),
    ("CUE_END",         TRIGGER["CUE_END"]),
    ("READY",           TRIGGER["READY"]),
    ("COUNTDOWN_START", TRIGGER["COUNTDOWN_START"]),
    ("COUNTDOWN_END",   TRIGGER["COUNTDOWN_END"]),
    ("MI_START",        TRIGGER["MI_START"]),
    ("MI_END",          TRIGGER["MI_END"]),
    ("FEEDBACK_START",  TRIGGER["FEEDBACK_START"]),
    ("COIN_EATEN",      TRIGGER["COIN_EATEN"]),
    ("FEEDBACK_END",    TRIGGER["FEEDBACK_END"]),
]
for name, code in simulated_sequence:
    print(f"  {name:20s} → code={code:3d}")
    send_trigger(code, duration_ms=5)
    time.sleep(0.3)
print()

# 测试 3: 短脉冲 vs 默认脉冲
print(">>> 测试3: 不同脉宽对比")
print("-" * 40)
for duration in [1, 3, 5, 10]:
    print(f"  脉宽={duration:2d}ms ...")
    send_trigger(TRIGGER["MI_START"], duration_ms=duration)
    time.sleep(0.5)
print()

# 测试 4: 快速连续相同 code
print(">>> 测试4: 快速连续相同 code (5Hz)")
print("-" * 40)
for i in range(5):
    send_trigger(TRIGGER["COIN_EATEN"], duration_ms=5)
    time.sleep(0.2)
print()

print("=" * 60)
print("  测试完成！")
if port_ok:
    print("  请确认示波器上观察到了对应宽度的脉冲波形。")
else:
    print("  并口未就绪，以上为纯日志模拟。请修复并口后重试。")
print("=" * 60)
