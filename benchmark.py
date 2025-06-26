import time
import random
import os
import argparse
from adaptive_checkpointer import (
    AdaptiveCheckpointer,
    InstrumentedCheckpointer,
    efficient_serialize_state,
    efficient_deserialize_state
)

def run_benchmark(total_events=50000, rollback_prob=0.02):
    print(f"Running benchmark with {total_events} events...")
    
    # Configurações
    strategies = [
        ("Fixed (100)", AdaptiveCheckpointer(base_interval=100)),
        ("Static √T", AdaptiveCheckpointer(base_interval=int(total_events**0.5))),
        ("Adaptive", InstrumentedCheckpointer(base_interval=100))
    ]
    
    results = {}
    
    for name, checkpointer in strategies:
        print(f"\nStrategy: {name}")
        start_time = time.time()
        state = {}
        max_mem = 0
        
        for event_id in range(total_events):
            # Atualiza estado
            state[event_id] = os.urandom(1024)  # 1KB por evento
            
            # Checkpoint
            if checkpointer.should_checkpoint(event_id):
                ckpt_data = efficient_serialize_state(state)
                checkpointer.save_checkpoint(event_id, ckpt_data)
            
            # Simula rollback
            if random.random() < rollback_prob:
                target = max(0, event_id - random.randint(1, 500))
                
                # Executa rollback
                ckpt_event, ckpt_data = checkpointer.get_last_checkpoint(target)
                state = efficient_deserialize_state(ckpt_data) if ckpt_event >= 0 else {}
                
                # Registra métricas
                depth = event_id - target
                if isinstance(checkpointer, InstrumentedCheckpointer):
                    checkpointer.record_rollback(depth)
        
        total_time = time.time() - start_time
        results[name] = {
            "total_time": total_time,
            "event_throughput": total_events / total_time
        }
        
        # Coleta métricas adicionais
        if isinstance(checkpointer, InstrumentedCheckpointer):
            report = checkpointer.get_report()
            results[name].update({
                "checkpoint_count": report["checkpoint_count"],
                "avg_rollback_depth": report["rollback_stats"]["avg_depth"]
            })
    
    # Exibe resultados
    print("\nBenchmark Results:")
    for strategy, metrics in results.items():
        print(f"\n{strategy}:")
        for k, v in metrics.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.4f}")
            else:
                print(f"  {k}: {v}")
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, default=50000, help="Total de eventos")
    parser.add_argument("--rollback", type=float, default=0.02, help="Probabilidade de rollback")
    args = parser.parse_args()
    
    results = run_benchmark(total_events=args.events, rollback_prob=args.rollback)
