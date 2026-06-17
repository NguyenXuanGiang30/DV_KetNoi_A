import os
import sys
import socket
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

PORT_MAPPING = {
    "IOT_INGESTION_URL": 8001,
    "CAMERA_STREAM_URL": 8002,
    "ACCESS_GATE_URL": 8003,
    "AI_VISION_URL": 8004,
    "ANALYTICS_URL": 8005,
    "CORE_BUSINESS_URL": 8006,
    "NOTIFICATION_URL": 8007
}

def get_local_ips():
    ips = []
    try:
        # Get hostname
        hostname = socket.gethostname()
        # Resolve IPs
        for ip in socket.gethostbyname_ex(hostname)[2]:
            ips.append(ip)
    except Exception as e:
        print(f"Error fetching IPs: {e}")
    
    # Try alternate socket connection method to get main active LAN IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        main_ip = s.getsockname()[0]
        if main_ip not in ips:
            ips.append(main_ip)
        s.close()
    except:
        pass
        
    return ips

def parse_env(file_path: Path):
    if not file_path.exists():
        return {}
    config = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                config[key.strip()] = val.strip()
    return config

def update_env(file_path: Path, updates: dict):
    if not file_path.exists():
        print("[-] Error: .env file does not exist!")
        return False
        
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    new_lines = []
    for line in lines:
        stripped = line.strip()
        updated = False
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, val = stripped.split("=", 1)
            key = key.strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                updated = True
        if not updated:
            new_lines.append(line)
            
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    return True

def main():
    print("==================================================")
    print("   Smart Campus LAN & Radmin IP Configuration Tool ")
    print("==================================================")
    
    if not ENV_PATH.exists():
        print(f"[-] Error: .env not found at {ENV_PATH}")
        print("[*] Creating .env from .env.example...")
        example = BASE_DIR / ".env.example"
        if example.exists():
            ENV_PATH.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            print("[-] Error: .env.example also not found. Exit.")
            sys.exit(1)

    # 1. Detect and print local IPs
    ips = get_local_ips()
    print("\n[+] Detected local IP addresses:")
    radmin_ips = [ip for ip in ips if ip.startswith("26.")]
    other_ips = [ip for ip in ips if not ip.startswith("26.")]
    
    if radmin_ips:
        for ip in radmin_ips:
            print(f"  -> Radmin IP : {ip} (Send this to your teammates!)")
    else:
        print("  -> Radmin IP : Not detected (Please make sure Radmin VPN is turned ON)")
        
    for ip in other_ips:
        print(f"  -> Local IP  : {ip}")

    # 2. Parse current settings
    config = parse_env(ENV_PATH)
    
    # 3. Interactive Loop
    while True:
        print("\n--- Current Service URL Configurations in .env ---")
        keys = list(PORT_MAPPING.keys())
        for idx, key in enumerate(keys, 1):
            val = config.get(key, "(not set)")
            print(f"{idx}. {key:<20} = {val}")
        print("8. Exit & Save")
        
        try:
            choice = input("\nSelect service number to update IP (1-7) or 8 to Exit: ").strip()
            if choice == "8":
                print("\n[+] Exiting. Configuration saved successfully!")
                break
                
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(keys):
                service_key = keys[choice_idx]
                port = PORT_MAPPING[service_key]
                partner_ip = input(f"Enter Radmin/LAN IP of partner for {service_key}: ").strip()
                if not partner_ip:
                    print("[-] IP cannot be empty.")
                    continue
                
                # Format to http://IP:PORT
                new_url = f"http://{partner_ip}:{port}"
                config[service_key] = new_url
                update_env(ENV_PATH, {service_key: new_url})
                print(f"[OK] Updated {service_key} -> {new_url} in .env")
            else:
                print("[-] Invalid selection.")
        except ValueError:
            print("[-] Please enter a number between 1 and 8.")
        except Exception as e:
            print(f"[-] Error: {e}")

if __name__ == "__main__":
    main()
