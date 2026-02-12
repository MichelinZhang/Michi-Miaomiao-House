# driver.py
import minimalmodbus
import time
import random
from PyQt6.QtCore import QMutex
from config import SIMULATION_MODE

class CylinderDriver:
    def __init__(self, port, slave_id=1):
        self.port = port
        self.instrument = None
        self.connected = False
        self.lock = QMutex()
        
        # --- 仿真参数 ---
        self._sim_pos = 0.0
        self._sim_target = 0.0
        self._sim_speed = 10.0
        self._last_update_time = time.time()
        
        # [NEW] 区分 输出力(Set) 和 受力(Real)
        self._sim_force_out = 0.0 # 输出力
        self._sim_force_real = 0.0 # 实际受力

    def connect(self):
        if SIMULATION_MODE:
            self.connected = True
            return True
        try:
            self.instrument = minimalmodbus.Instrument(self.port, 1)
            self.instrument.serial.baudrate = 115200
            self.instrument.serial.timeout = 0.1
            self.connected = True
            return True
        except:
            return False

    def disconnect(self):
        self.connected = False
        if self.instrument:
            try: self.instrument.serial.close()
            except: pass

    def move(self, pos, speed, force_limit):
        """发送运动指令"""
        if SIMULATION_MODE:
            self._sim_target = float(pos)
            self._sim_speed = max(1.0, float(speed))
            # 记录设定的输出力限制
            self._sim_force_out = float(force_limit) 
            self._last_update_time = time.time()
        else:
            self.lock.lock()
            try:
                pass
                # self.instrument.write_register(...)
            except: pass
            finally: self.lock.unlock()

    def get_status(self):
        """获取当前位置和状态"""
        if SIMULATION_MODE:
            current_time = time.time()
            dt = current_time - self._last_update_time
            self._last_update_time = current_time
            
            # 1. 计算位移
            move_step = self._sim_speed * dt
            diff = self._sim_target - self._sim_pos
            
            if abs(diff) < move_step: 
                self._sim_pos = self._sim_target
                reached = True
                # 到位后，实际受力变小，输出力保持
                self._sim_force_real = random.uniform(0.0, 2.0)
            else: 
                direction = 1.0 if diff > 0 else -1.0
                self._sim_pos += direction * move_step
                reached = False
                # 运动中，实际受力在 50% ~ 80% 的输出力之间波动
                base_load = self._sim_force_out * 0.6
                self._sim_force_real = base_load + random.uniform(-5.0, 5.0)

            return {
                'pos': self._sim_pos, 
                'reached': reached,
                'force_real': abs(self._sim_force_real), # 实际受力
                'force_out': self._sim_force_out         # 设定/输出力
            }
        
        self.lock.lock()
        try:
            # 真实返回: 请根据实际寄存器修改
            return {'pos': 0.0, 'reached': True, 'force_real': 0.0, 'force_out': 0.0} 
        except: return None
        finally: self.lock.unlock()