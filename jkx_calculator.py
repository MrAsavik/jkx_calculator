import os
import json
import csv
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- Configuration and Paths ---
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH  = os.path.join(BASE_DIR, 'config.json')
HISTORY_FILE = os.path.join(BASE_DIR, 'utility_history.csv')

# --- Load Config ---
def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config(CONFIG_PATH)
COEFF  = config['coefficients']
UI_CFG = config.get('ui', {})

# --- Helpers for parsing any date format ---
def _parse_date(s: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d.%m.%YT%H:%M:%S", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unknown date format: {s}")

# --- Initialization ---
def init_files():
    """Если CSV нет – создаём с новым заголовком (текущие показания + расходы + итог)."""
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f, delimiter=';')
            w.writerow([
                'date',
                'hot_curr',    # текущее показание горячей воды
                'cold_curr',   # текущее показание холодной воды
                'elec_curr',   # текущее показание электричества
                'hot_usage',   # расход горячей
                'cold_usage',  # расход холодной
                'elec_usage',  # расход эл-ва
                'total_cost'   # общая стоимость
            ])

# --- Data I/O ---
def read_history():
    """
    Читает HISTORY_FILE (delimiter=';') и возвращает кортеж списков:
    dates, hot_curr, cold_curr, elec_curr, hot_u, cold_u, elec_u, totals
    """
    dates = []; hot_c = []; cold_c = []; elec_c = []
    hot_u = []; cold_u = []; elec_u = []; totals = []
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            dates.append(_parse_date(row['date']))
            hot_c.append(float(row['hot_curr']))
            cold_c.append(float(row['cold_curr']))
            elec_c.append(float(row['elec_curr']))
            hot_u.append(float(row['hot_usage']))
            cold_u.append(float(row['cold_usage']))
            elec_u.append(float(row['elec_usage']))
            totals.append(float(row['total_cost']))
    return dates, hot_c, cold_c, elec_c, hot_u, cold_u, elec_u, totals

def write_new_values(curr, usage, total):
    """
    Добавляет в CSV строку:
      date;
      curr[0],curr[1],curr[2];
      usage[0],usage[1],usage[2];
      total
    """
    row = [
        datetime.now().isoformat(timespec='seconds'),
        curr[0], curr[1], curr[2],
        usage[0], usage[1], usage[2],
        total
    ]
    with open(HISTORY_FILE, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f, delimiter=';').writerow(row)

def get_last_readings():
    """
    Возвращает последние показания [hot_curr, cold_curr, elec_curr],
    либо [0.0,0.0,0.0] если записей нет.
    """
    dates, hot_c, cold_c, elec_c, *_ = read_history()
    if not dates:
        return [0.0, 0.0, 0.0]
    return [hot_c[-1], cold_c[-1], elec_c[-1]]

# --- Calculation ---
def calculate_utility_cost(prev, curr):
    """
    Вычисляет расход и общую стоимость:
      total, hot_u, cold_u, elec_u
    """
    if any(c < p for c, p in zip(curr, prev)):
        raise ValueError("Текущие показания не могут быть меньше предыдущих!")
    hot   = curr[0] - prev[0]
    cold  = curr[1] - prev[1]
    elec  = curr[2] - prev[2]
    sewage= hot + cold
    cost  = (
        hot   * COEFF['hot_water'] +
        cold  * COEFF['cold_water'] +
        sewage* COEFF['sewage'] +
        elec  * COEFF['electricity']
    )
    return round(cost, 2), hot, cold, elec

# --- Main Application ---
class UtilityApp(ctk.CTk):
    def __init__(self, config):
        super().__init__()
        # Appearance
        ctk.set_appearance_mode(UI_CFG.get('theme', 'dark'))
        ctk.set_default_color_theme(UI_CFG.get('color_theme', 'blue'))

        self.title("ЖКХ-CalculaTor")
        self._set_geometry("Расчет")

        # Ensure file and load last readings
        init_files()
        self.prev_values = get_last_readings()

        # Theme switch
        self.theme_switch = ctk.CTkOptionMenu(
            self, values=["light","dark"], command=self._on_theme_change
        )
        self.theme_switch.set(ctk.get_appearance_mode())
        self.theme_switch.grid(row=0, column=0, sticky="ne", padx=20, pady=10)

        # Tabview with auto-resize
        class ResizableTabview(ctk.CTkTabview):
            def set(inner, name):
                super().set(name)
                inner.master._set_geometry(name)

        self.tabview = ResizableTabview(self, width=900)
        self.tabview.add("Расчет"); self.tabview.add("История")
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_calc_tab()
        self._build_history_tab()

    def _on_theme_change(self, mode):
        ctk.set_appearance_mode(mode)

    def _set_geometry(self, tab_name):
        self.geometry("1200x800" if tab_name=="История" else "900x500")

    def _build_calc_tab(self):
        tab = self.tabview.tab("Расчет")
        tab.grid_columnconfigure(1, weight=1)
        frame = ctk.CTkFrame(tab, corner_radius=15)
        frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        frame.grid_columnconfigure(1, weight=1)

        labels = ["Горячая вода (м³):","Холодная вода (м³):","Электричество (кВт·ч):"]
        self.entries = []
        for i, txt in enumerate(labels):
            ctk.CTkLabel(frame, text=txt, anchor="w")\
               .grid(row=i, column=0, sticky="w", pady=5, padx=(10,5))
            ent = ctk.CTkEntry(frame, placeholder_text=str(self.prev_values[i]))
            ent.grid(row=i, column=1, sticky="ew", pady=5, padx=(5,10))
            self.entries.append(ent)

        self.btn_calc = ctk.CTkButton(
            frame, text="Рассчитать стоимость", command=self.on_calculate
        )
        self.btn_calc.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10, padx=20)

        self.btn_reset = ctk.CTkButton(
            frame, text="Новая калькуляция", command=self._reset_form, state="disabled"
        )
        self.btn_reset.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0,10), padx=20)

        self.result_lbl = ctk.CTkLabel(tab, text="", justify="left")
        self.result_lbl.grid(row=1, column=0, sticky="nw", padx=20, pady=(0,10))

        self.btn_copy = ctk.CTkButton(
            tab, text="Копировать результат", command=self._copy_result, state="disabled"
        )
        self.btn_copy.grid(row=1, column=1, sticky="ne", padx=20, pady=(0,10))

    def _build_history_tab(self):
        tab = self.tabview.tab("История")
        ctrl = ctk.CTkFrame(tab, fg_color="transparent")
        ctrl.pack(fill="x", padx=20, pady=(10,0))

        self.period_option = ctk.CTkOptionMenu(
            ctrl, values=["Все","3мес.","6мес.","1год"], command=lambda v: self._draw_history()
        )
        self.period_option.set("Все"); self.period_option.pack(side="left", padx=10)

        self.view_option = ctk.CTkSegmentedButton(
            ctrl, values=["Общий","Серии","Гисто"], command=lambda v: self._draw_history()
        )
        self.view_option.set("Общий"); self.view_option.pack(side="left", padx=10)

        self.hist_frame = ctk.CTkScrollableFrame(tab)
        self.hist_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self._draw_history()

    def on_calculate(self):
        try:
            curr = [float(e.get() or pv) for e,pv in zip(self.entries, self.prev_values)]
            total, hu, cu, eu = calculate_utility_cost(self.prev_values, curr)
        except ValueError as er:
            messagebox.showerror("Ошибка", str(er))
            return

        # lock inputs
        for e in self.entries: e.configure(state="disabled")
        self.btn_calc.configure(state="disabled")
        self.btn_copy.configure(state="normal")
        self.btn_reset.configure(state="normal")

        # show result
        self.result_lbl.configure(text=(
            f"Итоговая стоимость: {total} ₽\n"
            f"Горячая вода: {hu} м³\n"
            f"Холодная вода: {cu} м³\n"
            f"Электричество: {eu} кВт·ч"
        ))

        # write both curr and usage
        write_new_values(curr, [hu, cu, eu], total)
        self.prev_values = get_last_readings()
        self.tabview.set("История")
        self._draw_history()

    def _copy_result(self):
        txt = self.result_lbl.cget("text")
        self.clipboard_clear(); self.clipboard_append(txt)
        messagebox.showinfo("Скопировано", "Результат скопирован в буфер обмена")

    def _reset_form(self):
        self.result_lbl.configure(text="")
        self.prev_values = get_last_readings()
        for ent,pv in zip(self.entries,self.prev_values):
            ent.configure(state="normal")
            ent.delete(0, "end")
            ent.insert(0, str(pv))
        self.btn_calc.configure(state="normal")
        self.btn_copy.configure(state="disabled")
        self.btn_reset.configure(state="disabled")

    def _draw_history(self):
        for w in self.hist_frame.winfo_children(): w.destroy()

        dates, hot_c, cold_c, elec_c, hot_u, cold_u, elec_u, totals = read_history()
        period = self.period_option.get()
        if period!="Все":
            days = {"3мес.":90,"6мес.":180,"1год":365}[period]
            cutoff = datetime.now() - timedelta(days=days)
            filt = [(d,hu,cu,eu,t) 
                    for d,hu,cu,eu,t in zip(dates, hot_u, cold_u, elec_u, totals) if d>=cutoff]
            if filt:
                dates,hot_u,cold_u,elec_u,totals = zip(*filt)
            else:
                dates,hot_u,cold_u,elec_u,totals = [],[],[],[],[]

        # table
        ctk.CTkLabel(self.hist_frame,
                     text="Дата | Расход Г | Расход Х | Расход Э | Итого",
                     font=('Segoe UI',12,'bold')).pack(anchor='nw',padx=10,pady=(5,2))
        for d,hu,cu,eu,t in zip(dates, hot_u, cold_u, elec_u, totals):
            ctk.CTkLabel(self.hist_frame,
                         text=f"{d.date()} | {hu} | {cu} | {eu} | {t}"
            ).pack(anchor='nw',padx=10)

        # chart
        fig = Figure(dpi=100); ax = fig.add_subplot(111)
        labels = [d.date() for d in dates]
        view   = self.view_option.get()
        if view=="Общий":
            if totals: ax.plot(labels, totals, marker='o', label='Итого')
            ax.set_title("Общая стоимость"); ax.legend()
        elif view=="Серии":
            if hot_u: ax.plot(labels, hot_u, marker='o', label='Горячая')
            if cold_u: ax.plot(labels, cold_u, marker='o', label='Холодная')
            if elec_u: ax.plot(labels, elec_u, marker='o', label='Электричество')
            ax.set_title("Расходы по категориям"); ax.legend()
        else:
            w = 0.2; x=list(range(len(labels)))
            if hot_u: ax.bar([p-w for p in x], hot_u, w, label='Горячая')
            if cold_u: ax.bar(x, cold_u, w, label='Холодная')
            if elec_u: ax.bar([p+w for p in x], elec_u, w, label='Электричество')
            ax.set_xticks(x); ax.set_xticklabels(labels, rotation=45)
            ax.set_title("Гистограмма расходов"); ax.legend()

        ax.tick_params(axis='x', rotation=45)
        canvas = FigureCanvasTkAgg(fig, master=self.hist_frame)
        canvas.get_tk_widget().pack(fill='both', padx=10, pady=10)
        canvas.draw()

if __name__ == '__main__':
    app = UtilityApp(config)
    app.mainloop()
