
import tkinter as tk
from tkinter import ttk

EXCHANGE_RATE = 1.95583

def convert():
    try:
        bgn = float(entry.get())
        eur = round(bgn / EXCHANGE_RATE + 1e-8, 2)
        result_var.set(f"€{eur:.2f}")
    except ValueError:
        result_var.set("Invalid input")

root = tk.Tk()
root.title("Строймаркет Цаков")
root.geometry("500x300")
root.resizable(False, False)

ttk.Label(root, text="Роска, тук въвеждаш сумата в лева:").pack(pady=(30, 50))
entry = ttk.Entry(root, font=("Arial", 30))
entry.pack()

result_var = tk.StringVar(value="€0.00")
ttk.Label(root, textvariable=result_var, font=("Arial", 30)).pack(pady=(30, 10))

ttk.Button(root, text="Convert", command=convert).pack()

root.mainloop()
