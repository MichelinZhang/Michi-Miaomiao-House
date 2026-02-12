# ui_flow.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QListWidgetItem, QLabel, QDoubleSpinBox, QSpinBox, 
                             QPushButton, QGridLayout, QFrame)
from PyQt6.QtCore import Qt, QSize
from ui_components import IOSCard
import config

class StepCardWidget(IOSCard):
    def __init__(self, step_type, params=None):
        super().__init__()
        self.step_type = step_type
        
        # Main Layout: Vertical (Header + Body)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- 1. Header Section ---
        header = QFrame()
        header.setFixedHeight(32)
        
        # Determine Color & Title
        if "A" in step_type:
            bg_color, title_text = config.COLOR_BLUE, "Cylinder A Action"
        elif "B" in step_type:
            bg_color, title_text = config.COLOR_GREEN, "Cylinder B Action"
        else:
            bg_color, title_text = "#FF9500", "System Delay"
            
        header.setStyleSheet(f"background-color: {bg_color}; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10, 0, 10, 0)
        
        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet("color: white; font-weight: bold; font-size: 13px;")
        
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(24, 24)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet("QPushButton { color: rgba(255,255,255,0.8); border: none; font-weight: bold; } QPushButton:hover { color: white; }")
        btn_del.clicked.connect(self.delete_me)
        
        h_layout.addWidget(lbl_title)
        h_layout.addStretch()
        h_layout.addWidget(btn_del)
        
        main_layout.addWidget(header)

        # --- 2. Body Section ---
        body = QWidget()
        body_layout = QGridLayout(body)
        body_layout.setContentsMargins(15, 12, 15, 12)
        body_layout.setVerticalSpacing(10)
        body_layout.setHorizontalSpacing(15)

        # Init Controls
        self.spin_pos = self._make_spin(" mm", 0, 9999)
        self.spin_speed = self._make_spin(" mm/s", 1, 1000)
        self.spin_force = self._make_spin(" %", 1, 100)
        self.spin_push = self._make_spin(" mm", 0, 50)
        self.spin_time = self._make_spin(" s", 0, 9999)

        if "MOVE" in step_type:
            # Row 1: Motion
            self._add_field(body_layout, 0, 0, "Target Pos", self.spin_pos)
            self._add_field(body_layout, 0, 1, "Speed", self.spin_speed)
            
            # Row 2: Limits
            self._add_field(body_layout, 1, 0, "Force Limit", self.spin_force)
            self._add_field(body_layout, 1, 1, "Push Dist", self.spin_push)

            # Defaults
            if params:
                self.spin_pos.setValue(params.get('pos', 10.0))
                self.spin_speed.setValue(params.get('speed', 50.0))
                self.spin_force.setValue(params.get('force', 30.0))
                self.spin_push.setValue(params.get('push', 0.0))
            else:
                self.spin_pos.setValue(10.0); self.spin_speed.setValue(20.0)
                self.spin_force.setValue(30.0); self.spin_push.setValue(0.0)
                
            self.spin_time.hide()
        else:
            # Delay
            self._add_field(body_layout, 0, 0, "Duration", self.spin_time)
            self.spin_time.setValue(params.get('time', 1.0) if params else 1.0)
            for w in [self.spin_pos, self.spin_speed, self.spin_force, self.spin_push]: w.hide()

        main_layout.addWidget(body)

    def _make_spin(self, suffix, min_val, max_val):
        sb = QDoubleSpinBox()
        sb.setSuffix(suffix)
        sb.setRange(min_val, max_val)
        sb.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        sb.setStyleSheet("QDoubleSpinBox { border: 1px solid #E5E5EA; border-radius: 6px; padding: 4px; background: #F2F2F7; } QDoubleSpinBox:focus { border: 1px solid #007AFF; background: white; }")
        sb.setFixedHeight(30)
        return sb

    def _add_field(self, layout, row, col, label_text, widget):
        container = QWidget()
        v = QVBoxLayout(container)
        v.setContentsMargins(0,0,0,0)
        v.setSpacing(4)
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #8E8E93; font-size: 10px; font-weight: bold; text-transform: uppercase;")
        v.addWidget(lbl)
        v.addWidget(widget)
        layout.addWidget(container, row, col)

    def delete_me(self):
        list_w = self.parent().parent()
        if isinstance(list_w, QListWidget):
            for i in range(list_w.count()):
                if list_w.itemWidget(list_w.item(i)) == self:
                    list_w.takeItem(i)
                    break

    def get_data(self):
        if "MOVE" in self.step_type:
            return {
                "type": self.step_type,
                "pos": self.spin_pos.value(),
                "speed": self.spin_speed.value(), # 现在的单位是 mm/s
                "force": self.spin_force.value(), # 找回了力度
                "push": self.spin_push.value()    # 找回了推压距离
            }
        return {"type": "DELAY", "time": self.spin_time.value()}

class FlowEditor(QListWidget):
    def __init__(self):
        super().__init__()
        self.setSpacing(12) # 卡片间距

    def add_step(self, type_name, params=None):
        item = QListWidgetItem(self)
        # 根据类型调整卡片高度，MOVE类型有两行，需要高一点
        height = 170 if "MOVE" in type_name else 110
        item.setSizeHint(QSize(0, height))
        
        card = StepCardWidget(type_name, params)
        self.setItemWidget(item, card)
        self.scrollToBottom()

    def get_sequence(self):
        seq = []
        for i in range(self.count()):
            w = self.itemWidget(self.item(i))
            if w: seq.append(w.get_data())
        return seq

    def load_sequence(self, data):
        self.clear()
        for step in data:
            self.add_step(step['type'], step)