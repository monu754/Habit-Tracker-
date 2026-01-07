# 🎯 Data-Driven Habit Tracker (2026)

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![PySide6](https://img.shields.io/badge/UI-PySide6-green.svg)
![Matplotlib](https://img.shields.io/badge/Data-Matplotlib-orange.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A sleek, desktop-based habit tracking application built with **Python**, **PySide6 (Qt)**, and **Matplotlib**. This tool allows users to track daily consistency across multiple habits and provides real-time analytical insights through a KPI dashboard and trend visualizations.

<p align="center">
  <img src="screenshot.png" width="800" alt="Habit Tracker Dashboard">
</p>

## 🚀 Key Features
### 📅 Advanced Calendar System
* 365-Day View: A horizontally scrollable grid representing every single day of the year.

* Intuitive Tracking: Toggle habit completion status (Yes/No) with a simple click on the grid.

* Smart Visualization: Months are visually separated using alternating background colors for easier navigation.

* Today & Weekend Highlighting: The current date is highlighted in yellow, and weekends are marked in red to help you stay oriented.

* Auto-Scroll: On startup, the dashboard automatically scrolls to the current date.

### 📊 Real-Time Analytics
* KPI Cards: Four high-visibility cards providing instant feedback on your progress:

* Today: Percentage of habits completed for the current day.

* Best Streak: Your longest consecutive run of completing all habits.

* Weekly Avg: Completion percentage over the last 7 days.

* Monthly Avg: Completion percentage over the last 30 days.

* Annual Consistency Trend: A dynamic area-line chart visualizing your progress across the entire year.

* Monthly Breakdown: A bar chart comparing your average success rate month-by-month, featuring percentage labels above each bar.

### 🛠 Habit Management
* Full CRUD Support: Easily add new habits with specific times, edit existing ones, or delete habits you no longer wish to track.

* Hover-Sensitive Editing: A pencil icon (✏️) appears only when hovering over a habit name for a cleaner UI and quick modifications.

* Persistent Storage: Data is automatically saved to a local JSON file whenever changes are made.

### 🎨 Customization & Export
* Dual-Theme Engine: Seamlessly switch between Light Mode and Dark Mode. Every element, including graphs, adapts instantly.

* PDF Reporting: Export a professional summary including your current stats and snapshots of both your annual and monthly graphs.

* CSV Export: Generate a detailed spreadsheet containing your daily logs and a summarized performance section.

* Backup & Restore: Export your entire history to a standalone file to prevent data loss or move between devices.

### ⚡ Performance & Stability
* Anti-Wobble Design: Precisely calculated geometry ensures vertical stability, preventing the interface from "jittering" during horizontal scrolling.

* Shadow Effects: Modern UI with graphical drop shadows on cards and containers for a sleek, layered look.

## 🛠 Tech Stack
* **Language:** Python 3.x

* **GUI Framework:** PySide6 (Qt for Python)

* **Visualization:** Matplotlib

* **Reporting:** ReportLab (for PDF generation)

* **Data Handling:** JSON, CSV

## 🚀 Installation & Usage

### For Users
1.  Download the `HTracker.exe` from the [Releases](https://github.com/monu754/Habit-Tracker-/releases) section.
2.  Run the executable. No Python installation required!
3. Edit the habits and time-frame according to you by right-clicking on the habit

### For Developers
1.  Clone the repository:
    ```bash
    git clone https://github.com/monu754/Habit-Tracker-.git
    ```
2.  Install dependencies:
    ```bash
    pip install PySide6 matplotlib
    ```
3.  Run the application:
    ```bash
    python app.py
    ```



## ⚖️ License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
**Developed by Manotosh Mandal**