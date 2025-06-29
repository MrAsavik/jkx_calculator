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
        self.state("zoomed")  # старт во весь экран
        init_files()
        # Load last values
        self.prev_values = read_previous_values()
        # Layout
        self._configure_grid()
        self._create_widgets()
        self._draw_history()

    def _configure_grid(self):
        for i in range(8):
            self.grid_rowconfigure(i, weight=1)
        for j in range(2):
            self.grid_columnconfigure(j, weight=1)

    def _create_widgets(self):
        # CTkFrame for inputs
        frame = ctk.CTkFrame(self, corner_radius=15)
        frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)
        frame.grid_columnconfigure(1, weight=1)

        # Input fields with placeholder = last value
        labels = ['Горячая вода (м3):', 'Холодная вода (м3):', 'Электричество (кВт·ч):']
        self.entries = []
        for idx, text in enumerate(labels):
            lbl = ctk.CTkLabel(frame, text=text, anchor='w')
            lbl.grid(row=idx, column=0, sticky='w', padx=(10,5), pady=5)
            entry = ctk.CTkEntry(frame,
                                 placeholder_text=str(self.prev_values[idx]),
                                 width=200)
            entry.grid(row=idx, column=1, sticky='ew', padx=(5,10), pady=5)
            self.entries.append(entry)

        # Buttons aligned horizontally
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20)
        btn_frame.grid_columnconfigure((0,1), weight=1)

        self.btn_calc = ctk.CTkButton(btn_frame, text="Рассчитать стоимость",
                                      command=self.on_calculate)
        self.btn_calc.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.btn_prev = ctk.CTkButton(btn_frame, text="История показаний",
                                      command=self.on_show_history)
        self.btn_prev.grid(row=0, column=1, sticky="ew", padx=10, pady=10)

        # Result label
        self.result_lbl = ctk.CTkLabel(self, text="", justify='left')
        self.result_lbl.grid(row=2, column=0, columnspan=2, sticky="w", padx=40)

    def on_calculate(self):
        try:
            curr = [float(e.get() or pv) for e, pv in zip(self.entries, self.prev_values)]
            total, hu, cu, su, eu = calculate_utility_cost(self.prev_values, curr)
            text = (
                f"Итоговая стоимость: {total} ₽\n"
                f"Горячая вода: {hu} м³, Холодная вода: {cu} м³, Слив: {su} м³\n"
                f"Электричество: {eu} кВт·ч"
            )
            self.result_lbl.configure(text=text)
            write_new_values(curr, total)
            self.prev_values = curr
            self._draw_history()
        except ValueError as e:
            messagebox.showerror('Ошибка ввода', str(e))

    def on_show_history(self):
        # Open custom top-level instead of simple alert
        hist_win = ctk.CTkToplevel(self)
        hist_win.title("История показаний")
        hist_win.geometry("400x300")
        dates, totals = read_history()
        txt = "Дата\tВсего (₽)\n" + "\n".join(f"{d}\t{t}" for d, t in zip(dates, totals))
        text_box = ctk.CTkTextbox(hist_win, width=380, height=260, corner_radius=10)
        text_box.insert("0.0", txt)
        text_box.configure(state='disabled')
        text_box.pack(padx=10, pady=10, expand=True, fill='both')

    def _draw_history(self):
        dates, totals = read_history()
        # Prevent weird axis if only one point
        if len(dates) < 2:
            return
        # Remove old canvas
        for w in self.grid_slaves(row=3):
            w.destroy()
        fig = Figure(dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(dates, totals, marker='o', linewidth=2)
        ax.set_title("Динамика общей стоимости")
        ax.tick_params(axis='x', rotation=45)
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.get_tk_widget().grid(row=3, column=0, columnspan=2, sticky="nsew", padx=20, pady=(0,20))
        canvas.draw()

if __name__ == '__main__':    
    app = UtilityApp(config)
    app.mainloop()
