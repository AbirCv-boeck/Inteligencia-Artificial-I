import random


class AscensorEnv:
    """
    Entorno MDP limpio para el ascensor.

    Implementa un Proceso de Markov (MDP) porque:
    - ESTADO: tupla que captura todo lo relevante del momento presente
    - ACCIÓN: el agente elige libremente, el entorno ejecuta exactamente eso
    - RECOMPENSA: viene del RESULTADO de la acción, no de comparar con un ideal
    - TRANSICIÓN: el siguiente estado depende solo del estado actual + acción
    - ALEATORIEDAD: la generación de pasajeros introduce estocasticidad (MDP, no MP)

    No hay oráculo ni guía externa — el agente aprende solo por consecuencias.
    """

    SUBIR = 0
    BAJAR = 1
    ABRIR = 2

    def __init__(self, num_pisos=5, max_steps=200):
        self.num_pisos = num_pisos
        self.max_steps = max_steps
        self.reset()

    # ─────────────────────────────────────────────────────────
    def reset(self):
        self.piso_actual              = 1
        self.step_actual              = 0
        self.transportados            = 0
        self.tiempos_espera_atendidos = []
        self.pasajeros_esperando      = []
        self.pasajeros_dentro         = []
        self.ultimo_piso              = self.piso_actual

        for _ in range(3):
            self.generar_pasajero()

        return self.get_state()

    # ─────────────────────────────────────────────────────────
    def generar_pasajero(self):
        origen = random.randint(1, self.num_pisos)
        destino = origen
        while destino == origen:
            destino = random.randint(1, self.num_pisos)
        self.pasajeros_esperando.append({
            "origen":  origen,
            "destino": destino,
            "espera":  0
        })

    # ─────────────────────────────────────────────────────────
    def get_state(self):
        """
        S — el estado del MDP.

        Contiene TODO lo que el agente necesita para decidir:
        no guarda historial, solo el momento presente.
        Eso garantiza la propiedad de Markov.
        """
        pasajeros_arriba   = 0
        pasajeros_abajo    = 0
        pasajeros_en_piso  = 0
        pasajeros_entregar = 0

        for p in self.pasajeros_esperando:
            if   p["origen"] == self.piso_actual: pasajeros_en_piso += 1
            elif p["origen"]  > self.piso_actual: pasajeros_arriba  += 1
            else:                                 pasajeros_abajo   += 1

        for p in self.pasajeros_dentro:
            if p["destino"] == self.piso_actual:
                pasajeros_entregar += 1

        return (
            self.piso_actual,       # dónde está el ascensor
            pasajeros_en_piso,      # cuántos esperan aquí mismo
            pasajeros_arriba,       # cuántos esperan en pisos superiores
            pasajeros_abajo,        # cuántos esperan en pisos inferiores
            len(self.pasajeros_dentro),   # cuántos lleva dentro
            pasajeros_entregar,     # cuántos deben bajar aquí
        )

    # ─────────────────────────────────────────────────────────
    def step(self, accion):
        """
        T + R — transición y recompensa del MDP.

        El agente propone una acción. El entorno:
        1. Ejecuta EXACTAMENTE esa acción (sin corrección)
        2. Devuelve la recompensa basada en el RESULTADO
        3. Devuelve el nuevo estado S'

        El agente aprende solo por las consecuencias de sus propias decisiones.
        """
        self.step_actual += 1
        reward = -1  # coste base por paso (incentiva eficiencia)

        hay_dentro    = len(self.pasajeros_dentro) > 0
        hay_esperando = len(self.pasajeros_esperando) > 0

        # ── IDLE: nadie dentro, nadie esperando ───────────────
        # El ascensor no tiene nada útil que hacer.
        # Se queda quieto. Cualquier movimiento es inútil.
        if not hay_dentro and not hay_esperando:
            if accion in (self.SUBIR, self.BAJAR):
                reward -= 4     # moverse sin razón tiene coste extra
            # el ascensor NO se mueve físicamente en idle
            self.piso_actual = self.ultimo_piso
            if random.random() < 0.20:
                self.generar_pasajero()
            self.piso_actual = self.ultimo_piso  # reasignar tras posible generación
            done = self.step_actual >= self.max_steps
            return self.get_state(), reward, done, self.get_info()

        # ── EJECUTAR LA ACCIÓN EXACTAMENTE COMO EL AGENTE DECIDIÓ ──
        if accion == self.SUBIR:
            if self.piso_actual < self.num_pisos:
                self.piso_actual += 1
            else:
                reward -= 5     # chocó con el techo — acción inválida

        elif accion == self.BAJAR:
            if self.piso_actual > 1:
                self.piso_actual -= 1
            else:
                reward -= 5     # chocó con el suelo — acción inválida

        elif accion == self.ABRIR:
            reward += self._procesar_puerta()
            # _procesar_puerta devuelve +40 por entrega, +10 por recogida,
            # 0 si abre en un piso sin nadie (acción inútil pero no catastrófica)

        # ── RECOMPENSAS POR CONTEXTO (consecuencias del resultado) ──

        # Penalizar si tiene pasajeros dentro y está en su destino pero no abrió
        debe_entregar = any(
            p["destino"] == self.piso_actual
            for p in self.pasajeros_dentro
        )
        if debe_entregar and accion != self.ABRIR:
            reward -= 20    # estaba en el destino y no abrió — consecuencia grave

        # Penalizar si hay demanda en el piso actual y no abrió
        hay_demanda_aqui = any(
            p["origen"] == self.piso_actual
            for p in self.pasajeros_esperando
        )
        if hay_demanda_aqui and not hay_dentro and accion != self.ABRIR:
            reward -= 10    # había gente esperando aquí y pasó de largo

        # Penalizar espera acumulada de pasajeros (presión para ser eficiente)
        for p in self.pasajeros_esperando:
            p["espera"] += 1
            if p["espera"] > 15:
                reward -= 3     # pasajero esperando demasiado

        reward -= len(self.pasajeros_esperando) * 0.3   # presión proporcional

        # ── UPDATE FINAL ──────────────────────────────────────
        self.ultimo_piso = self.piso_actual

        if random.random() < 0.20:
            self.generar_pasajero()

        done = self.step_actual >= self.max_steps
        return self.get_state(), reward, done, self.get_info()

    # ─────────────────────────────────────────────────────────
    def _procesar_puerta(self):
        """
        Resultado de abrir la puerta:
        - Bajan todos los pasajeros que llegaron a su destino → +40 c/u
        - Suben todos los que esperan en este piso          → +10 c/u
        - Si no hay nadie → devuelve 0 (abrir fue inútil pero no penaliza)
        """
        recompensa    = 0
        nuevos_dentro = []

        # entregar
        for p in self.pasajeros_dentro:
            if p["destino"] == self.piso_actual:
                recompensa += 40
                self.transportados += 1
            else:
                nuevos_dentro.append(p)
        self.pasajeros_dentro = nuevos_dentro

        # recoger
        nuevos_esperando = []
        for p in self.pasajeros_esperando:
            if p["origen"] == self.piso_actual:
                self.tiempos_espera_atendidos.append(p["espera"])
                self.pasajeros_dentro.append({"destino": p["destino"]})
                recompensa += 10
            else:
                nuevos_esperando.append(p)
        self.pasajeros_esperando = nuevos_esperando

        return recompensa

    # ─────────────────────────────────────────────────────────
    def get_info(self):
        espera_promedio = (
            sum(self.tiempos_espera_atendidos) / len(self.tiempos_espera_atendidos)
            if self.tiempos_espera_atendidos else 0
        )
        return {
            "transportados":   self.transportados,
            "esperando":       len(self.pasajeros_esperando),
            "dentro":          len(self.pasajeros_dentro),
            "espera_promedio": espera_promedio,
        }