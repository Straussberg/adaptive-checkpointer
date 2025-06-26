import logging
import zstandard as zstd
import dill

# Configura logging
logger = logging.getLogger(__name__)

def efficient_serialize_state(state) -> bytes:
    """Serialize using Dill with Zstandard compression.
    
    Args:
        state: Qualquer objeto Python a ser serializado
        
    Returns:
        bytes: Dados serializados e comprimidos
        
    Raises:
        RuntimeError: Se a serialização falhar
    """
    try:
        # Serializa com dill (suporta mais tipos que pickle)
        dill_data = dill.dumps(state)
        
        # Comprime com Zstandard
        compressor = zstd.ZstdCompressor(level=3)
        return compressor.compress(dill_data)
        
    except Exception as e:
        logger.exception(f"Serialization failed: {str(e)}")
        raise RuntimeError("Serialization failed")

def efficient_deserialize_state(data: bytes):
    """Deserialize Zstandard compressed dill data.
    
    Args:
        data: Dados serializados e comprimidos
        
    Returns:
        object: Objeto desserializado
        
    Raises:
        RuntimeError: Se a desserialização falhar
    """
    try:
        # Descomprime com Zstandard
        decompressor = zstd.ZstdDecompressor()
        dill_data = decompressor.decompress(data)
        
        # Desserializa com dill
        return dill.loads(dill_data)
    except Exception as e:
        logger.exception(f"Deserialization failed: {str(e)}")
        raise RuntimeError("Deserialization failed")
