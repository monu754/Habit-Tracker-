import sys, os, json, csv, datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableView, QHeaderView, QFrame, QSizePolicy, 
    QAbstractItemView, QPushButton, QMenu, QFileDialog, QMessageBox, 
    QGraphicsDropShadowEffect, QScrollArea, QDialog, QLineEdit, 
    QFormLayout, QDialogButtonBox, QTabWidget, QAbstractScrollArea, QStyle
)
from PySide6.QtCore import Qt, QAbstractTableModel, QTimer, QRect, QPoint, Signal
from PySide6.QtGui import QColor, QFont, QAction, QIcon, QPainter
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# --- CONFIGURATION ---
YEAR = 2026
DEFAULT_HABITS = ["Workout", "Meditation", "Reading", "Coding", "Sleep 8h"]
DEFAULT_TIMES = ["07:00 AM", "08:00 AM", "09:00 PM", "10:00 PM", "11:00 PM"]
DAYS = 365
DATA_FILE = "habit_data.json"
ICON_NAME = "icon.ico" 

# --- THEMES ---
THEME_LIGHT = {
    "bg": "#F0F2F5", 
    "card": "#FFFFFF", "border": "#DDE2E7",
    "text_primary": "#1C1F26", "text_secondary": "#64748B",
    "shadow": "#15000000", 
    "month_even": "#E3F2FD", "month_odd":  "#F5F5F5", 
    "month_text": "#1565C0", "date_text": "#1C1F26", "day_text": "#64748B", "weekend_text": "#D32F2F", 
    "row_even": "#FFFFFF", "row_odd": "#F8FAFB",
    "today_bg": "#FFF9C4", "today_text": "#F57F17",
    "future_bg": "#F1F5F9", "completed": "#4CAF50",
    "chart_bg": "#FFFFFF", "chart_line": "#3B82F6", "chart_fill": "#3B82F6", "chart_bar": "#8B5CF6", "chart_grid": "#E2E8F0",
    "btn_add": "#10B981", "btn_export": "#6366F1", "date_badge_bg": "#FFFFFF", "date_badge_text": "#3B82F6", "date_badge_border": "#DDE2E7"
}

THEME_DARK = {
    "bg": "#0D1117", 
    "card": "#161B22", "border": "#30363D",
    "text_primary": "#F0F6FC", "text_secondary": "#8B949E",
    "shadow": "#80000000",
    "month_even": "#16213E", "month_odd":  "#21262D", 
    "month_text": "#58A6FF", "date_text": "#C9D1D9", "day_text": "#8B949E", "weekend_text": "#FF5252", 
    "row_even": "#161B22", "row_odd": "#0D1117",
    "today_bg": "#3E2C00", "today_text": "#D29922", 
    "future_bg": "#101318", "completed": "#2EA043", 
    "chart_bg": "#161B22", "chart_line": "#58A6FF", "chart_fill": "#58A6FF", "chart_bar": "#A371F7", "chart_grid": "#30363D",
    "btn_add": "#238636", "btn_export": "#8957E5", "date_badge_bg": "#161B22", "date_badge_text": "#58A6FF", "date_badge_border": "#30363D"
}

KPI_STYLES_LIGHT = {
    "Today":   {"bg": "#E3F2FD", "text": "#1976D2", "border": "#BBDEFB"},
    "Streak":  {"bg": "#FFEBEE", "text": "#D32F2F", "border": "#FFCDD2"},
    "Weekly":  {"bg": "#E8F5E9", "text": "#388E3C", "border": "#C8E6C9"},
    "Monthly": {"bg": "#F3E5F5", "text": "#7B1FA2", "border": "#E1BEE7"}
}

KPI_STYLES_DARK = {
    "Today":   {"text": "#79C0FF"},
    "Streak":  {"text": "#FFA198"},
    "Weekly":  {"text": "#56D364"},
    "Monthly": {"text": "#D2A8FF"}
}

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def apply_shadow(widget, blur=15, offset=4, color="#10000000"):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(offset)
    shadow.setColor(QColor(color))
    widget.setGraphicsEffect(shadow)

# --- COMPONENTS ---

class HoverHeader(QHeaderView):
    editRequested = Signal(int)

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setMouseTracking(True)
        self.hover_row = -1
        self.setSectionsClickable(True) 

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        row = self.logicalIndexAt(pos)
        if row != self.hover_row:
            self.hover_row = row
            self.viewport().update() 
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hover_row = -1
        self.viewport().update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        row = self.logicalIndexAt(pos)
        if row >= 3 and pos.x() > self.width() - 35:
            self.editRequested.emit(row)
            return
        super().mousePressEvent(event)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        super().paintSection(painter, rect, logicalIndex) 
        painter.restore()

        if logicalIndex >= 3 and logicalIndex == self.hover_row:
            painter.save()
            icon_rect = QRect(rect.right() - 25, rect.top(), 20, rect.height())
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            painter.setPen(QColor("#7F8C8D")) 
            painter.drawText(icon_rect, Qt.AlignCenter, "✏️")
            painter.restore()

class AnimatedButton(QPushButton):
    def __init__(self, text, bg_color, text_color="#FFFFFF", is_dropdown=False):
        super().__init__(text)
        self.bg_color = bg_color
        self.text_color = text_color
        self.is_dropdown = is_dropdown
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()

    def update_colors(self, bg, text):
        self.bg_color = bg
        self.text_color = text
        self.update_style()

    def update_style(self):
        padding = "10px 35px 10px 20px" if self.is_dropdown else "10px 20px"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.bg_color};
                color: {self.text_color};
                border-radius: 8px;
                padding: {padding};
                font-weight: 600;
                font-size: 13px;
                border: none;
                text-align: center;
            }}
            QPushButton:hover {{ 
                background-color: {self.bg_color};
                border: 2px solid #FFFFFF50; 
                padding: { "8px 33px 8px 18px" if self.is_dropdown else "8px 18px" };
            }}
            QPushButton::menu-indicator {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                right: 12px;
                width: 8px;
                height: 8px;
            }}
        """)

class KPICard(QFrame):
    def __init__(self, key, title, icon):
        super().__init__()
        self.key = key 
        self.icon_label = QLabel(icon)
        self.lbl_title = QLabel(title.upper())
        self.lbl_value = QLabel("0")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- FIXED: Centered Group Layout ---
        # 1. Header Layout (Icon + Title on same line)
        header_layout = QHBoxLayout()
        header_layout.addStretch() # Push from left
        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch() # Push from right
        # This keeps them together in the center
        
        layout.addLayout(header_layout)
        
        # 2. Value Layout (Centered text)
        self.lbl_value.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_value)
        
        self.setMinimumWidth(240)
        self.setFixedHeight(120)

    def apply_theme(self, is_dark):
        theme = THEME_DARK if is_dark else THEME_LIGHT
        if is_dark:
            style_data = KPI_STYLES_DARK.get(self.key, {"text": "#FFFFFF"})
            self.setStyleSheet(f"""
                QFrame {{ background-color: {theme['card']}; border: 1px solid {theme['border']}; border-radius: 12px; }}
                QLabel {{ border: none; background: transparent; }}
            """)
            text_color = style_data['text']
        else:
            style_data = KPI_STYLES_LIGHT.get(self.key, {"bg": "#FFFFFF", "text": "#000000", "border": "#E0E0E0"})
            self.setStyleSheet(f"""
                QFrame {{ background-color: {style_data['bg']}; border: 1px solid {style_data['border']}; border-radius: 12px; }}
                QLabel {{ border: none; background: transparent; }}
            """)
            text_color = style_data['text']

        apply_shadow(self, blur=10, offset=4, color=theme['shadow'])
        
        # --- PRESERVED LARGE FONT SIZES ---
        emoji_size = "32px" if self.key == "Today" else "22px"
        self.icon_label.setStyleSheet(f"color: {text_color}; font-size: {emoji_size};")
        self.lbl_title.setStyleSheet(f"color: {text_color}; font-size: 17px; font-weight: 800; opacity: 0.9;") 
        self.lbl_value.setStyleSheet(f"color: {text_color}; font-size: 28px; font-weight: 800;")

    def set_value(self, val): self.lbl_value.setText(str(val))

class HabitDialog(QDialog):
    def __init__(self, parent=None, name="", time="", is_dark=False):
        super().__init__(parent)
        self.setWindowTitle("Habit Details")
        self.setFixedWidth(380)
        theme = THEME_DARK if is_dark else THEME_LIGHT
        self.setStyleSheet(f"""
            QDialog {{ background-color: {theme['card']}; }}
            QLabel {{ color: {theme['text_primary']}; font-weight: 600; font-size: 13px; }}
            QLineEdit {{ 
                background: {theme['bg']}; color: {theme['text_primary']}; 
                border: 1px solid {theme['border']}; padding: 8px; border-radius: 6px;
            }}
            QPushButton {{ 
                background: {theme['btn_add']}; color: white; 
                padding: 8px 16px; border-radius: 6px; border: none; font-weight: bold;
            }}
        """)
        layout = QVBoxLayout(self)
        self.name_input = QLineEdit(name); self.name_input.setPlaceholderText("Habit Name")
        self.time_input = QLineEdit(time); self.time_input.setPlaceholderText("Time")
        form = QFormLayout()
        form.addRow("Name:", self.name_input)
        form.addRow("Time:", self.time_input)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    def get_data(self): return self.name_input.text(), self.time_input.text()

# --- MODEL ---
class HabitModel(QAbstractTableModel):
    def __init__(self, data, habit_names, habit_times, dates, today_idx, is_dark=False):
        super().__init__()
        self._data = data; self._habit_names = habit_names; self._habit_times = habit_times
        self._dates = dates; self._today_idx = today_idx; self.is_dark = is_dark
    def set_theme_mode(self, is_dark): self.is_dark = is_dark; self.layoutChanged.emit()
    def rowCount(self, parent=None): return len(self._habit_names) + 3 
    def columnCount(self, parent=None): return DAYS
    def data(self, index, role=Qt.DisplayRole):
        r, c = index.row(), index.column()
        theme = THEME_DARK if self.is_dark else THEME_LIGHT
        date_obj = self._dates[c]
        month_bg = theme['month_even'] if date_obj.month % 2 == 0 else theme['month_odd']
        if r == 0:
            if role == Qt.DisplayRole: return date_obj.strftime("%B").upper() if (date_obj.day == 1 or c == 0) else ""
            if role == Qt.BackgroundRole: return QColor(month_bg)
            if role == Qt.ForegroundRole: return QColor(theme['month_text'])
            if role == Qt.FontRole: return QFont("Segoe UI", 9, QFont.Bold)
            if role == Qt.TextAlignmentRole: return Qt.AlignCenter
        if r == 1:
            if role == Qt.DisplayRole: return date_obj.strftime("%d")
            if role == Qt.BackgroundRole: return QColor(theme['today_bg']) if c == self._today_idx else QColor(month_bg)
            if role == Qt.ForegroundRole: return QColor(theme['today_text']) if c == self._today_idx else QColor(theme['date_text'])
            if role == Qt.FontRole: return QFont("Segoe UI", 9, QFont.Bold)
            if role == Qt.TextAlignmentRole: return Qt.AlignCenter
        if r == 2:
            if role == Qt.DisplayRole: return date_obj.strftime("%a")
            if role == Qt.BackgroundRole: return QColor(theme['today_bg']) if c == self._today_idx else QColor(month_bg)
            if role == Qt.ForegroundRole: return QColor(theme['today_text']) if c == self._today_idx else (QColor(theme['weekend_text']) if date_obj.weekday() >= 5 else QColor(theme['day_text']))
            if role == Qt.FontRole: return QFont("Segoe UI", 8)
            if role == Qt.TextAlignmentRole: return Qt.AlignCenter
        habit_idx = r - 3 
        if habit_idx >= len(self._habit_names): return None
        if role == Qt.BackgroundRole:
            val = self._data[habit_idx][c]
            if val == 1: return QColor(theme['completed'])
            if c == self._today_idx: return QColor(theme['today_bg'])
            if date_obj > datetime.date.today(): return QColor(theme['future_bg'])
            return QColor(theme['row_even']) if habit_idx % 2 == 0 else QColor(theme['row_odd'])
        return None
    def headerData(self, section, orientation, role):
        if orientation == Qt.Vertical:
            if section < 3:
                if role == Qt.DisplayRole: return ["MONTH", "DATE", "DAY"][section]
                if role == Qt.FontRole: return QFont("Segoe UI", 8, QFont.Bold)
            else:
                habit_idx = section - 3
                if 0 <= habit_idx < len(self._habit_names):
                    if role == Qt.DisplayRole: return f"{self._habit_names[habit_idx]}\n{self._habit_times[habit_idx]}"
                    if role == Qt.FontRole: return QFont("Segoe UI", 9, QFont.Bold)
                    if role == Qt.ForegroundRole: return QColor(THEME_DARK['text_primary'] if self.is_dark else THEME_LIGHT['text_primary'])
        return None
    def toggle(self, index):
        r, c = index.row(), index.column()
        if r < 3 or self._dates[c] > datetime.date.today(): return 
        habit_idx = r - 3
        if habit_idx < len(self._data):
            self._data[habit_idx][c] = 1 - self._data[habit_idx][c]
            self.dataChanged.emit(index, index)

# --- MAIN APP ---
class HabitApp(QWidget):
    def __init__(self):
        super().__init__()
        icon_path = resource_path(ICON_NAME)
        if os.path.exists(icon_path): self.setWindowIcon(QIcon(icon_path))
        self.is_dark_mode = False 
        self.row_height = 50
        self.col_width = 42
        self.init_data()
        self.setup_ui()
        self.apply_theme()
        QTimer.singleShot(100, self.scroll_to_today)

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
                    d = json.load(f)
                    if isinstance(d, dict): 
                        self.habit_names = d.get("names", DEFAULT_HABITS.copy())
                        self.habit_times = d.get("times", [])
                        self.habit_data = d.get("data", [])
                        self.is_dark_mode = d.get("theme", False)
            except: pass
        if not self.habit_names:
            self.habit_names = DEFAULT_HABITS.copy(); self.habit_data = [[0]*DAYS for _ in DEFAULT_HABITS]
        while len(self.habit_times) < len(self.habit_names): self.habit_times.append("Any Time")
        while len(self.habit_data) < len(self.habit_names): self.habit_data.append([0]*DAYS)

    def setup_ui(self):
        self.setWindowTitle(f"Habit Dashboard — {YEAR}")
        self.resize(1350, 950)
        self.main_scroll = QScrollArea(self); self.main_scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(40, 40, 40, 40); self.layout.setSpacing(35)
        self.main_scroll.setWidget(self.container)
        root_layout = QVBoxLayout(self); root_layout.setContentsMargins(0, 0, 0, 0); root_layout.addWidget(self.main_scroll)

        header_frame = QFrame(); header_layout = QHBoxLayout(header_frame); header_layout.setContentsMargins(0, 0, 0, 0)
        title_box = QVBoxLayout(); title_box.setSpacing(5)
        self.title_lbl = QLabel(f"🎯 Habit Dashboard {YEAR}"); self.subtitle_lbl = QLabel(f"Consistency is key.")
        title_box.addWidget(self.title_lbl); title_box.addWidget(self.subtitle_lbl)
        controls_layout = QHBoxLayout(); controls_layout.setSpacing(12)
        self.date_lbl = QLabel(f"📅 {self.current_date.strftime('%B %d, %Y')}"); self.date_lbl.setAlignment(Qt.AlignCenter); self.date_lbl.setFixedHeight(38)
        self.btn_add = AnimatedButton(" + Habit ", "#28A745", is_dropdown=False); self.btn_add.clicked.connect(self.add_habit)
        self.btn_export = AnimatedButton("Export", "#7E3AF2", is_dropdown=True)
        self.menu = QMenu(self)
        self.menu.addAction("📄 CSV", self.export_csv); self.menu.addAction("📕 PDF", self.export_pdf)
        self.menu.addSeparator(); self.menu.addAction("💾 Backup", self.backup_data); self.menu.addAction("🔄 Restore", self.restore_data)
        self.btn_export.setMenu(self.menu)
        self.btn_theme = QPushButton(""); self.btn_theme.setFixedSize(38, 38); self.btn_theme.setCursor(Qt.PointingHandCursor); self.btn_theme.clicked.connect(self.toggle_theme)
        controls_layout.addWidget(self.date_lbl); controls_layout.addWidget(self.btn_add); controls_layout.addWidget(self.btn_export); controls_layout.addWidget(self.btn_theme)
        header_layout.addLayout(title_box); header_layout.addStretch(); header_layout.addLayout(controls_layout)
        self.layout.addWidget(header_frame)

        kpi_layout = QHBoxLayout(); kpi_layout.setSpacing(24)
        self.card_today = KPICard("Today", "Today", "🎯"); self.card_streak = KPICard("Streak", "Best Streak", "🔥")
        self.card_weekly = KPICard("Weekly", "Weekly Avg", "📈"); self.card_monthly = KPICard("Monthly", "Monthly Avg", "📊")
        for c in [self.card_today, self.card_streak, self.card_weekly, self.card_monthly]: kpi_layout.addWidget(c)
        self.layout.addLayout(kpi_layout)

        self.grid_container = QFrame(); grid_layout_inner = QVBoxLayout(self.grid_container); grid_layout_inner.setContentsMargins(0, 0, 0, 0)
        self.table = QTableView()
        self.model = HabitModel(self.habit_data, self.habit_names, self.habit_times, self.dates, self.today_idx, self.is_dark_mode)
        self.table.setModel(self.model)
        
        self.hover_header = HoverHeader(Qt.Vertical, self.table)
        self.table.setVerticalHeader(self.hover_header)
        self.hover_header.editRequested.connect(self.edit_habit_by_row)

        self.table.verticalHeader().setVisible(True); self.table.verticalHeader().setFixedWidth(160)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height); self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.horizontalHeader().setVisible(False); self.table.horizontalHeader().setDefaultSectionSize(self.col_width); self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.table.setFrameShape(QFrame.NoFrame)
        
        self.table.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.verticalHeader().customContextMenuRequested.connect(self.handle_header_menu)
        self.table.setFocusPolicy(Qt.NoFocus); self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.clicked.connect(self.on_cell_clicked)
        self.update_table_height()
        grid_layout_inner.addWidget(self.table)
        self.layout.addWidget(self.grid_container)

        self.tabs = QTabWidget(); self.tabs.setStyleSheet("QTabWidget::pane { border: 0; }")
        self.tab_annual = QWidget(); lay_annual = QVBoxLayout(self.tab_annual)
        self.fig_annual = Figure(figsize=(8, 3), dpi=100); self.canvas_annual = FigureCanvasQTAgg(self.fig_annual)
        lay_annual.addWidget(self.canvas_annual)
        self.tab_monthly = QWidget(); lay_monthly = QVBoxLayout(self.tab_monthly)
        self.fig_monthly = Figure(figsize=(8, 3), dpi=100); self.canvas_monthly = FigureCanvasQTAgg(self.fig_monthly)
        lay_monthly.addWidget(self.canvas_monthly)
        self.tabs.addTab(self.tab_annual, "Annual Trend"); self.tabs.addTab(self.tab_monthly, "Monthly Breakdown")
        self.chart_container = QFrame(); self.chart_container.setMinimumHeight(450)
        chart_main_layout = QVBoxLayout(self.chart_container); chart_main_layout.addWidget(self.tabs)
        self.layout.addWidget(self.chart_container)
        
        self.apply_month_spans(); self.update_analytics()

    def toggle_theme(self): self.is_dark_mode = not self.is_dark_mode; self.apply_theme(); self.save_data()
    def apply_theme(self):
        theme = THEME_DARK if self.is_dark_mode else THEME_LIGHT
        self.setStyleSheet(f"""
            QWidget {{ font-family: 'Segoe UI', sans-serif; }}
            QMenu {{ background: {theme['card']}; border: 1px solid {theme['border']}; }}
            QMenu::item {{ color: {theme['text_primary']}; padding: 6px 20px; }}
            QMenu::item:selected {{ background: {theme.get('row_odd', '#EEE')}; }}
            QTabWidget::pane {{ border: 1px solid {theme['border']}; background: {theme['card']}; border-radius: 8px; }}
            QTabBar::tab {{ background: {theme['bg']}; color: {theme['text_secondary']}; padding: 10px 20px; margin-right: 4px; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
            QTabBar::tab:selected {{ background: {theme['card']}; color: {theme['text_primary']}; font-weight: bold; }}
        """)
        self.container.setStyleSheet(f"background-color: {theme['bg']};"); self.main_scroll.setStyleSheet(f"background-color: {theme['bg']}; border: none;")
        
        self.title_lbl.setStyleSheet(f"color: {theme['text_primary']}; font-size: 34px; font-weight: 800;")
        
        self.subtitle_lbl.setStyleSheet(f"color: {theme['text_secondary']}; font-size: 18px;")
        self.date_lbl.setStyleSheet(f"background-color: {theme['date_badge_bg']}; color: {theme['date_badge_text']}; border: 1px solid {theme['date_badge_border']}; border-radius: 6px; padding: 0 16px; font-weight: 600;")
        self.btn_add.update_colors(theme['btn_add'], "#FFFFFF"); self.btn_export.update_colors(theme['btn_export'], "#FFFFFF")
        self.btn_theme.setText("☀️" if self.is_dark_mode else "🌙"); self.btn_theme.setStyleSheet(f"QPushButton {{ background-color: {theme['card']}; border: 1px solid {theme['border']}; border-radius: 19px; font-size: 16px; }} QPushButton:hover {{ border: 1px solid {theme['text_secondary']}; }}")
        for c in [self.grid_container, self.chart_container]: c.setStyleSheet(f"background: {theme['card']}; border: 1px solid {theme['border']}; border-radius: 12px;"); apply_shadow(c, blur=15, offset=4, color=theme['shadow'])
        self.table.setStyleSheet(f"QTableView {{ border: none; background: {theme['card']}; gridline-color: transparent; border-radius: 12px; }} QHeaderView::section {{ background: {theme['card']}; color: {theme['text_primary']}; border: none; border-bottom: 1px solid {theme['border']}; border-right: 1px solid {theme['border']}; padding-left: 10px; }}")
        self.model.set_theme_mode(self.is_dark_mode)
        for card in [self.card_today, self.card_streak, self.card_weekly, self.card_monthly]: card.apply_theme(self.is_dark_mode)
        self.update_analytics()

    def scroll_to_today(self):
        if self.today_idx > 0: self.table.scrollTo(self.model.index(0, self.today_idx), QAbstractItemView.PositionAtCenter)

    def edit_habit_by_row(self, row):
        if row < 3: return
        habit_idx = row - 3
        d = HabitDialog(self, self.habit_names[habit_idx], self.habit_times[habit_idx], self.is_dark_mode)
        if d.exec_() == QDialog.Accepted:
            n, t = d.get_data()
            if n:
                self.habit_names[habit_idx] = n; self.habit_times[habit_idx] = t; self.save_data()
                self.model.headerDataChanged.emit(Qt.Vertical, row, row)

    def handle_header_menu(self, pos):
        row = self.table.verticalHeader().logicalIndexAt(pos)
        if row < 3: return
        habit_idx = row - 3
        menu = QMenu(self); edit = menu.addAction(f"✏️ Edit"); delete = menu.addAction(f"🗑️ Delete")
        action = menu.exec_(self.table.verticalHeader().mapToGlobal(pos))
        if action == edit: self.edit_habit_by_row(row)
        elif action == delete:
            self.habit_names.pop(habit_idx); self.habit_times.pop(habit_idx); self.habit_data.pop(habit_idx)
            self.save_data(); self.model.layoutChanged.emit(); self.update_table_height(); self.update_analytics()

    def add_habit(self):
        d = HabitDialog(self, is_dark=self.is_dark_mode)
        if d.exec_() == QDialog.Accepted:
            n, t = d.get_data()
            if n:
                self.habit_names.append(n); self.habit_times.append(t); self.habit_data.append([0]*DAYS)
                self.save_data(); self.model.layoutChanged.emit(); self.update_table_height(); self.update_analytics()

    def update_table_height(self):
        total_rows = len(self.habit_names) + 3
        scrollbar_height = self.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        h = (total_rows * self.row_height) + scrollbar_height + 2
        self.table.setFixedHeight(h)

    def apply_month_spans(self):
        curr = -1; start = 0
        for c, d in enumerate(self.dates):
            if d.month != curr:
                if curr != -1: self.table.setSpan(0, start, 1, c-start)
                curr = d.month; start = c
        self.table.setSpan(0, start, 1, DAYS-start)

    def on_cell_clicked(self, index): self.model.toggle(index); self.save_data(); self.update_analytics()
    def save_data(self):
        with open(DATA_FILE, "w") as f: json.dump({ "names": self.habit_names, "times": self.habit_times, "data": self.habit_data, "theme": self.is_dark_mode }, f)
    def backup_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Backup", f"Habit_Backup_{datetime.date.today()}.json", "JSON (*.json)")
        if path:
            with open(path, "w") as f: json.dump({ "names": self.habit_names, "times": self.habit_times, "data": self.habit_data, "theme": self.is_dark_mode }, f)
    def restore_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Restore", "", "JSON (*.json)")
        if path:
            try:
                with open(path, "r") as f:
                    d = json.load(f)
                    self.habit_names = d.get("names", []); self.habit_times = d.get("times", [])
                    self.habit_data = d.get("data", []); self.is_dark_mode = d.get("theme", False)
                    self.model = HabitModel(self.habit_data, self.habit_names, self.habit_times, self.dates, self.today_idx, self.is_dark_mode)
                    self.table.setModel(self.model); self.update_table_height(); self.apply_month_spans(); self.apply_theme(); self.save_data()
            except: pass

    def calculate_stats(self):
        n = len(self.habit_names)
        if n == 0: return {}
        
        today_val = sum(self.habit_data[r][self.today_idx] for r in range(n)) if 0 <= self.today_idx < DAYS else 0
        today_pct = int((today_val / n) * 100)
        
        streak = 0; curr = 0
        for c in range(DAYS):
            if all(self.habit_data[r][c] == 1 for r in range(n)): curr += 1; streak = max(streak, curr)
            else: curr = 0
            
        def get_avg(days):
            if self.today_idx < 0: return 0
            start = max(0, self.today_idx - days + 1)
            total = n * (self.today_idx - start + 1)
            done = sum(sum(self.habit_data[r][c] for r in range(n)) for c in range(start, self.today_idx+1))
            return int((done/total)*100) if total > 0 else 0

        return {
            "today": f"{today_pct}%",
            "streak": f"{streak} Days",
            "weekly": f"{get_avg(7)}%",
            "monthly": f"{get_avg(30)}%"
        }

    def update_analytics(self):
        stats = self.calculate_stats()
        if not stats: return

        self.card_today.set_value(stats["today"])
        self.card_streak.set_value(stats["streak"])
        self.card_weekly.set_value(stats["weekly"])
        self.card_monthly.set_value(stats["monthly"])
        
        n = len(self.habit_names)
        theme = THEME_DARK if self.is_dark_mode else THEME_LIGHT
        
        daily_avgs = [sum(self.habit_data[r][c] for r in range(n))/n*100 for c in range(DAYS)]
        self.fig_annual.clear(); ax1 = self.fig_annual.add_subplot(111); self.fig_annual.patch.set_facecolor(theme['chart_bg']); ax1.set_facecolor(theme['chart_bg'])
        fill_rgba = tuple(int(theme['chart_fill'].lstrip('#')[i:i+2], 16)/255. for i in (0, 2, 4)) + (0.15,)
        ax1.fill_between(range(DAYS), daily_avgs, color=fill_rgba); ax1.plot(range(DAYS), daily_avgs, color=theme['chart_line'], linewidth=2)
        ax1.set_ylim(0, 105); ax1.set_xlim(0, DAYS)
        ax1.set_title("Annual Consistency Trend", color=theme['text_primary'], fontsize=10, weight='bold', pad=10)
        ax1.set_ylabel("Completion Rate (%)", color=theme['text_secondary'], fontsize=9)
        ax1.tick_params(axis='x', colors=theme['text_secondary']); ax1.tick_params(axis='y', colors=theme['text_secondary'])
        ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)
        ax1.spines['bottom'].set_color(theme['border']); ax1.spines['left'].set_color(theme['border'])
        month_starts = [i for i, d in enumerate(self.dates) if d.day == 1]
        ax1.set_xticks(month_starts); ax1.set_xticklabels([self.dates[i].strftime('%b') for i in month_starts], rotation=0, fontsize=8)
        self.fig_annual.subplots_adjust(left=0.08, right=0.98, top=0.85, bottom=0.15); self.canvas_annual.draw()
        
        monthly_data = {}
        for c, d in enumerate(self.dates):
            if d.month not in monthly_data: monthly_data[d.month] = []
            monthly_data[d.month].append(sum(self.habit_data[r][c] for r in range(n))/n*100)
        months = range(1, 13); month_avgs = [sum(monthly_data[m])/len(monthly_data[m]) if m in monthly_data else 0 for m in months]
        month_labels = [datetime.date(2000, m, 1).strftime('%b') for m in months]
        self.fig_monthly.clear(); ax2 = self.fig_monthly.add_subplot(111); self.fig_monthly.patch.set_facecolor(theme['chart_bg']); ax2.set_facecolor(theme['chart_bg'])
        bars = ax2.bar(month_labels, month_avgs, color=theme['chart_bar'])
        ax2.set_title("Average Success Rate by Month", color=theme['text_primary'], fontsize=10, weight='bold', pad=10)
        ax2.set_ylabel("Average (%)", color=theme['text_secondary'], fontsize=9)
        ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_visible(False); ax2.spines['bottom'].set_color(theme['border'])
        ax2.tick_params(axis='x', colors=theme['text_secondary']); ax2.tick_params(axis='y', colors=theme['text_secondary'])
        ax2.set_ylim(0, 115) 
        for bar in bars:
            height = bar.get_height()
            if height > 1: ax2.text(bar.get_x() + bar.get_width()/2., height + 1, f'{int(height)}%', ha='center', va='bottom', color=theme['text_primary'], fontsize=8, fontweight='bold')
        self.fig_monthly.subplots_adjust(left=0.08, right=0.98, top=0.85, bottom=0.15); self.canvas_monthly.draw()

    def export_csv(self):
        stats = self.calculate_stats()
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", f"Habits_{YEAR}.csv", "CSV (*.csv)")
        if path:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                
                # --- SUMMARY HEADER ---
                writer.writerow(["--- HABIT SUMMARY ---"])
                writer.writerow(["Current Streak", stats.get("streak", "0")])
                writer.writerow(["Today Completion", stats.get("today", "0%")])
                writer.writerow(["Weekly Average", stats.get("weekly", "0%")])
                writer.writerow(["Monthly Average", stats.get("monthly", "0%")])
                writer.writerow([]) # Empty row for spacing
                
                # --- DATA TABLE ---
                writer.writerow(["--- DAILY LOG ---"])
                writer.writerow(["Date"] + [f"{n} ({t})" for n, t in zip(self.habit_names, self.habit_times)])
                for c, d in enumerate(self.dates):
                    row = [d.strftime("%Y-%m-%d")] + ["Yes" if self.habit_data[r][c] else "No" for r in range(len(self.habit_names))]
                    writer.writerow(row)
            QMessageBox.information(self, "Export", "CSV (with Summary) saved successfully!")

    def export_pdf(self):
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", f"Habit_Report_{YEAR}.pdf", "PDF (*.pdf)")
        if not path: return
        try:
            stats = self.calculate_stats()
            
            # Save Charts
            self.fig_annual.savefig("temp_annual.png", facecolor=self.fig_annual.get_facecolor(), dpi=150)
            self.fig_monthly.savefig("temp_monthly.png", facecolor=self.fig_monthly.get_facecolor(), dpi=150)
            
            c = canvas.Canvas(path, pagesize=letter)
            w, h = letter
            
            # Title
            c.setFont("Helvetica-Bold", 24)
            c.drawString(50, h-50, f"Habit Report {YEAR}")
            
            # KPI Summary Text
            c.setFont("Helvetica", 12)
            y_text = h - 90
            c.drawString(50, y_text, f"• Current Streak: {stats.get('streak', '0')}")
            c.drawString(250, y_text, f"• Today's Completion: {stats.get('today', '0%')}")
            y_text -= 20
            c.drawString(50, y_text, f"• Weekly Average: {stats.get('weekly', '0%')}")
            c.drawString(250, y_text, f"• Monthly Average: {stats.get('monthly', '0%')}")
            
            # Draw Annual Chart
            c.drawImage("temp_annual.png", 50, h-350, width=500, height=200, preserveAspectRatio=True)
            
            # Draw Monthly Chart
            c.drawImage("temp_monthly.png", 50, h-600, width=500, height=200, preserveAspectRatio=True)
            
            c.save()
            
            # Cleanup
            if os.path.exists("temp_annual.png"): os.remove("temp_annual.png")
            if os.path.exists("temp_monthly.png"): os.remove("temp_monthly.png")
            
            QMessageBox.information(self, "Export", "PDF (with Stats & Charts) saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setFont(QFont("Segoe UI", 10))
    window = HabitApp(); window.show(); sys.exit(app.exec())