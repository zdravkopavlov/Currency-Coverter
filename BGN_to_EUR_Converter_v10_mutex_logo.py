
import tkinter as tk
from tkinter import ttk, PhotoImage
import os
import sys
import msvcrt
import tempfile



def resource_path(relative):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.abspath("."), relative)

lock_file_path = os.path.join(tempfile.gettempdir(), 'bgn_eur_converter.mutex')
lock_file = None

def acquire_lock():
    global lock_file
    try:
        lock_file = open(lock_file_path, 'w')
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
    except (OSError, IOError):
        sys.exit(0)  # Exit silently if already locked

def release_lock():
    global lock_file
    if lock_file:
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            lock_file.close()
            os.remove(lock_file_path)
        except:
            pass

# Lock the file on startup
acquire_lock()

DEFAULT_EXCHANGE_RATE = 1.95583

def convert(*args):
    try:
        bgn_text = entry_bgn.get().replace(",", ".")
        rate_text = entry_rate.get().replace(",", ".")
        bgn = float(bgn_text)
        rate = float(rate_text)
        eur = round(bgn / rate + 1e-8, 2)
        result_var.set(f"€{eur:.2f}")
    except ValueError:
        result_var.set("Въведи число")

def toggle_rate_lock():
    if entry_rate.cget("state") == "normal":
        entry_rate.config(state="disabled")
        btn_lock.config(text="🔒")
    else:
        entry_rate.config(state="normal")
        btn_lock.config(text="🔓")
    convert()

def close_app(event=None):
    release_lock()
    root.destroy()

# Set up UI
root = tk.Tk()
root.title("Строймаркет Цаков")
root.geometry("450x400")
root.resizable(False, False)
root.bind("<Escape>", close_app)
root.protocol("WM_DELETE_WINDOW", close_app)

ttk.Label(root, text="Роска, тук въвеждаш сумата в лева:").pack(pady=(20, 10))
entry_bgn = ttk.Entry(root, font=("Arial", 20))
entry_bgn.pack()
entry_bgn.focus_set()
entry_bgn.bind("<KeyRelease>", convert)

result_var = tk.StringVar(value="€0.00")
ttk.Label(root, textvariable=result_var, font=("Arial", 50)).pack(pady=(20, 10))

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

logo = PhotoImage(file=resource_path("logo.png"))
logo_label = ttk.Label(root, image=logo)
logo_label.image = logo  # Keep reference
logo_label.pack(pady=(10, 10))

root.mainloop()
