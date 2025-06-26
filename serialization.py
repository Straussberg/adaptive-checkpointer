import cbor2
import logging
import sys
from types import FunctionType, BuiltinFunctionType

# Configura logging
logger = logging.getLogger(__name__)

try:
    import zstandard as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False
    logger.warning("zstandard module not available. Using uncompressed serialization.")

# Mapeamento de tipos especiais
TYPE_MARKERS = {
    'complex': 1000,
    'range': 1001,
    'frozenset': 1002,
    'function': 1003,
    'class': 1004,
    'instance': 1005
}

def default_encoder(encoder, value):
    """Handles special types during serialization."""
    if isinstance(value, complex):
        return encoder.encode(cbor2.CBORTag(TYPE_MARKERS['complex'], [value.real, value.imag]))
    
    elif isinstance(value, range):
        return encoder.encode(cbor2.CBORTag(TYPE_MARKERS['range'], [value.start, value.stop, value.step]))
    
    elif isinstance(value, frozenset):
        return encoder.encode(cbor2.CBORTag(TYPE_MARKERS['frozenset'], list(value)))
    
    elif isinstance(value, (FunctionType, BuiltinFunctionType)):
        # Serializa apenas informações básicas de funções
        return encoder.encode(cbor2.CBORTag(
            TYPE_MARKERS['function'],
            {
                'name': value.__name__,
                'module': value.__module__,
                'qualname': getattr(value, '__qualname__', '')
            }
        ))
    
    elif isinstance(value, type):
        # Serializa informações básicas de classes
        return encoder.encode(cbor2.CBORTag(
            TYPE_MARKERS['class'],
            {
                'name': value.__name__,
                'module': value.__module__,
                'qualname': getattr(value, '__qualname__', '')
            }
        ))
    
    elif hasattr(value, '__dict__'):
        # Serializa instâncias de classes
        return encoder.encode(cbor2.CBORTag(
            TYPE_MARKERS['instance'],
            {
                'class': value.__class__,
                'state': value.__dict__
            }
        ))
    
    raise cbor2.CBOREncodeError(f"Cannot serialize type: {type(value)}")

def object_hook(decoder, tag):
    """Handles special types during deserialization."""
    if tag.tag == TYPE_MARKERS['complex']:
        return complex(tag.value[0], tag.value[1])
    
    elif tag.tag == TYPE_MARKERS['range']:
        return range(*tag.value)
    
    elif tag.tag == TYPE_MARKERS['frozenset']:
        return frozenset(tag.value)
    
    elif tag.tag == TYPE_MARKERS['function']:
        # Não reconstruímos a função, apenas retornamos informações
        return tag.value
    
    elif tag.tag == TYPE_MARKERS['class']:
        # Não reconstruímos a classe, apenas retornamos informações
        return tag.value
    
    elif tag.tag == TYPE_MARKERS['instance']:
        # Reconstruímos instâncias de classes simples
        cls = tag.value['class']
        instance = cls.__new__(cls)
        instance.__dict__.update(tag.value['state'])
        return instance
    
    return tag

def efficient_serialize_state(state) -> bytes:
    """Serialize using CBOR with optional Zstandard compression."""
    try:
        cbor_data = cbor2.dumps(
            state,
            default=default_encoder,
            value_sharing=True
        )
        
        if ZSTD_AVAILABLE:
            compressor = zstd.ZstdCompressor(level=3)
            return compressor.compress(cbor_data)
        return cbor_data
        
    except Exception as e:
        logger.exception(f"CBOR serialization failed: {str(e)}")
        # Fallback para pickle com protocolo mais recente
        import pickle
        try:
            return pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as pickle_err:
            logger.exception(f"Pickle fallback failed: {str(pickle_err)}")
            raise RuntimeError("Serialization failed with both CBOR and Pickle")

def efficient_deserialize_state(data: bytes):
    """Deserialize CBOR data with optional decompression."""
    try:
        if ZSTD_AVAILABLE:
            try:
                decompressor = zstd.ZstdDecompressor()
                data = decompressor.decompress(data)
            except zstd.ZstdError:
                # Não estava comprimido, usa direto
                pass
        
        return cbor2.loads(
            data,
            tag_hook=object_hook,
            value_sharing=True
        )
    except Exception as e:
        logger.exception(f"CBOR deserialization failed: {str(e)}")
        # Fallback para pickle
        import pickle
        try:
            return pickle.loads(data)
        except Exception as pickle_err:
            logger.exception(f"Pickle fallback failed: {str(pickle_err)}")
            raise RuntimeError("Deserialization failed with both CBOR and Pickle")
