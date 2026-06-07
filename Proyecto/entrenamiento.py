from entorno.ascensor_env import AscensorEnv
from agente.qlearning import QLearningAgent
import pickle
import copy


env = AscensorEnv()
agente = QLearningAgent()

EPISODIOS = 10000

historial_rewards = []
historial_transportados = []
historial_pendientes = []
historial_epsilon = []
historial_espera_promedio = []

mejor_reward = float("-inf")
mejor_qtable = None

for episodio in range(EPISODIOS):
    estado = env.reset()
    done = False
    recompensa_total = 0

    while not done:
        accion = agente.elegir_accion(estado)
        siguiente_estado, recompensa, done, info = env.step(accion)
        agente.actualizar(estado, accion, recompensa, siguiente_estado)
        estado = siguiente_estado
        recompensa_total += recompensa

    agente.decaer_epsilon()

    historial_rewards.append(recompensa_total)
    historial_transportados.append(info["transportados"])
    historial_pendientes.append(len(env.pasajeros_esperando))
    historial_epsilon.append(agente.epsilon)
    historial_espera_promedio.append(info["espera_promedio"])

    # Guarda la mejor Q-table encontrada
    if recompensa_total > mejor_reward:
        mejor_reward = recompensa_total
        mejor_qtable = copy.deepcopy(agente.q_table)

    if (episodio + 1) % 100 == 0:
        promedio_reward = sum(historial_rewards[-100:]) / 100
        promedio_transportados = sum(historial_transportados[-100:]) / 100
        promedio_espera = sum(historial_espera_promedio[-100:]) / 100
        print(
            f"Episodio {episodio + 1:>5}"
            f" | Reward: {promedio_reward:>8.2f}"
            f" | Transportados: {promedio_transportados:>5.2f}"
            f" | Espera: {promedio_espera:>5.2f}"
            f" | Epsilon: {agente.epsilon:.3f}"
        )

print("\nEntrenamiento finalizado.")
print(f"Mejor reward encontrado: {mejor_reward:.2f}")
print(f"Estados en Q-table: {len(agente.q_table)}")

metricas = {
    "rewards": historial_rewards,
    "transportados": historial_transportados,
    "pendientes": historial_pendientes,
    "epsilon": historial_epsilon,
    "espera_promedio": historial_espera_promedio
}

with open("metricas.pkl", "wb") as archivo:
    pickle.dump(metricas, archivo)

with open("qtable.pkl", "wb") as archivo:
    pickle.dump(mejor_qtable, archivo)

print("Métricas guardadas en metricas.pkl")
print("Tabla Q guardada en qtable.pkl")
print("\nCantidad de registros:")
print(f"  Rewards:        {len(historial_rewards)}")
print(f"  Transportados:  {len(historial_transportados)}")
print(f"  Pendientes:     {len(historial_pendientes)}")
print(f"  Epsilon:        {len(historial_epsilon)}")
print(f"  Espera Promedio:{len(historial_espera_promedio)}")