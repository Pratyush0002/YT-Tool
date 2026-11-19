import os
import sys
import time
import webbrowser
import threading
from pathlib import Path

# Ensure working directory is set to this file's folder
BASE_DIR = Path(__file__).resolve().parent
os.chdir(str(BASE_DIR))

def open_browser(port):
    time.sleep(1.2)
    url = f"http://127.0.0.1:{port}"
    print(f"\n[Browser] Opening {url} in your default browser...\n")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[Browser Error] Could not open browser automatically: {e}")

if __name__ == "__main__":
    from app import app

    port = 5000
    print("=" * 65)
    print(" 🚀 ShortsViral AI - YouTube Shorts Comedy Generator")
    print(f" URL: http://127.0.0.1:{port}")
    print("=" * 65)

    # Launch browser in a background thread
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Run the Flask web server
    try:
        app.run(host="127.0.0.1", port=port, debug=False)
    except Exception as e:
        print(f"\n[Error starting server]: {e}")
        input("\nPress Enter to exit...")
