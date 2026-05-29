import os, subprocess, sys, shutil

sys.stdout.reconfigure(encoding='utf-8')

SOO_DESKTOP = r"D:\공용테스트"

resource_files = [
    "cash_tab1.png", "cash_tab2.png", "miumiu.png", "sell_btn.png",
    "ch.png", "exit_shop_btn.png", "x.png", "alarm.mp3",
    "xz.bmp",
    "xz1.bmp", "xz2.bmp", "xz3.bmp", "xz4.bmp",
    "xz5.bmp", "xz6.bmp", "xz7.bmp", "xz8.bmp",
]

data_args = []
for f in resource_files:
    if os.path.exists(f):
        data_args += [f"--include-data-files={f}={f}"]

print("==================================================")
print("빌드 → soo 테스트 배포 (폴더 빌드)")
print("==================================================")

result = subprocess.run([
    ".venv\\Scripts\\python.exe", "-m", "nuitka",
    "--onefile",
    "--windows-console-mode=attach",
    "--windows-uac-admin",
    "--assume-yes-for-downloads",
    "--output-filename=secure_ui.exe",
    "--output-dir=dist",
    "--enable-plugin=tk-inter",
    "--include-package=cv2",
    "--include-package=mss",
    "--include-package=pydirectinput",
    "--include-package=pygetwindow",
    "--include-package=keyboard",
    "--include-package=pygame",
] + data_args + ["main_ui.py"])

if result.returncode != 0:
    print("\n[실패] 빌드 실패."); sys.exit(1)

os.makedirs(SOO_DESKTOP, exist_ok=True)
shutil.copy(r"dist\secure_ui.exe", SOO_DESKTOP)
print(f"\n[완료] {SOO_DESKTOP}\\secure_ui.exe 복사 완료!")
print("==================================================")
