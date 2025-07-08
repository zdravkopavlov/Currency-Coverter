
import tkinter as tk
from tkinter import ttk
import os
import sys
import msvcrt
import tempfile

# Locking setup to ensure only one instance
lock_file_path = os.path.join(tempfile.gettempdir(), 'bgn_eur_converter.mutex')
lock_file = None

def acquire_lock():
    global lock_file
    try:
        lock_file = open(lock_file_path, 'w')
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
    except (OSError, IOError):
        sys.exit(0)

def release_lock():
    global lock_file
    if lock_file:
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            lock_file.close()
            os.remove(lock_file_path)
        except:
            pass

acquire_lock()

DEFAULT_EXCHANGE_RATE = 1.95583

def from_bgn(*args):
    try:
        bgn = float(entry_bgn.get())
        eur = round(bgn / DEFAULT_EXCHANGE_RATE + 1e-8, 2)
        result_var_eur.set(f"€{eur:.2f}")
        entry_eur.delete(0, tk.END)
    except:
        result_var_eur.set("Въведи число")

def from_eur(*args):
    try:
        eur = float(entry_eur.get())
        bgn = round(eur * DEFAULT_EXCHANGE_RATE + 1e-8, 2)
        result_var_bgn.set(f"{bgn:.2f} лв.")
        entry_bgn.delete(0, tk.END)
    except:
        result_var_bgn.set("Въведи число")

def close_app(event=None):
    release_lock()
    root.destroy()

root = tk.Tk()
root.title("Строймаркет Цаков")
root.geometry("500x460")
root.resizable(False, False)
root.bind("<Escape>", close_app)
root.protocol("WM_DELETE_WINDOW", close_app)

# Input BGN → EUR
ttk.Label(root, text="Въведи сума в лева:").pack(pady=(15, 5))
entry_bgn = ttk.Entry(root, font=("Arial", 24))
entry_bgn.pack()
entry_bgn.focus_set()
entry_bgn.bind("<KeyRelease>", from_bgn)

result_var_eur = tk.StringVar(value="€0.00")
ttk.Label(root, textvariable=result_var_eur, font=("Arial", 24)).pack(pady=(10, 20))

# Input EUR → BGN
ttk.Label(root, text="Въведи сума в евро:").pack()
entry_eur = ttk.Entry(root, font=("Arial", 24))
entry_eur.pack()
entry_eur.bind("<KeyRelease>", from_eur)

result_var_bgn = tk.StringVar(value="0.00 лв.")
ttk.Label(root, textvariable=result_var_bgn, font=("Arial", 24)).pack(pady=(10, 10))

root.mainloop()
