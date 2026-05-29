import sys, base64, marshal, os, subprocess, zlib, hashlib
sys.stdout.reconfigure(encoding='utf-8')

print("==================================================")
print("[secure_ui2] cash_tab3/4 포함 버전 빌드 시작...")
print("==================================================")

with open('main_ui.py', 'r', encoding='utf-8') as f:
    code = f.read()

compiled = compile(code, 'main_ui.py', 'exec')
marshaled = marshal.dumps(compiled)
compressed = zlib.compress(marshaled, level=9)
_k1 = 'maple'; _k2 = 'planet'; _k3 = 'macro'
xor_key = hashlib.sha256((_k1 + _k2 + _k3).encode()).digest()
xored = bytes(b ^ xor_key[i % len(xor_key)] for i, b in enumerate(compressed))
encoded = base64.b64encode(xored).decode('utf-8')

payload = f"""import base64, marshal, zlib, hashlib
import tkinter
from tkinter import messagebox
import cv2, pyautogui, numpy, pygetwindow, pydirectinput, keyboard, requests, winsound, win32api, win32con, mss

_k1 = "maple"
_k2 = "planet"
_k3 = "macro"
_xk = hashlib.sha256((_k1 + _k2 + _k3).encode()).digest()
_raw = base64.b64decode("{encoded}")
_dec = bytes(b ^ _xk[i % len(_xk)] for i, b in enumerate(_raw))
exec(marshal.loads(zlib.decompress(_dec)), globals())
"""

with open('secure_ui2_src.py', 'w', encoding='utf-8') as f:
    f.write(payload)

resource_files = [
    'cash_tab1.png', 'cash_tab2.png', 'cash_tab3.png', 'cash_tab4.png',
    'miumiu.png', 'sell_btn.png', 'ch.png', 'exit_shop_btn.png', 'x.png',
    'alarm.mp3', 'xz1.bmp', 'xz2.bmp', 'xz3.bmp', 'xz4.bmp',
    'xz5.bmp', 'xz6.bmp', 'xz7.bmp', 'xz8.bmp',
]

add_data = []
for f in resource_files:
    if os.path.exists(f):
        add_data += ['--add-data', f'{f};.']
    else:
        print(f'  [WARNING] 없음: {f}')

cmd = [
    '.venv\\Scripts\\pyinstaller',
    '--onefile', '--noconsole',
    '--uac-admin', '--manifest=admin.manifest',
    '--name=secure_ui2',
    '--hidden-import=tkinter', '--hidden-import=tkinter.messagebox',
    '--hidden-import=cv2', '--hidden-import=pyautogui', '--hidden-import=numpy',
    '--hidden-import=pydirectinput', '--hidden-import=keyboard',
    '--hidden-import=requests', '--hidden-import=win32api', '--hidden-import=win32con',
    '--hidden-import=pygetwindow', '--hidden-import=winsound',
    '--hidden-import=mss', '--hidden-import=mss.windows',
    '--hidden-import=pygame', '--hidden-import=pygame.mixer',
] + add_data + ['secure_ui2_src.py']

result = subprocess.run(cmd)

if os.path.exists('secure_ui2_src.py'):
    os.remove('secure_ui2_src.py')

if result.returncode == 0:
    print("\n[완료] dist\\secure_ui2.exe 생성됨!")
else:
    print("\n[실패] 빌드 에러 확인하세요.")
print("==================================================")
