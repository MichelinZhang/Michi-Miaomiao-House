import minimalmodbus
import time
import random
import threading

# 全局仿真开关 (如果没有连接真实硬件，请保持为 True)
SIMULATION_MODE = True

class CylinderDriver:
    def __init__(self, port, slave_id=1):
        self.port = port
        self.slave_id = slave_id
        self.instrument = None
        self.connected = False
        self.lock = threading.Lock()  # 替代 QMutex
        
        # --- 仿真参数 ---
        self._sim_pos = 0.0
        self._sim_target = 0.0
        self._sim_speed = 10.0
        self._last_update_time = time.time()
        self._sim_force_out = 0.0
        self._sim_force_real = 0.0

    def connect(self):
        if SIMULATION_MODE:
            self.connected = True
            print(f"[{self.port}] Simulation Connected")
            return True
        try:
            # [修复] 使用局部变量 'inst' 先进行配置
            # 这样 Pylance 就知道 inst 是 Instrument 类型，而不是 None
            inst = minimalmodbus.Instrument(self.port, self.slave_id)
            inst.serial.baudrate = 115200
            inst.serial.timeout = 0.1
            
            # 配置成功后，再赋值给成员变量
            self.instrument = inst
            self.connected = True
            print(f"[{self.port}] Connected Successfully")
            return True
        except Exception as e:
            print(f"[{self.port}] Connection Failed: {e}")
            self.connected = False
            return False

    def disconnect(self):
        self.connected = False
        # [修复] 先判断是否为 None，再尝试关闭
        if self.instrument:
            try: 
                self.instrument.serial.close()
            except: 
                pass
        self.instrument = None

    def move(self, pos, speed, force_limit):
        """发送运动指令 (线程安全)"""
        if SIMULATION_MODE:
            with self.lock:
                self._sim_target = float(pos)
                self._sim_speed = max(1.0, float(speed))
                self._sim_force_out = float(force_limit)
                self._last_update_time = time.time()
        else:
            with self.lock:
                try:
                    # [修复] 增加非空检查
                    if self.instrument:
                        # 假设寄存器地址为 0 (请根据实际硬件手册修改地址和功能码)
                        # self.instrument.write_float(0, float(pos)) 
                        pass
                except Exception as e:
                    print(f"Move Error: {e}")

    def get_status(self):
        """获取状态 (线程安全)"""
        if SIMULATION_MODE:
            with self.lock:
                current_time = time.time()
                dt = current_time - self._last_update_time
                self._last_update_time = current_time
                
                # 物理仿真计算
                move_step = self._sim_speed * dt
                diff = self._sim_target - self._sim_pos
                
                reached = False
                if abs(diff) < move_step:
                    self._sim_pos = self._sim_target
                    reached = True
                    # 到位后受力随机波动 (0-2%)
                    self._sim_force_real = random.uniform(0.0, 2.0)
                else:
                    direction = 1.0 if diff > 0 else -1.0
                    self._sim_pos += direction * move_step
                    # 运动中受力 (50-70% 输出力)
                    base_load = self._sim_force_out * 0.6
                    self._sim_force_real = base_load + random.uniform(-5.0, 5.0)

                return {
                    'pos': self._sim_pos,
                    'reached': reached,
                    'force_real': abs(self._sim_force_real),
                    'force_out': self._sim_force_out
                }
        
        with self.lock:
            try:
                # 真实读取逻辑 (示例)
                if self.instrument:
                    # pos = self.instrument.read_float(0)
                    return {'pos': 0.0, 'reached': True, 'force_real': 0.0, 'force_out': 0.0}
                return None
            except:
                return None