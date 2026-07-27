from ping3 import ping
from ping3.errors import TimeExceeded, TimeToLiveExpired, HostUnknown

from lib.NetTracerCore.trace_data import HostData, PoolData, ProgressData, ErrorData

from threading import Thread
from collections import deque
from time import sleep

# Add singleton pattern if needed
class Tracer:
    def __init__(self):
        ping.EXCEPTIONS = True
        self._threads_pool: list[Thread] = []
        self._stop: bool = False
        self.loss_samples: int = 100 # Number of samples to calculate loss percentage
        self.time_avg_samples: int = 10 # Number of samples to calculate average time

    def _start_trace(self, host_data: HostData, progress_callback: ProgressData, error_callback: ErrorData):
        """Internal method to start tracing a single host. This method will be run in a separate thread for each host."""
        results = deque(maxlen=self.loss_samples) # Store last self.loss_samples ping results for loss calculation
        time_results = deque(maxlen=self.time_avg_samples) # Store last self.time_avg_samples ping times for average calculation

        while not self._stop:
            try:
                delay = ping(
                    host_data.host, 
                    timeout=host_data.timeout, 
                    size=host_data.payload_size, 
                    ttl=host_data.ttl, 
                    unit=host_data.unit,
                )
                sleep(host_data.interval) # Wait for the specified interval before the next ping
                if progress_callback:
                    progress_data = ProgressData(
                        host=host_data.host,
                        time=delay,
                        unit=host_data.unit,
                        ttl=host_data.ttl,
                        payload_size=host_data.payload_size,
                        loss=(1 - len(results) / self.loss_samples) * 100 if len(results) == self.loss_samples else 0, # Calculate loss percentage based on self.loss_samples
                        time_avg=(sum(time_results) / len(time_results)) if time_results else 0 # Calculate average time based on self.time_avg_samples
                    )
                    progress_callback(progress_data)
                    
            except (TimeExceeded, TimeToLiveExpired) as e:
                if error_callback:
                    error_data = ErrorData(
                        host=host_data.host,
                        error=str(e),
                        error_class=e.__class__.__name__
                    )
                    error_callback(error_data)

            except HostUnknown as e:
                if error_callback:
                    error_data = ErrorData(
                        host=host_data.host,
                        error=str(e),
                        error_class=e.__class__.__name__
                    )
                    error_callback(error_data)

            except Exception as e:
                if error_callback:
                    error_data = ErrorData(
                        host=host_data.host,
                        error=str(e),
                        error_class=e.__class__.__name__,
                    )
                    error_callback(error_data)
            finally:
                results.append(delay if isinstance(delay, (int, float)) else None) # Append delay or None for failed ping
                time_results.append(delay if isinstance(delay, (int, float)) else 0) # Append delay or 0 for failed ping

    def trace(self, trace_pool: PoolData, progress_callback: ProgressData = None, error_callback: ErrorData = None, daemon: bool = True):
        """Start tracing multiple hosts in separate threads.
        Args:
            trace_pool (PoolData): Data containing the list of hosts to trace and optional callbacks.
            progress_callback (ProgressData, optional): Callback function to receive progress updates. Defaults to None.
            error_callback (ErrorData, optional): Callback function to receive error updates. Defaults to None.
            daemon (bool, optional): Whether the threads should be daemon threads. Defaults to True.
        Returns:
            None

        Callbacks will receive instances of ProgressData and ErrorData respectively, containing relevant information about the trace progress and any errors encountered.
        """
        for host_data in trace_pool.hosts:
            thread = Thread(
                target=self._start_trace, 
                args=(
                    host_data, 
                    progress_callback, 
                    error_callback
                ), 
                daemon=daemon,
                name="ping_tracer_thread_" + str(host_data.host)
            )
            self._threads_pool.append(thread)
            
        for thread in self._threads_pool:
            thread.start()
        
    def stop(self):
        self._stop = True
        for thread in self._threads_pool:
            thread.join()

# # Test code
# t = Tracer()
# pool_data = PoolData(hosts=[HostData(host='github.com', interval=1)])
# t.trace(
#     pool_data, 
#     progress_callback=lambda data: print(f"Progress: {data}"), 
#     error_callback=lambda error: print(f"Error: {error}"),
# )
# sleep(2) # Let it run for a while
# print(ping('github.com', unit='ms')) # Test ping to ensure it's working
# t.stop()