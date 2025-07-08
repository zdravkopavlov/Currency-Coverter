
import tkinter as tk
from tkinter import ttk
import os
import sys

import tempfile

LOCK_FILE = os.path.join(tempfile.gettempdir(), 'bgn_eur_converter.lock')

# Function to check for existing instance
def check_single_instance():
    if os.path.exists(LOCK_FILE):
        print("Another instance is already running.")
        sys.exit(0)
    else:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))

def remove_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

# Default exchange rate
DEFAULT_EXCHANGE_RATE = 1.95583

def convert(*args):
    try:
        bgn = float(entry_bgn.get())
        rate = float(entry_rate.get())
        eur = round(bgn / rate + 1e-8, 2)
        result_var.set(f"€{eur:.2f}")
    except ValueError:
        result_var.set("Invalid input")

def toggle_rate_lock():
    if entry_rate.cget("state") == "normal":
        entry_rate.config(state="disabled")
        btn_lock.config(text="🔒")
    else:
        entry_rate.config(state="normal")
        btn_lock.config(text="🔓")
    convert()

def close_on_escape(event=None):
    root.destroy()

# Check for existing instance
check_single_instance()

# Set up UI
root = tk.Tk()
root.title("Строймаркет Цаков")
root.geometry("500x360")
root.resizable(False, False)
root.bind("<Escape>", close_on_escape)

# Remove lock file on close
root.protocol("WM_DELETE_WINDOW", lambda: (remove_lock(), root.destroy()))

ttk.Label(root, text="Роска, тук въвеждаш сумата в лева:").pack(pady=(20, 10))
entry_bgn = ttk.Entry(root, font=("Arial", 30))
entry_bgn.pack()
entry_bgn.focus_set()
entry_bgn.bind("<KeyRelease>", convert)

result_var = tk.StringVar(value="€0.00")
ttk.Label(root, textvariable=result_var, font=("Arial", 30)).pack(pady=(20, 10))

frame = ttk.Frame(root)
frame.pack(pady=(10, 5))
ttk.Label(frame, text="Курс:").pack(side="left", padx=(0, 5))
entry_rate = ttk.Entry(frame, font=("Arial", 14), width=10)
entry_rate.insert(0, str(DEFAULT_EXCHANGE_RATE))
entry_rate.pack(side="left")
entry_rate.bind("<KeyRelease>", convert)

btn_lock = ttk.Button(frame, text="🔒", width=3, command=toggle_rate_lock)
btn_lock.pack(side="left", padx=(5, 0))
entry_rate.config(state="disabled")

root.mainloop()
