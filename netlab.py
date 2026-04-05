import os
import re
import json
import socket
import logging
import requests
import threading
import subprocess
from datetime import datetime
from logging.handlers import RotatingFileHandler


BLACK = "\033[0;30m"
RED = "\033[0;31m"
GREEN = "\033[0;32m"
BROWN = "\033[0;33m"
BLUE = "\033[0;34m"
PURPLE = "\033[0;35m"
CYAN = "\033[0;36m"
LIGHT_GRAY = "\033[0;37m"
DARK_GRAY = "\033[1;30m"
LIGHT_RED = "\033[1;31m"
LIGHT_GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
LIGHT_BLUE = "\033[1;34m"
LIGHT_PURPLE = "\033[1;35m"
LIGHT_CYAN = "\033[1;36m"
LIGHT_WHITE = "\033[1;37m"
BOLD = "\033[1m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
CROSSED = "\033[9m"
RESET = "\033[0m"

def clear():
    os.system("clear")

clear()
version = "v3.0.0"

opennax = f"""{LIGHT_CYAN}
    ███████                                  ██████   █████   █████████   █████ █████
  ███░░░░░███                               ░░██████ ░░███   ███░░░░░███ ░░███ ░░███ 
 ███     ░░███ ████████   ██████  ████████   ░███░███ ░███  ░███    ░███  ░░███ ███  
░███      ░███░░███░░███ ███░░███░░███░░███  ░███░░███░███  ░███████████   ░░█████   
░███      ░███ ░███ ░███░███████  ░███ ░███  ░███ ░░██████  ░███░░░░░███    ███░███  
░░███     ███  ░███ ░███░███░░░   ░███ ░███  ░███  ░░█████  ░███    ░███   ███ ░░███ 
 ░░░███████░   ░███████ ░░██████  ████ █████ █████  ░░█████ █████   █████ █████ █████
   ░░░░░░░     ░███░░░   ░░░░░░  ░░░░ ░░░░░ ░░░░░    ░░░░░ ░░░░░   ░░░░░ ░░░░░ ░░░░░ 
               ░███                                                                  
               █████                                                                 
              ░░░░░                                                                  
{RESET}"""

print(opennax)
print(f"{CYAN}[*] Starting NetLab · {version}...{RESET}")

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


alerted_levels = set()

def setup_logger():
    log_filename = f"{LOG_DIR}/network_logs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    main_logger = logging.getLogger(LOG_DIR)
    main_logger.setLevel(logging.INFO)
    if not main_logger.handlers:
        main_handler = RotatingFileHandler(log_filename, maxBytes=5*1024*1024, backupCount=3)
        main_formatter = logging.Formatter("%(asctime)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
        main_handler.setFormatter(main_formatter)
        main_logger.addHandler(main_handler)


def get_local_ip_addresses():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return [ip]
    except Exception:
        return ["N/A"]

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        response.raise_for_status()
        return response.json().get('ip', 'N/A')
    except requests.RequestException:
        return "N/A"

current_public_ip = "N/A"
initial_mobile_state = None


def fetch_mobile_network_info_once():
    try:
        mobile_info_raw = subprocess.check_output(["termux-telephony-deviceinfo"], timeout=5).decode("utf-8")
        mobile_info = json.loads(mobile_info_raw)
        return {
            "operator": mobile_info.get("network_operator_name", "Unknown"),
            "network_type": mobile_info.get("network_type", "Unknown").upper(),
            "data_enabled": mobile_info.get("data_enabled", "Unknown"),
            "sim_state": mobile_info.get("sim_state", "Unknown")
        }
    except Exception:
        return None

def log_session_start():
    global current_public_ip
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    local_ips = get_local_ip_addresses()
    public_ip = get_public_ip()

    current_public_ip = public_ip

    battery_info = get_battery_status()
    if battery_info and battery_info.get('percentage') is not None:
        batt_str = f"{battery_info.get('percentage')}% ({battery_info.get('status', 'UNKNOWN').upper()})"
    else:
        batt_str = "Unknown"

    global initial_mobile_state
    initial_mobile_state = fetch_mobile_network_info_once()
    if initial_mobile_state:
        mob_str = f"Operator: {initial_mobile_state['operator']}, Network: {initial_mobile_state['network_type']}, Data: {initial_mobile_state['data_enabled']}, SIM: {initial_mobile_state['sim_state']}"
    else:
        mob_str = "Unknown"

    main_logger = logging.getLogger(LOG_DIR)

    print(
        f"{CYAN}--- STARTING MONITOR ---\n"
        f"· Time: {start_time}\n"
        f"· Local IP(s): {', '.join(local_ips)}\n"
        f"· Public IP: {public_ip}\n"
        f"· Battery: {batt_str}\n"
        f"· Mobile: {mob_str}\n"
        f"{RESET}"
    )

    main_logger.info(f"--- STARTING MONITOR ---")
    main_logger.info(f"Time: {start_time}")
    main_logger.info(f"Local IP(s): {', '.join(local_ips)}")
    main_logger.info(f"Public IP: {public_ip}")
    main_logger.info(f"Battery: {batt_str}")
    main_logger.info(f"Mobile: {mob_str}")


def ping_dns(dns_server, timeout=2):
    try:
        command = ["ping", "-c", "1", "-W", str(timeout), dns_server]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        for line in result.stdout.splitlines():
            if "time=" in line:
                try:
                    latency = float(line.split("time=")[1].split()[0])
                    return latency
                except (IndexError, ValueError):
                    pass
        return None
    except Exception as e:
        return None

def check_packet_loss(dns_server, count=5, timeout=2):
    try:
        command = ["ping", "-c", str(count), "-W", str(timeout), dns_server]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        match = re.search(r'(\d+)%\s*packet loss', result.stdout)
        if match:
            return int(match.group(1))
        return 100

    except FileNotFoundError:
        logging.getLogger(LOG_DIR).error(f"Ping command not found for packet loss check.")
        return 100

    except Exception as e:
        logging.getLogger(LOG_DIR).error(f"Error checking packet loss for {dns_server}: {e}")
        return 100

def test_web_connectivity(url="http://www.google.com", timeout=5):
    try:
        command = ["curl", "-I", "--max-time", str(timeout), url]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0

    except FileNotFoundError:
        logging.getLogger(LOG_DIR).error(f"Curl command not found for web connectivity test.")
        return False

    except Exception as e:
        logging.getLogger(LOG_DIR).error(f"Error testing web connectivity to {url}: {e}")
        return False

def get_best_dns():
    main_logger = logging.getLogger(LOG_DIR)
    dns_servers = [
        {"name": "Quad9", "ip": "9.9.9.9"},
        {"name": "Cloudflare DNS", "ip": "1.1.1.1"},
        {"name": "OpenDNS", "ip": "208.67.222.222"},
        {"name": "Google DNS", "ip": "8.8.8.8"},
        {"name": "Emergency DNS 1", "ip": "198.142.0.51"},
        {"name": "Emergency DNS 2", "ip": "198.142.0.52"}
    ]

    results = {}
    threads = []

    def check_server(server):
        latency = ping_dns(server["ip"], timeout=2)
        if latency is not None:
            results[server["ip"]] = (server, latency)

    for server in dns_servers:
        t = threading.Thread(target=check_server, args=(server,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    if results:
        best_dns = min(results.values(), key=lambda x: x[1])[0]
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        print(f"{LIGHT_GREEN}[{timestamp}] Best DNS: {best_dns['name']} ({best_dns['ip']}){RESET}")
        main_logger.info(f"[{timestamp}] Best DNS: {best_dns['name']} ({best_dns['ip']})")
        return best_dns["ip"]

    else:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        print(f"{RED}[{timestamp}] No functional DNS found.{RESET}")
        main_logger.error(f"[{timestamp}] No functional DNS found.")
        return None

def monitor_dns_latency():
    main_logger = logging.getLogger(LOG_DIR)
    max_failures, failure_count = 5, 0
    current_dns = "1.1.1.1"

    def background_dns_eval():
        nonlocal current_dns, failure_count
        new_best = get_best_dns()
        if new_best and new_best != current_dns:
            current_dns = new_best
            failure_count = 0

    threading.Thread(target=background_dns_eval, daemon=True).start()

    while True:
        if not current_dns:
            current_dns = get_best_dns()
            if not current_dns:
                print(f"{YELLOW}Waiting for coverage...{RESET}")
                threading.Event().wait(10)
                continue

        latency = ping_dns(current_dns)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        if latency is not None:
            if failure_count >= 2:
                print(f"{LIGHT_GREEN}[{timestamp}] Connection restored!{RESET}")
                main_logger.info(f"[{timestamp}] Connection restored!")
            failure_count = 0
            status_color = LIGHT_GREEN if latency < 50 else (BROWN if latency < 100 else RED)
            print(f"{status_color}[{timestamp}] Ping to {current_dns}: {latency:.1f} ms{RESET}")
            main_logger.info(f"[{timestamp}] Ping to {current_dns}: {latency} ms")
        else:
            failure_count += 1
            print(f"{RED}[{timestamp}] Ping to {current_dns}: Failed{RESET}")
            main_logger.info(f"[{timestamp}] Ping to {current_dns}: Failed")
            
            if failure_count == 2:
                print(f"{YELLOW}[ALERT] [{timestamp}] Connection unstable / Packet loss detected!{RESET}")
                main_logger.warning(f"[{timestamp}] Connection unstable / Packet loss detected!")

        if failure_count >= max_failures:
            print(f"{RED}[{timestamp}] Too many failures. Reevaluating DNS...{RESET}")
            main_logger.warning(f"[{timestamp}] Too many ping failures to {current_dns}. Reevaluating DNS.")
            current_dns, failure_count = None, 0

        threading.Event().wait(3)

def get_mobile_network_info():
    global current_public_ip, initial_mobile_state
    main_logger = logging.getLogger(LOG_DIR)
    previous_state = initial_mobile_state
    retry_delay = 5
    last_public_ip_check_time = datetime.now()
    public_ip_check_interval = 60

    while True:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        if (datetime.now() - last_public_ip_check_time).total_seconds() >= public_ip_check_interval:
            new_public_ip = get_public_ip()
            if new_public_ip != "N/A" and new_public_ip != current_public_ip:
                print(f"{YELLOW}[ALERT] [{timestamp}] Public IP changed: {current_public_ip} -> {new_public_ip}{RESET}")
                main_logger.warning(f"[{timestamp}] Public IP changed: {current_public_ip} -> {new_public_ip}")
                current_public_ip = new_public_ip
            last_public_ip_check_time = datetime.now()
        mobile_info_raw = None
        success = False

        try:
            mobile_info_raw = subprocess.check_output(["termux-telephony-deviceinfo"], timeout=5).decode("utf-8")
            success = True

        except subprocess.TimeoutExpired:
            main_logger.warning(f"[{timestamp}] Timeout getting mobile info. Retrying in {retry_delay} seconds...")
            threading.Event().wait(retry_delay)
            continue

        except FileNotFoundError:
             print(f"{RED}[{timestamp}] Error: 'termux-telephony-deviceinfo' command not found. Stopping mobile info checks.{RESET}")
             main_logger.error(f"[{timestamp}] 'termux-telephony-deviceinfo' command not found. Stopping mobile info checks.")
             success = False
             break

        except Exception as e:
            main_logger.error(f"[{timestamp}] Error retrieving mobile info: {e}. Retrying in {retry_delay} seconds...")
            threading.Event().wait(retry_delay)
            continue


        if success and mobile_info_raw:
            try:
                mobile_info = json.loads(mobile_info_raw)
                operator = mobile_info.get("network_operator_name", "Unknown")
                network_type = mobile_info.get("network_type", "Unknown").upper()
                data_enabled = mobile_info.get("data_enabled", "Unknown")
                sim_state = mobile_info.get("sim_state", "Unknown")

                current_state = {
                    "operator": operator,
                    "network_type": network_type,
                    "data_enabled": data_enabled,
                    "sim_state": sim_state
                }

                if current_state != previous_state:
                    print(f"{CYAN}[{timestamp}] Operator: {operator}, Network: {network_type}, Data: {data_enabled}, SIM: {sim_state}{RESET}")
                    main_logger.info(f"[{timestamp}] Operator: {operator}, Network: {network_type}, Data: {data_enabled}, SIM: {sim_state}")
                    previous_state = current_state

            except json.JSONDecodeError as e:
                 print(f"{RED}[{timestamp}] Error parsing mobile info JSON: {e}{RESET}")
                 main_logger.error(f"[{timestamp}] Error parsing mobile info JSON: {e}. Raw data: {mobile_info_raw[:100]}...")
            except Exception as e:
                 print(f"{RED}[{timestamp}] Error processing mobile info: {e}{RESET}")
                 main_logger.error(f"[{timestamp}] Error processing mobile info: {e}")

        threading.Event().wait(60)

def get_battery_status():
    main_logger = logging.getLogger(LOG_DIR)
    try:
        result_raw = subprocess.check_output(["termux-battery-status"], timeout=5).decode("utf-8")
        battery_info = json.loads(result_raw)
        return battery_info

    except FileNotFoundError:
        if not hasattr(get_battery_status, "logged_not_found"):
            main_logger.error("'termux-battery-status' command not found. Battery monitoring disabled.")
            get_battery_status.logged_not_found = True
        return None
        
    except subprocess.TimeoutExpired:
        main_logger.warning("Timeout getting battery status.")
        return None

    except json.JSONDecodeError:
        main_logger.error("Error parsing battery status JSON.")
        return None

    except Exception as e:
        main_logger.error(f"Error getting battery status: {e}")
        return None

def monitor_battery():
    global alerted_levels
    main_logger = logging.getLogger(LOG_DIR)
    interval_seconds = 60
    thresholds = [10, 20, 30, 40, 50, 60, 70, 80, 90]

    init_batt = get_battery_status()
    if init_batt and init_batt.get("percentage") is not None:
        p = init_batt.get("percentage")
        for l in thresholds:
            if p <= l:
                alerted_levels.add(l)

    while True:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        battery_info = get_battery_status()

        if battery_info:
            percentage = battery_info.get("percentage")
            status = battery_info.get("status", "UNKNOWN").upper()

            if percentage is not None:
                main_logger.info(f"[{timestamp}] Battery: {percentage}% ({status})")

                if status == "DISCHARGING":
                    for level in sorted(thresholds, reverse=True):
                        if percentage <= level:
                            if level not in alerted_levels:
                                print(f"{YELLOW}[{timestamp}] Battery info: {percentage}% (Discharging){RESET}")
                                main_logger.info(f"[{timestamp}] Battery info: {percentage}% (Discharging)")
                                for l in thresholds:
                                    if percentage <= l:
                                        alerted_levels.add(l)
                            break


                levels_to_remove = set()
                for alerted_level in alerted_levels:
                    if percentage > alerted_level or status != "DISCHARGING":
                        levels_to_remove.add(alerted_level)
                        if status != "DISCHARGING":
                            main_logger.info(f"[{timestamp}] Battery no longer discharging. Resetting alert for {alerted_level}%.")
                        else:
                            main_logger.info(f"[{timestamp}] Battery charged above {alerted_level}%. Resetting alert.")


                alerted_levels -= levels_to_remove

            else:
                main_logger.warning(f"[{timestamp}] Could not determine battery percentage from status.")
        else:
             if hasattr(get_battery_status, "logged_not_found"):
                 main_logger.info("Stopping battery monitoring thread due to missing command.")
                 break

        threading.Event().wait(interval_seconds)


def monitor_network():
    setup_logger()
    log_session_start()
    main_logger = logging.getLogger(LOG_DIR)

    mobile_thread = threading.Thread(target=get_mobile_network_info, daemon=True)
    dns_thread = threading.Thread(target=monitor_dns_latency, daemon=True)
    battery_thread = threading.Thread(target=monitor_battery, daemon=True)

    mobile_thread.start()
    dns_thread.start()
    battery_thread.start()

    while True:
        try:
            mobile_thread.join(timeout=1.0)
            dns_thread.join(timeout=1.0)
            battery_thread.join(timeout=1.0)

            if not (mobile_thread.is_alive() and dns_thread.is_alive()):
                 main_logger.error("A critical monitoring thread (Mobile or DNS) has unexpectedly stopped.")

            if not battery_thread.is_alive() and not hasattr(get_battery_status, "logged_not_found"):
                 main_logger.warning("Battery monitoring thread has stopped unexpectedly.")

        except KeyboardInterrupt:
             print(f"\n{RED}[-] Monitoring stopping...{RESET}")
             main_logger.info("KeyboardInterrupt received. Stopping monitoring.")
             break

try:
    if __name__ == "__main__":
        monitor_network()

except KeyboardInterrupt:
    print(f"\n{RED}Monitoring stopped by user (outer block){RESET}")
    logging.getLogger(LOG_DIR).info("Monitoring stopped by user (outer block).")

finally:
    main_logger = logging.getLogger(LOG_DIR)
    if main_logger.hasHandlers():
         main_logger.info("--- MONITORING ENDED ---")

    print(f"{CYAN}[*] Monitoring finished.{RESET}")
