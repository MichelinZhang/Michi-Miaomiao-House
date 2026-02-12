# worker.py
from PyQt6.QtCore import QThread, pyqtSignal, QWaitCondition, QMutex
import time

class ExecutorWorker(QThread):
    sig_log = pyqtSignal(str)
    sig_step = pyqtSignal(int)         # 当前步骤索引
    sig_progress = pyqtSignal(int, int)# (当前循环, 总循环)
    sig_finished = pyqtSignal()
    sig_status_change = pyqtSignal(str) # 运行状态
    
    # --- 新增：实时数据信号 (A缸状态, B缸状态) ---
    sig_realtime = pyqtSignal(dict, dict) 

    def __init__(self, driver_a, driver_b, sequence, cycles):
        super().__init__()
        self.drv_a = driver_a
        self.drv_b = driver_b
        self.sequence = sequence
        self.total_cycles = cycles
        self.running = True
        
        # 暂停控制
        self.paused = False
        self.mutex = QMutex()
        self.cond = QWaitCondition()

    def pause(self):
        self.mutex.lock()
        self.paused = True
        self.mutex.unlock()
        self.sig_status_change.emit("PAUSED")
        self.sig_log.emit(">>> 流程已暂停")

    def resume(self):
        self.mutex.lock()
        self.paused = False
        self.cond.wakeAll()
        self.mutex.unlock()
        self.sig_status_change.emit("RUNNING")
        self.sig_log.emit(">>> 流程继续")

    def stop(self):
        self.running = False
        self.resume()
        self.wait()

    def check_pause(self):
        self.mutex.lock()
        if self.paused:
            self.cond.wait(self.mutex)
        self.mutex.unlock()

    def run(self):
        self.sig_status_change.emit("RUNNING")
        self.sig_log.emit(f"开始执行，总计 {self.total_cycles} 次循环")
        
        for cycle in range(1, self.total_cycles + 1):
            if not self.running: break
            self.check_pause()
            
            self.sig_log.emit(f"=== 第 {cycle} 次循环 ===")
            self.sig_progress.emit(cycle, self.total_cycles)

            for idx, step in enumerate(self.sequence):
                if not self.running: break
                self.check_pause()
                
                self.sig_step.emit(idx)
                step_type = step['type']
                
                # 获取设定力度，默认30%
                force_limit = step.get('force', 30)

                if step_type == "MOVE_A":
                    self.sig_log.emit(f"步骤 {idx+1}: A缸 > {step['pos']}mm")
                    self.drv_a.move(step['pos'], step['speed'], force_limit)
                    # 等待 A 到位
                    if not self.wait_for_arrival(self.drv_a, step['pos']): break
                    
                elif step_type == "MOVE_B":
                    self.sig_log.emit(f"步骤 {idx+1}: B缸 > {step['pos']}mm")
                    self.drv_b.move(step['pos'], step['speed'], force_limit)
                    # 等待 B 到位
                    if not self.wait_for_arrival(self.drv_b, step['pos']): break
                    
                elif step_type == "DELAY":
                    t = step['time']
                    self.sig_log.emit(f"步骤 {idx+1}: 延时 {t}s")
                    # 细分延时
                    for _ in range(int(t * 10)):
                        if not self.running: break
                        self.check_pause()
                        # --- 修复：延时期间也要刷新 UI，否则力值会卡住 ---
                        self.report_status() 
                        time.sleep(0.1)

            if not self.running: break
            time.sleep(0.5)

        self.sig_finished.emit()
        self.sig_status_change.emit("STOPPED")

    def report_status(self):
        """读取并发送当前状态"""
        # 即使只动一个缸，也要读两个缸的状态，保证界面数据完整
        # 注意：在真实高频通讯中，这里可能需要优化频率，但在10Hz下没问题
        sa = self.drv_a.get_status()
        sb = self.drv_b.get_status()
        self.sig_realtime.emit(sa if sa else {}, sb if sb else {})
        return sa, sb

    def wait_for_arrival(self, active_driver, target_pos):
        """等待到位"""
        start_t = time.time()
        while self.running:
            self.check_pause()
            
            if time.time() - start_t > 30: # 超时 30s
                self.sig_log.emit("错误: 动作超时")
                return False
            
            # --- 修复：调用 report_status 刷新 UI ---
            sa, sb = self.report_status()
            
            # 判断当前驱动是否到位
            current_status = sa if active_driver == self.drv_a else sb
            
            if current_status and current_status.get('reached', False):
                # 再次校验位置误差
                if abs(current_status.get('pos', 0) - target_pos) < 1.0:
                    return True
            
            time.sleep(0.1)
        return False