import ipaddress
import subprocess
import platform
import os
import json

PING_TIMEOUT_SECONDS = 0.1


def ping_ip(ip: str, timeout_seconds: float = PING_TIMEOUT_SECONDS):
    current_os = platform.system().lower()
    if current_os == "windows":
        command = ["ping", "-n", "1", "-w", str(int(timeout_seconds * 1000)), ip]
    elif current_os == "darwin":
        command = ["ping", "-n", "-c", "1", "-W", str(int(timeout_seconds * 1000)), ip]
    else:
        # Linux/Android ping implementations vary, so keep CLI flags conservative
        # and rely on subprocess.run(timeout=...) as the real safeguard.
        command = ["ping", "-n", "-c", "1", "-W", "1", ip]

    try:
        # Enforce the timeout in Python because ping flag semantics differ
        # across Linux, Android/Termux, macOS, and Windows.
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout_seconds,
        )
        # returncode 0 means the ping was successful (pong received)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def scan_subnets(input_filename, output_filename):
    if not os.path.exists(input_filename):
        print(f"Error: Input file '{input_filename}' not found.")
        return

    if not os.path.exists(output_filename):
        print(f"{output_filename} doesn't exist. Creating...")
        with open(output_filename, "w") as f:
            json.dump({}, f)

    with open(output_filename, "r") as f:
        results = json.load(f)

    # Read subnets from input file
    with open(input_filename, "r") as f:
        subnets = f.read().splitlines()

    for subnet_str in subnets:
        subnet_str = subnet_str.strip()
        if not subnet_str:
            continue

        try:
            network = ipaddress.ip_network(subnet_str, strict=True)
            print(f"Scanning subnet: {network}")

            # .hosts() generates usable IP addresses (excludes network and broadcast addresses)
            for ip in network.hosts():
                if ping_ip(str(ip)):
                    print(f"  [+] Active IP found: {ip}")
                    cur_ips = results.get(str(network))
                    if not cur_ips:
                        results[str(network)] = [str(ip)]
                    elif str(ip) not in cur_ips:
                        results[str(network)] = [str(ip)] + cur_ips
                    break  # Exit the loop for this subnet on first success
                else:
                    print(f"ping {ip} timeout")

        except ValueError as e:
            print(f"  [!] Invalid CIDR format '{subnet_str}': {e}")

    # Write the results to the output file in JSON format
    with open(output_filename, "w") as f:
        # indent=4 makes the JSON easily readable (pretty-printed)
        json.dump(results, f, indent=4)

    print(f"\nDone. Wrote {len(results)} working IPs to '{output_filename}'.")


if __name__ == "__main__":
    subnets_file = input("Subnets file path: ")
    DEFAULT_OUTPUT_FILE = "scan_result.json"
    output_file = (
        input(f'Output file path ("{DEFAULT_OUTPUT_FILE}" by default): ')
        or DEFAULT_OUTPUT_FILE
    )
    scan_subnets(subnets_file, output_file)
