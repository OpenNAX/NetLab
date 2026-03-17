import os
import json
import socket
import logging
import requests
import threading
import subprocess
from datetime import datetime

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
version = "v2.0.0"

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
print(f"{CYAN}Starting NetLab · {version}...{RESET}")

LOG_DIR = "netlab_logs"
SENSITIVE_LOG_DIR = "netlab_sensitive_logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
if not os.path.exists(SENSITIVE_LOG_DIR):
    os.makedirs(SENSITIVE_LOG_DIR)

main_logger_name = 'netlab_main'
sensitive_logger_name = 'netlab_sensitive'

alerted_levels = set()

def setup_logger():
    log_filename = f"{LOG_DIR}/network_logs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    main_logger = logging.getLogger(main_logger_name)
    main_logger.setLevel(logging.INFO)
    if not main_logger.handlers:
        main_handler = logging.FileHandler(log_filename)
        main_formatter = logging.Formatter("%(message)s")
        main_handler.setFormatter(main_formatter)
        main_logger.addHandler(main_handler)

    sensitive_log_filename = f"{SENSITIVE_LOG_DIR}/sens_network_logs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    sensitive_logger = logging.getLogger(sensitive_logger_name)
    sensitive_logger.setLevel(logging.INFO)
    if not sensitive_logger.handlers:
        sensitive_handler = logging.FileHandler(sensitive_log_filename)
        sensitive_formatter = logging.Formatter("%(asctime)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
        sensitive_handler.setFormatter(sensitive_formatter)
        sensitive_logger.addHandler(sensitive_handler)


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

def log_session_start():
    global current_public_ip
    intro()
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    local_ips = get_local_ip_addresses()
    public_ip = get_public_ip()
    current_public_ip = public_ip

    main_logger = logging.getLogger(main_logger_name)
    sensitive_logger = logging.getLogger(sensitive_logger_name)

    print(
        f"{CYAN}--- STARTING MONITOR ---\n"
        f"· Time: {start_time}\n"
        f"· Local IP(s): {', '.join(local_ips)}\n"
        f"· Public IP: {public_ip}\n"
        f"{RESET}"
    )

    main_logger.info(f"--- STARTING MONITOR ---")
    main_logger.info(f"Time: {start_time}")
    main_logger.info(f"Local IP(s): {', '.join(local_ips)}")

    sensitive_logger.info(f"--- SESSION START ---")
    sensitive_logger.info(f"Public IP: {public_ip}")
    sensitive_logger.info(f"Local IP(s): {', '.join(local_ips)}")

def ping_dns(dns_server, timeout=2):
    try:
        command = ["ping", "-c", "1", "-W", str(timeout), dns_server]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

        for line in result.stdout.splitlines():
            if "time=" in line:
                try:
                    latency = float(line.split("time=")[1].split()[0])
                    return latency
                except (IndexError, ValueError):
                    pass
        return None

    except subprocess.CalledProcessError as e:
        logging.getLogger(main_logger_name).warning(f"Ping command failed for {dns_server}: {e.stderr}")
        return None

    except FileNotFoundError:
        logging.getLogger(main_logger_name).error(f"Ping command not found.")
        return None

    except Exception as e:
        logging.getLogger(main_logger_name).error(f"Error pinging {dns_server}: {e}")
        return None

def check_packet_loss(dns_server, count=5, timeout=2):
    try:
        command = ["ping", "-c", str(count), "-W", str(timeout), dns_server]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "packet loss" in line:
                    try:
                        packet_loss = int(line.split(", ")[2].split("%")[0])
                        return packet_loss
                    except (IndexError, ValueError):
                        pass
        return 100

    except FileNotFoundError:
        logging.getLogger(main_logger_name).error(f"Ping command not found for packet loss check.")
        return 100

    except Exception as e:
        logging.getLogger(main_logger_name).error(f"Error checking packet loss for {dns_server}: {e}")
        return 100

def test_web_connectivity(url="http://www.google.com", timeout=5):
    try:
        command = ["curl", "-I", "--max-time", str(timeout), url]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0

    except FileNotFoundError:
        logging.getLogger(main_logger_name).error(f"Curl command not found for web connectivity test.")
        return False
        
    except Exception as e:
        logging.getLogger(main_logger_name).error(f"Error testing web connectivity to {url}: {e}")
        return False

def get_best_dns():
    main_logger = logging.getLogger(main_logger_name)
    dns_servers = [
        {"name": "Quad9", "ip": "9.9.9.9"},
        {"name": "Cloudflare DNS", "ip": "1.1.1.1"},
        {"name": "OpenDNS", "ip": "208.67.222.222"},
        {"name": "Google DNS", "ip": "8.8.8.8"}
    ]

    emergency_dns = [
        {"name": "Emergency DNS 1", "ip": "198.142.0.51"},
        {"name": "Emergency DNS 2", "ip": "198.142.0.52"}
    ]

    results = {}
    for server in dns_servers + emergency_dns:
        latency = ping_dns(server["ip"], timeout=2)
        if latency is not None:
            results[server["ip"]] = (server, latency)

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
    global current_public_ip
    main_logger = logging.getLogger(main_logger_name)
    sensitive_logger = logging.getLogger(sensitive_logger_name)
    max_failures, failure_count, current_dns = 5, 0, None
    latencies = []
    interval = 5
    last_summary_time = datetime.now()
    last_public_ip_check_time = datetime.now()
    public_ip_check_interval = 60

    while True:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        if (datetime.now() - last_public_ip_check_time).total_seconds() >= public_ip_check_interval:
            new_public_ip = get_public_ip()
            if new_public_ip != "N/A" and new_public_ip != current_public_ip:
                print(f"{YELLOW}[ALERT] [{timestamp}] Public IP changed: {current_public_ip} -> {new_public_ip}{RESET}")
                main_logger.warning(f"[{timestamp}] Public IP changed: {current_public_ip} -> {new_public_ip}")
                sensitive_logger.warning(f"[{timestamp}] Public IP changed: {current_public_ip} -> {new_public_ip}")
                current_public_ip = new_public_ip
            last_public_ip_check_time = datetime.now()


        if not current_dns:
            current_dns = get_best_dns()
            if not current_dns:
                print(f"{YELLOW}Waiting for coverage...{RESET}")
                threading.Event().wait(10)
                continue

        latency = ping_dns(current_dns)

        if latency is not None:
            failure_count = 0
            latencies.append(latency)
            main_logger.info(f"[{timestamp}] Ping to {current_dns}: {latency} ms")

        else:
            failure_count += 1
            main_logger.info(f"[{timestamp}] Ping to {current_dns}: Failed")

        if (datetime.now() - last_summary_time).total_seconds() >= interval:
            avg_latency = sum(latencies) / len(latencies) if latencies else None
            
            status = "Unknown"
            status_color = RED
            if avg_latency is not None:
                if avg_latency < 50:
                    status = "Good"
                    status_color = LIGHT_GREEN

                elif avg_latency < 100:
                    status = "Medium"
                    status_color = BROWN
                else:
                    status = "Bad"
                    status_color = RED

            print(f"{status_color}[{timestamp}] Ping summary: Average: {avg_latency:.1f} ms ({status}){RESET}" if avg_latency is not None else f"{RED}[{timestamp}] Ping failed.{RESET}")
            main_logger.info(f"[{timestamp}] Ping summary: Average: {avg_latency:.1f} ms ({status})" if avg_latency is not None else f"[{timestamp}] Ping failed.")

            packet_loss = check_packet_loss(current_dns)
            if packet_loss is not None and packet_loss > 50:
                print(f"{RED}[ALERT] [{timestamp}] High packet loss ({packet_loss}%){RESET}")
                main_logger.warning(f"[{timestamp}] High packet loss ({packet_loss}%)")
            elif packet_loss is None:
                 main_logger.warning(f"[{timestamp}] Packet loss check failed for {current_dns}")


            if not test_web_connectivity():
                print(f"{RED}[ALERT] [{timestamp}] Web connectivity failed.{RESET}")
                main_logger.warning(f"[{timestamp}] Web connectivity failed.")

            latencies.clear()
            last_summary_time = datetime.now()

        if failure_count >= max_failures:
            print(f"{RED}Too many failures. Reevaluating DNS...{RESET}")
            main_logger.warning(f"[{timestamp}] Too many ping failures to {current_dns}. Reevaluating DNS.")
            current_dns, failure_count = None, 0
            latencies.clear()

        threading.Event().wait(1)

def get_mobile_network_info():
    main_logger = logging.getLogger(main_logger_name)
    sensitive_logger = logging.getLogger(sensitive_logger_name)
    previous_state = None
    retry_delay = 5

    while True:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
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

def evaluate_network_quality():
    main_logger = logging.getLogger(main_logger_name)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    dns_server = "8.8.8.8"
    avg_latency = ping_dns(dns_server)
    packet_loss = check_packet_loss(dns_server)

    if avg_latency is not None:
        latency_status = "Good" if avg_latency < 50 else "Bad"
    print(f"{LIGHT_GREEN}[{timestamp}] Latency: {avg_latency:.1f} ms ({latency_status}){RESET}" if avg_latency is not None else f"{RED}[{timestamp}] Latency test failed.{RESET}")
    main_logger.info(f"[{timestamp}] Latency test to {dns_server}: {avg_latency:.1f} ms ({latency_status})" if avg_latency is not None else f"[{timestamp}] Latency test to {dns_server} failed.")

    if packet_loss is not None:
        packet_loss_status = "Good" if packet_loss < 10 else "Bad"
    print(f"{LIGHT_GREEN if packet_loss < 10 else RED}[{timestamp}] Packet loss: {packet_loss}% ({packet_loss_status}){RESET}" if packet_loss is not None else f"{RED}[{timestamp}] Packet loss test failed.{RESET}")
    main_logger.info(f"[{timestamp}] Packet loss test to {dns_server}: {packet_loss}% ({packet_loss_status})" if packet_loss is not None else f"[{timestamp}] Packet loss test to {dns_server} failed.")

    download_test_url = "http://speed.cloudflare.com/__down?bytes=100000"
    speed_MBps, speed_Mbps = test_download_speed(download_test_url, timeout=10)

    print(f"{LIGHT_GREEN}[{timestamp}] Download speed: {speed_MBps:.2f} MB/s ({speed_Mbps:.2f} Mbps){RESET}" if speed_MBps is not None else f"{RED}[{timestamp}] Download test failed.{RESET}")
    main_logger.info(f"[{timestamp}] Download speedtest: {speed_MBps:.2f} MB/s ({speed_Mbps:.2f} Mbps)" if speed_MBps is not None else f"[{timestamp}] Download speedtest failed.")

def test_download_speed(url="http://speed.cloudflare.com/__down?bytes=100000", timeout=10):
    main_logger = logging.getLogger(main_logger_name)
    null_device = '/dev/null' if os.path.exists('/dev/null') else 'NUL'
    try:
        start_time = datetime.now()
        file_size_bytes = 100000

        command = ["curl", "-o", null_device, "--max-time", str(timeout), url]
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        end_time = datetime.now()

        download_time_seconds = (end_time - start_time).total_seconds()
        if download_time_seconds > 0:
            speed_bytes_per_sec = file_size_bytes / download_time_seconds
            speed_MBps = speed_bytes_per_sec / (1024 * 1024)
            speed_Mbps = speed_MBps * 8
            return speed_MBps, speed_Mbps
        else:
             return 0.0, 0.0

    except subprocess.CalledProcessError as e:
        main_logger.error(f"Curl command failed during download test: {e.stderr}")
        return None, None

    except FileNotFoundError:
        main_logger.error(f"Curl command not found for download speedtest.")
        return None, None

    except Exception as e:
        main_logger.error(f"Download speedtest failed: {e}")
        return None, None

def get_battery_status():
    main_logger = logging.getLogger(main_logger_name)
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
    main_logger = logging.getLogger(main_logger_name)
    interval_seconds = 60
    thresholds = [10, 20, 30, 40, 50, 60, 70, 80, 90]

    while True:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        battery_info = get_battery_status()

        if battery_info:
            percentage = battery_info.get("percentage")
            status = battery_info.get("status", "UNKNOWN").upper()

            if percentage is not None:
                main_logger.info(f"[{timestamp}] Battery: {percentage}% ({status})")

                if status == "DISCHARGING":
                    for level in thresholds:
                        if percentage <= level and level not in alerted_levels:
                            print(f"{YELLOW}[ALERT] [{timestamp}] Battery level low: {percentage}% (Discharging){RESET}")
                            main_logger.warning(f"[{timestamp}] Battery level low: {percentage}% (Discharging)")
                            alerted_levels.add(level)


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
    main_logger = logging.getLogger(main_logger_name)

    evaluate_network_quality()

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
             print(f"\n{RED}Monitoring stopping...{RESET}")
             main_logger.info("KeyboardInterrupt received. Stopping monitoring.")
             break

try:
    if __name__ == "__main__":
        monitor_network()

except KeyboardInterrupt:
    print(f"\n{RED}Monitoring stopped by user (outer block){RESET}")
    logging.getLogger(main_logger_name).info("Monitoring stopped by user (outer block).")
    logging.getLogger(sensitive_logger_name).info("--- SESSION END ---")

finally:
    main_logger = logging.getLogger(main_logger_name)
    sensitive_logger = logging.getLogger(sensitive_logger_name)
    if main_logger.hasHandlers():
         main_logger.info("--- MONITORING ENDED ---")

    if sensitive_logger.hasHandlers():
         sensitive_logger.info("--- SESSION END ---")
    print(f"{CYAN}Monitoring finished.{RESET}")