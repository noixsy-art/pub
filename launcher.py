import sys, os
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

import tkinter as tk
from tkinter import messagebox
import requests, tempfile, subprocess

CURRENT_VERSION = "6.7"
VERSION_URL = "https://raw.githubusercontent.com/noixsy-art/pub/main/version.txt"
EXE_URL = "https://raw.githubusercontent.com/noixsy-art/pub/main/secure_ui.exe"

def check_and_update():
    try:
        r = requests.get(VERSION_URL, timeout=5)
        if r.status_code != 200:
            return
        latest = r.text.strip()
        if latest == CURRENT_VERSION:
            return

        root = tk.Tk(); root.withdraw()
        if not messagebox.askyesno("업데이트", f"새 버전 {latest}이 있습니다.\n업데이트하시겠습니까?"):
            root.destroy(); return
        root.destroy()

        r2 = requests.get(EXE_URL, timeout=60, stream=True)
        if r2.status_code != 200:
            messagebox.showerror("오류", "업데이트 파일 다운로드 실패.")
            return

        tmp_path = os.path.join(tempfile.gettempdir(), "secure_ui_update.exe")
        with open(tmp_path, 'wb') as f:
            for chunk in r2.iter_content(chunk_size=8192):
                f.write(chunk)

        subprocess.Popen([tmp_path])
        sys.exit()

    except requests.exceptions.ConnectionError:
        pass
    except Exception:
        pass

if __name__ == '__main__':
    check_and_update()

    exe_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
    main_exe = os.path.join(exe_dir, "secure_ui.exe")
    if os.path.exists(main_exe):
        subprocess.Popen([main_exe])
    else:
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("오류", "secure_ui.exe를 찾을 수 없습니다.")
        root.destroy()
    sys.exit()
