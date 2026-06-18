import os
import sys
import time
import subprocess
import socket
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Services configuration
SERVICES = {
    "A1_IoT_Ingestion": ("services/iot_ingestion/src", 8001),
    "A2_Camera_Stream": ("services/camera_stream/src", 8002),
    "A3_Access_Gate": ("services/access_gate/src", 8003),
    "A4_AI_Vision": ("services/ai_vision/src", 8004),
    "A5_Analytics": ("services/analytics/src", 8005),
    "A6_Core_Business": ("services/core_business/src", 8006),
    "A7_Notification": ("services/notification/src", 8007),
}

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def kill_port_owner(port):
    """If a port is already in use, try to terminate it (especially on Windows)."""
    try:
        output = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
        pids = set()
        for line in output.splitlines():
            parts = line.strip().split()
            if len(parts) >= 5 and "LISTENING" in line:
                pids.add(parts[-1])
        for pid in pids:
            print(f"[INFO] Killing process PID {pid} listening on port {port}...")
            subprocess.run(f'taskkill /F /PID {pid}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def main():
    print("==================================================")
    print("   Smart Campus Service Verification Orchestrator")
    print("==================================================")
    
    # 1. Clean up active ports if any
    for name, (_, port) in SERVICES.items():
        if is_port_in_use(port):
            print(f"[WARN] Port {port} for {name} is already in use. Cleaning up...")
            kill_port_owner(port)
            time.sleep(1.0)
            
    processes = []
    
    # Start services
    # Override URLs so that local services can talk to each other outside Docker
    local_env = os.environ.copy()
    local_env["PYTHONIOENCODING"] = "utf-8"
    local_env["AI_VISION_URL"] = "http://localhost:8004"
    local_env["ACCESS_GATE_URL"] = "http://localhost:8003"
    local_env["CORE_BUSINESS_URL"] = "http://localhost:8006"
    local_env["ANALYTICS_URL"] = "http://localhost:8005"
    local_env["NOTIFICATION_URL"] = "http://localhost:8007"
    
    # Disable actual camera capture hardware since we might not have a webcam in headless CLI
    local_env["CAMERA_STREAM_URL"] = "mock" 
    
    print("\n[+] Starting services locally via Uvicorn...")
    log_dir = BASE_DIR / "scratch" / "logs"
    log_dir.mkdir(exist_ok=True)
    log_files = []
    
    for name, (src_dir, port) in SERVICES.items():
        app_dir = str(BASE_DIR / src_dir)
        cmd = [
            sys.executable, "-m", "uvicorn", "main:app",
            "--app-dir", app_dir,
            "--host", "127.0.0.1",
            "--port", str(port)
        ]
        
        # Open log file
        f_log = open(log_dir / f"{name}.log", "w", encoding="utf-8")
        log_files.append(f_log)
        
        # Start uvicorn
        p = subprocess.Popen(
            cmd,
            env=local_env,
            stdout=f_log,
            stderr=subprocess.STDOUT,
            text=True
        )
        processes.append((name, p, port))
        print(f"  -> Launched {name} on port {port} (PID: {p.pid})")
        
    # 3. Wait for services to start
    print("\n[WAIT] Waiting 5 seconds for services to initialize healthchecks...")
    time.sleep(5.0)
    
    # 4. Check if all ports are listening
    listening_ok = True
    for name, p, port in processes:
        # Check if process is still running
        if p.poll() is not None:
            print(f"[ERROR] {name} has CRASHED! Exit code: {p.poll()}")
            stdout, stderr = p.communicate()
            print(f"--- {name} STDERR ---")
            print(stderr)
            listening_ok = False
        elif not is_port_in_use(port):
            print(f"[ERROR] {name} is running but port {port} is not listening!")
            listening_ok = False
        else:
            print(f"[OK] {name} is listening on port {port}")
            
    if not listening_ok:
        print("\n[ERROR] Cannot run integration tests because some services failed to start.")
        # Terminate everything
        for name, p, _ in processes:
            if p.poll() is None:
                p.terminate()
        sys.exit(1)
        
    # 5. Run test_integration.py
    print("\n[+] Running test_integration.py to verify listener and inter-service calls...")
    test_cmd = [sys.executable, "test_integration.py"]
    # Pass overridden local env variables
    test_res = subprocess.run(
        test_cmd,
        env=local_env,
        capture_output=True,
        text=True
    )
    
    # Write output to log file
    log_path = BASE_DIR / "scratch" / "test_run_output.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=== test_integration.py STDOUT ===\n")
        f.write(test_res.stdout)
        f.write("\n=== test_integration.py STDERR ===\n")
        f.write(test_res.stderr)
        
    print(test_res.stdout)
    
    # 6. Stop all services
    print("\n[+] Stopping all services...")
    for name, p, _ in processes:
        if p.poll() is None:
            print(f"  -> Terminating {name} (PID: {p.pid})")
            p.terminate()
            p.wait(timeout=3.0)
            
    # Close log files
    for f_log in log_files:
        try:
            f_log.close()
        except:
            pass
            
    print("\n[OK] Cleanup complete. Verification finished successfully!")

if __name__ == "__main__":
    main()
