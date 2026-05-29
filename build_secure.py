import os
import subprocess
import sys
import shutil
import base64
import json
import requests

SHARED_DIR = r"D:\macro_test"

# ── 버전 설정 (배포 전 여기만 바꾸면 됨) ──
VERSION = "6.7"
# ─────────────────────────────────────────

with open("token.txt", "r") as _tf: GITHUB_TOKEN = _tf.read().strip()
GITHUB_REPO  = "noixsy-art/pub"
GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def github_upload(filepath, repo_filename):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{repo_filename}"
    with open(filepath, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    r = requests.get(url, headers=GITHUB_HEADERS)
    sha = r.json().get("sha", "") if r.status_code == 200 else ""
    data = {"message": f"update {repo_filename} v{VERSION}", "content": content}
    if sha:
        data["sha"] = sha
    r = requests.put(url, headers=GITHUB_HEADERS, data=json.dumps(data))
    if r.status_code in [200, 201]:
        print(f"  [GitHub] {repo_filename} 업로드 성공!")
    else:
        print(f"  [GitHub] {repo_filename} 업로드 실패: {r.status_code}")

sys.stdout.reconfigure(encoding='utf-8')

resource_files = [
    "cash_tab1.png",
    "cash_tab2.png",
    "miumiu.png",
    "sell_btn.png",
    "ch.png",
    "exit_shop_btn.png",
    "x.png",
    "투명.png",
]

pyinstaller_data = []
for f in resource_files:
    if os.path.exists(f):
        pyinstaller_data += [f"--add-data={f};."]
    else:
        print(f"  [WARNING] 리소스 없음 (건너뜀): {f}")

PYINSTALLER_COMMON = [
    ".venv\\Scripts\\pyinstaller",
    "--onefile", "--noconsole", "--uac-admin",
    "--manifest=admin.manifest",
    "--distpath=dist",
    "--hidden-import=tkinter",
    "--hidden-import=tkinter.messagebox",
    "--hidden-import=cv2",
    "--hidden-import=mss",
    "--hidden-import=pydirectinput",
    "--hidden-import=pygetwindow",
    "--hidden-import=keyboard",
    "--hidden-import=pygame",
    "--hidden-import=win32api",
    "--hidden-import=win32con",
    "--hidden-import=requests",
]

# ── 1. 배포용 빌드 (인증 있음) ──
print("==================================================")
print("[1/3단계] 배포용 secure_ui.exe 빌드 (인증 포함)...")
print("==================================================")
result = subprocess.run(PYINSTALLER_COMMON + ["--name=secure_ui"] + pyinstaller_data + ["main_ui.py"])
if result.returncode != 0:
    print("\n[실패] 배포용 빌드 실패."); sys.exit(1)
print("\n[완료] 배포용 빌드 성공!")

# ── 2. 테스트용 빌드 (인증 없음) ──
print("\n==================================================")
print("[2/3단계] 테스트용 secure_ui_test.exe 빌드 (인증 없음)...")
print("==================================================")

with open("main_ui.py", "r", encoding="utf-8") as f:
    src = f.read()

patched = src.replace("TEST_MODE = False", "TEST_MODE = True", 1)
with open("_test_build_tmp.py", "w", encoding="utf-8") as f:
    f.write(patched)

try:
    result_test = subprocess.run(PYINSTALLER_COMMON + ["--name=secure_ui_test"] + pyinstaller_data + ["_test_build_tmp.py"])
finally:
    if os.path.exists("_test_build_tmp.py"):
        os.remove("_test_build_tmp.py")
    for tmp in ["_test_build_tmp.spec"]:
        if os.path.exists(tmp): os.remove(tmp)

if result_test.returncode != 0:
    print("\n[실패] 테스트용 빌드 실패."); sys.exit(1)
print("\n[완료] 테스트용 빌드 성공!")

# ── 3. launcher.exe 빌드 ──
print("\n[3/3단계] launcher.exe 빌드 중 (PyInstaller)...")
result_launcher = subprocess.run([
    ".venv\\Scripts\\pyinstaller",
    "--onefile", "--noconsole", "--uac-admin",
    "--manifest=admin.manifest",
    "--hidden-import=tkinter",
    "--hidden-import=tkinter.messagebox",
    "--hidden-import=requests",
    "launcher.py",
])
if result_launcher.returncode == 0:
    print("\n[완료] launcher.exe 빌드 성공!")
else:
    print("\n[실패] launcher.exe 빌드 실패.")

# ── 4. 공유 폴더로 복사 ──
os.makedirs(SHARED_DIR, exist_ok=True)
shutil.copy("dist\\secure_ui.exe",      SHARED_DIR)
shutil.copy("dist\\secure_ui_test.exe", SHARED_DIR)
shutil.copy("dist\\launcher.exe",       SHARED_DIR)
print(f"\n[공유] {SHARED_DIR} 복사 완료")
print("  배포용  : secure_ui.exe      (인증 있음)")
print("  테스트용: secure_ui_test.exe (인증 없음, 바로 실행)")
print("==================================================")

# ── 5. GitHub 업로드 ──
print(f"\n[GitHub] v{VERSION} 업로드 중...")
version_file = "dist\\version.txt"
with open(version_file, "w") as f:
    f.write(VERSION)
github_upload(version_file, "version.txt")
github_upload("dist\\secure_ui.exe", "secure_ui.exe")
os.remove(version_file)
print(f"[GitHub] v{VERSION} 배포 완료!")
print("==================================================")
