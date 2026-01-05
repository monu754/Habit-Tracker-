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

# --- CUSTOM DIALOG FOR ADDING/EDITING HABITS ---
class HabitDialog(QDialog):
    def __init__(self, parent=None, name="", time=""):
        super().__init__(parent)
        self.setWindowTitle("Habit Details")
        self.setFixedWidth(400)
        
        self.setStyleSheet("""
            QDialog { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #F8F9FA);
                border-radius: 16px;
            }
            QLabel { 
                font-size: 13px; 
                font-weight: 600; 
                color: #2C3E50; 
                padding: 5px 0;
            }
            QLineEdit { 
                padding: 12px 16px; 
                border: 2px solid #E0E0E0; 
                border-radius: 8px; 
                background-color: #FFFFFF;
                color: #2C3E50;
                font-size: 14px;
                selection-background-color: #3498DB;
            }
            QLineEdit:focus {
                border: 2px solid #3498DB;
            }
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 700;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #1F618D;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("✨ Define Your Habit")
        title_label.setStyleSheet("font-size: 20px; font-weight: 800; color: #1A252F; padding: 0;")
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
    def __init__(self, data, habit_names, habit_times, dates, today_idx):
        super().__init__()
        self._data = data
        self._habit_names = habit_names
        self._habit_times = habit_times
        self._dates = dates
        self._today_idx = today_idx 

    def rowCount(self, parent=None): return len(self._habit_names) + 3 
    def columnCount(self, parent=None): return DAYS

    def data(self, index, role=Qt.DisplayRole):
        r, c = index.row(), index.column()
        
        # --- ROW 0: MONTH NAMES ---
        if r == 0:
            if role == Qt.DisplayRole:
                d = self._dates[c]
                if d.day == 1 or c == 0: return d.strftime("%B").upper()
                return ""
            if role == Qt.BackgroundRole: 
                return QColor(MONTH_COLORS.get(self._dates[c].month, "#FFFFFF"))
            if role == Qt.FontRole: 
                return QFont("Segoe UI", 10, QFont.Bold)
            if role == Qt.TextAlignmentRole: 
                return Qt.AlignCenter
            if role == Qt.ForegroundRole: 
                return QColor("#546E7A")

        # --- ROW 1: DAY NUMBERS ---
        if r == 1:
            if role == Qt.DisplayRole: 
                return self._dates[c].strftime("%d")
            if role == Qt.BackgroundRole:
                if c == self._today_idx: 
                    return QColor("#FFD54F")
                return QColor("#FAFAFA")
            if role == Qt.FontRole: 
                return QFont("Segoe UI", 9, QFont.Bold)
            if role == Qt.TextAlignmentRole: 
                return Qt.AlignCenter
            if role == Qt.ForegroundRole: 
                return QColor("#424242")

        # --- ROW 2: DAY NAMES ---
        if r == 2:
            if role == Qt.DisplayRole: 
                return self._dates[c].strftime("%a")
            if role == Qt.BackgroundRole:
                if c == self._today_idx: 
                    return QColor("#FFF9C4")
                return QColor("#FFFFFF")
            if role == Qt.FontRole: 
                return QFont("Segoe UI", 8, QFont.Medium)
            if role == Qt.TextAlignmentRole: 
                return Qt.AlignCenter
            if role == Qt.ForegroundRole:
                day_idx = self._dates[c].weekday()
                if day_idx >= 5: 
                    return QColor("#E91E63")
                return QColor("#78909C")

        # --- HABIT ROWS ---
        habit_idx = r - 3 
        if habit_idx >= len(self._habit_names): return None

        if role == Qt.BackgroundRole:
            if self._data[habit_idx][c] == 1: 
                return QColor("#4CAF50")
            if c == self._today_idx: 
                return QColor("#FFF9C4")
            return QColor("#FFFFFF") if habit_idx % 2 == 0 else QColor("#FAFAFA")
        
        if role == Qt.ToolTipRole:
            status = "✓ Completed" if self._data[habit_idx][c] == 1 else "○ Pending"
            return f"{status}\n{self._habit_names[habit_idx]} ({self._habit_times[habit_idx]})\n{self._dates[c].strftime('%B %d, %Y')}"
        
        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Vertical:
            if section == 0: 
                if role == Qt.DisplayRole: return "" 
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
                    return QColor("#2C3E50")
        return None

    def toggle(self, index):
        r, c = index.row(), index.column()
        if r < 3: return 
        habit_idx = r - 3
        if habit_idx < len(self._data):
            self._data[habit_idx][c] = 1 - self._data[habit_idx][c]
            self.dataChanged.emit(index, index)

# --- MODERN KPI CARD WITH ANIMATION ---
class KPICard(QFrame):
    def __init__(self, title, icon, accent_color="#3498DB"):
        super().__init__()
        self.accent_color = accent_color
        self.setStyleSheet(f"""
            QFrame {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFFFFF, stop:1 {accent_color}15);
                border: 2px solid {accent_color}30;
                border-radius: 16px;
            }}
            QLabel {{ border: none; background-color: transparent; }}
        """)
        apply_shadow(self, blur=15, offset=6, color="#15000000")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(24, 20, 24, 20)
        
        # Icon and Title Row
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {accent_color}; font-size: 24px; font-weight: 900;")
        
        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setStyleSheet("color: #7F8C8D; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        
        self.lbl_value = QLabel("0")
        self.lbl_value.setStyleSheet(f"color: {accent_color}; font-size: 32px; font-weight: 900;")
        
        layout.addLayout(header_layout)
        layout.addWidget(self.lbl_value)
        layout.addStretch()
        
        self.setFixedSize(220, 120)

    def set_value(self, val): 
        self.lbl_value.setText(str(val))

# --- MAIN APP ---
class HabitApp(QWidget):
    def __init__(self):
        super().__init__()
        icon_path = resource_path(ICON_NAME)
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.init_data()
        self.setup_ui()

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
            except:
                pass

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
        
        # Global Stylesheet
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', 'San Francisco', system-ui;
            }
            QScrollBar:vertical {
                border: none;
                background: #F5F5F5;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #BDBDBD;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9E9E9E;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.main_scroll = QScrollArea(self)
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setStyleSheet("QScrollArea { border: none; background-color: #F5F7FA; }")
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #F5F7FA;")
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(40, 35, 40, 35)
        self.layout.setSpacing(30)
        
        self.main_scroll.setWidget(self.container)

        # HEADER
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Title with gradient effect
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)
        
        title = QLabel(f"🎯 Habit Dashboard")
        title.setStyleSheet("font-size: 38px; font-weight: 900; color: #1A252F;")
        
        subtitle = QLabel(f"Year {YEAR} — Build Better Habits Every Day")
        subtitle.setStyleSheet("font-size: 14px; color: #7F8C8D; font-weight: 500;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        date_lbl = QLabel(f"📅  {self.current_date.strftime('%B %d, %Y')}")
        date_lbl.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #E3F2FD, stop:1 #BBDEFB);
            color: #1565C0; 
            font-size: 14px; 
            font-weight: 700; 
            padding: 12px 22px; 
            border-radius: 25px; 
            border: 2px solid #90CAF9;
        """)
        apply_shadow(date_lbl, blur=8, offset=3)

        btn_add = AnimatedButton(" ➕ Add Habit ", "#27AE60", "#229954")
        btn_add.clicked.connect(self.add_habit)

        btn_export = AnimatedButton(" 📊 Export Report  ▼ ", "#8E44AD", "#7D3C98")
        btn_export.setStyleSheet(btn_export.styleSheet() + "QPushButton::menu-indicator { image: none; }")
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { 
                background-color: white; 
                border: 2px solid #E0E0E0; 
                border-radius: 12px; 
                padding: 8px; 
            }
            QMenu::item { 
                padding: 10px 30px; 
                color: #2C3E50;
                font-size: 13px;
                font-weight: 600;
                border-radius: 6px;
            } 
            QMenu::item:selected { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E3F2FD, stop:1 #BBDEFB);
                color: #1565C0;
            }
        """)
        
        action_csv = QAction("📄 CSV (Raw Data)", self)
        action_csv.setIcon(self.create_color_icon("#27AE60"))
        action_csv.triggered.connect(self.export_csv)
        
        action_pdf = QAction("📕 PDF (Visual Report)", self)
        action_pdf.setIcon(self.create_color_icon("#E74C3C"))
        action_pdf.triggered.connect(self.export_pdf)
        
        menu.addAction(action_csv)
        menu.addAction(action_pdf)
        btn_export.setMenu(menu)

        header_layout.addWidget(title_container)
        header_layout.addStretch()
        header_layout.addWidget(date_lbl)
        header_layout.addSpacing(15)
        header_layout.addWidget(btn_add)
        header_layout.addSpacing(10)
        header_layout.addWidget(btn_export)
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
        grid_container = QFrame()
        grid_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 16px;
                border: 2px solid #E8EAF6;
            }
        """)
        apply_shadow(grid_container, blur=20, offset=6, color="#10000000")
        
        grid_layout_inner = QVBoxLayout(grid_container)
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

        self.table.setStyleSheet("""
            QTableView { 
                border: none; 
                background-color: white; 
                gridline-color: #F0F0F0; 
                border-radius: 16px;
                selection-background-color: transparent;
            }
            QHeaderView::section { 
                background-color: #FAFAFA; 
                color: #2C3E50; 
                padding-left: 15px; 
                border: none; 
                border-right: 1px solid #E8EAF6; 
                border-bottom: 2px solid #E8EAF6; 
                font-weight: 700; 
                font-size: 13px; 
                text-align: left;
            }
            QTableView::item:hover {
                background-color: #E3F2FD;
            }
        """)
        
        self.table.horizontalHeader().setVisible(False)
        self.table.setColumnWidth(0, 50)
        for i in range(DAYS): 
            self.table.setColumnWidth(i, 42)
        
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.clicked.connect(self.on_cell_clicked)
        
        self.update_table_height()

        grid_layout_inner.addWidget(self.table)
        self.layout.addWidget(grid_container)

        # CHART CONTAINER
        chart_container = QFrame()
        chart_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 16px;
                border: 2px solid #E8EAF6;
            }
        """)
        apply_shadow(chart_container, blur=20, offset=6, color="#10000000")
        
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(25, 25, 25, 25)

        chart_title = QLabel("📈 Annual Consistency Trend")
        chart_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #1A252F; padding-bottom: 10px;")
        chart_layout.addWidget(chart_title)

        self.fig = Figure(figsize=(9, 3.8), dpi=100)
        self.fig.patch.set_facecolor('white')
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setFixedHeight(380)
        
        chart_layout.addWidget(self.canvas)
        self.layout.addWidget(chart_container)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.main_scroll)

        self.apply_month_spans()
        self.update_analytics()
        if self.today_idx > 0: 
            self.table.scrollTo(self.model.index(0, self.today_idx), QAbstractItemView.PositionAtCenter)

    def handle_header_menu(self, pos):
        row = self.table.verticalHeader().logicalIndexAt(pos)
        if row < 3: return

        habit_idx = row - 3
        habit_name = self.habit_names[habit_idx]

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { 
                background-color: white; 
                border: 2px solid #E0E0E0; 
                border-radius: 12px;
                padding: 8px;
            } 
            QMenu::item { 
                padding: 10px 30px; 
                color: #2C3E50;
                font-weight: 600;
                border-radius: 6px;
            } 
            QMenu::item:selected { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E3F2FD, stop:1 #BBDEFB);
                color: #1565C0;
            }
        """)
        
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
        
        dialog = HabitDialog(self, old_name, old_time)
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
        dialog = HabitDialog(self)
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
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('#FAFAFA')
        
        # Create gradient fill
        ax.fill_between(range(DAYS), daily_avg, color='#6B9BD1', alpha=0.15)
        ax.plot(range(DAYS), daily_avg, color='#5A8AC0', linewidth=3, zorder=10)
        
        # Add smooth curve appearance
        ax.set_ylim(0, 110)
        ax.set_xlim(0, DAYS)
        
        # Style improvements
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#E0E0E0')
        ax.spines['bottom'].set_color('#E0E0E0')
        ax.spines['left'].set_linewidth(2)
        ax.spines['bottom'].set_linewidth(2)
        
        ax.tick_params(axis='x', colors='#7F8C8D', labelsize=10, length=6, width=2)
        ax.tick_params(axis='y', colors='#7F8C8D', labelsize=10, length=6, width=2)
        
        ax.grid(True, axis='y', linestyle='--', alpha=0.3, color='#BDBDBD', linewidth=1)
        ax.set_ylabel('Completion Rate (%)', fontsize=11, fontweight='600', color='#546E7A')
        ax.set_xlabel('Day of Year', fontsize=11, fontweight='600', color='#546E7A')
        
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
            
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Success")
            msg.setText("CSV Export Complete!")
            msg.setInformativeText(f"Saved to: {path}")
            msg.exec_()
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText("Export Failed")
            msg.setInformativeText(str(e))
            msg.exec_()

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", f"Habit_Report_{YEAR}.pdf", "PDF (*.pdf)")
        if not path: return
        try:
            self.fig.savefig("temp_chart.png", facecolor='white', dpi=150, bbox_inches='tight')
            
            c = canvas.Canvas(path, pagesize=letter)
            w, h = letter
            
            # Header
            c.setFont("Helvetica-Bold", 26)
            c.setFillColor(colors.HexColor("#1A252F"))
            c.drawString(50, h - 60, f"Habit Dashboard {YEAR}")
            
            c.setFont("Helvetica", 11)
            c.setFillColor(colors.HexColor("#7F8C8D"))
            c.drawString(50, h - 80, f"Generated: {datetime.date.today().strftime('%B %d, %Y')}")
            
            # KPI Cards
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
                
                # Card background
                c.setFillColor(colors.HexColor(color + "15"))
                c.roundRect(x, y, 120, 60, 8, fill=1, stroke=0)
                
                # Border
                c.setStrokeColor(colors.HexColor(color))
                c.setLineWidth(2)
                c.roundRect(x, y, 120, 60, 8, fill=0, stroke=1)
                
                # Text
                c.setFillColor(colors.HexColor("#7F8C8D"))
                c.setFont("Helvetica-Bold", 10)
                c.drawCentredString(x+60, y+42, lbl)
                
                c.setFont("Helvetica-Bold", 18)
                c.setFillColor(colors.HexColor(color))
                c.drawCentredString(x+60, y+18, val)
            
            # Chart
            c.drawImage("temp_chart.png", 50, h - 450, width=500, height=200, preserveAspectRatio=True)
            
            c.showPage()
            c.save()
            
            if os.path.exists("temp_chart.png"): 
                os.remove("temp_chart.png")
            
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Success")
            msg.setText("PDF Export Complete!")
            msg.setInformativeText(f"Saved to: {path}")
            msg.exec_()
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText("Export Failed")
            msg.setInformativeText(str(e))
            msg.exec_()

if __name__ == "__main__":
    myappid = 'mycompany.habit.tracker.6.0' 
    try: 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except: 
        pass
    
    app = QApplication(sys.argv)
    
    # Set application-wide font
    app.setFont(QFont("Segoe UI", 10))
    
    if os.path.exists(resource_path(ICON_NAME)):
        app.setWindowIcon(QIcon(resource_path(ICON_NAME)))
    
    window = HabitApp()
    window.show()
    sys.exit(app.exec())