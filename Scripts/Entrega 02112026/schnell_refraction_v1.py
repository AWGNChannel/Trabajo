"""Calculadora interactiva de Snell. Ejecutar: python refraccion_snell.py.
Solo requiere Python 3 con Tkinter. Ángulos medidos respecto a la normal.
"""
import math
import tkinter as tk
from tkinter import ttk


def calcular_refraccion(n1, n2, incidencia):
    """Devuelve (ángulo refractado o None si hay RIT, ángulo crítico o None)."""
    if not all(math.isfinite(v) for v in (n1, n2, incidencia)):
        raise ValueError('Introduce valores numéricos finitos.')
    if n1 <= 0 or n2 <= 0:
        raise ValueError('Los índices de refracción deben ser mayores que cero.')
    if not 0 <= incidencia <= 90:
        raise ValueError('El ángulo de incidencia debe estar entre 0° y 90°.')
    critico = math.degrees(math.asin(n2 / n1)) if n1 > n2 else None
    # Comparar ángulos evita desbordamientos al dividir índices muy grandes.
    if critico is not None and incidencia > critico + 1e-10:
        return None, critico
    seno = 0.0 if incidencia == 0 else (n1 / n2) * math.sin(math.radians(incidencia))
    critico = "n2 > n1"
    return math.degrees(math.asin(min(1.0, seno))), critico 





    
  
"""Calculadora interactiva de Snell. Ejecutar: python refraccion_snell.py.
Solo requiere Python 3 con Tkinter. Ángulos medidos respecto a la normal.
"""
import math
import tkinter as tk
from tkinter import ttk


def calcular_refraccion(n1, n2, incidencia):
    """Devuelve (ángulo refractado o None si hay RIT, ángulo crítico o None)."""
    if not all(math.isfinite(v) for v in (n1, n2, incidencia)):
        raise ValueError('Introduce valores numéricos finitos.')
    if n1 <= 0 or n2 <= 0:
        raise ValueError('Los índices de refracción deben ser mayores que cero.')
    if not 0 <= incidencia <= 90:
        raise ValueError('El ángulo de incidencia debe estar entre 0° y 90°.')
    critico = math.degrees(math.asin(n2 / n1)) if n1 > n2 else None
    # Comparar ángulos evita desbordamientos al dividir índices muy grandes.
    if critico is not None and incidencia > critico + 1e-10:
        return None, critico
    seno = 0.0 if incidencia == 0 else (n1 / n2) * math.sin(math.radians(incidencia))
    return math.degrees(math.asin(min(1.0, seno))), critico


class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Ley de Snell · Refracción')
        self.geometry('1000x660')
        self.minsize(820, 580)
        self.configure(bg='#f3f6fa')
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background='#f3f6fa')
        style.configure('TLabel', background='#f3f6fa', font=('Segoe UI', 11))
        style.configure('Title.TLabel', font=('Segoe UI', 22, 'bold'))
        style.configure('Result.TLabel', font=('Segoe UI', 17, 'bold'), foreground='#126a8a')
        outer = ttk.Frame(self, padding=24)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='Refracción · Ley de Snell', style='Title.TLabel').pack(anchor='w')
        ttk.Label(outer, text='Dos medios homogéneos separados por una interfaz plana.').pack(anchor='w', pady=(6, 18))
        body = ttk.Frame(outer)
        body.pack(fill='both', expand=True)
        controls = ttk.Frame(body, padding=(0, 0, 22, 0))
        controls.pack(side='left', fill='y')
        self.n1 = tk.StringVar(value='1.000')
        self.n2 = tk.StringVar(value='1.333')
        self.theta = tk.StringVar(value='30')
        for label, var in [('Índice del medio 1 · n₁', self.n1), ('Índice del medio 2 · n₂', self.n2), ('Ángulo de incidencia · θ₁ (°)', self.theta)]:
            ttk.Label(controls, text=label).pack(anchor='w', pady=(10, 5))
            ttk.Entry(controls, textvariable=var, width=28, font=('Segoe UI', 12)).pack(fill='x')
        self.slider = ttk.Scale(controls, from_=0, to=90, command=self.deslizar)
        self.slider.set(30)
        self.slider.pack(fill='x', pady=12)
        ttk.Button(controls, text='Intercambiar medios', command=self.intercambiar).pack(fill='x', pady=5)
        ttk.Button(controls, text='Restablecer', command=self.restablecer).pack(fill='x', pady=5)
        ttk.Label(controls, text='n₁ sen(θ₁) = n₂ sen(θ₂)', font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(24, 10))
        self.resultado = ttk.Label(controls, style='Result.TLabel', wraplength=265)
        self.resultado.pack(anchor='w', pady=8)
        self.estado = ttk.Label(controls, wraplength=265)
        self.estado.pack(anchor='w', pady=8)
        ttk.Label(controls, text='Todos los ángulos se miden desde\nla normal (línea discontinua).\n\nPuedes escribir decimales con\npunto o coma.', foreground='#536477').pack(anchor='w', pady=16)
        self.canvas = tk.Canvas(body, background='white', highlightthickness=0)
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda event: self.actualizar())
        for var in (self.n1, self.n2, self.theta):
            var.trace_add('write', lambda *args: self.actualizar())
        self.actualizar()

    def deslizar(self, value):
        self.theta.set(f'{float(value):.1f}')

    def intercambiar(self):
        a, b = self.n1.get(), self.n2.get()
        self.n1.set(b)
        self.n2.set(a)

    def restablecer(self):
        self.n1.set('1.000')
        self.n2.set('1.333')
        self.theta.set('30')

    def actualizar(self):
        c = self.canvas
        c.delete('all')
        try:
            n1, n2, t1 = [float(v.get().replace(',', '.')) for v in (self.n1, self.n2, self.theta)]
            t2, critico = calcular_refraccion(n1, n2, t1)
        except (ValueError, OverflowError) as exc:
            self.resultado.configure(text='Revisa los parámetros')
            self.estado.configure(text=str(exc) if 'could not convert' not in str(exc) else 'Completa los tres campos con números válidos.')
            return
        # Modificar el deslizador sin ejecutar su callback ni redondear la entrada.
        self.slider.configure(command='')
        self.slider.set(t1)
        self.slider.configure(command=self.deslizar)
        self.resultado.configure(text='Reflexión interna total' if t2 is None else f'θ₂ = {t2:.3f}°')
        self.estado.configure(text=(f'Ángulo crítico: {critico:.3f}°' if critico is not None else 'No hay ángulo crítico para este sentido de propagación.') + ('\nIncidencia rasante: caso límite.' if t1 == 90 else ''))
        w, h = max(c.winfo_width(), 350), max(c.winfo_height(), 380)
        x, y = w / 2, h / 2
        length = min(w * .41, h * .36)
        c.create_rectangle(0, 0, w, y, fill='#edf5ff', outline='')
        c.create_rectangle(0, y, w, h, fill='#d8f0ee', outline='')
        c.create_line(0, y, w, y, fill='#8295a7', width=2)
        c.create_line(x, 38, x, h - 35, fill='#65758b', dash=(6, 5))
        c.create_text(18, 22, anchor='w', text=f'Medio 1 · n₁ = {n1:g}', fill='#304966', font=('Segoe UI', 12))
        c.create_text(18, h - 22, anchor='w', text=f'Medio 2 · n₂ = {n2:g}', fill='#215e5b', font=('Segoe UI', 12))
        c.create_text(x + 9, 52, anchor='w', text='Normal', fill='#65758b')
        a = math.radians(t1)
        c.create_line(x - length * math.sin(a), y - length * math.cos(a), x, y, arrow=tk.LAST, width=3, fill='#d77b13')
        c.create_arc(x-55, y-55, x+55, y+55, start=90, extent=t1, style='arc', outline='#d77b13', width=2)
        c.create_text(15, 55, anchor='w', text=f'Incidente: {t1:.2f}°', fill='#aa5800')
        if t2 is not None:
            b = math.radians(t2)
            c.create_line(x, y, x + length * math.sin(b), y + length * math.cos(b), arrow=tk.LAST, width=3, fill='#087e8b')
            c.create_arc(x-65, y-65, x+65, y+65, start=270, extent=t2, style='arc', outline='#087e8b', width=2)
            c.create_text(15, h-55, anchor='w', text=f'Refractado: {t2:.2f}°', fill='#08636e')
        else:
            c.create_line(x, y, x + length * math.sin(a), y - length * math.cos(a), arrow=tk.LAST, width=3, fill='#b04b81')
            c.create_text(x, y+42, text='Sin rayo refractado propagante', fill='#963466')
        c.create_oval(x-4, y-4, x+4, y+4, fill='#243d50', outline='')


if __name__ == '__main__':
    Aplicacion().mainloop()

"""
n1,n2 = 1, 1.33
incidencia = 30
angulo_refractado, angulo_critico = calcular_refraccion(n1, n2, incidencia)
print(f"Ángulo de incidencia = {incidencia}. Ángulo refractado = {angulo_refractado}. Ángulo crítico = {angulo_critico}")"""