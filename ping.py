import json
import subprocess
import platform
import tkinter as tk
from tkinter import ttk
import threading
import time
import os

SETTINGS_FILE = "ping_monitor_settings.json"

def update_list():
    try:
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
            if "ips" in settings and isinstance(settings["ips"], dict):
                ips_to_ping = settings["ips"]
            if "geometry" in settings and isinstance(settings["geometry"], str):
                root.geometry(settings["geometry"])
            return settings
    except FileNotFoundError:
        print(f"Error: {SETTINGS_FILE} not found. Creating a default settings file.")
        default_settings = {"ips": {}, "Name": {}, "geometry": "142x72"} #Default size with border accounted for
        with open(SETTINGS_FILE, "w") as f:
            json.dump(default_settings, f, indent=4)
        return default_settings
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {SETTINGS_FILE}. Creating a default settings file.")
        default_settings = {"ips": {}, "Name": {}, "geometry": "142x72"} #Default size with border accounted for
        with open(SETTINGS_FILE, "w") as f:
            json.dump(default_settings, f, indent=4)
        return default_settings

def ping(ip_address):
    if platform.system() == "Windows":
        ping_command = ["ping", "-n", "1", ip_address]
        creationflags = subprocess.CREATE_NO_WINDOW
    else:
        ping_command = ["ping", "-c", "1", ip_address]
        creationflags = 0

    try:
        subprocess.check_output(ping_command, timeout=2, creationflags=creationflags)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False

def ping_and_update(ip, name_label, status_label, service):
    while running:
        if settings['ips'][service].get(ip, False):
            result = ping(ip)
            name_label.config(text=f"{settings['Name'].get(ip, 'Unknown')}")
            status_label.config(
                text=f"{'Online' if result else 'Offline'}",
                foreground="green" if result else "red",
            )
        else:
            name_label.config(text=f"{settings['Name'].get(ip, 'Unknown')}")
            status_label.config(text="Disabled", foreground="blue")
        time.sleep(1)

def start_pings():
    for service, ip_list in ips_to_ping.items():
        for ip in ip_list:
            if ip in ip_labels:
                name_label, status_label = ip_labels[ip]
                thread = threading.Thread(target=ping_and_update, args=(ip, name_label, status_label, service), daemon=True)
                thread.start()

def update_status(ipnr, status):
    for row in settings['Name']:
        if settings['Name'][row] == ipnr:
            ipnr = row
            break
    for service, ip_list in settings['ips'].items():
        if ipnr in ip_list:
            settings['ips'][service][ipnr] = status
            with open("ping_monitor_settings_3.json", "w") as json_file:
                json.dump(settings, json_file, indent=4)
            name_label, status_label = ip_labels[ipnr]
            status_label.config(text="Disabled" if not status else ("Online" if status else "Offline"), foreground="blue" if not status else ("green" if status else "red"))
            break

def print_label_text(event):
    parent_frame = event.widget.master
    name_label = None
    status_label = None
    for child in parent_frame.winfo_children():
        if child.winfo_class() == 'Label':
            if name_label is None:
                name_label = child
            else:
                status_label = child
                break
    if name_label and status_label:
        ipnr = name_label.cget('text')
        update_status(ipnr, not ("Disabled" in status_label.cget('text')))

if __name__ == "__main__":
    def start_move(event):
        global x, y
        x = event.x
        y = event.y

    def stop_move(event):
        global x, y
        x = None
        y = None

    def do_move(event):
        global x, y
        if x is not None and y is not None:
            new_x = root.winfo_x() + (event.x - x)
            new_y = root.winfo_y() + (event.y - y)
            root.geometry(f"+{new_x}+{new_y}")

    ips_to_ping = {}
    root = tk.Tk()
    root.title("Network Ping Monitor")
    root.configure(bg="black")

    style = ttk.Style()
    style.theme_use("clam")

    settings = update_list()
    ips_to_ping = settings.get('ips', {})
    ip_labels = {}
    e = 0
    for service, ip_list in settings.get('ips', {}).items():
        e += 1
        for ip in ip_list:
            e += 1
    e = e * 20
    e = max(e + 14, 70)

    if platform.system() == "Windows":
        root.attributes('-topmost', True)
    root.geometry(f"129x{e + 2}")  # +2 for the border
    root.overrideredirect(True)

    border_frame = tk.Frame(root, bg="black", highlightthickness=1, highlightbackground="black")
    border_frame.grid(row=0, column=0, sticky="nsew")

    main_frame = tk.Frame(border_frame, bg="#f0f0f0")
    main_frame.grid(row=0, column=0, sticky="nsew")

    row_index = 0
    for service, ip_list in settings.get('ips', {}).items():
        service_label = tk.Label(main_frame, text=service.upper(), font=("Arial", 10, "bold"), background=main_frame.cget("background"))
        service_label.grid(row=row_index, column=0, columnspan=2, padx=2, pady=(5, 0), sticky="w")
        row_index += 1
        for ip in ip_list:
            name_label = tk.Label(main_frame, text=f"{settings['Name'].get(ip, 'Unknown')}", font=("Arial", 8), background=main_frame.cget("background"), highlightthickness=0)
            status_label = tk.Label(main_frame, text="Disabled", font=("Arial", 8, "bold"), background=main_frame.cget("background"), highlightthickness=0, fg="blue")
            name_label.grid(row=row_index, column=0, sticky="w")
            status_label.grid(row=row_index, column=1, sticky="e")

            ip_labels[ip] = (name_label, status_label)
            name_label.bind("<Button-1>", print_label_text)
            status_label.bind("<Button-1>", print_label_text)
            row_index += 1

    root.bind("<Button-1>", start_move)
    root.bind("<ButtonRelease-1>", stop_move)
    root.bind("<B1-Motion>", do_move)

    def on_double_click(event):
        root.destroy()
        os._exit(0)

    root.bind("<Double-Button-1>", on_double_click)

    running = True
    auto_refresh_thread = threading.Thread(target=start_pings, daemon=True)
    auto_refresh_thread.start()

    root.mainloop()
