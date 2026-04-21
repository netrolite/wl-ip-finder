import json
import subprocess
import platform


def ping_ip(ip: str):
    current_os = platform.system().lower()
    if current_os == "windows":
        command = ["ping", "-n", "1", "-w", "0.2", ip]
    else:
        # For Linux/macOS
        command = ["ping", "-c", "1", "-W", "0.2", ip]

    try:
        # Run the command and suppress standard output and errors
        result = subprocess.run(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        # returncode 0 means the ping was successful (pong received)
        return result.returncode == 0
    except Exception:
        return False


if __name__ == "__main__":
    DEFAULT_INPUT_FILE = "scan_result.json"
    input_file = (
        input(f'Scan result file path ("{DEFAULT_INPUT_FILE}" by default): ')
        or DEFAULT_INPUT_FILE
    )
    DEFAULT_OUTPUT_FILE = "ping_result.json"
    output_file = (
        input(f'Output file path ("{DEFAULT_OUTPUT_FILE}" by default): ')
        or DEFAULT_OUTPUT_FILE
    )

    with open(input_file, "r") as f:
        subnets = json.load(f)
    result = []

    for subnet, ips in subnets.items():
        for ip in ips:
            if ping_ip(ip):
                print(f"[+] ping {ip} success")
                result.append(subnet)
                break
            else:
                print(f"ping {ip} timeout")

    with open(output_file, "w") as f:
        json.dump(result, f)
