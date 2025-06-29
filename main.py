import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# --- Constants and File Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VALUES_FILE = os.path.join(BASE_DIR, 'utility_values.txt')
HISTORY_FILE = os.path.join(BASE_DIR, 'utility_history.csv')

# Utility coefficients
COEFF = {
    'hot_water': 186.37,
    'cold_water': 41.00,
    'sewage': 28.10,
    'electricity': 4.95
}

# --- File Initialization ---
def init_files():
    # Initialize values file if missing
    if not os.path.exists(VALUES_FILE):
        with open(VALUES_FILE, 'w') as f:
            f.write("0.0\n0.0\n0.0")
    # Initialize history CSV if missing
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'hot_water', 'cold_water', 'electricity'])

# --- Data I/O ---
def read_previous_values():
    with open(VALUES_FILE, 'r') as f:
        lines = f.read().splitlines()
    return [float(x) for x in lines]


def write_new_values(values):
    with open(VALUES_FILE, 'w') as f:
        for v in values:
            f.write(f"{v}\n")
    # Append to history
    with open(HISTORY_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(timespec='seconds')] + values)

# --- Computation ---
def calculate_utility_cost(prev, curr):
    # Ensure no negative usage
    if any(c < p for c, p in zip(curr, prev)):
        raise ValueError('Текущие показания не могут быть меньше предыдущих.')

    hot_usage = curr[0] - prev[0]
    cold_usage = curr[1] - prev[1]
    sewage_usage = hot_usage + cold_usage
    elec_usage = curr[2] - prev[2]

    hot_cost = hot_usage * COEFF['hot_water']
    cold_cost = cold_usage * COEFF['cold_water']
    sewage_cost = sewage_usage * COEFF['sewage']
    elec_cost = elec_usage * COEFF['electricity']

    total = round(hot_cost + cold_cost + sewage_cost + elec_cost, 2)
    return total, hot_usage, cold_usage, sewage_usage, elec_usage

# --- UI Application ---
def main():
    init_files()

    root = tk.Tk()
    root.title('Расчет стоимости ЖКХ')
    root.geometry('450x350')

    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill='both', expand=True)

    # Validation: only allow float input
    def validate_float(text):
        if text == '':
            return True
        try:
            float(text)
            return True
        except ValueError:
            return False

    vcmd = (root.register(validate_float), '%P')

    # Input fields
    labels = ['Горячая вода (м3):', 'Холодная вода (м3):', 'Электричество (кВт·ч):']
    entries = []
    for i, text in enumerate(labels):
        lbl = ttk.Label(main_frame, text=text)
        lbl.grid(row=i, column=0, sticky='w', pady=5)
        var = tk.StringVar()
        ent = ttk.Entry(main_frame, textvariable=var, validate='key', validatecommand=vcmd)
        ent.grid(row=i, column=1, pady=5)
        entries.append(var)

    result_var = tk.StringVar()
    result_lbl = ttk.Label(main_frame, textvariable=result_var, wraplength=400)
    result_lbl.grid(row=4, column=0, columnspan=2, pady=10)

    # Actions
    def on_calculate():
        try:
            curr = [float(var.get()) for var in entries]
            prev = read_previous_values()
            total, hu, cu, su, eu = calculate_utility_cost(prev, curr)
            result_var.set(
                f"Итоговая стоимость: {total} руб\n"
                f"Горячая вода: {hu} м3\n"
                f"Холодная вода: {cu} м3\n"
                f"Слив: {su} м3\n"
                f"Электричество: {eu} кВт·ч"
            )
            write_new_values(curr)
        except ValueError as e:
            messagebox.showerror('Ошибка', str(e))

    def on_show_previous():
        prev = read_previous_values()
        messagebox.showinfo('Прошлые показания',
                            f"Горячая вода: {prev[0]}\n"
                            f"Холодная вода: {prev[1]}\n"
                            f"Электричество: {prev[2]}")

    btn_calc = ttk.Button(main_frame, text='Рассчитать стоимость', command=on_calculate)
    btn_calc.grid(row=5, column=0, columnspan=2, pady=10)

    btn_prev = ttk.Button(main_frame, text='Показать прошлые значения', command=on_show_previous)
    btn_prev.grid(row=6, column=0, columnspan=2)

    root.mainloop()


if __name__ == '__main__':
    main()
