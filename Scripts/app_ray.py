import math
import tkinter as tk
from tkinter import ttk 


class Aplication(tk-Tk) :
    def __init__(self) :
        super().__init__() 
        self.title("Simulador submarino mediante propagación de rayos. Creador : Santiago Lage Orozco")
        self.geometry("1000x660")
        self.minsize(820, 580)
        self.configure(bg='#f3f6fa')

        # Styles
        style = ttk.Style(self)
        style.theme_use('alt')

        # Main style types, preserved for backgrounds, fonts, etc
        style.configure('TFrame', background='#f3ffff')
        style.configure('TLabel', background='#f3f6fa', font=('Segoe UI', 11))
        style.configure('Title.Tlabel', font=('Segoe UI', 22, 'bold'))
        style.configure('Result.TLabel', font=('Segoe UI', 17, 'bold'), foreground='#126a8a')

        # Header frame
        outer_frame = ttk.Frame(self, )