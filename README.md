# 🎯 Data-Driven Habit Tracker (2026)

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![PySide6](https://img.shields.io/badge/UI-PySide6-green.svg)
![Matplotlib](https://img.shields.io/badge/Data-Matplotlib-orange.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A sleek, desktop-based habit tracking application built with **Python**, **PySide6 (Qt)**, and **Matplotlib**. This tool allows users to track daily consistency across multiple habits and provides real-time analytical insights through a KPI dashboard and trend visualizations.

<p align="center">
  <img src="screenshot.png" width="800" alt="Habit Tracker Dashboard">
</p>

## ✨ Features

* **Interactive Habit Grid:** A 365-day scrollable interface with dynamic month-based color coding and centered month headers.
* **Automatic Highlighting:** The current date column is automatically highlighted in **Gold** and **Yellow** to keep you focused.
* **KPI Dashboard:** Real-time calculation of:
    * **Today %:** Completion progress for the current day.
    * **Best Streak:** Your longest run of "Perfect Days" (all habits completed).
    * **Weekly/Monthly Averages:** Rolling completion rates to track long-term trends.
* **Data Visualization:** Integrated Matplotlib chart showing yearly consistency patterns with labeled axes.
* **Persistent Storage:** Automatically saves progress to a local `habit_data.json` file.

## 🚀 Installation & Usage

### For Users
1.  Download the `HabitTracker.exe` from the [Releases](https://github.com/monu754/Habit-Tracker-/releases) section.
2.  Run the executable. No Python installation required!

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

## 🛠️ Built With
* **PySide6:** For a modern, high-performance Graphical User Interface.
* **Matplotlib:** For rendering the yearly consistency trend graph.
* **JSON:** For lightweight, local data persistence.

## ⚖️ License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
**Developed by Manotosh Mandal**