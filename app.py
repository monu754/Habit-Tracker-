import sys, os, json, datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableView, QHeaderView, QFrame, QSizePolicy, QAbstractItemView
)
from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtGui import QColor, QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# --- CONFIGURATION ---
YEAR = 2026
HABITS = ["Workout", "Meditation", "Reading", "Coding", "Sleep 8h"]
DAYS = 365
DATA_FILE = "habit_data.json"

# Pastel colors for Month Backgrounds
MONTH_COLORS = {
    1: "#E3F2FD",  2: "#E8F5E9",  3: "#FFFDE7",  4: "#FCE4EC",
    5: "#F3E5F5",  6: "#E0F7FA",  7: "#FFF3E0",  8: "#E8EAF6",
    9: "#E0F2F1", 10: "#FBE9E7", 11: "#EFEBE9", 12: "#E1F5FE"
}

# --- DATA MODEL ---
class HabitModel(QAbstractTableModel):
    def __init__(self, data, dates, today_idx):
        super().__init__()
        self._data = data
        self._dates = dates
        self._today_idx = today_idx  # Store today's index for highlighting

    # +2 Rows: Row 0 = Month Name, Row 1 = Day Number, Row 2+ = Habits
    def rowCount(self, parent=None): return len(HABITS) + 2
    def columnCount(self, parent=None): return DAYS

    def data(self, index, role=Qt.DisplayRole):
        r, c = index.row(), index.column()
        
        # --- 1. FORCE BLACK TEXT ---
        if role == Qt.ForegroundRole:
            return QColor("#000000")

        # --- 2. ROW 0: MONTH NAMES ---
        if r == 0:
            if role == Qt.DisplayRole:
                # Show month name only on the 1st of the month
                d = self._dates[c]
                if d.day == 1 or c == 0:
                    return d.strftime("%B").upper()
                return ""
            if role == Qt.BackgroundRole:
                return QColor(MONTH_COLORS.get(self._dates[c].month, "#FFFFFF"))
            if role == Qt.FontRole:
                f = QFont()
                f.setBold(True)
                f.setPointSize(11)
                return f
            if role == Qt.TextAlignmentRole:
                return Qt.AlignCenter

        # --- 3. ROW 1: DAY NUMBERS ---
        if r == 1:
            if role == Qt.DisplayRole:
                return self._dates[c].strftime("%d")
            
            if role == Qt.BackgroundRole:
                # HIGHLIGHT: If this is today's column, use Gold
                if c == self._today_idx:
                    return QColor("#FFD700") # Gold Highlight for Header
                return QColor("#E5E7E9") 
                
            if role == Qt.FontRole:
                f = QFont()
                f.setBold(True)
                return f
            if role == Qt.TextAlignmentRole:
                return Qt.AlignCenter

        # --- 4. HABIT ROWS (Offset by 2) ---
        habit_idx = r - 2
        
        if role == Qt.BackgroundRole:
            # Priority 1: Completed Habit (Green)
            if self._data[habit_idx][c] == 1:
                return QColor("#2ECC71") # Green
            
            # Priority 2: Today's Column (Light Yellow Highlight)
            if c == self._today_idx:
                return QColor("#FFF9C4") # Light Yellow
            
            # Priority 3: Standard Striped Background
            return QColor("#FFFFFF") if habit_idx % 2 == 0 else QColor("#F8F9FA")
        
        if role == Qt.ToolTipRole:
            return f"{HABITS[habit_idx]} on {self._dates[c].strftime('%b %d')}"
            
        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            if section == 0: return ""       
            if section == 1: return "DAY"    
            return HABITS[section - 2]       

        if role == Qt.ForegroundRole:
            return QColor("#000000")
            
        return None

    def toggle(self, index):
        r, c = index.row(), index.column()
        if r < 2: return # Don't toggle header rows
        
        habit_idx = r - 2
        self._data[habit_idx][c] = 1 - self._data[habit_idx][c]
        self.dataChanged.emit(index, index)

# --- CUSTOM KPI CARD ---
class KPICard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            QFrame { 
                background-color: white; 
                border: 1px solid #BDC3C7; 
                border-radius: 8px; 
            }
            QLabel { border: none; background-color: transparent; }
        """)
        layout = QVBoxLayout(self)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #7F8C8D; font-size: 11px; font-weight: bold;")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        
        self.lbl_value = QLabel("0")
        self.lbl_value.setStyleSheet("color: #000000; font-size: 20px; font-weight: bold;")
        self.lbl_value.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        self.setFixedSize(140, 75)

    def set_value(self, val):
        self.lbl_value.setText(str(val))

# --- MAIN APP ---
class HabitApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_data()
        self.setup_ui()

    def init_data(self):
        self.start_date = datetime.date(YEAR, 1, 1)
        self.dates = [self.start_date + datetime.timedelta(days=i) for i in range(DAYS)]
        
        # --- TIME TRAVEL LOGIC (Determine Today) ---
        today = datetime.date.today()
        if today.year < YEAR: 
            self.current_date = self.start_date # Start of 2026
        elif today.year > YEAR:
            self.current_date = datetime.date(YEAR, 12, 31)
        else:
            self.current_date = today

        # Calculate index for today so we can pass it to the model
        self.today_idx = (self.current_date - self.start_date).days
        
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f: 
                self.habit_data = json.load(f)
        else:
            self.habit_data = [[0]*DAYS for _ in HABITS]

    def setup_ui(self):
        self.setWindowTitle(f"Habit Dashboard – {YEAR}")
        self.resize(1280, 850)
        self.setStyleSheet("""
            QWidget { background-color: #F0F2F5; font-family: 'Segoe UI', sans-serif; color: #000000; }
            QTableView { gridline-color: #E5E7E9; border: 1px solid #BDC3C7; }
            QHeaderView::section { background-color: #E5E7E9; border: none; padding: 4px; font-weight: bold; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. HEADER
        header_layout = QHBoxLayout()
        title = QLabel(f"Habit Dashboard – {YEAR}")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2C3E50;")
        
        date_str = f"{self.current_date.strftime('%B')} {self.current_date.day}, {self.current_date.year}"
        date_lbl = QLabel(f"Today: {date_str}")
        date_lbl.setStyleSheet("font-size: 14px; color: #566573; font-weight: bold;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(date_lbl)
        layout.addLayout(header_layout)

        # 2. KPI CARDS
        kpi_layout = QHBoxLayout()
        self.card_today = KPICard("TODAY %")
        self.card_streak = KPICard("BEST STREAK")
        self.card_weekly = KPICard("WEEKLY AVG")
        self.card_monthly = KPICard("MONTHLY AVG")
        
        for card in [self.card_today, self.card_streak, self.card_weekly, self.card_monthly]:
            kpi_layout.addWidget(card)
        kpi_layout.addStretch()
        layout.addLayout(kpi_layout)

        # 3. HABIT GRID
        self.table = QTableView()
        # Pass today_idx to the model here
        self.model = HabitModel(self.habit_data, self.dates, self.today_idx)
        self.table.setModel(self.model)
        
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setFixedWidth(100)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setColumnWidth(0, 40)
        for i in range(DAYS):
            self.table.setColumnWidth(i, 35)

        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.clicked.connect(self.on_cell_clicked)
        layout.addWidget(self.table, stretch=2)

        # 4. CHART
        self.fig = Figure(figsize=(8, 2), dpi=100)
        self.fig.patch.set_facecolor('#F0F2F5')
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setFixedHeight(220)
        layout.addWidget(self.canvas)

        self.apply_month_spans()
        self.update_analytics()

        # AUTO-SCROLL to Today
        if self.today_idx > 0:
            self.table.scrollTo(self.model.index(0, self.today_idx), QAbstractItemView.PositionAtCenter)

    def apply_month_spans(self):
        current_month = -1
        start_col = 0
        for c, date in enumerate(self.dates):
            if date.month != current_month:
                if current_month != -1:
                    self.table.setSpan(0, start_col, 1, c - start_col)
                current_month = date.month
                start_col = c
        self.table.setSpan(0, start_col, 1, DAYS - start_col)

    def on_cell_clicked(self, index):
        self.model.toggle(index)
        self.save_data()
        self.update_analytics()

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.habit_data, f)

    def update_analytics(self):
        # Calculations (same as before)
        completed_today = 0
        if 0 <= self.today_idx < DAYS:
            completed_today = sum(self.habit_data[r][self.today_idx] for r in range(len(HABITS)))
        today_pct = int((completed_today / len(HABITS)) * 100) if DAYS > 0 else 0
        
        best_streak = 0
        current_streak = 0
        for c in range(DAYS):
            if all(self.habit_data[r][c] == 1 for r in range(len(HABITS))):
                current_streak += 1
                best_streak = max(best_streak, current_streak)
            else:
                current_streak = 0

        weekly_avg = 0
        if self.today_idx >= 0:
            start_wk = max(0, self.today_idx - 6)
            days_count = (self.today_idx - start_wk) + 1
            if days_count > 0:
                total_complete = 0
                for c in range(start_wk, self.today_idx + 1):
                    total_complete += sum(self.habit_data[r][c] for r in range(len(HABITS)))
                weekly_avg = int((total_complete / (len(HABITS) * days_count)) * 100)

        monthly_avg = 0
        if self.today_idx >= 0:
            start_mo = max(0, self.today_idx - 29)
            days_count = (self.today_idx - start_mo) + 1
            if days_count > 0:
                total_complete = 0
                for c in range(start_mo, self.today_idx + 1):
                    total_complete += sum(self.habit_data[r][c] for r in range(len(HABITS)))
                monthly_avg = int((total_complete / (len(HABITS) * days_count)) * 100)

        self.card_today.set_value(f"{today_pct}%")
        self.card_streak.set_value(f"{best_streak} Days")
        self.card_weekly.set_value(f"{weekly_avg}%")
        self.card_monthly.set_value(f"{monthly_avg}%")

        # Graph
        daily_avg = [sum(self.habit_data[r][c] for r in range(len(HABITS))) / len(HABITS) * 100 for c in range(DAYS)]
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('#F0F2F5')
        ax.fill_between(range(DAYS), daily_avg, color='#3498DB', alpha=0.5)
        ax.plot(range(DAYS), daily_avg, color='#2980B9', linewidth=1.5)
        ax.set_title("Yearly Consistency Trend", fontsize=10, fontweight='bold', color='#2C3E50', pad=10)
        ax.set_ylabel("Completion (%)", fontsize=8, color='#566573')
        ax.set_xlabel("Day of Year", fontsize=8, color='#566573')
        ax.grid(True, axis='y', linestyle='--', alpha=0.3)
        ax.set_ylim(0, 105)
        ax.set_xlim(0, DAYS)
        ax.tick_params(axis='both', labelsize=8, colors='#566573')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#BDC3C7')
        ax.spines['bottom'].set_color('#BDC3C7')
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HabitApp()
    window.show()
    sys.exit(app.exec())