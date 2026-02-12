# ui_manual.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QDoubleSpinBox, QGroupBox)
from PyQt6.QtCore import Qt
from ui_components import IOSCard, ModernButton
import config

class CylinderManualCard(IOSCard):
    """ 单个电缸的手动控制卡片 """
    def __init__(self, title, driver, color_theme):
        super().__init__()
        self.driver = driver
        
        layout = QVBoxLayout(self)
        
        # 标题栏
        header = QHBoxLayout()
        lbl_icon = QLabel("●")
        lbl_icon.setStyleSheet(f"color: {color_theme}; font-size: 18px;")
        header.addWidget(lbl_icon)
        header.addWidget(QLabel(title, styleSheet="font-weight: bold; font-size: 16px;"))
        layout.addLayout(header)

        # 实时数据显示
        self.lbl_pos = QLabel("0.00 mm")
        self.lbl_pos.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color_theme};")
        self.lbl_force = QLabel("0.0 %")
        
        info_grid = QGridLayout()
        info_grid.addWidget(QLabel("实时位置:"), 0, 0)
        info_grid.addWidget(self.lbl_pos, 0, 1)
        info_grid.addWidget(QLabel("实时力度:"), 1, 0)
        info_grid.addWidget(self.lbl_force, 1, 1)
        layout.addLayout(info_grid)

        # 控制区
        ctrl_box = QGroupBox("点动控制")
        ctrl_box.setStyleSheet("border:1px solid #E5E5EA; border-radius:8px; margin-top:10px; padding-top:10px;")
        grid = QGridLayout(ctrl_box)
        
        # 输入参数
        self.spin_target = QDoubleSpinBox(); self.spin_target.setSuffix(" mm"); self.spin_target.setRange(0, 500)
        self.spin_speed = QDoubleSpinBox(); self.spin_speed.setSuffix(" %"); self.spin_speed.setValue(20)
        
        grid.addWidget(QLabel("目标位置:"), 0, 0)
        grid.addWidget(self.spin_target, 0, 1)
        grid.addWidget(QLabel("速度:"), 1, 0)
        grid.addWidget(self.spin_speed, 1, 1)

        # 按钮
        btn_home = ModernButton("回零", config.COLOR_SUBTEXT)
        btn_home.clicked.connect(self.cmd_home)
        
        btn_move = ModernButton("执行", color_theme)
        btn_move.clicked.connect(self.cmd_move)
        
        btn_stop = ModernButton("急停", config.COLOR_RED)
        btn_stop.clicked.connect(self.cmd_stop)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_home)
        btn_row.addWidget(btn_move)
        btn_row.addWidget(btn_stop)
        
        layout.addWidget(ctrl_box)
        layout.addLayout(btn_row)

    def update_status(self, data):
        if data:
            # --- 【修复】使用 .get() 方法，防止 KeyError ---
            # 即使 data 里没有 pos 或 force，也不会闪退，而是显示 0.0
            pos = data.get('pos', 0.0)
            force = data.get('force', 0.0)
            
            self.lbl_pos.setText(f"{pos:.2f} mm")
            self.lbl_force.setText(f"{force:.1f} %")

    def cmd_home(self):
        if self.driver: self.driver.home_cylinder()

    def cmd_move(self):
        if self.driver:
            # 简单移动，不带推压
            self.driver.move(self.spin_target.value(), self.spin_speed.value(), 30)

    def cmd_stop(self):
        if self.driver: self.driver.stop_motion()

class ManualPanel(QWidget):
    def __init__(self, drv_a, drv_b):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        
        self.card_a = CylinderManualCard("电缸 A (左)", drv_a, config.COLOR_BLUE)
        self.card_b = CylinderManualCard("电缸 B (右)", drv_b, config.COLOR_GREEN)
        
        layout.addWidget(self.card_a)
        layout.addWidget(self.card_b)

    def update_ui(self, data_a, data_b):
        self.card_a.update_status(data_a)
        self.card_b.update_status(data_b)