import sys, os, json, csv, datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableView, QHeaderView, QFrame, QSizePolicy, 
    QAbstractItemView, QPushButton, QMenu, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QAbstractTableModel, QSize
from PySide6.QtGui import QColor, QFont, QAction, QIcon, QPixmap, QPainter

# Matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# --- CONFIGURATION ---
YEAR = 2026
HABITS = ["Workout", "Meditation", "Reading", "Coding", "Sleep 8h"]
DAYS = 365
DATA_FILE = "habit_data.json"

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
        self._today_idx = today_idx 

    def rowCount(self, parent=None): return len(HABITS) + 2
    def columnCount(self, parent=None): return DAYS

    def data(self, index, role=Qt.DisplayRole):
        r, c = index.row(), index.column()
        
        if role == Qt.ForegroundRole: return QColor("#000000")

        # Row 0: Month Names
        if r == 0:
            if role == Qt.DisplayRole:
                d = self._dates[c]
                if d.day == 1 or c == 0: return d.strftime("%B").upper()
                return ""
            if role == Qt.BackgroundRole:
                return QColor(MONTH_COLORS.get(self._dates[c].month, "#FFFFFF"))
            if role == Qt.FontRole:
                f = QFont(); f.setBold(True); f.setPointSize(11)
                return f
            if role == Qt.TextAlignmentRole: return Qt.AlignCenter

        # Row 1: Day Numbers
        if r == 1:
            if role == Qt.DisplayRole: return self._dates[c].strftime("%d")
            if role == Qt.BackgroundRole:
                if c == self._today_idx: return QColor("#FFD700") 
                return QColor("#E5E7E9") 
            if role == Qt.FontRole:
                f = QFont(); f.setBold(True); return f
            if role == Qt.TextAlignmentRole: return Qt.AlignCenter

        # Row 2+: Habits
        habit_idx = r - 2
        if role == Qt.BackgroundRole:
            if self._data[habit_idx][c] == 1: return QColor("#2ECC71") # Green
            if c == self._today_idx: return QColor("#FFF9C4") # Today Highlight
            return QColor("#FFFFFF") if habit_idx % 2 == 0 else QColor("#F8F9FA")
        
        if role == Qt.ToolTipRole:
            return f"{HABITS[habit_idx]} on {self._dates[c].strftime('%b %d')}"
        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            if section == 0: return ""; 
            if section == 1: return "DAY"; 
            return HABITS[section - 2]
        if role == Qt.ForegroundRole: return QColor("#000000")
        return None

    def toggle(self, index):
        r, c = index.row(), index.column()
        if r < 2: return 
        habit_idx = r - 2
        self._data[habit_idx][c] = 1 - self._data[habit_idx][c]
        self.dataChanged.emit(index, index)

# --- KPI CARD ---
class KPICard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("QFrame { background-color: white; border: 1px solid #BDC3C7; border-radius: 8px; } QLabel { border: none; background-color: transparent; }")
        layout = QVBoxLayout(self)
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #7F8C8D; font-size: 11px; font-weight: bold;")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_value = QLabel("0")
        self.lbl_value.setStyleSheet("color: #000000; font-size: 20px; font-weight: bold;")
        self.lbl_value.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_title); layout.addWidget(self.lbl_value)
        self.setFixedSize(140, 75)
    def set_value(self, val): self.lbl_value.setText(str(val))

# --- MAIN APP ---
class HabitApp(QWidget):
    def __init__(self):
        super().__init__()
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
        
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f: self.habit_data = json.load(f)
        else: self.habit_data = [[0]*DAYS for _ in HABITS]

    def create_color_icon(self, color_hex):
        """Generates a simple colored square icon dynamically"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(color_hex))
        return QIcon(pixmap)

    def setup_ui(self):
        self.setWindowTitle(f"Habit Dashboard – {YEAR}")
        self.resize(1280, 850)
        self.setStyleSheet("""
            QWidget { background-color: #F0F2F5; font-family: 'Segoe UI', sans-serif; color: #000000; }
            QTableView { gridline-color: #E5E7E9; border: 1px solid #BDC3C7; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20); layout.setSpacing(15)

        # 1. HEADER
        header_layout = QHBoxLayout()
        title = QLabel(f"Habit Dashboard – {YEAR}")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2C3E50;")
        
        # --- EXPORT BUTTON & MENU ---
        btn_export = QPushButton("📥 Export Report  ▼")
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
                border: none;
            }
            QPushButton:hover { background-color: #2980B9; }
            QPushButton::menu-indicator { 
                image: none; /* Hide default ugly arrow, we added text arrow */
            }
        """)
        
        # Custom Styled Menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                padding: 5px 0px;
            }
            QMenu::item {
                padding: 8px 25px 8px 10px; /* Top Right Bottom Left */
                font-size: 13px;
                color: #2C3E50;
            }
            QMenu::item:selected {
                background-color: #F4F6F8;
                color: #2980B9;
            }
            QMenu::icon {
                padding-left: 10px;
            }
        """)

        # Action: CSV (Green Icon)
        action_csv = QAction("Export as CSV (Data)", self)
        action_csv.setIcon(self.create_color_icon("#27AE60")) # Green
        action_csv.triggered.connect(self.export_csv)
        
        # Action: PDF (Red Icon)
        action_pdf = QAction("Export as PDF (Report)", self)
        action_pdf.setIcon(self.create_color_icon("#E74C3C")) # Red
        action_pdf.triggered.connect(self.export_pdf)
        
        menu.addAction(action_csv)
        menu.addAction(action_pdf)
        btn_export.setMenu(menu)

        date_str = f"{self.current_date.strftime('%B')} {self.current_date.day}, {self.current_date.year}"
        date_lbl = QLabel(f"Today: {date_str}")
        date_lbl.setStyleSheet("font-size: 14px; color: #566573; font-weight: bold;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(btn_export)
        header_layout.addSpacing(15)
        header_layout.addWidget(date_lbl)
        layout.addLayout(header_layout)

        # 2. KPI CARDS
        kpi_layout = QHBoxLayout()
        self.card_today = KPICard("TODAY %")
        self.card_streak = KPICard("BEST STREAK")
        self.card_weekly = KPICard("WEEKLY AVG")
        self.card_monthly = KPICard("MONTHLY AVG")
        for c in [self.card_today, self.card_streak, self.card_weekly, self.card_monthly]: kpi_layout.addWidget(c)
        kpi_layout.addStretch()
        layout.addLayout(kpi_layout)

        # 3. HABIT GRID
        self.table = QTableView()
        self.model = HabitModel(self.habit_data, self.dates, self.today_idx)
        self.table.setModel(self.model)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setFixedWidth(100)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setColumnWidth(0, 40)
        for i in range(DAYS): self.table.setColumnWidth(i, 35)
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
        if self.today_idx > 0: self.table.scrollTo(self.model.index(0, self.today_idx), QAbstractItemView.PositionAtCenter)

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
        with open(DATA_FILE, "w") as f: json.dump(self.habit_data, f)

    def update_analytics(self):
        comp_today = sum(self.habit_data[r][self.today_idx] for r in range(len(HABITS))) if 0 <= self.today_idx < DAYS else 0
        self.today_pct = int((comp_today / len(HABITS)) * 100)
        
        self.best_streak = 0
        curr = 0
        for c in range(DAYS):
            if all(self.habit_data[r][c] == 1 for r in range(len(HABITS))): curr+=1; self.best_streak = max(self.best_streak, curr)
            else: curr=0

        self.weekly_avg = 0
        if self.today_idx >= 0:
            start = max(0, self.today_idx - 6)
            total = sum(sum(self.habit_data[r][c] for r in range(len(HABITS))) for c in range(start, self.today_idx+1))
            self.weekly_avg = int((total / (len(HABITS) * ((self.today_idx-start)+1))) * 100)

        self.monthly_avg = 0
        if self.today_idx >= 0:
            start = max(0, self.today_idx - 29)
            total = sum(sum(self.habit_data[r][c] for r in range(len(HABITS))) for c in range(start, self.today_idx+1))
            self.monthly_avg = int((total / (len(HABITS) * ((self.today_idx-start)+1))) * 100)

        self.card_today.set_value(f"{self.today_pct}%")
        self.card_streak.set_value(f"{self.best_streak} Days")
        self.card_weekly.set_value(f"{self.weekly_avg}%")
        self.card_monthly.set_value(f"{self.monthly_avg}%")

        daily_avg = [sum(self.habit_data[r][c] for r in range(len(HABITS))) / len(HABITS) * 100 for c in range(DAYS)]
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('#F0F2F5')
        ax.fill_between(range(DAYS), daily_avg, color='#3498DB', alpha=0.5)
        ax.plot(range(DAYS), daily_avg, color='#2980B9', linewidth=1.5)
        ax.set_title("Yearly Consistency Trend", fontsize=10, fontweight='bold', color='#2C3E50', pad=10)
        ax.set_ylim(0, 105); ax.set_xlim(0, DAYS); ax.axis('off')
        self.canvas.draw()

    # --- EXPORT CSV ---
    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV Report", f"Habit_Report_{YEAR}.csv", "CSV Files (*.csv)")
        if not path: return
        
        try:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Date"] + HABITS + ["Daily Completion %"])
                for c, date in enumerate(self.dates):
                    row = [date.strftime("%Y-%m-%d")]
                    daily_sum = 0
                    for r in range(len(HABITS)):
                        val = self.habit_data[r][c]
                        row.append("Completed" if val == 1 else "Missed")
                        daily_sum += val
                    row.append(f"{int(daily_sum/len(HABITS)*100)}%")
                    writer.writerow(row)
            QMessageBox.information(self, "Success", f"Data exported successfully to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # --- EXPORT PDF ---
    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", f"Habit_Report_{YEAR}.pdf", "PDF Files (*.pdf)")
        if not path: return

        try:
            self.fig.savefig("temp_chart.png", facecolor='#F0F2F5')
            c = canvas.Canvas(path, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 24)
            c.drawString(50, height - 60, f"Habit Dashboard Report - {YEAR}")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 85, f"Generated on: {datetime.date.today().strftime('%B %d, %Y')}")

            y_kpi = height - 160
            c.setStrokeColor(colors.lightgrey)
            c.setFillColor(colors.whitesmoke)
            labels = ["Today Completion", "Best Streak", "Weekly Average", "Monthly Average"]
            values = [f"{self.today_pct}%", f"{self.best_streak} Days", f"{self.weekly_avg}%", f"{self.monthly_avg}%"]
            
            for i in range(4):
                x_pos = 50 + (i * 130)
                c.rect(x_pos, y_kpi, 120, 60, fill=1)
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 10)
                c.drawCentredString(x_pos + 60, y_kpi + 40, labels[i])
                c.setFont("Helvetica-Bold", 18)
                c.drawCentredString(x_pos + 60, y_kpi + 15, values[i])
                c.setFillColor(colors.whitesmoke)

            c.drawImage("temp_chart.png", 50, height - 400, width=500, height=180)

            y_table = height - 450
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y_table, "Monthly Completion Rates")
            
            y_row = y_table - 30
            c.setFont("Helvetica", 10)
            
            c.drawString(50, y_row, "Month")
            c.drawString(200, y_row, "Completion %")
            y_row -= 20
            c.line(50, y_row + 15, 300, y_row + 15)

            current_month = -1
            month_total = 0
            month_days = 0
            
            for i, date in enumerate(self.dates):
                if date.month != current_month:
                    if current_month != -1:
                        avg = int((month_total / (len(HABITS) * month_days)) * 100) if month_days > 0 else 0
                        c.drawString(50, y_row, datetime.date(YEAR, current_month, 1).strftime("%B"))
                        c.drawString(200, y_row, f"{avg}%")
                        y_row -= 20
                    current_month = date.month
                    month_total = 0
                    month_days = 0
                month_total += sum(self.habit_data[r][i] for r in range(len(HABITS)))
                month_days += 1
            
            avg = int((month_total / (len(HABITS) * month_days)) * 100) if month_days > 0 else 0
            c.drawString(50, y_row, datetime.date(YEAR, current_month, 1).strftime("%B"))
            c.drawString(200, y_row, f"{avg}%")

            c.save()
            if os.path.exists("temp_chart.png"): os.remove("temp_chart.png")
            QMessageBox.information(self, "Success", f"PDF Report saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HabitApp()
    window.show()
    sys.exit(app.exec())