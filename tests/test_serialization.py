import pytest
import sys
from adaptive_checkpointer.serialization import efficient_serialize_state, efficient_deserialize_state

# Classe global para teste
class GlobalTestClass:
    def __init__(self, value=100, name="test"):
        self.value = value
        self.name = name
    
    def method(self, x):
        return self.value * x

def test_basic_types():
    """Testa tipos básicos de Python."""
    data = {
        "int": 42,
        "float": 3.14,
        "str": "hello",
        "bool": True,
        "bytes": b"binary",
        "none": None,
        "list": [1, 2, 3],
        "dict": {"a": 1, "b": 2},
        "set": {4, 5, 6},
        "tuple": (7, 8, 9),
        "complex": 3+4j,
        "range": range(5, 15, 2)
    }
    
    serialized = efficient_serialize_state(data)
    deserialized = efficient_deserialize_state(serialized)
    
    assert deserialized == data

def test_global_class():
    """Testa instâncias de classe global."""
    obj = GlobalTestClass(200, "global_test")
    
    serialized = efficient_serialize_state(obj)
    deserialized = efficient_deserialize_state(serialized)
    
    assert deserialized.value == 200
    assert deserialized.name == "global_test"
    assert deserialized.method(2) == 400

def test_local_class():
    """Testa instâncias de classe definida localmente."""
    # Classe local
    class LocalTestClass:
        def __init__(self):
            self.number = 42
            self.text = "local"
        
        def get_info(self):
            return f"{self.text}_{self.number}"
    
    obj = LocalTestClass()
    
    serialized = efficient_serialize_state(obj)
    deserialized = efficient_deserialize_state(serialized)
    
    assert deserialized.number == 42
    assert deserialized.text == "local"
    assert deserialized.get_info() == "local_42"

def test_functions():
    """Testa serialização de funções."""
    def normal_function(x):
        return x * 2
    
    lambda_function = lambda x: x ** 2
    
    # Testa função normal
    serialized_normal = efficient_serialize_state(normal_function)
    deserialized_normal = efficient_deserialize_state(serialized_normal)
    assert deserialized_normal(5) == 10
    
    # Testa lambda
    serialized_lambda = efficient_serialize_state(lambda_function)
    deserialized_lambda = efficient_deserialize_state(serialized_lambda)
    assert deserialized_lambda(4) == 16

def test_circular_reference():
    """Testa referências circulares."""
    data = {}
    data["self"] = data  # Referência circular
    data["nested"] = {"parent": data}  # Referência aninhada
    
    serialized = efficient_serialize_state(data)
    deserialized = efficient_deserialize_state(serialized)
    
    # Verifica referências circulares
    assert deserialized["self"] is deserialized
    assert deserialized["nested"]["parent"] is deserialized

def test_module_level():
    """Testa serialização em nível de módulo."""
    import math
    serialized = efficient_serialize_state(math.sqrt)
    deserialized = efficient_deserialize_state(serialized)
    assert deserialized(25) == 5.0

def test_performance():
    """Testa desempenho com grandes estruturas de dados."""
    large_data = {
        "matrix": [[i * j for j in range(1000)] for i in range(1000)],
        "text": "a" * 1000000,
        "objects": [GlobalTestClass(i, f"obj_{i}") for i in range(1000)]
    }
    
    serialized = efficient_serialize_state(large_data)
    deserialized = efficient_deserialize_state(serialized)
    
    assert deserialized["matrix"][500][500] == 250000
    assert len(deserialized["text"]) == 1000000
    assert deserialized["objects"][999].name == "obj_999"

if __name__ == "__main__":
    pytest.main([__file__])
