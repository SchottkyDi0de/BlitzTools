from pydantic import BaseModel

from typing import List, Optional, Callable


class ProgressData(BaseModel):
    host: str # IP address or hostname
    time: float # time taken for the ping
    unit: str # time unit for progress callback
    ttl: int # hop limit
    payload_size: int # size of the payload in bytes
    loss: float # percentage of lost packets
    time_avg: float # average time of the last N samples
    request_count: int = 0 # field to track the number of requests sent for this host


class ErrorData(BaseModel):
    host: str
    error: str # error message
    error_class: str # error class name


class HostData(BaseModel):
    host: str # IP address or hostname
    ttl: int = 64 # hop limit
    timeout: float = 1.0 # sec
    payload_size: int = 56 # bytes
    interval: float = 1.0 # sec
    unit: str = 'ms' # time unit for progress callback


class PoolData(BaseModel):
    hosts: List[HostData]
    progress_callback: Optional[Callable] = None
    error_callback: Optional[Callable] = None
