import sys, os, json, csv, datetime
import ctypes
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableView, QHeaderView, QFrame, QSizePolicy, 
    QAbstractItemView, QPushButton, QMenu, QFileDialog, QMessageBox, 
    QGraphicsDropShadowEffect, QScrollArea, QDialog, QLineEdit, QFormLayout, QDialogButtonBox,
    QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QAbstractTableModel, QSize, QPropertyAnimation, QEasingCurve, Property, QTimer
from PySide6.QtGui import QColor, QFont, QAction, QIcon, QPixmap, QPainter, QLinearGradient

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# --- CONFIGURATION ---
YEAR = 2026
DEFAULT_HABITS = ["Workout", "Meditation", "Reading", "Coding", "Sleep 8h"]
DEFAULT_TIMES = ["07:00 AM", "08:00 AM", "09:00 PM", "10:00 PM", "11:00 PM"]
DAYS = 365
DATA_FILE = "habit_data.json"
ICON_NAME = "icon.ico" 

MONTH_COLORS = {
    1: "#E3F2FD", 2: "#E8F5E9", 3: "#FFFDE7", 4: "#FCE4EC",
    5: "#F3E5F5", 6: "#E0F7FA", 7: "#FFF3E0", 8: "#E8EAF6",
    9: "#E0F2F1", 10: "#FBE9E7", 11: "#EFEBE9", 12: "#E1F5FE"
}

# --- COLOR PALETTES ---
THEME_LIGHT = {
    "bg": "#F5F7FA", "card": "#FFFFFF", "text": "#1A252F", "text_sec": "#7F8C8D",
    "border": "#E0E0E0", "hover": "#F0F2F5", "shadow": "#10000000",
    "table_header": "#FAFAFA", "table_grid": "#F0F0F0", "scroll": "#BDBDBD",
    "chart_bg": "#FFFFFF", "chart_fill": "#6B9BD1", "chart_line": "#5A8AC0",
    "accent": "#3498DB", "success": "#4CAF50",
    "tooltip_bg": "#FFFFFF", "tooltip_text": "#000000", "tooltip_border": "#CCCCCC" # Added Explicit Tooltip Colors
}

THEME_DARK = {
    "bg": "#121212", "card": "#1E1E1E", "text": "#E0E0E0", "text_sec": "#A0A0A0",
    "border": "#333333", "hover": "#2C2C2C", "shadow": "#50000000",
    "table_header": "#252525", "table_grid": "#2C2C2C", "scroll": "#555555",
    "chart_bg": "#1E1E1E", "chart_fill": "#3498DB", "chart_line": "#5DADE2",
    "accent": "#5DADE2", "success": "#66BB6A",
    "tooltip_bg": "#2C3E50", "tooltip_text": "#FFFFFF", "tooltip_border": "#1A252F" # Added Explicit Tooltip Colors
}

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def apply_shadow(widget, blur=15, offset=4, color="#30000000"):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(offset)
    shadow.setColor(QColor(color))
    widget.setGraphicsEffect(shadow)

# --- ANIMATED BUTTON ---
class AnimatedButton(QPushButton):
    def __init__(self, text, color="#3498DB", hover_color="#2980B9"):
        super().__init__(text)
        self.base_color = color
        self.hover_color = hover_color
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 10px;
                padding: 12px 28px;
                font-weight: 700;
                font-size: 14px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                padding: 13px 28px 11px 28px;
            }}
        """)
        apply_shadow(self, blur=10, offset=4, color="#20000000")

# --- CUSTOM DIALOG ---
class HabitDialog(QDialog):
    def __init__(self, parent=None, name="", time="", is_dark=False):
        super().__init__(parent)
        self.setWindowTitle("Habit Details")
        self.setFixedWidth(400)
        self.is_dark = is_dark
        theme = THEME_DARK if is_dark else THEME_LIGHT
        
        self.setStyleSheet(f"""
            QDialog {{ 
                background-color: {theme['card']};
                border: 1px solid {theme['border']};
                border-radius: 16px;
            }}
            QLabel {{ 
                font-size: 13px; 
                font-weight: 600; 
                color: {theme['text']}; 
                padding: 5px 0;
            }}
            QLineEdit {{ 
                padding: 12px 16px; 
                border: 2px solid {theme['border']}; 
                border-radius: 8px; 
                background-color: {theme['bg']};
                color: {theme['text']};
                font-size: 14px;
                selection-background-color: {theme['accent']};
            }}
            QLineEdit:focus {{
                border: 2px solid {theme['accent']};
            }}
            QPushButton {{
                background-color: {theme['accent']};
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 700;
                font-size: 13px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {theme['chart_line']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title_label = QLabel("✨ Define Your Habit")
        title_label.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {theme['text']}; padding: 0;")
        layout.addWidget(title_label)
        
        form = QFormLayout()
        form.setSpacing(15)
        
        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("e.g., Morning Workout")
        
        self.time_input = QLineEdit(time)
        self.time_input.setPlaceholderText("e.g., 07:00 AM")
        
        form.addRow("Habit Name:", self.name_input)
        form.addRow("Time Frame:", self.time_input)
        
        layout.addLayout(form)
        layout.addSpacing(10)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        for button in buttons.buttons():
            button.setCursor(Qt.PointingHandCursor)
            
        layout.addWidget(buttons)

    def get_data(self):
        return self.name_input.text(), self.time_input.text()

# --- DATA MODEL ---
class HabitModel(QAbstractTableModel):
    def __init__(self, data, habit_names, habit_times, dates, today_idx, is_dark=False):
        super().__init__()
        self._data = data
        self._habit_names = habit_names
        self._habit_times = habit_times
        self._dates = dates
        self._today_idx = today_idx 
        self.is_dark = is_dark

    def set_theme_mode(self, is_dark):
        self.is_dark = is_dark
        self.layoutChanged.emit()

    def rowCount(self, parent=None): return len(self._habit_names) + 3 
    def columnCount(self, parent=None): return DAYS

    def data(self, index, role=Qt.DisplayRole):
        r, c = index.row(), index.column()
        theme = THEME_DARK if self.is_dark else THEME_LIGHT
        
        # --- ROW 0: MONTH NAMES ---
        if r == 0:
            if role == Qt.DisplayRole:
                d = self._dates[c]
                if d.day == 1 or c == 0: return d.strftime("%B").upper()
                return ""
            if role == Qt.BackgroundRole: 
                # Restored Month Colors with dimming for Dark Mode
                color_hex = MONTH_COLORS.get(self._dates[c].month, "#FFFFFF")
                if self.is_dark:
                    return QColor(color_hex).darker(150)
                return QColor(color_hex)
            
            if role == Qt.FontRole: return QFont("Segoe UI", 10, QFont.Bold)
            if role == Qt.TextAlignmentRole: return Qt.AlignCenter
            if role == Qt.ForegroundRole: 
                return QColor("#546E7A") if not self.is_dark else QColor("#DDDDDD")
            if role == Qt.ToolTipRole:
                return f"{self._dates[c].strftime('%B %Y')}"

        # --- ROW 1: DAY NUMBERS ---
        if r == 1:
            if role == Qt.DisplayRole: return self._dates[c].strftime("%d")
            if role == Qt.BackgroundRole:
                if c == self._today_idx: return QColor("#FFD54F") 
                return QColor(theme['bg'])
            if role == Qt.FontRole: return QFont("Segoe UI", 9, QFont.Bold)
            if role == Qt.TextAlignmentRole: return Qt.AlignCenter
            if role == Qt.ForegroundRole: 
                return QColor("#000000") if c == self._today_idx else QColor(theme['text'])
            
            # Specific Tooltip for Date Row
            if role == Qt.ToolTipRole:
                return self._dates[c].strftime("%B %d, %Y")

        # --- ROW 2: DAY NAMES ---
        if r == 2:
            if role == Qt.DisplayRole: return self._dates[c].strftime("%a")
            if role == Qt.BackgroundRole:
                if c == self._today_idx: return QColor("#FFF9C4") 
                return QColor(theme['card'])
            if role == Qt.FontRole: return QFont("Segoe UI", 8, QFont.Medium)
            if role == Qt.TextAlignmentRole: return Qt.AlignCenter
            if role == Qt.ForegroundRole:
                day_idx = self._dates[c].weekday()
                if day_idx >= 5: return QColor("#E91E63") 
                return QColor(theme['text_sec'])
            
            # Specific Tooltip for Day Row
            if role == Qt.ToolTipRole:
                return self._dates[c].strftime("%A")

        # --- HABIT ROWS ---
        habit_idx = r - 3 
        if habit_idx >= len(self._habit_names): return None

        if role == Qt.BackgroundRole:
            if self._data[habit_idx][c] == 1: return QColor(theme['success'])
            if c == self._today_idx: return QColor("#FFF9C4") if not self.is_dark else QColor("#4A4A3A")
            return QColor(theme['card']) if habit_idx % 2 == 0 else QColor(theme['bg'])
        
        # Habit Rows Tooltip
        if role == Qt.ToolTipRole:
            status = "✓ Completed" if self._data[habit_idx][c] == 1 else "○ Pending"
            return f"{status}\n{self._habit_names[habit_idx]} ({self._habit_times[habit_idx]})\n{self._dates[c].strftime('%B %d, %Y')}"
        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Vertical:
            if section == 0: 
                if role == Qt.DisplayRole: return "MONTHS"
                if role == Qt.FontRole: return QFont("Segoe UI", 9, QFont.Bold)
            if section == 1: 
                if role == Qt.DisplayRole: return "DAY" 
            if section == 2: 
                if role == Qt.DisplayRole: return "WEEK" 
            
            habit_idx = section - 3
            if 0 <= habit_idx < len(self._habit_names):
                if role == Qt.DisplayRole:
                    return f"{self._habit_names[habit_idx]}\n{self._habit_times[habit_idx]}"
                if role == Qt.FontRole:
                    return QFont("Segoe UI", 9, QFont.Bold)
                if role == Qt.ForegroundRole:
                    return QColor(THEME_DARK['text'] if self.is_dark else THEME_LIGHT['text'])
        return None

    def toggle(self, index):
        r, c = index.row(), index.column()
        if r < 3: return 
        habit_idx = r - 3
        if habit_idx < len(self._data):
            self._data[habit_idx][c] = 1 - self._data[habit_idx][c]
            self.dataChanged.emit(index, index)

# --- KPI CARD ---
class KPICard(QFrame):
    def __init__(self, title, icon, accent_color="#3498DB"):
        super().__init__()
        self.accent_color = accent_color
        self.icon_char = icon
        self.title_text = title
        
        self.icon_label = QLabel(icon)
        self.lbl_title = QLabel(title.upper())
        self.lbl_value = QLabel("0")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(24, 20, 24, 20)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        layout.addWidget(self.lbl_value)
        layout.addStretch()
        self.setFixedSize(220, 120)
        
        self.apply_theme(False) 

    def apply_theme(self, is_dark):
        theme = THEME_DARK if is_dark else THEME_LIGHT
        bg_color = theme['card']
        border_color = theme['border']
        
        bg_gradient_end = f"{self.accent_color}15" if not is_dark else f"{self.accent_color}25"
        
        self.setStyleSheet(f"""
            QFrame {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {bg_color}, stop:1 {bg_gradient_end});
                border: 2px solid {border_color};
                border-radius: 16px;
            }}
            QLabel {{ border: none; background-color: transparent; }}
        """)
        apply_shadow(self, blur=15, offset=6, color="#000000" if is_dark else "#15000000")
        
        self.icon_label.setStyleSheet(f"color: {self.accent_color}; font-size: 24px; font-weight: 900;")
        self.lbl_title.setStyleSheet(f"color: {theme['text_sec']}; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        self.lbl_value.setStyleSheet(f"color: {self.accent_color}; font-size: 32px; font-weight: 900;")

    def set_value(self, val): 
        self.lbl_value.setText(str(val))

# --- MAIN APP ---
class HabitApp(QWidget):
    def __init__(self):
        super().__init__()
        icon_path = resource_path(ICON_NAME)
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.is_dark_mode = False 
        self.init_data()
        self.setup_ui()
        self.apply_theme() 

    def init_data(self):
        self.start_date = datetime.date(YEAR, 1, 1)
        self.dates = [self.start_date + datetime.timedelta(days=i) for i in range(DAYS)]
        today = datetime.date.today()
        if today.year < YEAR: self.current_date = self.start_date 
        elif today.year > YEAR: self.current_date = datetime.date(YEAR, 12, 31)
        else: self.current_date = today
        self.today_idx = (self.current_date - self.start_date).days
        
        self.habit_names = []
        self.habit_times = []
        self.habit_data = []

        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f: 
                    loaded_content = json.load(f)
                    if isinstance(loaded_content, list): 
                        self.habit_names = DEFAULT_HABITS.copy()
                        self.habit_times = DEFAULT_TIMES.copy()
                        self.habit_data = loaded_content
                    elif isinstance(loaded_content, dict): 
                        self.habit_names = loaded_content.get("names", DEFAULT_HABITS.copy())
                        self.habit_times = loaded_content.get("times", [])
                        self.habit_data = loaded_content.get("data", [])
            except: pass

        if not self.habit_names:
            self.habit_names = DEFAULT_HABITS.copy()
            self.habit_data = [[0]*DAYS for _ in DEFAULT_HABITS]
        
        while len(self.habit_times) < len(self.habit_names):
            self.habit_times.append("Any Time")

        while len(self.habit_data) < len(self.habit_names):
            self.habit_data.append([0]*DAYS)

    def create_color_icon(self, color_hex):
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(color_hex))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 16, 16, 4, 4)
        painter.end()
        return QIcon(pixmap)

    def setup_ui(self):
        self.setWindowTitle(f"Habit Dashboard — {YEAR}")
        self.resize(1450, 950)
        
        # Main Layout
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scroll Area
        self.main_scroll = QScrollArea(self)
        self.main_scroll.setWidgetResizable(True)
        
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(40, 35, 40, 35)
        self.layout.setSpacing(30)
        
        self.main_scroll.setWidget(self.container)
        root_layout.addWidget(self.main_scroll)

        # HEADER
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)
        
        self.title_lbl = QLabel(f"🎯 Habit Dashboard")
        self.title_lbl.setStyleSheet("font-size: 38px; font-weight: 900;")
        
        self.subtitle_lbl = QLabel(f"Year {YEAR} — Build Better Habits Every Day")
        self.subtitle_lbl.setStyleSheet("font-size: 14px; font-weight: 500;")
        
        title_layout.addWidget(self.title_lbl)
        title_layout.addWidget(self.subtitle_lbl)
        
        self.date_lbl = QLabel(f"📅  {self.current_date.strftime('%B %d, %Y')}")
        self.date_lbl.setAlignment(Qt.AlignCenter)
        apply_shadow(self.date_lbl, blur=8, offset=3)

        btn_add = AnimatedButton(" ➕ Add Habit ", "#27AE60", "#229954")
        btn_add.clicked.connect(self.add_habit)

        self.btn_export = AnimatedButton(" 📊 Export Report  ▼ ", "#8E44AD", "#7D3C98")
        self.btn_export.setStyleSheet(self.btn_export.styleSheet() + "QPushButton::menu-indicator { image: none; }")
        
        self.menu = QMenu(self)
        self.action_csv = QAction("📄 CSV (Raw Data)", self)
        self.action_csv.setIcon(self.create_color_icon("#27AE60"))
        self.action_csv.triggered.connect(self.export_csv)
        
        self.action_pdf = QAction("📕 PDF (Visual Report)", self)
        self.action_pdf.setIcon(self.create_color_icon("#E74C3C"))
        self.action_pdf.triggered.connect(self.export_pdf)
        
        self.menu.addAction(self.action_csv)
        self.menu.addAction(self.action_pdf)
        self.btn_export.setMenu(self.menu)

        # Theme Toggle Button
        self.btn_theme = QPushButton(" 🌙 ")
        self.btn_theme.setFixedSize(45, 45)
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.clicked.connect(self.toggle_theme)
        apply_shadow(self.btn_theme, blur=8, offset=3)

        header_layout.addWidget(title_container)
        header_layout.addStretch()
        header_layout.addWidget(self.date_lbl)
        header_layout.addSpacing(15)
        header_layout.addWidget(btn_add)
        header_layout.addSpacing(10)
        header_layout.addWidget(self.btn_export)
        header_layout.addSpacing(10)
        header_layout.addWidget(self.btn_theme) # Moved next to Export
        self.layout.addWidget(header_frame)

        # KPI CARDS
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(25)
        
        self.card_today = KPICard("Today's Progress", "🎯", "#6B9BD1")
        self.card_streak = KPICard("Best Streak", "🔥", "#BB4F4F")
        self.card_weekly = KPICard("Weekly Average", "📈", "#B4A7D6")
        self.card_monthly = KPICard("Monthly Average", "📊", "#85C1A7")
        
        for c in [self.card_today, self.card_streak, self.card_weekly, self.card_monthly]: 
            kpi_layout.addWidget(c)
        kpi_layout.addStretch()
        self.layout.addLayout(kpi_layout)

        # GRID CONTAINER
        self.grid_container = QFrame()
        apply_shadow(self.grid_container, blur=20, offset=6)
        
        grid_layout_inner = QVBoxLayout(self.grid_container)
        grid_layout_inner.setContentsMargins(0, 0, 0, 0)

        self.table = QTableView()
        self.model = HabitModel(self.habit_data, self.habit_names, self.habit_times, self.dates, self.today_idx)
        self.table.setModel(self.model)
        
        self.row_height = 58
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setFixedWidth(160)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        
        self.table.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.verticalHeader().customContextMenuRequested.connect(self.handle_header_menu)
        
        self.table.horizontalHeader().setVisible(False)
        self.table.setColumnWidth(0, 50)
        for i in range(DAYS): self.table.setColumnWidth(i, 42)
        
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.clicked.connect(self.on_cell_clicked)
        
        self.update_table_height()
        grid_layout_inner.addWidget(self.table)
        self.layout.addWidget(self.grid_container)

        # CHART CONTAINER
        self.chart_container = QFrame()
        apply_shadow(self.chart_container, blur=20, offset=6)
        
        chart_layout = QVBoxLayout(self.chart_container)
        chart_layout.setContentsMargins(25, 25, 25, 25)

        self.chart_title = QLabel("📈 Annual Consistency Trend")
        self.chart_title.setStyleSheet("font-size: 18px; font-weight: 800; padding-bottom: 10px;")
        chart_layout.addWidget(self.chart_title)

        self.fig = Figure(figsize=(9, 3.8), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setFixedHeight(380)
        
        chart_layout.addWidget(self.canvas)
        self.layout.addWidget(self.chart_container)

        self.apply_month_spans()
        self.update_analytics()
        if self.today_idx > 0: 
            self.table.scrollTo(self.model.index(0, self.today_idx), QAbstractItemView.PositionAtCenter)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        
    def apply_theme(self):
        theme = THEME_DARK if self.is_dark_mode else THEME_LIGHT
        
        # --- FIXED: Explicit Tooltip Styling for Visibility ---
        base_style = f"""
            QWidget {{ font-family: 'Segoe UI', system-ui; }}
            QScrollBar:vertical {{ border: none; background: {theme['bg']}; width: 12px; border-radius: 6px; }}
            QScrollBar::handle:vertical {{ background: {theme['scroll']}; border-radius: 6px; min-height: 30px; }}
            QScrollBar::handle:vertical:hover {{ background: {theme['accent']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            
            /* DYNAMIC TOOLTIP STYLING */
            QToolTip {{ 
                background-color: {theme['tooltip_bg']}; 
                color: {theme['tooltip_text']}; 
                border: 1px solid {theme['tooltip_border']};
                font-family: 'Segoe UI';
                font-size: 12px;
                padding: 4px;
            }}
        """
        self.setStyleSheet(base_style)
        
        self.container.setStyleSheet(f"background-color: {theme['bg']};")
        self.main_scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: {theme['bg']}; }}")
        
        # Text Colors
        self.title_lbl.setStyleSheet(f"font-size: 38px; font-weight: 900; color: {theme['text']};")
        self.subtitle_lbl.setStyleSheet(f"font-size: 14px; font-weight: 500; color: {theme['text_sec']};")
        self.chart_title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {theme['text']}; padding-bottom: 10px;")

        # Date Label
        if self.is_dark_mode:
            self.date_lbl.setStyleSheet(f"background-color: {theme['card']}; color: {theme['accent']}; font-size: 14px; font-weight: 700; padding: 12px 22px; border-radius: 25px; border: 2px solid {theme['border']};")
        else:
            self.date_lbl.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E3F2FD, stop:1 #BBDEFB); color: #1565C0; font-size: 14px; font-weight: 700; padding: 12px 22px; border-radius: 25px; border: 2px solid #90CAF9;")

        # Theme Button
        self.btn_theme.setText(" ☀️ " if self.is_dark_mode else " 🌙 ")
        self.btn_theme.setStyleSheet(f"QPushButton {{ background-color: {theme['card']}; color: {theme['text']}; border-radius: 10px; border: 1px solid {theme['border']}; font-size: 20px; }} QPushButton:hover {{ background-color: {theme['hover']}; }}")

        # Menu Styling
        self.menu.setStyleSheet(f"""
            QMenu {{ background-color: {theme['card']}; border: 1px solid {theme['border']}; border-radius: 12px; padding: 8px; }}
            QMenu::item {{ padding: 10px 30px; color: {theme['text']}; font-weight: 600; border-radius: 6px; }} 
            QMenu::item:selected {{ background-color: {theme['hover']}; color: {theme['accent']}; }}
        """)

        # Containers
        for container in [self.grid_container, self.chart_container]:
            container.setStyleSheet(f"background-color: {theme['card']}; border-radius: 16px; border: 1px solid {theme['border']};")
            apply_shadow(container, blur=20, offset=6, color="#000000" if self.is_dark_mode else "#10000000")

        # Table Styling
        self.table.setStyleSheet(f"""
            QTableView {{ border: none; background-color: {theme['card']}; gridline-color: {theme['table_grid']}; border-radius: 16px; }}
            QHeaderView::section {{ background-color: {theme['table_header']}; color: {theme['text']}; padding-left: 15px; border: none; border-right: 1px solid {theme['border']}; border-bottom: 2px solid {theme['border']}; font-weight: 700; font-size: 13px; text-align: left; }}
        """)

        # Update Model and Components
        self.model.set_theme_mode(self.is_dark_mode)
        for card in [self.card_today, self.card_streak, self.card_weekly, self.card_monthly]:
            card.apply_theme(self.is_dark_mode)
        
        self.update_analytics() 

    def handle_header_menu(self, pos):
        row = self.table.verticalHeader().logicalIndexAt(pos)
        if row < 3: return

        habit_idx = row - 3
        habit_name = self.habit_names[habit_idx]
        
        menu = QMenu(self)
        menu.setStyleSheet(self.menu.styleSheet())
        
        rename_action = QAction(f"✏️ Edit '{habit_name}'", self)
        rename_action.triggered.connect(lambda: self.edit_habit(habit_idx))
        
        delete_action = QAction(f"🗑️ Delete '{habit_name}'", self)
        delete_action.triggered.connect(lambda: self.delete_habit(habit_idx))

        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.exec_(self.table.verticalHeader().mapToGlobal(pos))

    def edit_habit(self, index):
        old_name = self.habit_names[index]
        old_time = self.habit_times[index]
        
        dialog = HabitDialog(self, old_name, old_time, self.is_dark_mode)
        if dialog.exec_() == QDialog.Accepted:
            new_name, new_time = dialog.get_data()
            if new_name:
                self.habit_names[index] = new_name
                self.habit_times[index] = new_time
                self.save_data()
                self.model.headerDataChanged.emit(Qt.Vertical, index+3, index+3)

    def delete_habit(self, index):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Delete Habit")
        msg_box.setText(f"Are you sure you want to delete '{self.habit_names[index]}'?")
        msg_box.setInformativeText("All data for this habit will be permanently lost.")
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        theme = THEME_DARK if self.is_dark_mode else THEME_LIGHT
        msg_box.setStyleSheet(f"QMessageBox {{ background-color: {theme['card']}; color: {theme['text']}; }} QLabel {{ color: {theme['text']}; }} QPushButton {{ color: {theme['text']}; }}")
        
        reply = msg_box.exec_()
        if reply == QMessageBox.Yes:
            del self.habit_names[index]
            del self.habit_times[index]
            del self.habit_data[index]
            self.save_data()
            self.model.layoutChanged.emit()
            self.update_table_height()
            self.update_analytics()

    def add_habit(self):
        dialog = HabitDialog(self, is_dark=self.is_dark_mode)
        if dialog.exec_() == QDialog.Accepted:
            new_name, new_time = dialog.get_data()
            if new_name:
                self.habit_names.append(new_name)
                self.habit_times.append(new_time)
                self.habit_data.append([0] * DAYS)
                self.save_data()
                self.model.layoutChanged.emit()
                self.update_table_height()
                self.update_analytics()

    def update_table_height(self):
        total_rows = len(self.habit_names) + 3 
        calc_height = (total_rows * self.row_height) + 5
        self.table.setFixedHeight(calc_height)

    def apply_month_spans(self):
        curr = -1; start = 0
        for c, d in enumerate(self.dates):
            if d.month != curr:
                if curr != -1: self.table.setSpan(0, start, 1, c - start)
                curr = d.month; start = c
        self.table.setSpan(0, start, 1, DAYS - start)
    
    def on_cell_clicked(self, index): 
        self.model.toggle(index)
        self.save_data()
        self.update_analytics()
    
    def save_data(self):
        save_package = {
            "names": self.habit_names,
            "times": self.habit_times,
            "data": self.habit_data
        }
        with open(DATA_FILE, "w") as f: 
            json.dump(save_package, f)
    
    def update_analytics(self):
        num_habits = len(self.habit_names)
        if num_habits == 0:
            self.card_today.set_value("0%")
            self.card_streak.set_value("0 Days")
            self.card_weekly.set_value("0%")
            self.card_monthly.set_value("0%")
            return

        comp_today = sum(self.habit_data[r][self.today_idx] for r in range(num_habits)) if 0 <= self.today_idx < DAYS else 0
        self.today_pct = int((comp_today / num_habits) * 100)
        
        self.best_streak = 0; curr = 0
        for c in range(DAYS):
            if all(self.habit_data[r][c] == 1 for r in range(num_habits)): 
                curr+=1
                self.best_streak = max(self.best_streak, curr)
            else: 
                curr=0
        
        self.weekly_avg = 0
        if self.today_idx >= 0:
            start = max(0, self.today_idx - 6)
            total = sum(sum(self.habit_data[r][c] for r in range(num_habits)) for c in range(start, self.today_idx+1))
            self.weekly_avg = int((total / (num_habits * ((self.today_idx-start)+1))) * 100)
        
        self.monthly_avg = 0
        if self.today_idx >= 0:
            start = max(0, self.today_idx - 29)
            total = sum(sum(self.habit_data[r][c] for r in range(num_habits)) for c in range(start, self.today_idx+1))
            self.monthly_avg = int((total / (num_habits * ((self.today_idx-start)+1))) * 100)
        
        self.card_today.set_value(f"{self.today_pct}%")
        self.card_streak.set_value(f"{self.best_streak} Days")
        self.card_weekly.set_value(f"{self.weekly_avg}%")
        self.card_monthly.set_value(f"{self.monthly_avg}%")

        daily_avg = [sum(self.habit_data[r][c] for r in range(num_habits)) / num_habits * 100 for c in range(DAYS)]
        
        # --- MATPLOTLIB THEME UPDATE ---
        theme = THEME_DARK if self.is_dark_mode else THEME_LIGHT
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor(theme['chart_bg'])
        ax.set_facecolor(theme['chart_bg'])
        
        # Create gradient fill
        ax.fill_between(range(DAYS), daily_avg, color=theme['chart_fill'], alpha=0.15)
        ax.plot(range(DAYS), daily_avg, color=theme['chart_line'], linewidth=3, zorder=10)
        
        ax.set_ylim(0, 110)
        ax.set_xlim(0, DAYS)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(theme['border'])
        ax.spines['bottom'].set_color(theme['border'])
        ax.spines['left'].set_linewidth(2)
        ax.spines['bottom'].set_linewidth(2)
        
        tick_color = theme['text_sec']
        ax.tick_params(axis='x', colors=tick_color, labelsize=10, length=6, width=2)
        ax.tick_params(axis='y', colors=tick_color, labelsize=10, length=6, width=2)
        
        grid_color = theme['border']
        ax.grid(True, axis='y', linestyle='--', alpha=0.3, color=grid_color, linewidth=1)
        ax.set_ylabel('Completion Rate (%)', fontsize=11, fontweight='600', color=theme['text_sec'])
        ax.set_xlabel('Day of Year', fontsize=11, fontweight='600', color=theme['text_sec'])
        
        self.fig.subplots_adjust(top=0.95, bottom=0.15, left=0.08, right=0.97)
        self.canvas.draw()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", f"Habit_Report_{YEAR}.csv", "CSV (*.csv)")
        if not path: return
        try:
            with open(path, "w", newline="") as f:
                headers = ["Date"]
                for i, name in enumerate(self.habit_names):
                    headers.append(f"{name} ({self.habit_times[i]})")
                headers.append("Daily %")
                
                writer = csv.writer(f)
                writer.writerow(headers)
                for c, date in enumerate(self.dates):
                    row = [date.strftime("%Y-%m-%d")]
                    d_sum = 0
                    num_habits = len(self.habit_names)
                    if num_habits == 0: continue
                    
                    for r in range(num_habits):
                        v = self.habit_data[r][c]
                        row.append("Yes" if v==1 else "No")
                        d_sum+=v
                    row.append(f"{int(d_sum/num_habits*100)}%")
                    writer.writerow(row)
            
            QMessageBox.information(self, "Success", f"CSV Export Complete!\nSaved to: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export Failed: {str(e)}")

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", f"Habit_Report_{YEAR}.pdf", "PDF (*.pdf)")
        if not path: return
        try:
            self.fig.patch.set_facecolor('white')
            ax = self.fig.gca()
            ax.set_facecolor('white')
            for spine in ax.spines.values(): spine.set_color('#E0E0E0')
            ax.tick_params(colors='#7F8C8D')
            ax.xaxis.label.set_color('#546E7A')
            ax.yaxis.label.set_color('#546E7A')
            
            self.fig.savefig("temp_chart.png", facecolor='white', dpi=150, bbox_inches='tight')
            
            self.update_analytics()
            
            c = canvas.Canvas(path, pagesize=letter)
            w, h = letter
            
            c.setFont("Helvetica-Bold", 26)
            c.setFillColor(colors.HexColor("#1A252F"))
            c.drawString(50, h - 60, f"Habit Dashboard {YEAR}")
            
            c.setFont("Helvetica", 11)
            c.setFillColor(colors.HexColor("#7F8C8D"))
            c.drawString(50, h - 80, f"Generated: {datetime.date.today().strftime('%B %d, %Y')}")
            
            y = h - 150
            c.setStrokeColor(colors.HexColor("#E0E0E0"))
            c.setLineWidth(2)
            
            kpis = [
                ("Today", f"{self.today_pct}%", "#6B9BD1"),
                ("Streak", f"{self.best_streak}", "#E8A87C"),
                ("Weekly", f"{self.weekly_avg}%", "#B4A7D6"),
                ("Monthly", f"{self.monthly_avg}%", "#85C1A7")
            ]
            
            for i, (lbl, val, color) in enumerate(kpis):
                x = 50 + (i * 130)
                c.setFillColor(colors.HexColor(color + "15"))
                c.roundRect(x, y, 120, 60, 8, fill=1, stroke=0)
                c.setStrokeColor(colors.HexColor(color))
                c.setLineWidth(2)
                c.roundRect(x, y, 120, 60, 8, fill=0, stroke=1)
                c.setFillColor(colors.HexColor("#7F8C8D"))
                c.setFont("Helvetica-Bold", 10)
                c.drawCentredString(x+60, y+42, lbl)
                c.setFont("Helvetica-Bold", 18)
                c.setFillColor(colors.HexColor(color))
                c.drawCentredString(x+60, y+18, val)
            
            c.drawImage("temp_chart.png", 50, h - 450, width=500, height=180, preserveAspectRatio=True)
            c.showPage()
            c.save()
            
            if os.path.exists("temp_chart.png"): os.remove("temp_chart.png")
            QMessageBox.information(self, "Success", f"PDF Export Complete!\nSaved to: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export Failed: {str(e)}")

if __name__ == "__main__":
    myappid = 'mycompany.habit.tracker.7.0' 
    try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except: pass
    
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    if os.path.exists(resource_path(ICON_NAME)):
        app.setWindowIcon(QIcon(resource_path(ICON_NAME)))
    
    window = HabitApp()
    window.show()
    sys.exit(app.exec())