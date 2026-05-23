"""
ICMP Ping Latency Monitor for 8.8.8.8 (Google DNS)
Monitors ping latency and displays real-time statistics
"""
import subprocess
import re
import sys
import statistics
from datetime import datetime
from collections import deque


class PingMonitor:
    def __init__(self, host="8.8.8.8", window_size=10, interval=1):
        """
        Initialize the ping monitor
        
        Args:
            host: Target host to ping (default: 8.8.8.8)
            window_size: Number of recent pings to track for statistics
            interval: Interval between pings in seconds
        """
        self.host = host
        self.window_size = window_size
        self.interval = interval
        self.latencies = deque(maxlen=window_size)
        self.packet_count = 0
        self.loss_count = 0
        
    def ping_once(self):
        """
        Perform a single ICMP ping and return latency in ms
        Returns None if ping fails
        """
        try:
            if sys.platform == "win32":
                # Windows ping command
                result = subprocess.run(
                    ["ping", "-n", "1", "-w", "1000", self.host],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Parse output for latency
                    match = re.search(r"time[<=]+(\d+)ms", result.stdout)
                    if match:
                        return float(match.group(1))
            else:
                # Unix/Linux/Mac ping command
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", "1000", self.host],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Parse output for latency
                    match = re.search(r"time=(\d+\.?\d*)ms", result.stdout)
                    if match:
                        return float(match.group(1))
            return None
        except Exception as e:
            print(f"Error pinging: {e}")
            return None
    
    def get_statistics(self):
        """Calculate statistics for collected latencies"""
        if not self.latencies:
            return None
        
        latency_list = list(self.latencies)
        return {
            "min": min(latency_list),
            "max": max(latency_list),
            "avg": statistics.mean(latency_list),
            "stdev": statistics.stdev(latency_list) if len(latency_list) > 1 else 0
        }
    
    def display_status(self, latency):
        """Display current ping status"""
        self.packet_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if latency is not None:
            self.latencies.append(latency)
            stats = self.get_statistics()
            
            print(f"\r[{timestamp}] Ping #{self.packet_count} | "
                  f"Latency: {latency:.2f}ms | "
                  f"Avg: {stats['avg']:.2f}ms | "
                  f"Min: {stats['min']:.2f}ms | "
                  f"Max: {stats['max']:.2f}ms | "
                  f"Loss: {self.loss_count}/{self.packet_count} "
                  f"({100*self.loss_count/self.packet_count:.1f}%)", end="")
        else:
            self.loss_count += 1
            print(f"\r[{timestamp}] Ping #{self.packet_count} | "
                  f"Request timeout | "
                  f"Loss: {self.loss_count}/{self.packet_count} "
                  f"({100*self.loss_count/self.packet_count:.1f}%)", end="")
        
        sys.stdout.flush()
    
    def monitor(self, duration=None):
        """
        Start monitoring ping latency
        
        Args:
            duration: How long to monitor in seconds (None for infinite)
        """
        print(f"Starting ICMP ping monitor for {self.host}...")
        print("Press Ctrl+C to stop\n")
        
        try:
            import time
            start_time = time.time()
            
            while True:
                latency = self.ping_once()
                self.display_status(latency)
                
                if duration and (time.time() - start_time) >= duration:
                    break
                
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
            self.print_final_statistics()
    
    def print_final_statistics(self):
        """Print final statistics"""
        if self.packet_count == 0:
            print("No pings were sent.")
            return
        
        print(f"\n--- Final Statistics for {self.host} ---")
        print(f"Packets sent: {self.packet_count}")
        print(f"Packets lost: {self.loss_count}")
        print(f"Packet loss: {100*self.loss_count/self.packet_count:.1f}%")
        
        if self.latencies:
            stats = self.get_statistics()
            print(f"Min latency: {stats['min']:.2f}ms")
            print(f"Max latency: {stats['max']:.2f}ms")
            print(f"Avg latency: {stats['avg']:.2f}ms")
            print(f"Std deviation: {stats['stdev']:.2f}ms")


if __name__ == "__main__":
    # Create monitor for 8.8.8.8 and start monitoring
    monitor = PingMonitor(host="8.8.8.8", window_size=10, interval=1)
    monitor.monitor()   


