import time
import random
import os
from adaptive_checkpointer import (
    AdaptiveCheckpointer,
    efficient_serialize_state,
    efficient_deserialize_state
)

class SimpleSimulation:
    def __init__(self):
        self.state = {}
        self.event_count = 0
        self.checkpointer = AdaptiveCheckpointer(base_interval=200)
    
    def process_event(self):
        self.event_count += 1
        node_id = f"node{random.randint(1, 5)}"
        
        # Atualiza estado
        if node_id not in self.state:
            self.state[node_id] = {"count": 0, "messages": []}
        
        self.state[node_id]["count"] += 1
        self.state[node_id]["messages"].append(f"msg_{self.event_count}")
        
        # Checkpoint adaptativo
        if self.checkpointer.should_checkpoint(self.event_count):
            ckpt_data = efficient_serialize_state(self.state)
            self.checkpointer.save_checkpoint(self.event_count, ckpt_data)
            print(f"Checkpoint at event {self.event_count}")
        
        # Simula rollback (1% de chance)
        if random.random() < 0.01:
            target_event = max(0, self.event_count - random.randint(10, 100))
            print(f"Rollback triggered! From {self.event_count} to {target_event}")
            self.rollback(target_event)
    
    def rollback(self, target_event):
        start_time = time.time()
        
        # Recupera checkpoint
        ckpt_event, ckpt_data = self.checkpointer.get_last_checkpoint(target_event)
        if ckpt_event >= 0:
            self.state = efficient_deserialize_state(ckpt_data)
            print(f"Loaded checkpoint from event {ckpt_event}")
        else:
            self.state = {}
            print("Reset to initial state")
        
        # Atualiza contador e registra rollback
        self.event_count = target_event
        depth = self.event_count - ckpt_event if ckpt_event >=0 else self.event_count
        self.checkpointer.record_rollback(depth)
        
        print(f"Rollback completed in {time.time() - start_time:.4f}s")
    
    def run(self, num_events):
        for _ in range(num_events):
            self.process_event()
        print("Simulation completed successfully!")
        print(f"Final state: {list(self.state.keys())}")

if __name__ == "__main__":
    sim = SimpleSimulation()
    sim.run(1000)

