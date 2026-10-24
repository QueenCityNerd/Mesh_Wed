import os
import subprocess
import time
from html import escape
import meshtastic.serial_interface
from pubsub import pub

# Configuration
SERIAL_PORT = "/dev/ttyUSB0"  # Adjust if using /dev/ttyACM0

# Local path to your cloned Mesh_Wed Git repository on the Raspberry Pi
REPO_DIR = "/home/malachi/Mesh_Wed"
OUTPUT_HTML = os.path.join(REPO_DIR, "index.html")

MAX_CHECKINS = 100

# Message Board Configuration
LOG_FILE = "/home/malachi/mesh_room_log.txt"
MAX_HISTORY_TO_SEND = 5

# Git auto-publish settings
AUTO_PUSH_TO_GITHUB = True
PUSH_INTERVAL = 60  # Minimum seconds between git pushes

net_checkins = []
last_push_time = 0
NET_TAG = "#mwm"


def process_checkin(sender_id, short_name, text):
    global net_checkins
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    net_checkins.insert(
        0,
        {
            "time": timestamp,
            "sender_id": sender_id,
            "short_name": short_name,
            "text": text,
        },
    )

    if len(net_checkins) > MAX_CHECKINS:
        net_checkins.pop()

    write_html_report()
    maybe_git_push()


def maybe_git_push():
    global last_push_time
    if not AUTO_PUSH_TO_GITHUB:
        return

    current_time = time.time()
    if current_time - last_push_time > PUSH_INTERVAL:
        try:
            # Run git commands scoped directly to your local Mesh_Wed repo folder
            subprocess.run(
                ["git", "add", "index.html"],
                cwd=REPO_DIR,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["git", "commit", "-m", "Auto-update STMesh #mwm roster"],
                cwd=REPO_DIR,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["git", "push"],
                cwd=REPO_DIR,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            last_push_time = current_time
            print(f"[{time.strftime('%H:%M:%S')}] Roster successfully pushed to https://queencitynerd.github.io/Mesh_Wed/")
        except subprocess.CalledProcessError as e:
            print(f"[{time.strftime('%H:%M:%S')}] Git push skipped/failed (Check local git status): {e}")


def write_html_report():
    roster_rows = []
    for entry in net_checkins:
        roster_rows.append(
            "<tr>"
            f"<td>{entry['time']}</td>"
            f"<td><span class='short-name'>{escape(entry['short_name'])}</span><span"
            f" class='node-id'>({escape(entry['sender_id'])})</span></td>"
            f"<td>{escape(entry['text'])}</td>"
            "</tr>"
        )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="30">
    <title>STMesh &bull; #mwm Net Monitor</title>
    <style>
        :root {{
            --bg-color: #0f1115;
            --card-bg: #161b22;
            --border-color: #30363d;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --accent-blue: #58a6ff;
            --accent-green: #238636;
            --code-bg: #21262d;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 20px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 20px;
            margin-bottom: 25px;
        }}
        h1 {{
            font-size: 1.8rem;
            margin: 0 0 5px 0;
            font-family: monospace;
            color: var(--text-primary);
        }}
        .subtitle {{
            color: var(--text-secondary);
            font-size: 0.95rem;
        }}
        .info-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 15px 20px;
            margin-bottom: 25px;
            font-size: 0.9rem;
        }}
        .info-card h3 {{
            margin-top: 0;
            color: var(--accent-blue);
            font-size: 1rem;
        }}
        .info-card code {{
            background-color: var(--code-bg);
            padding: 2px 6px;
            border-radius: 4px;
            color: #7ee787;
            font-family: monospace;
        }}
        h2 {{
            font-size: 1.2rem;
            margin-top: 30px;
            margin-bottom: 12px;
            color: var(--text-primary);
            border-left: 3px solid var(--accent-blue);
            padding-left: 10px;
        }}
        .table-container {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            overflow-x: auto;
            margin-bottom: 25px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th, td {{
            padding: 12px 16px;
            font-size: 0.9rem;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            background-color: #1f242c;
            color: var(--text-secondary);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        tr:hover {{
            background-color: #1c2128;
        }}
        .short-name {{
            font-weight: bold;
            color: var(--accent-blue);
            font-family: monospace;
            background: var(--code-bg);
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .node-id {{
            color: var(--text-secondary);
            font-size: 0.8rem;
            font-family: monospace;
            margin-left: 6px;
        }}
        footer {{
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.8rem;
            margin-top: 40px;
            border-top: 1px solid var(--border-color);
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>STMesh #mwm Net Monitor</h1>
            <div class="subtitle">STMesh Weekly 24-Hour Net &bull; LongFast Channel</div>
        </header>

        <div class="info-card">
            <h3>How to Check In</h3>
            <p>Participating in the weekly STMesh net is simple! Open your Meshtastic app, change to the <strong>LongFast</strong> channel, and broadcast a message containing the tag <code>#mwm</code> along with your comments for the net.</p>
            <p style="margin-bottom: 0;">Your check-in will automatically log to this roster with your timestamp, node short name, ID, and comment. Page auto-refreshes every 30 seconds.</p>
        </div>

        <h2>Check-In Log ({len(net_checkins)} Entries)</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th style="width: 25%;">Timestamp</th>
                        <th style="width: 25%;">Node</th>
                        <th style="width: 50%;">Comment / Message</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(roster_rows) if roster_rows else '<tr><td colspan="3" style="text-align: center; color: #8b949e;">No #mwm check-ins recorded yet for STMesh today.</td></tr>'}
                </tbody>
            </table>
        </div>

        <footer>
            STMesh Community Net &bull; Auto-generated via Meshtastic Node &bull; Hosted on GitHub Pages &bull; Last Render: {time.strftime('%Y-%m-%d %H:%M:%S')}
        </footer>
    </div>
</body>
</html>
"""
    try:
        with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
            f.write(html_content)
    except IOError as e:
        print(f"Error writing HTML file: {e}")


def send_recent_log(interface, destination_id):
    """Reads the log and sends up to the last 5 entries as individual packets."""
    if not os.path.exists(LOG_FILE):
        interface.sendText(
            "Board is currently empty.", destinationId=destination_id, wantAck=False
        )
        return

    try:
        with open(LOG_FILE, "r") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        if not lines:
            interface.sendText(
                "Board is currently empty.",
                destinationId=destination_id,
                wantAck=False,
            )
            return

        recent = lines[-MAX_HISTORY_TO_SEND:]
        print(f"Sending {len(recent)} history entry/entries...")

        for idx, entry in enumerate(recent, 1):
            if len(entry) > 200:
                entry = entry[:197] + "..."

            print(f" Sending line {idx}/{len(recent)}: {entry}")
            interface.sendText(
                entry, destinationId=destination_id, wantAck=False
            )
            time.sleep(3.5)

    except Exception as e:
        print(f"Error reading log file: {e}")
        interface.sendText(
            "Error retrieving history.",
            destinationId=destination_id,
            wantAck=False,
        )


def on_receive(packet, interface):
    try:
        decoded = packet.get("decoded", {})
        if decoded.get("portnum") == "TEXT_MESSAGE_APP":
            text = decoded.get("text", "").strip()
            sender_id = packet.get("fromId", "unknown")
            my_node_id = getattr(interface.myInfo, "my_node_num", None)

            # 1. Handle Direct Messages (DM Message Board)
            if packet.get("to") == my_node_id:
                print(f"Received DM from {sender_id}: {text}")

                if text.lower() in ["history", "read", "board"]:
                    print(f"Sending history back to {sender_id}...")
                    send_recent_log(interface, sender_id)
                else:
                    timestamp = time.strftime("%m-%d %H:%M")
                    entry = f"[{timestamp}] {sender_id}: {text}"

                    with open(LOG_FILE, "a") as f:
                        f.write(entry + "\n")

                    interface.sendText(
                        "Posted to board.", destinationId=sender_id, wantAck=False
                    )
                    print(f"Added to board: {entry}")

            # 2. Handle Channel Messages (#mwm Net Monitor)
            if NET_TAG in text.lower():
                short_name = "UNK"
                if hasattr(interface, "nodes") and sender_id in interface.nodes:
                    node_info = interface.nodes[sender_id]
                    short_name = node_info.get("user", {}).get(
                        "shortName", "UNK"
                    )

                print(
                    f"Captured #mwm check-in from [{short_name}]"
                    f" ({sender_id})"
                )
                process_checkin(sender_id, short_name, text)

    except Exception as e:
        print(f"Error handling packet: {e}")


def main():
    print(f"Connecting to STMesh node on {SERIAL_PORT}...")
    interface = meshtastic.serial_interface.SerialInterface(devPath=SERIAL_PORT)

    pub.subscribe(on_receive, "meshtastic.receive")

    print(
        "STMesh Combined #mwm Monitor & Room Server running. Output target:"
        f" {OUTPUT_HTML}"
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        interface.close()


if __name__ == "__main__":
    main()
