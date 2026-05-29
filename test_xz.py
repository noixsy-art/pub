import cv2
import numpy as np
import mss
import os
import tkinter as tk
from tkinter import messagebox

BASE = os.path.dirname(os.path.abspath(__file__))
THRESHOLD = 0.65

# 템플릿 로드
templates = []
names = ["xz.bmp"] + [f"xz{i}.bmp" for i in range(1, 9)]
for name in names:
    path = os.path.join(BASE, name)
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is not None:
        templates.append((name, img))
        print(f"로드 성공: {name} {img.shape[1]}x{img.shape[0]}")
    else:
        print(f"로드 실패: {name}")

# 화면 캡처 후 저장
with mss.mss() as sct:
    img = sct.grab(sct.monitors[1])
frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
fh, fw = frame_gray.shape
cv2.imwrite(r"D:\공용테스트\debug_screen.png", frame)
print(f"\n화면 캡처 저장: D:\\공용테스트\\debug_screen.png ({fw}x{fh})")

# 매칭 테스트
results = []
for name, tmpl in templates:
    tmpl_gray = cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY)
    if tmpl_gray.shape[0] > fh or tmpl_gray.shape[1] > fw:
        line = f"{name}: 템플릿이 화면보다 큼 (건너뜀)"
    else:
        res = cv2.matchTemplate(frame_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
        _, maxv, _, _ = cv2.minMaxLoc(res)
        flag = " ★감지!" if maxv >= THRESHOLD else ""
        line = f"{name}: {maxv:.3f}{flag}"
    results.append(line)
    print(line)

root = tk.Tk(); root.withdraw()
messagebox.showinfo("XZ 매칭 결과", "\n".join(results) + f"\n\n임계값: {THRESHOLD}\n캡처: D:\\공용테스트\\debug_screen.png")
root.destroy()
