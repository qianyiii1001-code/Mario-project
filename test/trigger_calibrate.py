"""
并口 Trigger 校准脚本 ── 逐个发送已知 code，确认 BrainProducts 实际录到的值。
用法:
    1. 启动 BrainProducts 录制
    2. 以管理员运行: python trigger_calibrate.py
    3. 观察终端打印的 code，与 BP 录制值对比
    4. 如果 BP 录到的值与发送值不一致，记录下映射关系
"""
import ctypes
import time

_PORT = 0x3FF8  # ← 你的并口地址
_PULSE_MS = 20  # 校准用更长脉宽，确保 BP 一定抓到

# ── 加载驱动 ──
_inpout = None
for dll in ("inpoutx64.dll", "inpout32.dll"):
    try:
        _inpout = ctypes.WinDLL(dll)
        print(f"[OK] 加载 {dll}")
        break
    except OSError:
        pass

if _inpout is None:
    print("[FATAL] 未找到 inpout 驱动")
    exit(1)

# 验证并口可访问
try:
    _inpout.Inp32(_PORT)
    print(f"[OK] 并口 0x{_PORT:04X} 可访问")
except Exception as e:
    print(f"[FATAL] 并口访问失败: {e}")
    exit(1)

_write = getattr(_inpout, "DlPortWritePortUchar", None)
if _write is None:
    _write = _inpout.Out32
    print("[INFO] 使用 Out32（16位写），无 DlPortWritePortUchar")
else:
    print("[OK] 使用 DlPortWritePortUchar（8位写）")


def pulse(code, duration_ms=_PULSE_MS):
    """发送单个 trigger 脉冲"""
    _write(_PORT, code)
    time.sleep(duration_ms / 1000.0)
    _write(_PORT, 0)
    time.sleep(0.05)  # 脉冲间 50ms 间隔
    print(f"  -> 已发送 code={code:3d}  (0x{code:02X}  二进制 {code:08b})")


# ==========================================
# 第一轮: 逐位测试（找出每根数据线对应 BP 的 bit）
# ==========================================
print("\n" + "=" * 60)
print("第1轮: 单 bit 测试 —— 一次只拉高一根数据线")
print("=" * 60)
bits = [1, 2, 4, 8, 16, 32, 64, 128]
for b in bits:
    input(f"\n按回车发送 code={b:3d} (bit {bits.index(b)}) ...")
    pulse(b)

# ==========================================
# 第二轮: 全高 + 全低
# ==========================================
print("\n" + "=" * 60)
print("第2轮: 全高/全低 测试")
print("=" * 60)
input("\n按回车发送 code=255 (全高) ...")
pulse(255)
input("\n按回车发送 code=0 (全低/归零) ...")
pulse(0)

# ==========================================
# 第三轮: 当前 TRIGGER 表中你实际会用的 code
# ==========================================
print("\n" + "=" * 60)
print("第3轮: 实验用 Trigger Code 验证")
print("=" * 60)
trigger_codes = {
    "EXPERIMENT_END": 1,
    "BLOCK_START": 10,
    "BLOCK_END": 11,
    "REST_START": 20,
    "REST_END": 21,
    "CUE_START": 30,
    "CUE_END": 31,
    "READY": 40,
    "COUNTDOWN_START": 50,
    "COUNTDOWN_END": 51,
    "MI_START": 60,
    "MI_END": 61,
    "FEEDBACK_START": 70,
    "FEEDBACK_END": 71,
    "COIN_EATEN": 80,
}
for name, code in trigger_codes.items():
    input(f"\n按回车发送 {name:20s} code={code:3d} ...")
    pulse(code)

print("\n" + "=" * 60)
print("校准完成！")
print("请停止 BP 录制，对比终端打印的 code 与 BP 录制值。")
print("=" * 60)
