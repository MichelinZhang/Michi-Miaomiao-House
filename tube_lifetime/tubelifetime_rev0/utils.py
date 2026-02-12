# utils.py
import ctypes

def prevent_sleep(enable=True):
    """
    防止 Windows 进入睡眠或关闭屏幕
    ES_CONTINUOUS: 通知系统状态设置是持续性的
    ES_SYSTEM_REQUIRED: 防止系统睡眠
    ES_DISPLAY_REQUIRED: 防止屏幕关闭
    """
    try:
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002
        
        if enable:
            # 阻止睡眠 + 阻止熄屏
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
            print("系统电源设置: 已启用防熄屏模式")
        else:
            # 恢复默认
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            print("系统电源设置: 已恢复默认")
    except Exception as e:
        print(f"电源设置失败: {e}")