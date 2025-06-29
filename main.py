import os
import json
import csv
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- Configuration and Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
VALUES_FILE = os.path.join(BASE_DIR, 'utility_values.txt')
HISTORY_FILE = os.path.join(BASE_DIR, 'utility_history.csv')

# --- Load Config ---

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config(CONFIG_PATH)
COEFF = config['coefficients']
UI_CFG = config.get('ui', {})

# --- Initialization ---

def init_files():
    if not os.path.exists(VALUES_FILE):
        with open(VALUES_FILE, 'w') as f:
            f.write("0.0\n0.0\n0.0")
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'hot_water', 'cold_water', 'electricity', 'total_cost'])

# --- Data I/O ---

def read_previous_values():
    with open(VALUES_FILE, 'r') as f:
        lines = f.read().splitlines()
    return [float(x) for x in lines]


def write_new_values(curr, total):
    with open(VALUES_FILE, 'w') as f:
        f.write("\n".join(str(v) for v in curr))
    with open(HISTORY_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(timespec='seconds')] + curr + [total])


def read_history():
    dates, totals = [], []
    with open(HISTORY_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dates.append(row['date'])
            totals.append(float(row['total_cost']))
    return dates, totals

# --- Calculation ---

def calculate_utility_cost(prev, curr):
    if any(c < p for c, p in zip(curr, prev)):
        raise ValueError('Текущие показания не могут быть меньше предыдущих!')
    hot_u = curr[0] - prev[0]
    cold_u = curr[1] - prev[1]
    elec_u = curr[2] - prev[2]
    sewage_u = hot_u + cold_u
    cost = {
        'hot': hot_u * COEFF['hot_water'],
        'cold': cold_u * COEFF['cold_water'],
        'sewage': sewage_u * COEFF['sewage'],
        'elec': elec_u * COEFF['electricity']
    }
    total = round(sum(cost.values()), 2)
    return total, hot_u, cold_u, sewage_u, elec_u

# --- Main Application ---

class UtilityApp(ctk.CTk):
    def __init__(self, config):
        super().__init__()
        # Appearance
        ctk.set_appearance_mode(UI_CFG.get('theme', 'dark'))
        ctk.set_default_color_theme(UI_CFG.get('color_theme', 'blue'))
        # Window
        self.title("ЖКХ-CalculaTor")
        self.state("zoomed")
        init_files()
        self.prev_values = read_previous_values()
        # Tabview
        self.tabview = ctk.CTkTabview(self, width=800)
        self.tabview.add("Расчет")
        self.tabview.add("История")
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_calc_tab()
        self._build_history_tab()

    def _build_calc_tab(self):
        tab = self.tabview.tab("Расчет")
        tab.grid_columnconfigure(1, weight=1)
        frame = ctk.CTkFrame(tab, corner_radius=15)
        frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        frame.grid_columnconfigure(1, weight=1)
        labels = ['Горячая вода (м3):', 'Холодная вода (м3):', 'Электричество (кВт·ч):']
        self.entries = []
        for i, txt in enumerate(labels):
            lbl = ctk.CTkLabel(frame, text=txt, anchor='w')
            lbl.grid(row=i, column=0, sticky='w', pady=5, padx=(10,5))
            ent = ctk.CTkEntry(frame, placeholder_text=str(self.prev_values[i]))
            ent.grid(row=i, column=1, sticky='ew', pady=5, padx=(5,10))
            self.entries.append(ent)
        btn_calc = ctk.CTkButton(frame, text="Рассчитать стоимость", command=self.on_calculate)
        btn_calc.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10, padx=20)
        btn_hist = ctk.CTkButton(frame, text="Перейти в историю", command=lambda: self.tabview.set("История"))
        btn_hist.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5, padx=20)
        self.result_lbl = ctk.CTkLabel(tab, text="", justify='left')
        self.result_lbl.grid(row=1, column=0, sticky='nw', padx=20, pady=(0,10))

    def _build_history_tab(self):
        tab = self.tabview.tab("История")
        btn_refresh = ctk.CTkButton(tab, text="Обновить", command=self._draw_history)
        btn_refresh.pack(anchor='ne', padx=10, pady=10)
        self.hist_frame = ctk.CTkScrollableFrame(tab)
        self.hist_frame.pack(fill='both', expand=True, padx=20, pady=(0,20))
        # Initial draw
        self._draw_history()

    def on_calculate(self):
        try:
            curr = [float(e.get() or pv) for e, pv in zip(self.entries, self.prev_values)]
            total, hu, cu, su, eu = calculate_utility_cost(self.prev_values, curr)
            self.result_lbl.configure(text=
                f"Итоговая стоимость: {total} ₽\n"
                f"Горячая вода: {hu} м³, Холодная вода: {cu} м³, Слив: {su} м³\n"
                f"Электричество: {eu} кВт·ч"
            )
            write_new_values(curr, total)
            self.prev_values = curr
            self.tabview.set("История")
            self._draw_history()
        except ValueError as e:
            messagebox.showerror('Ошибка ввода', str(e))

    def _draw_history(self):
        # Clear history frame
        for widget in self.hist_frame.winfo_children():
            widget.destroy()
        dates, totals = read_history()
        # Table area
        header = ctk.CTkLabel(self.hist_frame, text="Дата | Итог (₽)", font=('Segoe UI', 12, 'bold'))
        header.pack(anchor='nw', padx=10, pady=(5,2))
        for d, t in zip(dates, totals):
            ctk.CTkLabel(self.hist_frame, text=f"{d} | {t}").pack(anchor='nw', padx=10)
        # Graph area
        fig = Figure(dpi=100)
        ax = fig.add_subplot(111)
        if len(dates) > 1:
            ax.plot(dates, totals, marker='o', linewidth=2)
        elif len(dates) == 1:
            ax.scatter(dates, totals, s=50)
            ax.text(0.5, 0.5, 'Только одна точка', transform=ax.transAxes,
                    ha='center', va='center')
        else:
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center')
        ax.set_title("Динамика общей стоимости")
        ax.tick_params(axis='x', rotation=45)
        canvas = FigureCanvasTkAgg(fig, master=self.hist_frame)
        canvas.get_tk_widget().pack(fill='both', expand=False, padx=10, pady=10)
        canvas.draw()

if __name__ == '__main__':
    app = UtilityApp(config)
    app.mainloop()
