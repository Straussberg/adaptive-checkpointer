import bisect
import threading
from collections import deque
from .serialization import efficient_serialize_state, efficient_deserialize_state

class AdaptiveCheckpointer:
    def __init__(self,
                 base_interval: int = 100,
                 decay_factor: float = 0.9,
                 max_levels: int = 5,
                 adaptation_window: int = 1000):
        # Armazenamento interno de checkpoints
        self.checkpoints = {}               # {event_id: serialized_bytes}
        self.checkpoint_events = []         # lista ordenada de event_ids

        # Histórico de profundidades de rollback para adaptividade
        self.rollback_depths = deque(maxlen=adaptation_window)

        # Parâmetros de adaptação
        self.base_interval = base_interval
        self.decay_factor = decay_factor
        self.max_levels = max_levels
        self.adaptation_trigger = base_interval * 10
        self.last_adaptation_event = 0

        # Níveis de checkpoint (intervalos exponenciais)
        self.current_levels = self._initialize_levels()

    def _initialize_levels(self):
        """Inicializa os intervalos de checkpoint em níveis exponenciais."""
        return [self.base_interval * (2 ** i) for i in range(self.max_levels)]

    def _dynamic_threshold(self):
        """Calcula o novo intervalo base via suavização exponencial das rollbacks."""
        if not self.rollback_depths:
            return self.base_interval
        avg = sum(self.rollback_depths) / len(self.rollback_depths)
        smoothed = avg * self.decay_factor
        # Garante que fique entre 1 e 10× o intervalo base
        return max(1, min(int(smoothed), self.base_interval * 10))

    def should_checkpoint(self, event_id: int) -> bool:
        """
        Decide se deve criar um checkpoint neste evento.
        Atualiza os níveis periodicamente com base em rollbacks.
        """
        if event_id == 0:
            return True

        # Recalcula níveis apenas a cada 'adaptation_trigger' eventos
        if event_id - self.last_adaptation_event >= self.adaptation_trigger:
            di = self._dynamic_threshold()
            self.current_levels = [di * (2 ** i) for i in range(self.max_levels)]
            self.last_adaptation_event = event_id

        # Se o ID do evento é múltiplo de qualquer nível, retorna True
        return any(event_id % interval == 0 for interval in self.current_levels)

    def save_checkpoint(self, event_id: int, state: object):
        """
        Serializa o objeto 'state' usando CBOR+Zstd e armazena internamente.
        Mantém a lista de event_ids ordenada para buscas rápidas.
        """
        serialized = efficient_serialize_state(state)
        self.checkpoints[event_id] = serialized
        bisect.insort(self.checkpoint_events, event_id)

    def get_last_checkpoint(self, target_event: int) -> tuple[int, object]:
        """
        Recupera o checkpoint mais próximo <= target_event.
        Desserializa o estado e o retorna como objeto Python.
        """
        idx = bisect.bisect_right(self.checkpoint_events, target_event) - 1
        if idx < 0:
            return -1, None
        ev = self.checkpoint_events[idx]
        serialized = self.checkpoints.get(ev, b'')
        state = efficient_deserialize_state(serialized)
        return ev, state

    def record_rollback(self, depth: int):
        """
        Registra a profundidade de um rollback para ajustar adaptativamente
        os intervalos de checkpoint.
        """
        self.rollback_depths.append(depth)

    def optimize_storage(self, current_event: int):
        """
        Opcional: Remove checkpoints muito antigos para limitar uso de memória.
        """
        keep_from = current_event - 2 * max(self.current_levels)
        # Filtra apenas os eventos que ainda estão dentro da janela
        self.checkpoint_events = [
            e for e in self.checkpoint_events if e >= keep_from
        ]
        # Reconstrói o dicionário de checkpoints
        self.checkpoints = {
            e: self.checkpoints[e] for e in self.checkpoint_events
        }
