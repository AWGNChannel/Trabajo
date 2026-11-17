import math
import tkinter as tk
from tkinter import ttk 


class Aplicacion (tk.Tk) :
    def __init__(self) : 
        super().__init__()
        self.title('Título de la aplicacion . Subtítulo')
        self.geometry('1000x660')  # XY
        self.minsize(820, 580)
        self.configure(bg='#f3f6fa')  # RGB

        # Define el gestor de estilos y asigna el tema
        style = ttk.Style(self)
        style.theme_use('clam') # [aqua] macOS, step, clam, alt, default, classic, [vista, winxpnative, winnative] windows
        
        # Estilos para las partes de la ventana
        style.configure('TFrame', background='#f3ffff')
        style.configure('TLabel', background='#f3f6fa', font=('Segoe UI', 11))
        style.configure('Title.TLabel', font=('Segoe UI', 22, 'bold'))
        style.configure('Result.TLabel', font=('Segoe UI', 17, 'bold'), foreground='#126a8a')

        # Define un contenedor
        outer = ttk.Frame(self, padding=24)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='título . subtítulo', style='Title.TLabel').pack(anchor='w') # Anchor alinea el título al oeste (west)
        ttk.Label(outer, text='título secundario, anotaciones...').pack(anchor='w', pady=(6, 18)) # Añade 6px por arriba y 18px por abajo

        # Contenedor principal
        body = ttk.Frame(outer)
        body.pack(fill='both', expand=True)  # expand=True le permite a este contenedor ganar espacio cuando se amplia la ventana

        controls = ttk.Frame(body, padding=(0, 0, 22, 0))  # padding son los márgenes (izqd., arriba, drcha., abajo)
        controls.pack(side='left', fill='y')

        # Definición de variables
        self.n1 = tk.StringVar(value='1.000')
        self.n2 = tk.StringVar(value='1.333')
        self.theta = tk.StringVar(value='30')

        # Crea etiquetas para los campos y crea casillas para escribir los valores
        for label, var in [('Variable 1', self.n1), ('Variable 2', self.n2), ('Variable 3', self.theta)] :
            ttk.Label(controls, text=label).pack(anchor='w', pady=(10,5))
            ttk.Entry(controls, textvariable=var, width=28, font=('Segoe UI', 12)).pack(fill='x')

        # Crea un 'slider' para la 3era variable
        self.slider = ttk.Scale(controls, from_=0, to=90, command=self.deslizar)  # sefl.deslizr es el método que seutilizará al cambiar de posición
        self.slider.set(30)
        self.slider.pack(fill='x', pady=12)


        # Crea los botones para intercambiar las variables y para restablecer a los valores poor defecto
        ttk.Button(controls, text='Intercambiar variables',command=self.intercambiar).pack(fill='x', pady=5)
        ttk.Button(controls, text='Reestablecer variables',command=self.restablecer).pack(fill='x', pady=5)
        ttk.Label(controls, text='texto de apoyo adicional', font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(24, 10))

        # Crearemos las etiquetas de resultado y estado
        self.resultado = ttk.Label(controls, style='Result.TLabel', wraplength=265)  # Resultado actual (se modificará después)
        self.resultado.pack(anchor='w', pady=8)
        self.estado = ttk.Label(controls, wraplength=265)  # Mensajes adicionales
        self.estado.pack(anchor='w', pady=8)
        ttk.Label(controls, text='Texto informativo por si hacen falta, por ejemplo, instrucciones.', foreground='#536477').pack(anchor='w', pady=16)
        

        # Crearesmos el lienzo para el dibujo
        self.canvas = tk.Canvas(body, background='white', highlightthickness=0) # EL último parámetro controla el borde
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda event:self.actualizar())  # Este es el caso de que el lienzo cambie de tamaño
        # Cambios en las variables
        for var in (self.n1, self.n2, self.theta) :
            var.trace_add('write', lambda *args: self.actualizar()) # trace_add es un monitor, se activa cuando hay un cambio (escritura en este caso) y llama a la función actualizar()
        # Dibuja automaticamente
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


    def actualizar(self) :
        c = self.canvas
        c.delete('all')

        # Obtén los valores y comprueba que sean los correctos, luego haz las cuentas
        try :
            n1, n2, t1 = [
                float(v.get().replace(',', '.')) for v in (self.n1, self.n2, self.theta)
            ]

            t2, critico = 28.563, 0.000  # Aquí añades tu función matemática

        except (ValueError, OverflowError) as exc:
            self.resultado.configure(text='Revisa los parámetros')
            self.estado.configure(text=str(exc) if 'could not convert' not in str(exc) else 'Completa los tres campos con números válidos.')
            return    # La aplicación permanece abierta, solo no actualiza lso valores

        # Sincronizar el deslizador con la variable theta
        self.slider.configure(command='')
        self.slider.set(t1)  # Le llamamos 't1' arriba en lugar de 'theta'
        self.slider.configure(command=self.deslizar)
        # Actualiza los textos
        self.resultado.configure(text='Condición q' if t2 is None else f'θ₂ = {t2:.3f}°')
        self.estado.configure(text=(f'Condición 2: {critico:.3f}°' if critico is not None else 'Has incumplido la condición 2.') + ('\nHas llegado a un caso concreto.' if t1 == 90 else ''))
       
        # Preparar las coordenadas del dibujo
        w = max(c.winfo_width(), 350)
        h = max(c.winfo_height(), 380)  # Esos dos números son por referencia

        x, y = w/2, h/2
        length = min(w*.41, h*.36)   # Y estos valores?

        # Dibujado
        ## Dibujo de los medios y la normal entre ambos
        c.create_rectangle(0, 0, w, y, fill='#edf5ff', outline='')
        c.create_rectangle(0, y, w, h, fill='#d8f0ee', outline='')   # Posiciones

        c.create_line(0, y, w, y, fill='#8295a7', width=2) # Traza la horizontal
        c.create_line(x, 38, x, h-35, fill='#65758b', dash=(6,5))
        c.create_line(0, y, w, y, fill='#8295a7', width=2)
        c.create_line(x, 38, x, h - 35, fill='#65758b', dash=(6, 5))
        c.create_text(18, 22, anchor='w', text=f'Medio 1 · n₁ = {n1:g}', fill='#304966', font=('Segoe UI', 12))
        c.create_text(18, h - 22, anchor='w', text=f'Medio 2 · n₂ = {n2:g}', fill='#215e5b', font=('Segoe UI', 12))

        # Rayo incidente (radianes)
        a = math.radians(t1)
        c.create_line(
            x - length * math.sin(a),
            y - length * math.cos(a),
            x,
            y,
            arrow=tk.LAST,
            width=3,
            fill='#d77b13'
        )

        # Arco del ángulo incidente
        c.create_arc(
            x-55, y-55,
            x+55, y+55,
            start=90,
            extent=t1,
            style='arc',
            outline='#d77b13',
            width=2
        )
       
        # Dibujado del rayo refractado
        if t2 is not None :
            b = math.radians(t2)

            c.create_line(
                x, y,
                x + length * math.sin(b),
                y + length * math.cos(b),
                arrow=tk.LAST,
                width=3,
                fill='#087e8b'
            )
        # Si hay reflexión interna
        else : 
            c.create_line(
                x, y,
                x + length * math.sin(b),
                y - length * math.cos(b),
                arrow=tk.LAST,
                width=3,
                fill='#b04b81'
            )
        c.create_oval(
            x-4, y-4,
            x+4, y+4,
            fill='#243d50',
            outline=''
        )
        


if __name__ == '__main__':
    Aplicacion().mainloop()