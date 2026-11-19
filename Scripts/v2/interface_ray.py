import math
import tkinter as tk
from tkinter import ttk 


class InterfaceRay(tk.Tk) :
    def __init__(self, database) :
        super().__init__() 
        self.title("Simulador submarino mediante propagación de rayos. Creador : Santiago Lage Orozco")
        self.geometry("10s00x660")
        self.minsize(820, 580)
        self.configure(bg='#f3f6fa')

        # Styles
        style = ttk.Style(self)
        style.theme_use('alt')

        # Main style types, preserved for backgrounds, fonts, etc
        style.configure('TFrame', background='#f3ffff')
        style.configure('TLabel', background='#f3f6fa', font=('Segoe UI', 11))
        style.configure('Title.TLabel', font=('Segoe UI', 22, 'bold'))
        style.configure('Result.TLabel', font=('Segoe UI', 17, 'bold'), foreground='#126a8a')

        # Data Frame
        data_frame = ttk.Frame(self, padding=24)
        data_frame.pack(fill='both', expand=True)
        ttk.Label(data_frame, text="Datos", style="Title.TLabel").pack(anchor="nw")

        body_data = ttk.Frame(data_frame)
        body_data.pack(fill='both', expand=True)

        datalist = database.list()




if __name__ == '__main__' :

    database = []
    app = InterfaceRay(database)
    app.mainloop()