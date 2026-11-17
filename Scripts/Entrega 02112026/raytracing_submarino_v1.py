#!/usr/bin/env python3
"""Primera simulación Monte Carlo 3D de un detector sin lente.

Ejemplo: python raytracing_submarino.py --receptor PIN --distancia 20

Dependencias: numpy y matplotlib. Unidades: nm, W, s, m, grados, mm².
La geometría usa una fuente puntual y un detector centrado en el eje +z.
Por convención, toda comprobación mayor, menor o igual a 0 se hizo respecto a 1e-15.
El ángulo de incidencia configura la dirección inicial respecto a +z en el
plano xz. El diezmado solo reduce las trayectorias dibujadas, no simuladas.  # Reduce las simuladas, preciamente para no hacer un programa tan computacionalmente elevado
# Sería bueno añadir todos los parámetros como --distancia y explicarlos aquí.

"""

import argparse
import math
from dataclasses import dataclass
from collections import Counter
import numpy as np

H_PLANCK = 6.62607015e-34
C0 = 299792458.0

@dataclass
class Config:
    longitud_onda_nm: float = 450.0
    receptor: str = 'PIN'
    potencia_w: float = 0.001
    angulo_deg: float = 0.0
    diezmado: int = 1
    distancia_m: float = 1.0
    intervalo_s: float = 1.0
    a: float = 0.18
    b: float = 0.11
    g: float = 0.924
    max_rayos: int = 100
    max_eventos: int = 10000
    limite_lateral_m: float = 200.0
    semilla: int = 42
    absorcion: str = 'eventos'


def nueva_direccion(u, g, rng):
    """HG para cos(psi); azimut uniforme y base local ortonormal."""

    # Creación del ángulo psi vertical
    xi = rng.random() # xi_1 : probabilidad acumulada del scattering para cierto mu
    # Condición para g = 0
    if abs(g) < 1e-6:     
        mu = 2.0 * xi - 1.0
    # Caso general de g
    else:
        # Calcular mu en función del xi generado
        mu = (1 + g*g - ((1-g*g)/(1-g+2*g*xi))**2)/(2*g) 
    mu = np.clip(mu, -1.0, 1.0)   # Se ajusta mu a los valores -1 ~ 1

    # Generación del ángulo azimutal
    phi = 2 * np.pi * rng.random()

    # Obtención de la nueva dirección y la base u'
    auxiliar = np.eye(3)[np.argmin(np.abs(u))]  # Calcula la dirección absoluta de u y selecciona su eje más pequeño. Elije ese eje de la identidad como el vector a (se explica el porqué)

    # e1 se calcula como la proyeccción de a en el eje de u y lego, restando, obtenemos la componente perpemndicular.
    e1 = auxiliar - np.dot(auxiliar, u) * u
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(u, e1)

    # Por la doc. mu = cos(psi) -> sin(psi) = sqrt(1-mu**2)
    nueva = mu*u + np.sqrt(max(0.0, 1-mu*mu)) * (np.cos(phi)*e1 + np.sin(phi)*e2)

    # Finalmente normalizamos para conseguir una base ortonormal
    return nueva / np.linalg.norm(nueva)


def distancia_salida(r, u, limite, distancia):
    """Primera salida de la caja: x,y=±limite; z=-distancia o +2*distancia."""

    # Define lso límites de las coordenadas x, y y z. Un array representa lso limites infereiores y el otro los superiores (es arbitrario)
    bajos = np.array([-limite, -limite, -distancia])
    altos = np.array([limite, limite, 2*distancia])
    candidatos = []
    for i in range(3):
        # Se busca si la dirección de u (en los 3 ejes, de ahí el for) es positivo (primera condición) o negativa (segunda). Se calcula la distancia hasta cada uno de lso puntos dependiendo de su dirección.
        # Todo este bloque está para comprobar si se sobrepasan  los límites y, por tanto, se debe descartar el rayo.
        if u[i] > 1e-15:
            candidatos.append((altos[i] - r[i]) / u[i])
        elif u[i] < -1e-15:
            candidatos.append((bajos[i] - r[i]) / u[i])
    return min(candidatos) if candidatos else math.inf


def simular(cfg):

    # Comprobamos si los parámetros son correctos.
    if cfg.longitud_onda_nm <= 0 or cfg.distancia_m <= 0 or cfg.intervalo_s <= 0:
        raise ValueError('Longitud de onda, distancia e intervalo deben ser positivos.')
    if cfg.potencia_w < 0 or cfg.a < 0 or cfg.b < 0 or not -1 < cfg.g < 1:
        raise ValueError('Potencia, a y b deben ser no negativos y -1 < g < 1.')
    if cfg.diezmado < 1 or cfg.max_rayos < 1 or cfg.max_eventos < 1 or cfg.limite_lateral_m <= 0:
        raise ValueError('Diezmado, número de rayos, eventos y límite deben ser positivos.')
    if not -90 < cfg.angulo_deg < 90:
        raise ValueError('El ángulo de lanzamiento debe estar entre -90 y 90 grados.')

    # Áreas de los fotodiodos
    areas_mm2 = {'PIN': 7.5, 'APD': 0.0314}  
    area = areas_mm2[cfg.receptor]
    radio = math.sqrt(area * 1e-6 / math.pi)   # Las áreas están en mm2. Son áreas de fotodiodos comerciales, son variables (pero se deberían introducir en mm2)
    energia = H_PLANCK * C0 / (cfg.longitud_onda_nm * 1e-9)

    # Calcular el flujo de fotones
    flujo = cfg.potencia_w / energia

    # Este parámetro está puesto por si se espera un flujo de más de un segundo, se usará para hacer operaciones con distintas modulaciones (para futuro)
    # Número de fotones por segundo (Potencia lumínica)
    esperados = flujo * cfg.intervalo_s

    # Esperanza de fotones, no realización entera; rayos igualmente ponderados.
    n = min(cfg.max_rayos, math.ceil(esperados)) if esperados > 0 else 0 # Se ajusta el número de rayo sal máximo establecido (definido arriba, en cfg)

    # Definir la aleatoriedad de la simulación 
    rng = np.random.default_rng(cfg.semilla)  # Si no hay una semilla específica, se aleatoriza.

    # Ángulo de entrada y dirección de porpagación inicial
    theta = math.radians(cfg.angulo_deg)
    u0 = np.array([math.sin(theta), 0.0, math.cos(theta)])

    #######
    # Estas inicializaciones son para preparar los resultados de la simulación.
    estados = Counter()   # Counter es un diccionario que tiene un número entero asignado como valor. Se irá aumentando a medida que ocurran los estados correspondientes (recepción = 73, absorción = 20, etc...)
    trayectorias = []    # Todas las trayectorias de lso fotones
    pesos_captados = []   # Todos los pesos de lso fotones
    distancias_captadas = []   # Todas las distancias totales de cada trayectoria.
    #######


    # Por cada uno de los fotones
    for indice in range(n):

        r = np.zeros(3)   # r es su vector de coordenadas
        u = u0.copy()     # u es su vector de dirección 
        peso = 1.0        # relevante si absorcion = continua
        distancia_total = 0.0
        puntos = [r.copy()] if indice % cfg.diezmado == 0 else None   # En este array se guardarán las coordenadas del fotón simulado.
        estado = 'limite_eventos'   # Se actualiza el estado. Si el rayo llega al recepto o se llega al máximo número de eventos, se reemplaza.

        # Se comenzará a generar el recorrido de los fotones
        for _ in range(cfg.max_eventos):
            tasa = cfg.a + cfg.b if cfg.absorcion == 'eventos' else cfg.b  # Si la absorción es por 'eventos' c = a + b, si no c = b porque la absorción se modelará como constante.
            s_interaccion = rng.exponential(1/tasa) if tasa > 0 else math.inf   # Distancia de interacción fotón <-> partícula. Si tasa = 0 no hay interacción con el medio.
            s_salida = distancia_salida(r, u, cfg.limite_lateral_m, cfg.distancia_m)
            s_receptor = (cfg.distancia_m - r[2])/u[2] if u[2] > 1e-15 and r[2] < cfg.distancia_m else math.inf   # Se comprueba si la distancia total (puede no ser paralela, de ahí el vector dirección dividiendo). Si la direccióon es nula y el receptor se ha superado se considera que el plano es inalcanzable.
            s = min(s_interaccion, s_salida, s_receptor)  # Esto es un selector de eventos, pues el primero siempre se cumpliría, el segundo y el tercero representan dos condiciones diferentes, pero al cumplirse se acaba la ejecución.
            r = r + s*u   # Se añade el valor recorrido a r
            distancia_total += s   # Se actualiza la distancia
            if cfg.absorcion == 'continua':
                peso *= math.exp(-cfg.a*s)   # Se actuaiza el valor del peso del trayecto del fotón. Solo pata 'continua'.
            if puntos is not None:
                puntos.append(r.copy())  # Solo se actualiza si el valor no es un diezmado. ACTUALIZACIÓN, SE COMPRUEBA ARRIBA SI EL VALOR ES NONE Y SE ELIMINARÍA UNA ITERACCIÓN DEL BUCLE.

            # Evento de recepción. Se tiene que comprobar si el fotón llegó al área del receptor.
            if s == s_receptor:
                if r[0]**2 + r[1]**2 <= radio**2:    # ACTUALIZACIÓN. COMPROBAR LAS COMPOENTES X E Y DE LA POSICIÓN r Y HACER EL PRODUCTO ESCALAR DE LOS MISMOS. COMPROBAR SI EL MODULO DEL RESULTADO ES MENOR AL RADIO DEL RECEPTOR.
                    estado = 'captado'  # Actualizamos el estado a 'captado'.
                    pesos_captados.append(peso)   # Se guarda el peso de la trayectoria.
                    distancias_captadas.append(distancia_total)   # Se guarda la distancia reciorrida en la trayectoria.
                else:
                    estado = 'fuera_del_detector'  # Falló la detección
                break
            if s == s_salida:
                estado = 'salida_del_dominio'    # Se incumplieron los límites del espacio de simulación.
                break

            # ACTUALIZACIÓN. SE PUEDE BUSCAR UNA FORMA DE QUE LAS INTERACCIONES CON EL MEDIO SEAN DEPENDIENTES DE LA PROBABILIDAD. CUANDO OCURRA ABSORCIÓN SE HAGA LA LÓGICA DE ABAJAO Y CUANDO OCURRA SCATTERING SE RECURRA A LA FUNCIÓN HG.
            if cfg.absorcion == 'eventos' and rng.random() < cfg.a / (cfg.a + cfg.b):   # Ocurrió una absorción, por lo que se elimina esta trayectoria y se considera que el fotón fue 'absorbido'. Solo para 'eventos'.
                estado = 'absorbido'
                break
            u = nueva_direccion(u, cfg.g, rng)   # El scattering está modelado según HG, por lo que siempre ocurre, solo qeu está fuertemente centrado en 0º (dependiente de g).
        
        # Actualiza los estados qeu ocurrieron
        estados[estado] += 1

        # Si existe una trayectoria,se añade a 'trayectorias', asignada a un estado concreto.
        if puntos is not None:
            trayectorias.append((np.array(puntos), estado))   # En este punto, 'puntos' tiene todos los componentes de las posiciones de los fotones en cada interacción.


    ########
    ##

    # Se calcula la media de los pesos de todas las trayectorias
    ganancia = sum(pesos_captados)/n if n else 0.0

    # Seguimos dentro de la fucnión 'simular()'. El resultado es un diccionario con los resultados calculados y los parámetros iniciales.
    return dict(area_mm2=area, radio_m=radio, energia_j=energia, flujo_s=flujo,
                fotones_esperados=esperados, n_rayos=n, estados=estados,
                ganancia=ganancia, potencia_receptor_w=cfg.potencia_w*ganancia,
                trayectorias=trayectorias, distancias=distancias_captadas)
    ##
    ########


def mostrar_grafica(resultado, cfg):
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    colores = {'captado': 'green', 'absorbido': 'red', 'fuera_del_detector': 'orange',
               'salida_del_dominio': 'gray', 'limite_eventos': 'purple'}
    for puntos, estado in resultado['trayectorias']:
        ax.plot(puntos[:, 2], puntos[:, 0], puntos[:, 1], color=colores[estado], alpha=.7, lw=1)
    ax.scatter([cfg.distancia_m], [0], [0], c='blue', marker='x', s=70, label='Centro del detector')
    ax.set(xlabel='z (m): eje del enlace', ylabel='x (m)', zlabel='y (m)',
           title='Trayectorias 3D: verde captado, rojo absorbido, naranja fuera')
    ax.legend()
    plt.tight_layout()
    plt.show()


def main():
    # Define p, el parser, como las opciones (--help existe).
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--lambda-nm', type=float, default=450, dest='longitud_onda_nm', help='Longitud de onda del emisor')
    p.add_argument('--receptor', type=str.upper, choices=['PIN', 'APD'], default='PIN', help='Tipo de receptor. En esta versión afecta al área de recpción')
    p.add_argument('--potencia', type=float, default=0.001, dest='potencia_w', help='Potencia óptica emitida [W]')
    p.add_argument('--angulo', type=float, default=0, dest='angulo_deg', help='Ángulo inicial respecto a +z [grados]')
    p.add_argument('--diezmado', type=int, default=1, help='Dibujar uno de cada N rayos')
    p.add_argument('--distancia', type=float, default=1, dest='distancia_m', help='distancia donde se situa el receptor')
    p.add_argument('--intervalo', type=float, default=1, dest='intervalo_s', help='Duración para calcular fotones esperados [s]')
    p.add_argument('--a', type=float, default=.18, help='Coeficiente de absorción [1/m]')
    p.add_argument('--b', type=float, default=.11, help='Coeficiente de scattering [1/m]')
    p.add_argument('--g', type=float, default=.924, help='Parámetro de anisotropía HG')
    p.add_argument('--max-rayos', type=int, default=100, dest='max_rayos', help='máximo número de simulaciones')
    p.add_argument('--max-eventos', type=int, default=10000, dest='max_eventos', help='máximo número de eventos que ocurren al calcular la simulación')
    p.add_argument('--limite-lateral', type=float, default=200, dest='limite_lateral_m', help='define los límites x e y del espacio de simualciones')
    p.add_argument('--semilla', type=int, default=42, help='define la semilla inicial para el rng')
    p.add_argument('--absorcion', choices=['eventos', 'continua'], default='eventos', help='"eventos" calcula la absorción según una probabilidad y la vuelve destructiva. "continua" hace una ponderación en base a pesos')
    p.add_argument('--sin-grafica', action='store_true', help='desactiva la gráfica de resultados')
    
    # Obtiene los parámetros qeu se le han pasado al programa.
    args = vars(p.parse_args())  # Conviente los parámetros en un diccionario
    sin_grafica = args.pop('sin_grafica')  # Este se elimina porqu eno pertenece a la clase Config()


    try:
        cfg = Config(**args)  # Claves y valores de args
        r = simular(cfg)
    except ValueError as exc:
        p.error(str(exc))

    # Se imprime por pantalla (siempre)
    print(f'Receptor: {cfg.receptor} | área: {r["area_mm2"]:.4g} mm² | radio equivalente: {r["radio_m"]*1e3:.4g} mm')
    print(f'Energía por fotón: {r["energia_j"]:.6g} J')
    print(f'Flujo emitido: {r["flujo_s"]:.6g} fotones/s')
    print(f'Fotones esperados en {cfg.intervalo_s:g} s: {r["fotones_esperados"]:.6g}')
    print(f'Rayos simulados: {r["n_rayos"]}; modo de absorción: {cfg.absorcion}')
    print(f'Coeficientes: a={cfg.a:g}, b={cfg.b:g}, c={cfg.a+cfg.b:g} m⁻¹; g={cfg.g:g}')
    print('Estados:', dict(r['estados']))
    print(f'Fracción óptica estimada: {r["ganancia"]:.6g}')
    print(f'Potencia óptica media estimada en el detector: {r["potencia_receptor_w"]:.6g} W')

    # Si no se ha captado ningún fotón
    if not r['estados'].get('captado', 0):
        print('Sin captaciones: esto no demuestra que la potencia real sea cero.')

    # Si hay trayectorias que han superado el límite de eventos
    if r['estados'].get('limite_eventos', 0):
        print('Aviso: hay trayectorias truncadas por el límite de eventos.')

    # Mostrar la gráfica 
    if not sin_grafica and r['n_rayos']:  # Tiene que haber trayectorias para mostrarla.
        mostrar_grafica(r, cfg)

if __name__ == '__main__':
    main()
