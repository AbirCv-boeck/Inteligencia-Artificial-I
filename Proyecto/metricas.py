import pickle
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


# ─────────────────────────────────────────────
# MEDIA MÓVIL
# ─────────────────────────────────────────────
def media_movil(datos, ventana=200):
    resultado = []
    for i in range(len(datos)):
        inicio = max(0, i - ventana + 1)
        promedio = sum(datos[inicio:i + 1]) / (i - inicio + 1)
        resultado.append(promedio)
    return resultado


# ─────────────────────────────────────────────
# CARGAR MÉTRICAS
# ─────────────────────────────────────────────
with open("metricas.pkl", "rb") as archivo:
    metricas = pickle.load(archivo)

rewards         = metricas["rewards"]
espera_promedio = metricas["espera_promedio"]
epsilon_hist    = metricas["epsilon"]

episodios = list(range(1, len(rewards) + 1))

# ─────────────────────────────────────────────
# SUAVIZAR CURVAS
# ─────────────────────────────────────────────
rewards_mm = media_movil(rewards)
espera_mm  = media_movil(espera_promedio)

# ─────────────────────────────────────────────
# RESULTADOS FINALES EN CONSOLA
# ─────────────────────────────────────────────
print("\n===== RESULTADOS FINALES =====")
print(f"Reward final:          {rewards_mm[-1]:.2f}")
print(f"Espera promedio final: {espera_mm[-1]:.2f}")
print(f"Epsilon final:         {epsilon_hist[-1]:.4f}")
print(f"Episodios entrenados:  {len(rewards)}")

# ─────────────────────────────────────────────
# BUSCAR PUNTO DE INTERSECCIÓN reward vs epsilon
# Se normaliza reward a [0,1] para compararlo con epsilon
# La intersección es donde el agente empieza a explotar más que explorar
# ─────────────────────────────────────────────
r_min = min(rewards_mm)
r_max = max(rewards_mm)
r_rango = r_max - r_min if r_max != r_min else 1.0
rewards_norm = [(r - r_min) / r_rango for r in rewards_mm]

interseccion_ep = None
for i in range(1, len(episodios)):
    # cruce: reward_norm pasa por encima de epsilon
    if rewards_norm[i - 1] <= epsilon_hist[i - 1] and rewards_norm[i] > epsilon_hist[i]:
        interseccion_ep = episodios[i]
        break

# ─────────────────────────────────────────────
# FIGURA — 2x2
# ─────────────────────────────────────────────
fig = plt.figure(figsize=(15, 10))
fig.suptitle(
    "Dashboard de Entrenamiento — Ascensor IA",
    fontsize=14, fontweight='bold', y=0.99
)
gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.32)


# ── GRÁFICA 1: Reward ─────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(episodios, rewards,    color='lightsteelblue', alpha=0.3, linewidth=0.5, label='Raw')
ax1.plot(episodios, rewards_mm, color='steelblue',      linewidth=2,             label='Media móvil')
ax1.axhline(0, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
ax1.set_title("Curva de Aprendizaje — Reward")
ax1.set_xlabel("Episodio")
ax1.set_ylabel("Reward")
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)


# ── GRÁFICA 2: Epsilon ────────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(episodios, epsilon_hist, color='darkorange', linewidth=2)
ax2.set_title("Decaimiento de Epsilon (ε)")
ax2.set_xlabel("Episodio")
ax2.set_ylabel("Epsilon")
ax2.set_ylim(0, 1.05)
ax2.grid(True, alpha=0.3)
ax2.annotate(
    f"ε final = {epsilon_hist[-1]:.4f}",
    xy=(len(episodios), epsilon_hist[-1]),
    xytext=(len(episodios) * 0.45, 0.35),
    arrowprops=dict(arrowstyle='->', color='gray', lw=1.2),
    fontsize=9, color='darkorange'
)


# ── GRÁFICA 3: Tiempo de espera ───────────────────────────
ax3 = fig.add_subplot(gs[1, 0])
ax3.plot(episodios, espera_promedio, color='lightsalmon', alpha=0.3, linewidth=0.5, label='Raw')
ax3.plot(episodios, espera_mm,       color='tomato',      linewidth=2,             label='Media móvil')
ax3.set_title("Tiempo Promedio de Espera")
ax3.set_xlabel("Episodio")
ax3.set_ylabel("Pasos de espera")
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)


# ── GRÁFICA 4: Reward + Epsilon unificados (eje doble) ────
ax4 = fig.add_subplot(gs[1, 1])
ax4b = ax4.twinx()  # eje Y derecho para epsilon

# reward normalizado en eje izquierdo
l1, = ax4.plot(episodios, rewards_mm, color='steelblue',  linewidth=2, label='Reward (media móvil)')
ax4.set_ylabel("Reward", color='steelblue')
ax4.tick_params(axis='y', labelcolor='steelblue')
ax4.axhline(0, color='steelblue', linestyle='--', linewidth=0.6, alpha=0.4)

# epsilon en eje derecho
l2, = ax4b.plot(episodios, epsilon_hist, color='darkorange', linewidth=2, label='Epsilon (ε)')
ax4b.set_ylabel("Epsilon (ε)", color='darkorange')
ax4b.tick_params(axis='y', labelcolor='darkorange')
ax4b.set_ylim(0, 1.05)

# línea y anotación de intersección
if interseccion_ep is not None:
    ax4.axvline(
        interseccion_ep,
        color='mediumseagreen', linestyle='--', linewidth=1.5, alpha=0.8
    )
    y_pos = ax4.get_ylim()[0] + (ax4.get_ylim()[1] - ax4.get_ylim()[0]) * 0.05
    ax4.annotate(
        f"Intersección\nep. {interseccion_ep}",
        xy=(interseccion_ep, y_pos),
        xytext=(interseccion_ep + len(episodios) * 0.05, y_pos),
        arrowprops=dict(arrowstyle='->', color='mediumseagreen', lw=1.2),
        fontsize=8, color='mediumseagreen'
    )

ax4.set_title("Reward vs Epsilon — Exploración → Explotación")
ax4.set_xlabel("Episodio")
ax4.grid(True, alpha=0.3)

# leyenda unificada de ambos ejes
lineas = [l1, l2]
etiquetas = [l.get_label() for l in lineas]
ax4.legend(lineas, etiquetas, fontsize=9, loc='center right')


# ─────────────────────────────────────────────
# GUARDAR Y MOSTRAR
# ─────────────────────────────────────────────
plt.savefig("dashboard_entrenamiento.png", dpi=150, bbox_inches='tight')
print("\nDashboard guardado en: dashboard_entrenamiento.png")
plt.show()