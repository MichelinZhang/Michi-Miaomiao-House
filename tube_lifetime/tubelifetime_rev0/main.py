# main.py
import sys
import json
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSpinBox, QFileDialog, QFrame,
                             QTabWidget, QDialog, QFormLayout, QDoubleSpinBox, 
                             QDialogButtonBox, QButtonGroup, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

import config
from ui_components import IOSCard, ModernButton, SlidingStackedWidget, Toast, ForceGauge, CounterWidget, RealTimeChart
from ui_flow import FlowEditor
from ui_manual import ManualPanel
from driver import CylinderDriver
from worker import ExecutorWorker
from utils import prevent_sleep

# --- 监控线程：专门负责后台读取状态 ---
class MonitorThread(QThread):
    sig_status = pyqtSignal(dict, dict) # 发送 A, B 缸状态

    def __init__(self, drv_a, drv_b):
        super().__init__()
        self.drv_a = drv_a
        self.drv_b = drv_b
        self.running = True
        self.paused = False # 自动运行时暂停监控，避免抢锁

    def run(self):
        while self.running:
            if not self.paused:
                try:
                    # 获取状态，这里如果报错也不会崩UI
                    sa = self.drv_a.get_status()
                    sb = self.drv_b.get_status()
                    self.sig_status.emit(sa if sa else {}, sb if sb else {})
                except Exception:
                    pass
            
            # 控制刷新率 10Hz
            time.sleep(0.1)

    def stop(self):
        self.running = False
        self.wait()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能电缸控制系统 Ultimate (Pro)")
        self.resize(1200, 800)
        
        # 1. 初始化硬件
        self.drv_a = CylinderDriver("COM3")
        self.drv_b = CylinderDriver("COM4")
        self.max_speed = config.DEFAULT_MAX_SPEED
        self.current_seq_data = [] # 存储当前运行的流程副本，用于界面显示
        
        # 2. 初始化核心线程
        self.worker = None
        self.monitor = MonitorThread(self.drv_a, self.drv_b)
        self.monitor.sig_status.connect(self.on_monitor_update)

        prevent_sleep(True)
        self.setup_ui()
        self.setup_connections()

        # Toast 提示层
        self.toast = Toast(self)

        # 3. 延时连接硬件，避免启动白屏
        QTimer.singleShot(100, self.connect_hardware)

    def connect_hardware(self):
        self.toast.show_msg("正在连接硬件...", 0)
        ok_a = self.drv_a.connect()
        ok_b = self.drv_b.connect()
        if ok_a and ok_b:
            self.toast.show_msg("硬件连接成功", 2000)
            self.monitor.start() # 连接成功后开启监控
        else:
            self.toast.show_msg("硬件连接失败，进入仿真模式", 3000)
            self.monitor.start()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(20)
        
        # === 左侧控制栏 ===
        left_layout = QVBoxLayout()
        
        # 1. 标题
        left_layout.addWidget(QLabel("智能电缸控制系统", styleSheet="font-size:20px; font-weight:bold; margin-bottom:10px;"))

        # 2. 计数器
        self.counter_widget = CounterWidget()
        left_layout.addWidget(self.counter_widget)
        
        # 3. 控制按钮区
        ctrl_card = IOSCard()
        l_ctrl = QVBoxLayout(ctrl_card)
        l_ctrl.setSpacing(12)
        
        # 循环设置
        h_cycle = QHBoxLayout()
        h_cycle.addWidget(QLabel("目标次数:"))
        self.spin_cycles = QSpinBox(); self.spin_cycles.setRange(1, 99999); self.spin_cycles.setValue(100)
        self.spin_cycles.setFixedHeight(30)
        h_cycle.addWidget(self.spin_cycles)
        l_ctrl.addLayout(h_cycle)

        # 按钮组：使用 Grid 布局 2x2
        btn_grid = QGridLayout()
        
        self.btn_run = ModernButton("▶ 开始", config.COLOR_GREEN)
        self.btn_pause = ModernButton("II 暂停", "#FF9500") # 橙色
        self.btn_stop = ModernButton("■ 停止", config.COLOR_RED)
        self.btn_reset = ModernButton("⟳ 复位", config.COLOR_BLUE)
        
        # 初始状态
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        
        btn_grid.addWidget(self.btn_run, 0, 0)
        btn_grid.addWidget(self.btn_pause, 0, 1)
        btn_grid.addWidget(self.btn_stop, 1, 0)
        btn_grid.addWidget(self.btn_reset, 1, 1)
        
        l_ctrl.addLayout(btn_grid)
        left_layout.addWidget(ctrl_card)

        # 4. 导航菜单
        nav_card = IOSCard()
        l_nav = QVBoxLayout(nav_card)
        l_nav.addWidget(QLabel("视图切换", styleSheet="color:#888; font-size:12px;"))
        
        self.btn_view_monitor = ModernButton("📊 运行监控", config.COLOR_BLUE)
        self.btn_view_editor = ModernButton("📝 流程编排", config.COLOR_BG, config.COLOR_TEXT)
        self.btn_view_manual = ModernButton("🎮 手动调试", config.COLOR_BG, config.COLOR_TEXT)
        
        l_nav.addWidget(self.btn_view_monitor)
        l_nav.addWidget(self.btn_view_editor)
        l_nav.addWidget(self.btn_view_manual)
        left_layout.addWidget(nav_card)
        
        left_layout.addStretch()
        
        # 简单的状态字（替代原来的大Log）
        self.lbl_status_tiny = QLabel("系统就绪")
        self.lbl_status_tiny.setStyleSheet("color:#AAA; font-size:12px;")
        left_layout.addWidget(self.lbl_status_tiny)

        root_layout.addLayout(left_layout, 25)

        # === 右侧内容区 (多页面) ===
        self.stack = SlidingStackedWidget()
        
        # >> 页面1: 监控仪表盘 (Dashboard) <<
        self.page_monitor = QWidget()
        lay_mon = QVBoxLayout(self.page_monitor)
        
        # 顶部：仪表盘区域
        dash_card = IOSCard()
        h_dash = QHBoxLayout(dash_card)
        h_dash.setContentsMargins(20, 40, 20, 40)
        
        self.gauge_a = ForceGauge("A缸 A-Cylinder", config.COLOR_BLUE)
        self.gauge_b = ForceGauge("B缸 B-Cylinder", config.COLOR_GREEN)
        
        h_dash.addStretch()
        h_dash.addWidget(self.gauge_a)
        h_dash.addStretch() # 增加一点间距
        h_dash.addWidget(self.gauge_b)
        h_dash.addStretch()
        
        lay_mon.addWidget(dash_card, 30) # 调整占比
        
        # 中部：实时曲线图
        self.chart = RealTimeChart()
        lay_mon.addWidget(self.chart, 40)
        
        # 底部：详细状态区域
        status_box = IOSCard()
        lay_status = QVBoxLayout(status_box)
        lay_status.setContentsMargins(20, 20, 20, 20)
        
        lay_status.addWidget(QLabel("当前步骤详情 (Current Step):", styleSheet="font-weight:bold; font-size:16px; color:#888;"))
        
        self.lbl_current_step = QLabel("等待开始...\nWaiting to start")
        self.lbl_current_step.setStyleSheet("""
            font-family: "Microsoft YaHei UI"; 
            font-size: 20px; 
            color: #1C1C1E; 
            font-weight: bold; 
            line-height: 1.5;
        """)
        self.lbl_current_step.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_current_step.setWordWrap(True)
        
        lay_status.addWidget(self.lbl_current_step)
        lay_mon.addWidget(status_box, 30)
        
        self.stack.addWidget(self.page_monitor)

        # >> 页面2: 流程编辑器 <<
        self.page_editor = QWidget()
        lay_edit = QVBoxLayout(self.page_editor)
        
        # 编辑器工具栏
        tool_card = IOSCard()
        tool_bar = QHBoxLayout(tool_card)
        tool_bar.setContentsMargins(10,10,10,10)
        tool_bar.addWidget(QLabel("流程编排", styleSheet="font-weight:bold; font-size:18px;"))
        tool_bar.addStretch()
        
        for name, code, color in [("+ A缸", "MOVE_A", config.COLOR_BLUE), 
                                  ("+ B缸", "MOVE_B", config.COLOR_GREEN), 
                                  ("+ 延时", "DELAY", "#FF9500")]: 
            btn = ModernButton(name, color)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda _, t=code: self.flow_editor.add_step(t))
            tool_bar.addWidget(btn)
        
        btn_save = ModernButton("💾", config.COLOR_BG, config.COLOR_TEXT)
        btn_save.setFixedWidth(40); btn_save.clicked.connect(self.save_flow)
        tool_bar.addWidget(btn_save)
        
        btn_load = ModernButton("📂", config.COLOR_BG, config.COLOR_TEXT)
        btn_load.setFixedWidth(40); btn_load.clicked.connect(self.load_flow)
        tool_bar.addWidget(btn_load)

        lay_edit.addWidget(tool_card)
        
        self.flow_editor = FlowEditor()
        self.flow_editor.setStyleSheet("QListWidget { border: none; background: transparent; }")
        lay_edit.addWidget(self.flow_editor)
        
        self.stack.addWidget(self.page_editor)

        # >> 页面3: 手动模式 <<
        self.manual_panel = ManualPanel(self.drv_a, self.drv_b)
        self.stack.addWidget(self.manual_panel)

        root_layout.addWidget(self.stack, 75)
        
    def closeEvent(self, event):
        """ [Robustness] 窗口关闭时安全停止所有线程，防止后台残留或报错 """
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        
        if self.monitor and self.monitor.isRunning():
            self.monitor.stop()
            self.monitor.wait()
        event.accept()

    def setup_connections(self):
        # 导航切换
        self.btn_view_monitor.clicked.connect(lambda: self.switch_view(0))
        self.btn_view_editor.clicked.connect(lambda: self.switch_view(1))
        self.btn_view_manual.clicked.connect(lambda: self.switch_view(2))

        # 运行控制
        self.btn_run.clicked.connect(self.action_run)
        self.btn_pause.clicked.connect(self.action_pause)
        self.btn_stop.clicked.connect(self.action_stop)
        self.btn_reset.clicked.connect(self.action_reset)

    def switch_view(self, idx):
        # [关键优化] 动画锁：如果正在动画，禁止切换，防止闪退
        if self.stack.is_animating():
            return

        # [Robustness] 运行时禁止切换视图，防止进入手动模式导致硬件冲突
        # 通过判断 btn_run 是否被禁用（运行时被禁用）来确定状态
        if not self.btn_run.isEnabled() and idx != 0:
            return

        # 更新按钮样式
        btns = [self.btn_view_monitor, self.btn_view_editor, self.btn_view_manual]
        for i, btn in enumerate(btns):
            if i == idx:
                btn.bg_color = config.COLOR_BLUE
                btn.text_color = "white"
            else:
                btn.bg_color = config.COLOR_BG
                btn.text_color = config.COLOR_TEXT
            btn.update_style()
        self.stack.slideInIdx(idx)

    def on_monitor_update(self, sa, sb):
        # [关键优化] 动画锁：切屏时暂停数据刷新，彻底解决卡顿
        if self.stack.is_animating():
            return

        # 1. 更新仪表盘 (传递 3 个值: 实测力, 输出力, 位移)
        # 使用 .get() 防止字典键不存在导致报错
        self.gauge_a.set_values(
            sa.get('force_real', 0.0), 
            sa.get('force_out', 0.0), 
            sa.get('pos', 0.0)
        )
        self.gauge_b.set_values(
            sb.get('force_real', 0.0), 
            sb.get('force_out', 0.0), 
            sb.get('pos', 0.0)
        )
        
        # 2. 更新曲线图
        self.chart.append_data(sa.get('force_real', 0.0), sb.get('force_real', 0.0))
        
        # 3. 如果在手动页，更新手动面板
        if self.stack.currentWidget() == self.manual_panel:
            self.manual_panel.update_ui(sa, sb)

    def action_run(self):
        seq = self.flow_editor.get_sequence()
        if not seq: 
            self.toast.show_msg("流程为空！")
            return
        
        # [NEW] 保存流程数据副本用于显示
        self.current_seq_data = seq

        # 自动切到监控页
        self.switch_view(0)
        
        # 暂停监控线程，改由 Worker 主动汇报
        self.monitor.paused = True
        
        # 数据拷贝
        final_seq = [s.copy() for s in seq]

        self.worker = ExecutorWorker(self.drv_a, self.drv_b, final_seq, self.spin_cycles.value())
        # 连接信号
        self.worker.sig_progress.connect(self.counter_widget.update_count) # 连接计数器
        self.worker.sig_step.connect(self.update_step_display) # 连接步骤显示
        self.worker.sig_finished.connect(self.on_finished)
        self.worker.sig_log.connect(lambda s: self.lbl_status_tiny.setText(s)) # 只在左下角显示简单Log
        
        # 连接自动运行时的实时数据
        self.worker.sig_realtime.connect(self.on_monitor_update)
        
        self.worker.start()
        self.update_btn_state(running=True)
        self.toast.show_msg("测试已启动")

    def update_step_display(self, idx):
        """ [NEW] 详细显示当前步骤信息 """
        if idx >= len(self.current_seq_data): return
        
        step = self.current_seq_data[idx]
        stype = step['type']
        
        # Rich Text Formatting for Dashboard
        if stype == "MOVE_A":
            color = config.COLOR_BLUE
            title = "A-Cylinder Moving"
            details = f"""
            <div style='margin-top:10px;'>
                <b>Target:</b> {step['pos']} <span style='color:#888'>mm</span> &nbsp;|&nbsp; 
                <b>Speed:</b> {step['speed']} <span style='color:#888'>mm/s</span><br>
                <b>Force Limit:</b> {step.get('force', 30)} <span style='color:#888'>%</span>
            </div>
            """
        elif stype == "MOVE_B":
            color = config.COLOR_GREEN
            title = "B-Cylinder Moving"
            details = f"""
            <div style='margin-top:10px;'>
                <b>Target:</b> {step['pos']} <span style='color:#888'>mm</span> &nbsp;|&nbsp; 
                <b>Speed:</b> {step['speed']} <span style='color:#888'>mm/s</span><br>
                <b>Force Limit:</b> {step.get('force', 30)} <span style='color:#888'>%</span>
            </div>
            """
        elif stype == "DELAY":
            color = "#FF9500"
            title = "Waiting..."
            details = f"<div style='margin-top:10px; font-size:20px;'><b>Time:</b> {step['time']} <span style='color:#888'>s</span></div>"
            
        html = f"""
        <div style='font-family: "Segoe UI", sans-serif;'>
            <div style='color:{color}; font-size:18px; font-weight:bold; margin-bottom:5px;'>{title}</div>
            <div style='font-size:24px; color:#333; font-weight:bold;'>
                Step {idx+1} <span style='font-size:16px; color:#999; font-weight:normal;'>/ {len(self.current_seq_data)}</span>
            </div>
            {details}
        </div>
        """
        self.lbl_current_step.setText(html)

    def action_pause(self):
        if self.worker:
            if self.worker.paused:
                self.worker.resume()
                self.btn_pause.setText("II 暂停")
                self.btn_pause.bg_color = "#FF9500" 
            else:
                self.worker.pause()
                self.btn_pause.setText("▶ 继续")
                self.btn_pause.bg_color = config.COLOR_GREEN 
            self.btn_pause.update_style()

    def action_stop(self):
        if self.worker:
            self.worker.stop()
            self.lbl_status_tiny.setText("正在停止...")
            self.toast.show_msg("正在请求停止...")

    def action_reset(self):
        # 只有停止时才能复位
        self.counter_widget.update_count(0, self.spin_cycles.value())
        self.lbl_current_step.setText("已复位\nReady")
        self.lbl_status_tiny.setText("计数已复位")
        self.toast.show_msg("计数已复位")

    def on_finished(self):
        self.update_btn_state(running=False)
        self.lbl_current_step.setText("测试完成\nFinished")
        self.lbl_status_tiny.setText("运行结束")
        self.toast.show_msg("运行结束", 3000)
        self.monitor.paused = False # 恢复监控

    def update_btn_state(self, running):
        self.btn_run.setEnabled(not running)
        self.btn_reset.setEnabled(not running)
        
        # [Robustness] 运行时禁用所有视图切换，确保用户停留在监控页
        self.btn_view_editor.setEnabled(not running)
        self.btn_view_manual.setEnabled(not running)
        self.btn_view_monitor.setEnabled(not running)
        
        self.btn_pause.setEnabled(running)
        self.btn_stop.setEnabled(running)
        
    def save_flow(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存", "", "JSON (*.json)")
        if path:
            try:
                with open(path, 'w') as f: json.dump(self.flow_editor.get_sequence(), f)
                self.toast.show_msg("保存成功")
            except Exception as e:
                self.toast.show_msg(f"保存失败: {e}")

    def load_flow(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开", "", "JSON (*.json)")
        if path:
            try:
                with open(path, 'r') as f: self.flow_editor.load_sequence(json.load(f))
                self.toast.show_msg("流程已加载")
            except Exception as e:
                self.toast.show_msg(f"加载失败: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(config.GLOBAL_STYLESHEET)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())