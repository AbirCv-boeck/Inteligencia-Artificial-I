import pickle
import matplotlib.pyplot as plt


# -------------------------
# MEDIA MOVIL
# -------------------------

def media_movil(datos, ventana=200):

    resultado = []

    for i in range(len(datos)):

        inicio = max(
            0,
            i - ventana + 1
        )

        promedio = sum(
            datos[inicio:i + 1]
        ) / (
            i - inicio + 1
        )

        resultado.append(
            promedio
        )

    return resultado


# -------------------------
# CARGAR METRICAS
# -------------------------

with open(
    "metricas.pkl",
    "rb"
) as archivo:

    metricas = pickle.load(
        archivo
    )


rewards = metricas[
    "rewards"
]

transportados = metricas[
    "transportados"
]

espera_promedio = metricas[
    "espera_promedio"
]


# -------------------------
# SUAVIZAR CURVAS
# -------------------------

rewards_mm = media_movil(
    rewards
)

transportados_mm = media_movil(
    transportados
)

espera_mm = media_movil(
    espera_promedio
)


# -------------------------
# RESULTADOS FINALES
# -------------------------

print(
    "\n===== RESULTADOS FINALES ====="
)

print(
    f"Reward final: "
    f"{rewards_mm[-1]:.2f}"
)

print(
    f"Transportados finales: "
    f"{transportados_mm[-1]:.2f}"
)

print(
    f"Espera promedio final: "
    f"{espera_mm[-1]:.2f}"
)


# -------------------------
# GRAFICA 1
# -------------------------

plt.figure(
    figsize=(10, 5)
)

plt.plot(
    rewards_mm
)

plt.title(
    "Curva de Aprendizaje (Reward)"
)

plt.xlabel(
    "Episodios"
)

plt.ylabel(
    "Reward"
)

plt.grid()

plt.show()


# -------------------------
# GRAFICA 2
# -------------------------

plt.figure(
    figsize=(10, 5)
)

plt.plot(
    transportados_mm
)

plt.title(
    "Pasajeros Transportados"
)

plt.xlabel(
    "Episodios"
)

plt.ylabel(
    "Transportados"
)

plt.grid()

plt.show()


# -------------------------
# GRAFICA 3
# -------------------------

plt.figure(
    figsize=(10, 5)
)

plt.plot(
    espera_mm
)

plt.title(
    "Tiempo Promedio de Espera"
)

plt.xlabel(
    "Episodios"
)

plt.ylabel(
    "Pasos de Espera"
)

plt.grid()

plt.show()