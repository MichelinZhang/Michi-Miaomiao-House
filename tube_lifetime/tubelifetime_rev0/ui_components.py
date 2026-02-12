# ui_components.py
from PyQt6.QtWidgets import (QFrame, QPushButton, QGraphicsDropShadowEffect, QProgressBar,
                             QLabel, QStackedWidget, QWidget, QHBoxLayout, 
                             QVBoxLayout)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer, QParallelAnimationGroup, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QCursor, QPainterPath
import config

class IOSCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 15))
        self.setGraphicsEffect(shadow)

class ModernButton(QPushButton):
    def __init__(self, text, bg_color=config.COLOR_BLUE, text_color="white"):
        super().__init__(text)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(40) # 固定高度，防止错位
        
        self.bg_color = bg_color
        self.text_color = text_color
        self.update_style()

    def update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.bg_color};
                color: {self.text_color};
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {QColor(self.bg_color).lighter(110).name()}; }}
            QPushButton:pressed {{ background-color: {QColor(self.bg_color).darker(110).name()}; }}
            QPushButton:disabled {{ background-color: #D1D1D6; color: #8E8E93; }}
        """)

    def setAlpha(self, alpha):
        # 简单通过禁用状态来实现视觉变灰，不仅是透明度
        self.setEnabled(alpha > 0.8)
    
class SlidingStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.m_direction = Qt.Orientation.Horizontal
        self.m_speed = 800 # 动画时长 ms
        self.m_animation_type = QEasingCurve.Type.OutCubic # 丝滑曲线
        self.m_now = 0
        self.m_next = 0
        self.m_wrap = False
        self.m_pnow = QPoint(0, 0)
        self.m_active = False

    def slideInIdx(self, idx):
        if idx > self.count() - 1:
            idx = idx % self.count()
            self.m_wrap = True
        
        self.slideInWgt(self.widget(idx))

    def slideInWgt(self, newwidget):
        if self.m_active: return
        self.m_active = True
        
        _now = self.currentWidget()
        _next = newwidget
        if _now == _next:
            self.m_active = False
            return

        offsetx, offsety = self.frameRect().width(), self.frameRect().height()
        self.widget(self.indexOf(_next)).setGeometry(0, 0, offsetx, offsety)
        
        # 这里的逻辑是简单的推拉效果
        if self.indexOf(_next) > self.indexOf(_now):
            offsetx = offsetx
            offsety = 0
        else:
            offsetx = -offsetx
            offsety = 0

        pnext = _next.pos()
        pnow = _now.pos()
        self.m_pnow = pnow

        # 动画组
        self.anim_group = QParallelAnimationGroup()
        
        anim_now = QPropertyAnimation(_now, b"pos")
        anim_now.setDuration(self.m_speed)
        anim_now.setEasingCurve(self.m_animation_type)
        anim_now.setStartValue(QPoint(pnow.x(), pnow.y()))
        anim_now.setEndValue(QPoint(pnow.x() - offsetx, pnow.y() + offsety))
        
        anim_next = QPropertyAnimation(_next, b"pos")
        anim_next.setDuration(self.m_speed)
        anim_next.setEasingCurve(self.m_animation_type)
        anim_next.setStartValue(QPoint(pnext.x() + offsetx, pnext.y() + offsety))
        anim_next.setEndValue(QPoint(pnext.x(), pnext.y()))
        
        self.anim_group.addAnimation(anim_now)
        self.anim_group.addAnimation(anim_next)
        
        self.anim_group.finished.connect(self.animationDoneSlot)
        self.anim_group.start()
        
        _next.show()
        _next.raise_()
        self.setCurrentWidget(_next)

    def animationDoneSlot(self):
        self.setCurrentWidget(self.currentWidget())
        self.m_active = False

# --- 新增：Toast 消息提示 (替代生硬的 Label) ---
class Toast(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QHBoxLayout(self)
        self.lbl = QLabel("")
        self.lbl.setStyleSheet("""
            background-color: #333333; color: white; 
            padding: 8px 16px; border-radius: 20px; font-weight: bold;
        """)
        # 阴影
        shadow = QGraphicsDropShadowEffect(self.lbl)
        shadow.setBlurRadius(10); shadow.setColor(QColor(0,0,0,50))
        self.lbl.setGraphicsEffect(shadow)
        
        layout.addWidget(self.lbl)
        
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(300)
        
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_toast)

    def show_msg(self, text, duration=2000):
        self.lbl.setText(text)
        self.lbl.adjustSize()
        self.adjustSize()
        
        # 居中底部显示
        p = self.parent()
        if p:
            geo = p.geometry()
            self.move(geo.width()//2 - self.width()//2, geo.height() - 80)
        
        self.stop_all()
        self.show()
        self.setWindowOpacity(0)
        
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()
        
        self.timer.start(duration)

    def hide_toast(self):
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self.hide)
        self.anim.start()

    def stop_all(self):
        self.anim.stop()
        self.timer.stop()
        try: self.anim.finished.disconnect()
        except: pass

class ForceGauge(QFrame):
    """ 
    全能仪表盘 
    显示: 1.位移(Main) 2.输出力(Sub/Arc)
    """
    def __init__(self, title, color="#007AFF", parent=None):
        super().__init__(parent)
        self.title = title
        self.color = QColor(color)
        
        # 数据存储
        self.val_real = 0.0   # 实际受力 %
        self.val_out = 0.0    # 输出力 %
        self.val_pos = 0.0    # 位移 mm
        
        self.setFixedSize(200, 200) # 尺寸稍微加大以容纳更多信息
        self.setStyleSheet("background: transparent;")

    def set_values(self, real, out, pos):
        """ 一次性更新所有数据 """
        self.val_real = max(0.0, min(100.0, real))
        self.val_out = out
        self.val_pos = pos
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        rect = QRectF(10, 10, w-20, h-20)

        # 1. 绘制背景槽 (240度环，开口向下)
        pen_bg = QPen(QColor("#F2F2F7"), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_bg)
        # 这里的角度单位是 1/16 度。
        # 起始角度：从 210 度开始 (左下)
        # 跨度：-240 度 (顺时针画到右下)
        painter.drawArc(rect, int(210 * 16), int(-240 * 16))
        
        # 2. 绘制 输出力 进度条 (Output Force)
        pen_val = QPen(self.color, 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_val)
        # 限制范围 0-100
        v_out = max(0.0, min(100.0, self.val_out))
        span = -240 * (v_out / 100.0)
        painter.drawArc(rect, int(210 * 16), int(span * 16))
        
        # 3. 绘制文字
        painter.setPen(QColor("#1C1C1E"))
        
        # A. 中间大数值 (位移)
        font_big = QFont("Segoe UI", 32, QFont.Weight.Bold)
        painter.setFont(font_big)
        text_pos = f"{self.val_pos:.1f}"
        metrics = painter.fontMetrics()
        tx = (w - metrics.horizontalAdvance(text_pos)) / 2
        ty = h / 2 - 5 # 稍微偏上
        painter.drawText(int(tx), int(ty), text_pos)
        
        # B. 中间标签 "mm"
        font_label = QFont("Segoe UI", 12)
        painter.setFont(font_label)
        painter.setPen(QColor("#8E8E93"))
        text_label = "mm"
        tx = (w - painter.fontMetrics().horizontalAdvance(text_label)) / 2
        painter.drawText(int(tx), int(ty + 30), text_label)

        # 4. 底部数值 (输出力)
        painter.setPen(QColor("#1C1C1E"))
        font_sub = QFont("Segoe UI", 12, QFont.Weight.Bold)
        painter.setFont(font_sub)
        
        text_out = f"Output: {self.val_out:.0f}%"
        tx_out = (w - painter.fontMetrics().horizontalAdvance(text_out)) / 2
        y_sub = h - 35
        painter.drawText(int(tx_out), int(y_sub), text_out)

        # 5. 顶部标题
        painter.setPen(self.color)
        font_title = QFont("Segoe UI", 11, QFont.Weight.Bold)
        painter.setFont(font_title)
        tx_title = (w - painter.fontMetrics().horizontalAdvance(self.title)) / 2
        painter.drawText(int(tx_title), 35, self.title)

class SlidingStackedWidget(QStackedWidget):
    """ 带动画状态查询的滑动容器 """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.m_direction = Qt.Orientation.Horizontal
        self.m_speed = 600
        self.m_animation_type = QEasingCurve.Type.OutQuart
        self.m_active = False # 动画状态锁

    def is_animating(self):
        """ [NEW] 外部查询锁 """
        return self.m_active

    def slideInIdx(self, idx):
        if idx > self.count() - 1: idx = idx % self.count()
        self.slideInWgt(self.widget(idx))

    def slideInWgt(self, newwidget):
        # [NEW] 如果正在动画中，拒绝新的切换请求
        if self.m_active: return
        self.m_active = True
        
        _now = self.currentWidget()
        _next = newwidget
        if _now == _next:
            self.m_active = False
            return

        offsetx, offsety = self.frameRect().width(), self.frameRect().height()
        self.widget(self.indexOf(_next)).setGeometry(0, 0, offsetx, offsety)
        
        if self.indexOf(_next) > self.indexOf(_now):
            offsetx, offsety = offsetx, 0
        else:
            offsetx, offsety = -offsetx, 0

        pnext = _next.pos()
        pnow = _now.pos()
        
        self.anim_group = QParallelAnimationGroup()
        
        anim_now = QPropertyAnimation(_now, b"pos")
        anim_now.setDuration(self.m_speed)
        anim_now.setEasingCurve(self.m_animation_type)
        anim_now.setStartValue(QPoint(pnow.x(), pnow.y()))
        anim_now.setEndValue(QPoint(pnow.x() - offsetx, pnow.y() + offsety))
        
        anim_next = QPropertyAnimation(_next, b"pos")
        anim_next.setDuration(self.m_speed)
        anim_next.setEasingCurve(self.m_animation_type)
        anim_next.setStartValue(QPoint(pnext.x() + offsetx, pnext.y() + offsety))
        anim_next.setEndValue(QPoint(pnext.x(), pnext.y()))
        
        self.anim_group.addAnimation(anim_now)
        self.anim_group.addAnimation(anim_next)
        self.anim_group.finished.connect(self.animationDoneSlot)
        self.anim_group.start()
        
        _next.show()
        _next.raise_()
        self.setCurrentWidget(_next)

    def animationDoneSlot(self):
        self.setCurrentWidget(self.currentWidget())
        self.m_active = False
class CounterWidget(IOSCard):
    """ 计数显示器 """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        self.lbl_title = QLabel("CYCLE PROGRESS")
        self.lbl_title.setStyleSheet("color: #8E8E93; font-size: 12px; font-weight: bold; letter-spacing: 1px;")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.lbl_count = QLabel("0 / 0")
        self.lbl_count.setStyleSheet("color: #1C1C1E; font-size: 32px; font-weight: bold; font-family: 'Segoe UI';")
        self.lbl_count.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Progress Bar
        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(6)
        self.pbar.setTextVisible(False)
        self.pbar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: #E5E5EA;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {config.COLOR_BLUE};
                border-radius: 3px;
            }}
        """)
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_count)
        layout.addWidget(self.pbar)
    
    def update_count(self, current, total):
        self.lbl_count.setText(f"{current} <span style='font-size:18px; color:#AEAEB2;'>/ {total}</span>")
        self.pbar.setMaximum(total)
        self.pbar.setValue(current)

class RealTimeChart(IOSCard):
    """ 实时受力曲线图 """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_a = []
        self.data_b = []
        self.max_points = 200 # 显示最近200个点 (约20秒)
        self.setMinimumHeight(250)
        # 设置白色背景以便曲线更清晰
        self.setStyleSheet("background-color: white; border-radius: 12px;")

    def append_data(self, val_a, val_b):
        self.data_a.append(val_a)
        self.data_b.append(val_b)
        if len(self.data_a) > self.max_points:
            self.data_a.pop(0)
            self.data_b.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        mx, my = 50, 30 # 边距
        
        # 1. 绘制标题
        painter.setPen(QColor("#1C1C1E"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(mx, 20, "Real-time Force Curve (%)")
        
        # 2. 绘制坐标轴和网格
        painter.setPen(QPen(QColor("#E5E5EA"), 1))
        painter.drawLine(int(mx), int(my), int(mx), int(h-my)) # Y轴
        painter.drawLine(int(mx), int(h-my), int(w-mx), int(h-my)) # X轴
        
        painter.setFont(QFont("Segoe UI", 8))
        for i in range(0, 101, 20):
            y = (h - my) - (i / 100.0) * (h - 2*my)
            # 网格线
            painter.setPen(QPen(QColor("#F2F2F7"), 1))
            painter.drawLine(int(mx), int(y), int(w-mx), int(y))
            # 刻度标签
            painter.setPen(QColor("#8E8E93"))
            painter.drawText(5, int(y+4), 40, 20, Qt.AlignmentFlag.AlignRight, f"{i}%")

        if len(self.data_a) < 2: return

        # 3. 绘制曲线
        step_x = (w - 2*mx) / (self.max_points - 1)
        
        def get_y(val):
            v = max(0, min(100, val))
            return (h - my) - (v / 100.0) * (h - 2*my)

        path_a = QPainterPath()
        path_b = QPainterPath()
        
        path_a.moveTo(mx, get_y(self.data_a[0]))
        path_b.moveTo(mx, get_y(self.data_b[0]))
        
        for i in range(1, len(self.data_a)):
            x = mx + i * step_x
            path_a.lineTo(x, get_y(self.data_a[i]))
            path_b.lineTo(x, get_y(self.data_b[i]))
            
        painter.setPen(QPen(QColor(config.COLOR_BLUE), 2)); painter.drawPath(path_a)
        painter.setPen(QPen(QColor(config.COLOR_GREEN), 2)); painter.drawPath(path_b)