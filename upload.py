import sys
import base64, marshal, zlib, hashlib, requests, json

sys.stdout.reconfigure(encoding='utf-8')

print("==================================================")
print("[업로드] main_ui.py 암호화 후 GitHub 업로드 시작...")
print("==================================================")

# 1. 암호화
with open("main_ui.py", "r", encoding="utf-8") as f:
    code = f.read()

compiled = compile(code, "main_ui.py", "exec")
marshaled = marshal.dumps(compiled)
compressed = zlib.compress(marshaled, level=9)
_k1 = "maple"; _k2 = "planet"; _k3 = "macro"
xor_key = hashlib.sha256((_k1 + _k2 + _k3).encode()).digest()
xored = bytes(b ^ xor_key[i % len(xor_key)] for i, b in enumerate(compressed))
encoded = base64.b64encode(xored).decode()

# 2. GitHub 업로드
with open("token.txt", "r") as _tf: TOKEN = _tf.read().strip()
REPO  = "noixsy-art/pub"
FILE  = "code.enc"

headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}

r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{FILE}", headers=headers)
sha = r.json().get("sha", "") if r.status_code == 200 else ""

data = {"message": "update code", "content": base64.b64encode(encoded.encode()).decode()}
if sha: data["sha"] = sha

r = requests.put(f"https://api.github.com/repos/{REPO}/contents/{FILE}", headers=headers, data=json.dumps(data))

if r.status_code in [200, 201]:
    print("[완료] GitHub 업로드 성공!")
    print(f"URL: https://raw.githubusercontent.com/{REPO}/main/{FILE}")
else:
    print(f"[실패] {r.status_code}: {r.text[:300]}")
print("==================================================")
