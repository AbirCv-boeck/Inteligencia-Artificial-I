import random


class QLearningAgent:

    def __init__(
        self,
        alpha=0.1,
        gamma=0.95,
        epsilon=1.0,
        epsilon_min=0.01,
        epsilon_decay=0.995,
        num_acciones=3
    ):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.num_acciones = num_acciones
        self.q_table = {}

    def get_q(self, estado, accion):
        # Valor inicial optimista: incentiva exploración temprana
        return self.q_table.get((estado, accion), 1.0)

    def elegir_accion(self, estado):
        # Exploración
        if random.random() < self.epsilon:
            return random.randint(0, self.num_acciones - 1)

        # Explotación: elige entre las mejores acciones
        valores_q = [
            self.get_q(estado, accion)
            for accion in range(self.num_acciones)
        ]
        max_q = max(valores_q)
        mejores_acciones = [
            accion
            for accion, valor in enumerate(valores_q)
            if valor == max_q
        ]
        return random.choice(mejores_acciones)

    def actualizar(self, estado, accion, recompensa, siguiente_estado):
        q_actual = self.get_q(estado, accion)
        mejor_q_siguiente = max(
            self.get_q(siguiente_estado, a)
            for a in range(self.num_acciones)
        )
        nuevo_q = q_actual + self.alpha * (
            recompensa + self.gamma * mejor_q_siguiente - q_actual
        )
        self.q_table[(estado, accion)] = nuevo_q

    def decaer_epsilon(self):
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            if self.epsilon < self.epsilon_min:
                self.epsilon = self.epsilon_min