import random


class AscensorEnv:

    SUBIR = 0
    BAJAR = 1
    ABRIR = 2

    def __init__(self, num_pisos=5, max_steps=200):
        self.num_pisos = num_pisos
        self.max_steps = max_steps
        self.reset()


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

    
    def get_state(self):
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
            self.piso_actual,
            pasajeros_en_piso,
            pasajeros_arriba,
            pasajeros_abajo,
            len(self.pasajeros_dentro),
            pasajeros_entregar,
        )

    # ----------------------------
    def _destino_mas_cercano(self):
        """El destino más cercano entre todos los pasajeros dentro."""
        if not self.pasajeros_dentro:
            return None
        return min(
            (p["destino"] for p in self.pasajeros_dentro),
            key=lambda d: abs(d - self.piso_actual)
        )

    def _origen_mas_cercano(self):
        """El origen más cercano entre todos los pasajeros esperando."""
        if not self.pasajeros_esperando:
            return None
        return min(
            (p["origen"] for p in self.pasajeros_esperando),
            key=lambda x: abs(x - self.piso_actual)
        )

    # 
    def _accion_correcta(self):
        """
        Devuelve la única acción correcta dado el estado actual.
        Esta función define el comportamiento determinista del ascensor:

        PRIORIDAD 1 — hay pasajeros dentro:
            - Si alguno debe bajar aquí → ABRIR
            - Si no → moverse hacia el destino más cercano (SUBIR o BAJAR)
            - De paso: si hay demanda en el piso actual también → ABRIR

        PRIORIDAD 2 — sin pasajeros dentro, hay demanda:
            - Si hay alguien esperando aquí → ABRIR
            - Si no → moverse hacia el origen más cercano (SUBIR o BAJAR)

        PRIORIDAD 3 — idle (nadie dentro, nadie esperando):
            - Cualquier acción es equivalente; devolvemos ABRIR como neutro.
        """
        hay_dentro   = len(self.pasajeros_dentro) > 0
        hay_esperando = len(self.pasajeros_esperando) > 0

        # PRIORIDAD 1: pasajeros dentro
        if hay_dentro:
            # ¿alguno baja aquí?
            if any(p["destino"] == self.piso_actual for p in self.pasajeros_dentro):
                return self.ABRIR

            # ¿alguien espera aquí de paso?
            if any(p["origen"] == self.piso_actual for p in self.pasajeros_esperando):
                return self.ABRIR

            # moverse hacia el destino más cercano
            destino = self._destino_mas_cercano()
            if   self.piso_actual < destino: return self.SUBIR
            elif self.piso_actual > destino: return self.BAJAR
            else:                            return self.ABRIR

        # PRIORIDAD 2: sin pasajeros dentro
        if hay_esperando:
            # ¿alguien espera aquí?
            if any(p["origen"] == self.piso_actual for p in self.pasajeros_esperando):
                return self.ABRIR

            # moverse hacia el origen más cercano
            origen = self._origen_mas_cercano()
            if   self.piso_actual < origen: return self.SUBIR
            elif self.piso_actual > origen: return self.BAJAR
            else:                           return self.ABRIR

        # PRIORIDAD 3: idle
        return self.ABRIR 

    # 
    def step(self, accion):
        """
        El agente propone una acción. El entorno la compara con la acción
        correcta determinista (_accion_correcta). Si coincide, recompensa
        y ejecuta. Si no coincide, penaliza fuertemente y ejecuta la acción
        CORRECTA de todas formas para que el ascensor no se bloquee.

        Esto elimina la oscilación por completo: aunque el agente proponga
        la acción incorrecta, el ascensor siempre se mueve en la dirección
        correcta. El agente aprende por la señal de reward, no por el movimiento.
        """
        self.step_actual += 1
        reward = -1  # coste base por paso

        accion_correcta = self._accion_correcta()

        hay_dentro    = len(self.pasajeros_dentro) > 0
        hay_esperando = len(self.pasajeros_esperando) > 0
        estado_idle   = not hay_dentro and not hay_esperando

        #  IDLE
        # No hay nadie dentro ni esperando: el ascensor debe quedarse quieto.
        # No ejecutamos ningún movimiento físico.
        # Penalizamos más si el agente propone moverse (es inútil).
        if estado_idle:
            if accion in (self.SUBIR, self.BAJAR):
                reward -= 8   # moverse sin razón
            else:
                reward -= 1   # ABRIR en idle: casi neutro
            # el ascensor NO se mueve físicamente
            if random.random() < 0.20:
                self.generar_pasajero()
            self.ultimo_piso = self.piso_actual
            done = self.step_actual >= self.max_steps
            return self.get_state(), reward, done, self.get_info()

        # EVALUAR ACCIÓN DEL AGENTE
        if accion == accion_correcta:
            # acción correcta: recompensa según lo que logra
            if accion == self.ABRIR:
                reward += self.procesar_puerta()   # +40 entrega, +10 recogida
            else:
                reward += 4  # bonus por moverse en dirección correcta
        else:
            # acción incorrecta: penalización fuerte
            reward -= 12

        # ── EJECUTAR LA ACCIÓN CORRECTA (no la del agente si es incorrecta) ──
        # Así el ascensor NUNCA oscila físicamente aunque el agente se equivoque.
        # El agente aprende por reward, el ascensor siempre avanza.
        if accion_correcta == self.ABRIR:
            if accion != self.ABRIR:
                # el agente no abrió pero debía: ejecutar apertura igual
                self.procesar_puerta()
        else:
            self._ejecutar_movimiento(accion_correcta)

        #  PENALIZACIÓN POR ESPERA ACUMULADA
        for p in self.pasajeros_esperando:
            p["espera"] += 1
            if p["espera"] > 15:
                reward -= 5

        reward -= len(self.pasajeros_esperando) * 0.5

        # UPDATE 
        self.ultimo_piso = self.piso_actual

        if random.random() < 0.20:
            self.generar_pasajero()

        done = self.step_actual >= self.max_steps
        return self.get_state(), reward, done, self.get_info()

    # ----------------------------
    def _ejecutar_movimiento(self, accion):
        """Mueve el ascensor físicamente. Solo SUBIR/BAJAR cambian el piso."""
        if   accion == self.SUBIR and self.piso_actual < self.num_pisos:
            self.piso_actual += 1
        elif accion == self.BAJAR and self.piso_actual > 1:
            self.piso_actual -= 1
        # ABRIR no mueve el piso

    # ----------------------------
    def procesar_puerta(self):
        """
        1. Baja a todos los que llegaron a su destino.
        2. Sube a todos los que esperan en este piso.
        """
        recompensa    = 0
        nuevos_dentro = []

        for p in self.pasajeros_dentro:
            if p["destino"] == self.piso_actual:
                recompensa += 40
                self.transportados += 1
            else:
                nuevos_dentro.append(p)
        self.pasajeros_dentro = nuevos_dentro

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

    # ----------------------------
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