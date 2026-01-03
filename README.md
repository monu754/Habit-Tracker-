# 🎯 Data-Driven Habit Tracker (2026)

`![App Screenshot](image.png)`

A sleek, desktop-based habit tracking application built with **Python**, **PySide6 (Qt)**, and **Matplotlib**. This tool allows users to track daily consistency across multiple habits and provides real-time analytical insights through a KPI dashboard and trend visualizations.

## ✨ Features

* **Interactive Habit Grid:** A 365-day scrollable interface with dynamic month-based color coding.
* **Automatic Highlighting:** The current date is automatically highlighted in gold to keep you focused.
* **KPI Dashboard:** Real-time calculation of:
    * **Today %:** Progress for the current day.
    * **Best Streak:** Your longest run of "Perfect Days" (all habits completed).
    * **Weekly/Monthly Averages:** Rolling completion rates to track long-term trends.
* **Data Visualization:** Integrated Matplotlib chart showing yearly consistency patterns.
* **Persistent Storage:** Automatically saves progress to a local JSON file.

## 🚀 Installation & Usage

### For Users
1. Download the `HabitTracker.exe` from the [Releases](https://github.com/monu754/Habit-Tracker-/releases/tag/v1.0.0) section.
2. Run the executable. No Python installation required!

### For Developers
1. Clone the repository:
   ```bash
   git clone [https://github.com/monu754/Habit-Tracker-.git](https://github.com/monu754/Habit-Tracker-.git)

2. Install the Dependencies:
    ```bash
    pip install PySide6 matplotlib

3. Run the application:
    ```bash
    python app.py


🛠️ Built With
PySide6: For a modern, high-performance Graphical User Interface.

Matplotlib: For rendering the yearly consistency trend graph.

JSON: For lightweight, local data persistence.


