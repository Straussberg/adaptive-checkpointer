import os
import bisect

try:
    import redis
except ImportError:
    redis = None

try:
    import boto3
except ImportError:
    boto3 = None

class StorageBackend:
    def save(self, event_id: int, data: bytes):
        raise NotImplementedError

    def load(self, event_id: int) -> bytes:
        raise NotImplementedError


class MemoryStorage(StorageBackend):
    def __init__(self):
        self.data = {}

    def save(self, event_id: int, data: bytes):
        self.data[event_id] = data

    def load(self, event_id: int) -> bytes:
        return self.data.get(event_id, b'')


class DiskStorage(StorageBackend):
    def __init__(self, path: str = None, directory: str = None):
        # aceita 'path' ou 'directory' para compatibilidade com testes
        self.path = path or directory or "checkpoints"
        os.makedirs(self.path, exist_ok=True)

    def save(self, event_id: int, data: bytes):
        with open(os.path.join(self.path, f"ckpt_{event_id}.bin"), "wb") as f:
            f.write(data)

    def load(self, event_id: int) -> bytes:
        try:
            with open(os.path.join(self.path, f"ckpt_{event_id}.bin"), "rb") as f:
                return f.read()
        except FileNotFoundError:
            return b''


class RedisStorage(StorageBackend):
    def __init__(self, host='localhost', port=6379, db=0, prefix="ckpt"):
        if redis is None:
            raise RuntimeError("Redis library not installed")
        self.client = redis.Redis(host=host, port=port, db=db)
        self.prefix = prefix

    def save(self, event_id: int, data: bytes):
        self.client.set(f"{self.prefix}:{event_id}", data)

    def load(self, event_id: int) -> bytes:
        return self.client.get(f"{self.prefix}:{event_id}") or b''


class S3Storage(StorageBackend):
    def __init__(self, bucket: str, prefix: str = "checkpoints", region: str = "us-east-1"):
        if boto3 is None:
            raise RuntimeError("boto3 library not installed")
        self.s3 = boto3.resource('s3', region_name=region)
        self.bucket = self.s3.Bucket(bucket)
        self.prefix = prefix

    def save(self, event_id: int, data: bytes):
        self.bucket.put_object(
            Key=f"{self.prefix}/ckpt_{event_id}.bin",
            Body=data
        )

    def load(self, event_id: int) -> bytes:
        try:
            obj = self.bucket.Object(f"{self.prefix}/ckpt_{event_id}.bin")
            return obj.get()['Body'].read()
        except Exception:
            return b''


class TieredBackend(StorageBackend):
    """Unified backend with multiple layers."""
    def __init__(self):
        self.layers = []

    def add_ram_layer(self, max_events: int = 10000):
        self.layers.append((max_events, MemoryStorage()))
        return self

    def add_nvme_layer(self, max_events: int, path: str = "/pmem"):
        self.layers.append((max_events, DiskStorage(path=path)))
        return self

    def add_redis_layer(self, max_events: int, **kwargs):
        self.layers.append((max_events, RedisStorage(**kwargs)))
        return self

    def add_s3_layer(self, max_events: int, **kwargs):
        self.layers.append((max_events, S3Storage(**kwargs)))
        return self

    def save(self, event_id: int, data: bytes):
        for threshold, backend in self.layers:
            if event_id <= threshold:
                backend.save(event_id, data)
                return
        # fallback to last layer
        self.layers[-1][1].save(event_id, data)

    def load(self, event_id: int) -> bytes:
        for _, backend in self.layers:
            d = backend.load(event_id)
            if d:
                return d
        return b''

