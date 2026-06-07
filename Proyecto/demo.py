import pickle
import pygame
from entorno.ascensor_env import AscensorEnv
from agente.qlearning import QLearningAgent
from visualizacion.pygame_view import PygameView


def main():
    env = AscensorEnv()
    agente = QLearningAgent()

    # Cargar tabla Q entrenada
    with open("qtable.pkl", "rb") as archivo:
        agente.q_table = pickle.load(archivo)

    # Sin exploración en demo
    agente.epsilon = 0

    vista = PygameView()

    acciones = {
        0: "SUBIR",
        1: "BAJAR",
        2: "ABRIR"
    }

    estado = env.reset()
    done = False
    running = True

    while running and not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        accion = agente.elegir_accion(estado)
        siguiente_estado, recompensa, done, info = env.step(accion)

        vista.dibujar(env, acciones[accion])

        print("\n==============================")
        print(f"Acción:        {acciones[accion]}")
        print(f"Reward:        {recompensa:.2f}")
        print(f"Piso actual:   {env.piso_actual}")
        print(f"Transportados: {info['transportados']}")
        print(f"Esperando:     {info['esperando']}")
        print(f"Dentro:        {info['dentro']}")

        estado = siguiente_estado
        pygame.time.delay(500)

    pygame.quit()
    print("\nDemostración finalizada.")
    print(f"Total transportados: {info['transportados']}")
    print(f"Espera promedio:     {info['espera_promedio']:.2f}")


if __name__ == "__main__":
    main()