# config.py

SIMULATION_MODE = True  # !!! 连接真实硬件改为 False !!!

# --- 默认硬件参数 (用户可在界面修改) ---
DEFAULT_MAX_SPEED = 100.0  # mm/s
DEFAULT_MAX_FORCE = 100.0  # %

# --- iOS 风格配色 ---
COLOR_BG = "#F2F2F7"        
COLOR_WHITE = "#FFFFFF"     
COLOR_TEXT = "#1C1C1E"      
COLOR_SUBTEXT = "#8E8E93"   
COLOR_BLUE = "#007AFF"      
COLOR_GREEN = "#34C759"     
COLOR_RED = "#FF3B30"       
COLOR_BORDER = "#E5E5EA"    

# --- 强制全局样式表 ---
GLOBAL_STYLESHEET = f"""
    QMainWindow, QWidget {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
        font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
        font-size: 14px;
    }}
    QFrame#Card {{
        background-color: {COLOR_WHITE};
        border-radius: 12px;
        border: 1px solid {COLOR_BORDER};
    }}
    QLineEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {COLOR_BG};
        border: 1px solid {COLOR_BORDER};
        border-radius: 6px;
        padding: 4px 8px;
        color: {COLOR_TEXT};
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {COLOR_BLUE};
        background-color: {COLOR_WHITE};
    }}
    /* 选项卡样式 */
    QTabWidget::pane {{ border: none; }}
    QTabBar::tab {{
        background: {COLOR_BG};
        color: {COLOR_SUBTEXT};
        padding: 8px 20px;
        font-weight: bold;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}
    QTabBar::tab:selected {{
        background: {COLOR_WHITE};
        color: {COLOR_BLUE};
    }}
    QScrollBar:vertical {{ width: 6px; background: transparent; }}
    QScrollBar::handle:vertical {{ background: #C7C7CC; border-radius: 3px; }}
"""