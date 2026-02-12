import time
import threading
import logging
from driver import CylinderDriver

class TestEngine:
    def __init__(self, broadcast_func):
        """
        :param broadcast_func: async function(type, payload) to send WS messages
        """
        self.broadcast = broadcast_func
        self.drv_a = CylinderDriver("COM3")
        self.drv_b = CylinderDriver("COM4")
        
        self.running = False
        self.paused = False
        self.main_thread = None
        self.monitor_thread = None
        
        # 初始化连接
        self.drv_a.connect()
        self.drv_b.connect()
        
        # 启动后台监控线程 (10Hz)
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def start_sequence(self, sequence, total_cycles):
        if self.running: return
        self.running = True
        self.paused = False
        # 在独立线程运行流程，避免阻塞 API
        self.main_thread = threading.Thread(target=self._run_logic, args=(sequence, total_cycles), daemon=True)
        self.main_thread.start()
        self.broadcast("status", {"state": "RUNNING"})

    def stop(self):
        self.running = False
        self.broadcast("status", {"state": "STOPPED"})
        self.broadcast("log", "🛑 用户请求停止")

    def pause_resume(self):
        self.paused = not self.paused
        state = "PAUSED" if self.paused else "RUNNING"
        self.broadcast("status", {"state": state})
        self.broadcast("log", f"{'⏸️ 暂停' if self.paused else '▶️ 继续'} 测试")

    def _monitor_loop(self):
        """高频读取硬件状态并推送"""
        while True:
            try:
                sa = self.drv_a.get_status() or {}
                sb = self.drv_b.get_status() or {}
                # 推送遥测数据 (Telemetry)
                self.broadcast("telemetry", {"cylA": sa, "cylB": sb})
            except Exception as e:
                logging.error(f"Monitor error: {e}")
            time.sleep(0.1) # 10Hz 刷新率

    def _run_logic(self, sequence, total_cycles):
        self.broadcast("log", f"🚀 测试开始，目标循环: {total_cycles} 次")
        
        for cycle in range(1, total_cycles + 1):
            if not self.running: break
            
            # 暂停等待
            while self.paused and self.running: time.sleep(0.2)

            self.broadcast("progress", {"current": cycle, "total": total_cycles})
            self.broadcast("log", f"=== 循环 {cycle} / {total_cycles} ===")

            for idx, step in enumerate(sequence):
                if not self.running: break
                while self.paused and self.running: time.sleep(0.2)

                self.broadcast("step_update", {"step_idx": idx})
                
                step_type = step.get('type')
                force = step.get('force', 30)
                
                # --- 动作执行 ---
                if step_type == "MOVE_A":
                    self.broadcast("log", f"[步骤 {idx+1}] A缸 -> {step['pos']}mm")
                    self.drv_a.move(step['pos'], step['speed'], force)
                    if not self._wait_arrival(self.drv_a, step['pos']): break
                    
                elif step_type == "MOVE_B":
                    self.broadcast("log", f"[步骤 {idx+1}] B缸 -> {step['pos']}mm")
                    self.drv_b.move(step['pos'], step['speed'], force)
                    if not self._wait_arrival(self.drv_b, step['pos']): break
                    
                elif step_type == "DELAY":
                    t = step.get('time', 1.0)
                    self.broadcast("log", f"[步骤 {idx+1}] 延时 {t}s")
                    # 细分延时以支持快速停止
                    end_time = time.time() + t
                    while time.time() < end_time:
                        if not self.running: break
                        time.sleep(0.1)

        self.running = False
        self.broadcast("status", {"state": "FINISHED"})
        self.broadcast("log", "✅ 测试流程结束")

    def _wait_arrival(self, driver, target, timeout=30):
        start = time.time()
        while self.running:
            s = driver.get_status()
            if s and s['reached'] and abs(s['pos'] - target) < 1.0:
                return True
            if time.time() - start > timeout:
                self.broadcast("log", "❌ 错误: 动作超时")
                return False
            time.sleep(0.05)
        return False