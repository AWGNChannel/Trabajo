import math
from dataclasses import dataclass

from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
import matplotlib.pyplot as plt


# ============================================================
# UTILIDADES
# ============================================================

def db_to_linear(db):
    """Convierte una razón de potencia en dB a escala lineal."""
    return 10 ** (db / 10)


def linear_to_db(value):
    """Convierte una razón de potencia lineal a dB."""
    if value <= 0:
        return -math.inf

    return 10 * math.log10(value)


# ============================================================
# FUENTE
# ============================================================

@dataclass
class Source:
    """
    Fuente óptica.

    x, y:
        Posición de la fuente.

    power_dbm:
        Potencia óptica de entrada en dBm.

    theta_i_deg:
        Ángulo de incidencia theta_i respecto de la normal
        a la discontinuidad d1.
    """

    x: float = 0.0
    y: float = 0.0

    power_dbm: float = 0.0
    theta_i_deg: float = 30.0


# ============================================================
# DISCONTINUIDAD ENTRE MEDIOS
# ============================================================

@dataclass
class DielectricInterface:
    """
    Interfaz plana entre dos medios.

    La interfaz se encuentra en x = x.

    n1:
        Índice del medio donde se encuentra la fuente.

    n2:
        Índice del segundo medio.

    polarization:
        's' o 'p'.
    """

    x: float

    n1: float = 1.33
    n2: float = 1.4905

    polarization: str = "s"

    # --------------------------------------------------------
    # LEY DE SNELL
    # --------------------------------------------------------

    def transmitted_angle(self, theta_i):
        """
        Calcula theta_t usando la ley de Snell.

        Los ángulos se reciben/devuelven en radianes.
        """

        value = (self.n1 / self.n2) * math.sin(theta_i)

        if abs(value) > 1:
            raise ValueError(
                "Se produce reflexión interna total: "
                "no existe ángulo transmitido real."
            )

        return math.asin(value)

    # --------------------------------------------------------
    # FRESNEL
    # --------------------------------------------------------

    def fresnel_reflectance(self, theta_i, theta_t):
        """
        Coeficiente de reflexión de POTENCIA.
        """

        n1 = self.n1
        n2 = self.n2

        if self.polarization.lower() == "s":

            r = (
                n1 * math.cos(theta_i)
                - n2 * math.cos(theta_t)
            ) / (
                n1 * math.cos(theta_i)
                + n2 * math.cos(theta_t)
            )

        elif self.polarization.lower() == "p":

            r = (
                n2 * math.cos(theta_i)
                - n1 * math.cos(theta_t)
            ) / (
                n2 * math.cos(theta_i)
                + n1 * math.cos(theta_t)
            )

        else:
            raise ValueError(
                "La polarización debe ser 's' o 'p'."
            )

        return r ** 2

    def fresnel_transmittance(self, theta_i, theta_t):
        """
        Coeficiente de transmisión de potencia.

        Para una interfaz sin absorción:
            T = 1 - R
        """

        R = self.fresnel_reflectance(
            theta_i,
            theta_t
        )

        return 1 - R


# ============================================================
# ESPEJO
# ============================================================

@dataclass
class Mirror:
    """
    Espejo plano situado en x = x.

    reflectivity:
        Reflectividad en potencia.

        1.0 -> reflector perfecto.
    """

    x: float
    reflectivity: float = 1.0


# ============================================================
# RECEPTOR
# ============================================================

@dataclass
class Receiver:
    """
    El receptor NO tiene posición fija.

    Su posición se calcula siguiendo el rayo reflejado.
    """

    x: float
    y: float = 0.0

    received_power_dbm: float = -math.inf


# ============================================================
# RESULTADOS
# ============================================================

@dataclass
class SimulationResult:

    theta_i_deg: float
    theta_t_deg: float

    phi_i_deg: float
    phi_r_deg: float

    epsilon_i_deg: float
    epsilon_t_deg: float

    R_interface: float
    T_interface: float

    total_efficiency: float
    total_loss_db: float

    input_power_dbm: float
    received_power_dbm: float

    source_position: tuple
    first_interface_position: tuple
    mirror_position: tuple
    second_interface_position: tuple
    receiver_position: tuple


# ============================================================
# SISTEMA COMPLETO
# ============================================================

class OpticalSystem:

    def __init__(
        self,
        source,
        interface,
        mirror
    ):

        self.source = source
        self.interface = interface
        self.mirror = mirror

        # El receptor está en el mismo plano vertical
        # que la fuente.
        self.receiver = Receiver(
            x=source.x
        )

    # ========================================================
    # SIMULACIÓN
    # ========================================================

    def simulate(self):

        source = self.source
        interface = self.interface
        mirror = self.mirror

        # ----------------------------------------------------
        # Comprobaciones geométricas
        # ----------------------------------------------------

        if not (
            source.x
            < interface.x
            < mirror.x
        ):

            raise ValueError(
                "Debe cumplirse:\n"
                "source.x < interface.x < mirror.x"
            )

        theta_i = math.radians(
            source.theta_i_deg
        )

        if not (0 <= theta_i < math.pi / 2):

            raise ValueError(
                "theta_i debe estar en el intervalo "
                "[0, 90) grados."
            )

        # ====================================================
        # ETAPA III
        # n1 -> n2
        # ====================================================

        theta_t = interface.transmitted_angle(
            theta_i
        )

        R = interface.fresnel_reflectance(
            theta_i,
            theta_t
        )

        T = 1 - R

        # ----------------------------------------------------
        # Punto donde el rayo alcanza d1
        # ----------------------------------------------------

        dx1 = interface.x - source.x

        y_d1_first = (
            source.y
            + dx1 * math.tan(theta_i)
        )

        P1 = (
            interface.x,
            y_d1_first
        )

        # ====================================================
        # ETAPA II
        # Propagación hasta el espejo
        # ====================================================

        dx2 = mirror.x - interface.x

        y_mirror = (
            y_d1_first
            + dx2 * math.tan(theta_t)
        )

        P2 = (
            mirror.x,
            y_mirror
        )

        # Ley de reflexión
        phi_i = theta_t
        phi_r = phi_i

        # ====================================================
        # RETORNO POR MEDIO 2
        # ====================================================

        y_d1_return = (
            y_mirror
            + dx2 * math.tan(phi_r)
        )

        P3 = (
            interface.x,
            y_d1_return
        )

        # ====================================================
        # ETAPA I
        # n2 -> n1
        # ====================================================

        epsilon_i = phi_r

        # Por reciprocidad:
        epsilon_t = theta_i

        # ====================================================
        # POSICIÓN AUTOMÁTICA DEL RECEPTOR
        # ====================================================

        y_receiver = (
            y_d1_return
            + dx1 * math.tan(epsilon_t)
        )

        self.receiver.y = y_receiver

        P4 = (
            self.receiver.x,
            self.receiver.y
        )

        # ====================================================
        # POTENCIA
        # ====================================================

        #
        # Primera transmisión:
        #
        #   P1 = T Pin
        #
        # Espejo:
        #
        #   P2 = Rm T Pin
        #
        # Segunda transmisión:
        #
        #   Pr = T Rm T Pin
        #

        efficiency = (
            T ** 2
            * mirror.reflectivity
        )

        loss_db = linear_to_db(
            efficiency
        )

        received_power_dbm = (
            source.power_dbm
            + loss_db
        )

        path_losses_dBm = (
            
        )

        self.receiver.received_power_dbm = (
            received_power_dbm
        )



        # ====================================================
        # RESULTADO
        # ====================================================

        return SimulationResult(

            theta_i_deg=math.degrees(theta_i),
            theta_t_deg=math.degrees(theta_t),

            phi_i_deg=math.degrees(phi_i),
            phi_r_deg=math.degrees(phi_r),

            epsilon_i_deg=math.degrees(epsilon_i),
            epsilon_t_deg=math.degrees(epsilon_t),

            R_interface=R,
            T_interface=T,

            total_efficiency=efficiency,
            total_loss_db=loss_db,

            input_power_dbm=source.power_dbm,
            received_power_dbm=received_power_dbm,

            source_position=(
                source.x,
                source.y
            ),

            first_interface_position=P1,

            mirror_position=P2,

            second_interface_position=P3,

            receiver_position=P4
        )

    # ========================================================
    # REPRESENTACIÓN GRÁFICA
    # ========================================================

    def plot(self, result):

        S = result.source_position
        D1a = result.first_interface_position
        M = result.mirror_position
        D1b = result.second_interface_position
        R = result.receiver_position

        plt.figure(
            figsize=(11, 7)
        )

        # ----------------------------------------------------
        # Límites verticales
        # ----------------------------------------------------

        y_values = [
            S[1],
            D1a[1],
            M[1],
            D1b[1],
            R[1]
        ]

        y_min = min(y_values)
        y_max = max(y_values)

        margin = max(
            (y_max - y_min) * 0.15,
            0.5
        )

        # ----------------------------------------------------
        # Discontinuidad
        # ----------------------------------------------------

        plt.axvline(
            self.interface.x,
            linestyle="--",
            label="Discontinuidad $d_1$"
        )

        # ----------------------------------------------------
        # Espejo
        # ----------------------------------------------------

        plt.axvline(
            self.mirror.x,
            linewidth=3,
            label="Espejo $d_2$"
        )

        # ----------------------------------------------------
        # Trayectoria
        # ----------------------------------------------------

        x_ray = [
            S[0],
            D1a[0],
            M[0],
            D1b[0],
            R[0]
        ]

        y_ray = [
            S[1],
            D1a[1],
            M[1],
            D1b[1],
            R[1]
        ]

        plt.plot(
            x_ray,
            y_ray,
            marker="o",
            linewidth=2,
            label="Trayectoria del rayo"
        )

        # ----------------------------------------------------
        # Fuente y receptor
        # ----------------------------------------------------

        plt.scatter(
            *S,
            s=100,
            label="Fuente"
        )

        plt.scatter(
            *R,
            s=100,
            label="Receptor"
        )

        plt.text(
            S[0],
            S[1],
            "  S"
        )

        plt.text(
            R[0],
            R[1],
            "  R"
        )

        # ----------------------------------------------------
        # Regiones
        # ----------------------------------------------------

        x_middle_n1 = (
            self.source.x
            + self.interface.x
        ) / 2

        x_middle_n2 = (
            self.interface.x
            + self.mirror.x
        ) / 2

        plt.text(
            x_middle_n1,
            y_max + margin * 0.5,
            f"Medio 1\n$n_1={self.interface.n1}$",
            ha="center"
        )

        plt.text(
            x_middle_n2,
            y_max + margin * 0.5,
            f"Medio 2\n$n_2={self.interface.n2}$",
            ha="center"
        )

        plt.xlabel("Distancia perpendicular al espejo")
        plt.ylabel("Posición transversal")

        plt.title(
            "Sistema óptico fuente - discontinuidad - espejo - receptor"
        )

        plt.grid(True)
        plt.legend()

        plt.ylim(
            y_min - margin,
            y_max + margin
        )

        plt.axis("equal")


        # ============================================================
        # CLOSE-UP DE LA REGIÓN INTERFAZ - ESPEJO
        # ============================================================

        ax = plt.gca()

        # Márgenes del zoom en mm
        closeup_x_margin_left = 1.0
        closeup_x_margin_right = 1.0
        closeup_y_margin = 2.0

        # Puntos relevantes ya calculados
        # D1a = primera incidencia en la interfaz
        # M   = incidencia en el espejo
        # D1b = retorno a la interfaz

        # Crear eje inset
        axins = inset_axes(
            ax,
            width="42%",
            height="42%",
            loc="lower right"
        )

        # Dibujar la interfaz y el espejo en el close-up
        axins.axvline(
            self.interface.x,
            linestyle="--"
        )

        axins.axvline(
            self.mirror.x,
            linewidth=3
        )

        # Dibujar solo la parte relevante del rayo
        x_close = [D1a[0], M[0], D1b[0]]
        y_close = [D1a[1], M[1], D1b[1]]

        axins.plot(
            x_close,
            y_close,
            marker="o",
            linewidth=2
        )

        # Resaltar los puntos
        axins.scatter(*D1a, s=50)
        axins.scatter(*M, s=50)
        axins.scatter(*D1b, s=50)

        # Etiquetas pequeñas
        axins.text(D1a[0], D1a[1], "  d1")
        axins.text(M[0], M[1], "  d2")
        axins.text(D1b[0], D1b[1], "  d1")

        # Límites del zoom
        local_y_min = min(D1a[1], M[1], D1b[1])
        local_y_max = max(D1a[1], M[1], D1b[1])

        axins.set_xlim(
            self.interface.x - closeup_x_margin_left,
            self.mirror.x + closeup_x_margin_right
        )

        axins.set_ylim(
            local_y_min - closeup_y_margin,
            local_y_max + closeup_y_margin
        )

        axins.set_title("Close-up interfaz-espejo", fontsize=9)
        axins.grid(True)

        # Marcar en la figura principal la región ampliada
        mark_inset(
            ax,
            axins,
            loc1=2,
            loc2=1,
            fc="none",
            ec="0.5"
        )


        plt.tight_layout()
        plt.show()





# ============================================================
# EJEMPLO DE UTILIZACIÓN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # PARÁMETROS DEL SISTEMA
    # --------------------------------------------------------

    source = Source(

        # Fuente en x = 0
        x=0.0,
        y=0.0,

        # Potencia óptica
        power_dbm=10.0,

        # theta_i
        theta_i_deg=30.0
    )

    interface = DielectricInterface(

        # Distancia desde fuente hasta discontinuidad
        x=1997.0,

        n1=1.33,
        n2=1.4905,

        polarization="s"
    )

    mirror = Mirror(

        # Distancia perpendicular fuente/receptor -> espejo
        x=2000.00,

        # Reflector perfecto
        reflectivity=1.0
    )

    # --------------------------------------------------------
    # CREAR SISTEMA
    # --------------------------------------------------------

    system = OpticalSystem(
        source=source,
        interface=interface,
        mirror=mirror
    )

    # --------------------------------------------------------
    # SIMULAR
    # --------------------------------------------------------

    result = system.simulate()

    # --------------------------------------------------------
    # MOSTRAR RESULTADOS
    # --------------------------------------------------------

    print()
    print("========== RESULTADOS ==========")

    print(
        f"theta_i   = {result.theta_i_deg:.4f} deg"
    )

    print(
        f"theta_t   = {result.theta_t_deg:.4f} deg"
    )

    print(
        f"phi_i     = {result.phi_i_deg:.4f} deg"
    )

    print(
        f"phi_r     = {result.phi_r_deg:.4f} deg"
    )

    print(
        f"epsilon_i = {result.epsilon_i_deg:.4f} deg"
    )

    print(
        f"epsilon_t = {result.epsilon_t_deg:.4f} deg"
    )

    print()

    print(
        f"R interfaz = {result.R_interface:.6f}"
    )

    print(
        f"T interfaz = {result.T_interface:.6f}"
    )

    print()

    print(
        f"Eficiencia total = "
        f"{100 * result.total_efficiency:.4f} %"
    )

    print(
        f"Pérdida total = "
        f"{result.total_loss_db:.4f} dB"
    )

    print()

    print(
        f"Potencia entrada = "
        f"{result.input_power_dbm:.4f} dBm"
    )

    print(
        f"Potencia receptor = "
        f"{result.received_power_dbm:.4f} dBm"
    )

    print()

    print(
        "Posición fuente:",
        result.source_position
    )

    print(
        "Primera incidencia d1:",
        result.first_interface_position
    )

    print(
        "Incidencia espejo:",
        result.mirror_position
    )

    print(
        "Retorno a d1:",
        result.second_interface_position
    )

    print(
        "Posición receptor:",
        result.receiver_position
    )

    # --------------------------------------------------------
    # DIBUJAR SISTEMA
    # --------------------------------------------------------

    system.plot(result)