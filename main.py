import os
import json
import csv
from datetime import datetime, timedelta
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
            writer.writerow(['date', 'hot_usage', 'cold_usage', 'elec_usage', 'total_cost'])

# --- Data I/O ---
def read_previous_values():
    with open(VALUES_FILE, 'r') as f:
        lines = f.read().splitlines()
    return [float(x) for x in lines]


def write_new_values(curr, usage, total):
    with open(VALUES_FILE, 'w') as f:
        f.write("\n".join(str(v) for v in curr))
    with open(HISTORY_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(timespec='seconds')] + usage + [total])


def read_history():
    dates, hot_u, cold_u, elec_u, totals = [], [], [], [], []
    with open(HISTORY_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dates.append(datetime.fromisoformat(row['date']))
            hot_u.append(float(row['hot_usage']))
            cold_u.append(float(row['cold_usage']))
            elec_u.append(float(row['elec_usage']))
            totals.append(float(row['total_cost']))
    return dates, hot_u, cold_u, elec_u, totals

# --- Calculation ---
def calculate_utility_cost(prev, curr):
    if any(c < p for c, p in zip(curr, prev)):
        raise ValueError('Текущие показания не могут быть меньше предыдущих!')
    hot_u = curr[0] - prev[0]
    cold_u = curr[1] - prev[1]
    elec_u = curr[2] - prev[2]
    sewage_u = hot_u + cold_u
    cost = (
        hot_u * COEFF['hot_water'] +
        cold_u * COEFF['cold_water'] +
        sewage_u * COEFF['sewage'] +
        elec_u * COEFF['electricity']
    )
    total = round(cost, 2)
    return total, hot_u, cold_u, elec_u

# --- Main Application ---
class UtilityApp(ctk.CTk):
    def __init__(self, config):
        super().__init__()
        # Appearance settings
        ctk.set_appearance_mode(UI_CFG.get('theme', 'dark'))
        ctk.set_default_color_theme(UI_CFG.get('color_theme', 'blue'))

        # Window
        self.title("ЖКХ-CalculaTor")
        self._set_geometry('Расчет')
        init_files()
        self.prev_values = read_previous_values()

        # Theme toggle
        self.theme_switch = ctk.CTkOptionMenu(
            self, values=["light", "dark"], command=self._on_theme_change)
        self.theme_switch.set(ctk.get_appearance_mode())
        self.theme_switch.grid(row=0, column=0, sticky='ne', padx=20, pady=10)

        # Resizable Tabview
        class ResizableTabview(ctk.CTkTabview):
            def set(inner_self, name):
                super().set(name)
                inner_self.master._set_geometry(name)

        self.tabview = ResizableTabview(self, width=900)
        self.tabview.add("Расчет")
        self.tabview.add("История")
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Build tabs
        self._build_calc_tab()
        self._build_history_tab()

    def _on_theme_change(self, mode):
        ctk.set_appearance_mode(mode)

    def _set_geometry(self, tab_name):
        # Set window size based on active tab
        if tab_name == 'История':
            self.geometry('1200x800')
        else:
            self.geometry('900x500')

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
        ctrl_frame = ctk.CTkFrame(tab, fg_color="transparent")
        ctrl_frame.pack(fill='x', padx=20, pady=(10,0))
        self.period_option = ctk.CTkOptionMenu(ctrl_frame,
            values=["Все", "3 месяца", "6 месяцев", "1 год"],
            command=lambda v: self._draw_history())
        self.period_option.set("Все")
        self.period_option.pack(side='left', padx=10)
        self.view_option = ctk.CTkSegmentedButton(ctrl_frame,
            values=["Общий", "Серии", "Гистограмма"],
            command=lambda v: self._draw_history())
        self.view_option.set("Общий")
        self.view_option.pack(side='left', padx=10)
        self.hist_frame = ctk.CTkScrollableFrame(tab)
        self.hist_frame.pack(fill='both', expand=True, padx=20, pady=10)
        self._draw_history()

    def on_calculate(self):
        try:
            curr = [float(e.get() or pv) for e, pv in zip(self.entries, self.prev_values)]
            total, hu, cu, eu = calculate_utility_cost(self.prev_values, curr)
            self.result_lbl.configure(text=
                f"Итоговая стоимость: {total} ₽\n"
                f"Горячая вода: {hu} м³, Холодная вода: {cu} м³, Электричество: {eu} кВт·ч"
            )
            write_new_values(curr, [hu, cu, eu], total)
            self.prev_values = curr
            self.tabview.set("История")
            self._draw_history()
        except ValueError as e:
            messagebox.showerror('Ошибка ввода', str(e))

    def _draw_history(self):
        for widget in self.hist_frame.winfo_children():
            widget.destroy()
        dates, hot_u, cold_u, elec_u, totals = read_history()
        period = self.period_option.get()
        if period != "Все":
            days_map = {"3 месяца":90, "6 месяцев":180, "1 год":365}
            cutoff = datetime.now() - timedelta(days=days_map.get(period, 0))
            filtered = [(d, h, c, e, t) for d,h,c,e,t in zip(dates, hot_u, cold_u, elec_u, totals) if d >= cutoff]
            if filtered:
                dates, hot_u, cold_u, elec_u, totals = zip(*filtered)
            else:
                dates, hot_u, cold_u, elec_u, totals = [], [], [], [], []
        header = ctk.CTkLabel(self.hist_frame, text="Дата | Горячая | Холодная | Электр. | Итого", font=('Segoe UI', 12, 'bold'))
        header.pack(anchor='nw', padx=10, pady=(5,2))
        for d,h,c,e,t in zip(dates, hot_u, cold_u, elec_u, totals):
            ctk.CTkLabel(self.hist_frame, text=f"{d.date()} | {h} | {c} | {e} | {t}").pack(anchor='nw', padx=10)
        # Plotting
        fig = Figure(dpi=100)
        ax = fig.add_subplot(111)
        view = self.view_option.get()
        labels = [d.date() for d in dates]
        if view == "Общий":
            if totals:
                ax.plot(labels, totals, marker='o', linewidth=2)
            ax.set_title("Общая стоимость")
        elif view == "Серии":
            if hot_u:
                ax.plot(labels, hot_u, marker='o', label='Горячая')
            if cold_u:
                ax.plot(labels, cold_u, marker='o', label='Холодная')
            if elec_u:
                ax.plot(labels, elec_u, marker='o', label='Электричество')
            ax.set_title("Расходы по категориям")
            ax.legend()
        else:
            width = 0.2
            x = list(range(len(labels)))
            if hot_u:
                ax.bar([p - width for p in x], hot_u, width, label='Горячая')
            if cold_u:
                ax.bar(x, cold_u, width, label='Холодная')
            if elec_u:
                ax.bar([p + width for p in x], elec_u, width, label='Электричество')
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45)
            ax.set_title("Гистограмма расходов")
            ax.legend()
        ax.tick_params(axis='x', rotation=45)
        canvas = FigureCanvasTkAgg(fig, master=self.hist_frame)
        canvas.get_tk_widget().pack(fill='both', expand=False, padx=10, pady=10)
        canvas.draw()

if __name__ == '__main__':
    app = UtilityApp(config)
    app.mainloop()
