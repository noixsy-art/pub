import sys
import os
import glob
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # 모니터별 DPI 인식
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass
import cv2
import pyautogui
import numpy as np
import mss
import pygetwindow as gw
import pydirectinput
import keyboard
import time
import random
import threading
import requests
import tkinter as tk
import winsound
import win32api
import win32con
import win32gui
from tkinter import messagebox
try:
    import pygame
    pygame.mixer.init()
    PYGAME_OK = True
except:
    PYGAME_OK = False

# --- ⚙️ 핵심 기본 설정 ⚙️ ---
GAME_WINDOW_TITLE = "MapleStory Worlds-메이플 플래닛"
INVENTORY_KEY = 'i'    

LOOT_CYCLE_TIME = 90    
SELL_CYCLE_TIME = 600   
BUFF_CYCLE_TIME = 1200  

pyautogui.PAUSE = 0.0
pyautogui.MINIMUM_DURATION = 0.0
PRESET_FILE = "preset.txt"
current_preset_file = [None]

# 🔒 구글 시트 웹게시 CSV URL (동결)
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR632hwJAnyG3RA6mdhM2VRPF9aONBfDs38yvSzqx3-dNS4d76sAJ6ChtDXUTs4BpFZJPqwKq3l35QO/pub?output=csv"
# ----------------------------

# 모던 다크 모드 색상 표
C_BG_MAIN = "#1e1e1e"      
C_BG_CARD = "#2d2d2d"      
C_TEXT_MAIN = "#ffffff"    
C_TEXT_MUTED = "#aaaaaa"   
C_POINT = "#00ffcc"        
C_ACCENT = "#ff5555"       
C_ENTRY_BG = "#3d3d3d"     

def resource_path(relative_path):
    # exe 옆에 같은 이름 파일이 있으면 그걸 우선 사용 (사용자 커스텀 이미지)
    if getattr(sys, 'frozen', False):
        custom = os.path.join(os.path.dirname(sys.executable), relative_path)
        if os.path.exists(custom):
            return custom
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def _get_primary_monitor(sct):
    """Windows 주 모니터 반환 — 주 모니터는 항상 left=0, top=0"""
    for m in sct.monitors[1:]:
        if m['left'] == 0 and m['top'] == 0:
            return m
    return sct.monitors[1]

def _calc_coord_scale():
    try:
        with mss.mss() as _sct:
            phys_w = _get_primary_monitor(_sct)['width']
        log_w = ctypes.windll.user32.GetSystemMetrics(0)
        if phys_w > 0 and log_w > 0 and phys_w != log_w:
            return log_w / phys_w
        return 1.0
    except:
        return 1.0

_COORD_SCALE = _calc_coord_scale()

def get_preset_dir():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.abspath(".")
    folder = os.path.join(base, "preset")
    os.makedirs(folder, exist_ok=True)
    return folder

def get_all_presets():
    d = get_preset_dir()
    return sorted(glob.glob(os.path.join(d, "*.txt")))

# 전역 변수 초기화
minimap_offset = None  
hp_bar_offset = None
POTION_KEY = 'insert'
HP_THRESHOLD = 50
max_detected_hp_pixel_ratio = 100.0
mp_bar_offset = None
MP_POTION_KEY = ''
MP_THRESHOLD = 30
max_detected_mp_pixel_ratio = 100.0

last_custom_key_time = time.time()
next_custom_delay = 60
last_custom_key_time_2 = time.time()
next_custom_delay_2 = 120
last_custom_key_time_3 = time.time()
next_custom_delay_3 = 180

SKILL_KEY_1 = 's'
SKILL_MODE_1 = 'TAP'  
SKILL_KEY_2 = 'd'
SKILL_MODE_2 = 'TAP'

state = "HUNT" 
last_loot_time = time.time()
last_sell_time = time.time() 
last_buff_time = time.time() 
start_time = time.time()
next_sell_delay = random.uniform(SELL_CYCLE_TIME * 0.83, SELL_CYCLE_TIME * 1.18)
next_loot_delay = random.uniform(LOOT_CYCLE_TIME * 0.83, LOOT_CYCLE_TIME * 1.18)
last_idle_time = time.time()
next_idle_delay = random.uniform(480, 900)
left_limit = None
right_limit = None
return_x = None        
right_limit_1f = None  
floor_2_y = None        
current_direction = 'right'

center_x = None
skill_count = 0
teleport_rect = None  # (x1, y1, x2, y2) 미니맵 좌표 기준 네모칸

macro_running = False
macro_paused = False
test_running = False

_logged_in_key = ""
_logged_in_pc = ""

reference_minimap = None  # 맵 감지용 기준 미니맵

transparent_template = None
transparent_last_score = 0.0
transparent_detect_count = 0
transparent_scan_paused = False
ALERT_COOLDOWN = 5.0

btn_f5 = None; btn_f6 = None; btn_f7 = None; btn_f8 = None

WIN32_KEY_MAP = {
    'delete': win32con.VK_DELETE,
    'shift': win32con.VK_SHIFT,
    'insert': win32con.VK_INSERT,
    'space': win32con.VK_SPACE,
    'control': win32con.VK_CONTROL,
    'alt': win32con.VK_MENU,
    'page up': win32con.VK_PRIOR,
    'page down': win32con.VK_NEXT,
    'home': win32con.VK_HOME,
    'end': win32con.VK_END
}

# Insert/Delete/Home/End/PgUp/PgDn 은 Extended Key — 플래그 없으면 Numpad 키로 인식됨
_EXTENDED_VK_CODES = {
    win32con.VK_INSERT, win32con.VK_DELETE,
    win32con.VK_HOME,   win32con.VK_END,
    win32con.VK_PRIOR,  win32con.VK_NEXT,
}

# ── SendInput 스캔코드 기반 하드웨어 입력 시스템 ──
_PUL = ctypes.POINTER(ctypes.c_ulong)

class _KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", _PUL)]

class _MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", _PUL)]

class _HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class _InputUnion(ctypes.Union):
    _fields_ = [("ki", _KeyBdInput), ("mi", _MouseInput), ("hi", _HardwareInput)]

class _INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", _InputUnion)]

_INPUT_KEYBOARD   = 1
_KEYEVENTF_KEYUP  = 0x0002
_KEYEVENTF_SCAN   = 0x0008
_KEYEVENTF_EXTKEY = 0x0001

# 키 이름 → (스캔코드, 확장키 여부)
_SCAN_MAP = {
    'a':(0x1E,False),'b':(0x30,False),'c':(0x2E,False),'d':(0x20,False),
    'e':(0x12,False),'f':(0x21,False),'g':(0x22,False),'h':(0x23,False),
    'i':(0x17,False),'j':(0x24,False),'k':(0x25,False),'l':(0x26,False),
    'm':(0x32,False),'n':(0x31,False),'o':(0x18,False),'p':(0x19,False),
    'q':(0x10,False),'r':(0x13,False),'s':(0x1F,False),'t':(0x14,False),
    'u':(0x16,False),'v':(0x2F,False),'w':(0x11,False),'x':(0x2D,False),
    'y':(0x15,False),'z':(0x2C,False),
    '0':(0x0B,False),'1':(0x02,False),'2':(0x03,False),'3':(0x04,False),
    '4':(0x05,False),'5':(0x06,False),'6':(0x07,False),'7':(0x08,False),
    '8':(0x09,False),'9':(0x0A,False),
    'space':(0x39,False),'enter':(0x1C,False),'escape':(0x01,False),
    'backspace':(0x0E,False),'tab':(0x0F,False),
    'shift':(0x2A,False),'ctrl':(0x1D,False),'alt':(0x38,False),'control':(0x1D,False),
    'f1':(0x3B,False),'f2':(0x3C,False),'f3':(0x3D,False),'f4':(0x3E,False),
    'f5':(0x3F,False),'f6':(0x40,False),'f7':(0x41,False),'f8':(0x42,False),
    'f9':(0x43,False),'f10':(0x44,False),'f11':(0x57,False),'f12':(0x58,False),
    'up':(0x48,True),'down':(0x50,True),'left':(0x4B,True),'right':(0x4D,True),
    'insert':(0x52,True),'delete':(0x53,True),
    'home':(0x47,True),'end':(0x4F,True),
    'page up':(0x49,True),'page down':(0x51,True),
    'caps lock':(0x3A,False),'num lock':(0x45,False),
}

def _get_scan(key_str):
    key_str = (key_str or '').strip().lower()
    if key_str in _SCAN_MAP:
        return _SCAN_MAP[key_str]
    if len(key_str) == 1:
        vk = win32api.VkKeyScan(key_str) & 0xFF
        sc = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
        return (sc, False)
    return (0, False)

def _raw_key(scan, extended, key_up):
    extra = ctypes.c_ulong(0)
    flags = _KEYEVENTF_SCAN
    if extended: flags |= _KEYEVENTF_EXTKEY
    if key_up:   flags |= _KEYEVENTF_KEYUP
    ki = _KeyBdInput(0, scan, flags, 0, ctypes.pointer(extra))
    union = _InputUnion(); union.ki = ki
    inp = _INPUT(_INPUT_KEYBOARD, union)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))

def _sc_keydown(key_str):
    sc, ext = _get_scan(key_str)
    if sc: _raw_key(sc, ext, False)

def _sc_keyup(key_str):
    sc, ext = _get_scan(key_str)
    if sc: _raw_key(sc, ext, True)

def _human_hold():
    return max(0.06, min(0.14, random.gauss(0.10, 0.02)))

def _sc_press(key_str):
    sc, ext = _get_scan(key_str)
    if not sc: return
    _raw_key(sc, ext, False)
    time.sleep(_human_hold())
    _raw_key(sc, ext, True)


def _imread_korean(path, flag=cv2.IMREAD_COLOR):
    buf = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(buf, flag) if buf.size else None

def load_transparent_template():
    global transparent_template
    path = resource_path("투명.png")
    img = _imread_korean(path)
    if img is not None:
        transparent_template = img
        print(f"[감지] 투명.png 로드 성공 ({img.shape[1]}x{img.shape[0]})")
    else:
        transparent_template = None
        print("[감지] 투명.png 로드 실패 - 파일 없음")

TRANSPARENT_THRESHOLD = 0.75

def alert_loop():
    global transparent_last_score, transparent_detect_count
    last_alert = 0
    while macro_running:
        if transparent_scan_paused:
            time.sleep(0.5); continue
        if time.time() - last_alert < ALERT_COOLDOWN:
            time.sleep(0.3); continue
        if transparent_template is None:
            time.sleep(1.0); continue
        try:
            with mss.mss() as sct:
                img = sct.grab(_get_primary_monitor(sct))
            frame_gray = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2GRAY)
            tmpl_gray = cv2.cvtColor(transparent_template, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(frame_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
            _, best_score, _, _ = cv2.minMaxLoc(res)
            transparent_last_score = best_score
            if best_score >= TRANSPARENT_THRESHOLD:
                transparent_detect_count += 1
                last_alert = time.time()
                def _alarm():
                    def _beep():
                        try: ctypes.windll.kernel32.Beep(880, 400)
                        except: pass
                        try: ctypes.windll.kernel32.Beep(1100, 400)
                        except: pass
                        try: ctypes.windll.kernel32.Beep(880, 600)
                        except: pass
                    threading.Thread(target=_beep, daemon=False).start()
                root.after(0, _alarm)
                root.after(0, stop_macro)
                root.after(500, lambda: messagebox.showwarning("감지", "거짓말탐지기 발견"))
        except Exception as e:
            print(f"[감지 오류] {e}")
        time.sleep(0.5)

def capture_minimap_snapshot():
    """미니맵 스냅샷 캡처 (캐릭터 노란 도트 마스킹)"""
    if not minimap_offset: return None
    win = get_game_window()
    if not win: return None
    x = win.left + minimap_offset[0]; y = win.top + minimap_offset[1]
    w, h = minimap_offset[2], minimap_offset[3]
    try:
        with mss.mss() as sct:
            img = sct.grab({"left": x, "top": y, "width": w, "height": h})
        img_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
        # 캐릭터 노란 도트 회색으로 덮기 (맵 구조 비교에 영향 없게)
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        lower_y = np.array([22, 160, 160]); upper_y = np.array([38, 255, 255])
        mask = cv2.inRange(hsv, lower_y, upper_y)
        img_bgr[mask > 0] = [100, 100, 100]
        return img_bgr
    except: return None

def map_guard_loop():
    """맵 이탈 감지 루프 - 기준 맵과 다른 맵 감지되면 즉시 올스탑"""
    global reference_minimap, macro_running
    time.sleep(3)  # 매크로 시작 직후 안정화 대기
    reference_minimap = capture_minimap_snapshot()
    if reference_minimap is None:
        print("[맵 감지] 기준 미니맵 캡처 실패 - 맵 감지 비활성화")
        return
    print("[맵 감지] 기준 맵 저장 완료")

    fail_count = 0
    while macro_running:
        time.sleep(5)
        if not macro_running: break
        current = capture_minimap_snapshot()
        if current is None: continue
        if current.shape != reference_minimap.shape: continue

        ref_gray = cv2.cvtColor(reference_minimap, cv2.COLOR_BGR2GRAY)
        cur_gray = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
        result = cv2.matchTemplate(cur_gray, ref_gray, cv2.TM_CCOEFF_NORMED)
        score = float(result[0][0])

        if score < 0.45:
            fail_count += 1
            print(f"[맵 감지] 유사도 낮음: {score:.2f} ({fail_count}/3)")
            if fail_count >= 3:
                print(f"[맵 감지] 다른 맵 확정 → 매크로 긴급 정지")
                root.after(0, emergency_map_stop)
                break
        else:
            fail_count = 0

def emergency_map_stop():
    """맵 이탈 감지 시 긴급 정지 + 알림"""
    stop_macro()
    if PYGAME_OK:
        try: pygame.mixer.music.stop()
        except: pass
    winsound.Beep(1000, 300); winsound.Beep(800, 300); winsound.Beep(600, 500)
    messagebox.showwarning("맵 이탈 감지", "다른 맵이 감지되어 매크로를 자동 정지했습니다!")


def get_game_window():
    wins = gw.getWindowsWithTitle(GAME_WINDOW_TITLE)
    if not wins: return None
    return wins[0]

def send_hardware_key(key_str):
    time.sleep(random.uniform(0.04, 0.14))
    _sc_press(key_str)

# --- 📍 지형 세팅 모듈 ---
def select_minimap():
    global minimap_offset
    win = get_game_window()
    if not win:
        messagebox.showerror("오류", "❌ 게임 창을 찾을 수 없습니다.")
        return
    win.restore(); win.activate(); time.sleep(0.5)
    with mss.mss() as _sct:
        _raw = _sct.grab({"left": win.left, "top": win.top, "width": win.width, "height": win.height})
    img = cv2.cvtColor(np.array(_raw), cv2.COLOR_BGRA2BGR)
    window_name = "SELECT_MINIMAP"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    roi = cv2.selectROI(window_name, img, False)
    cv2.destroyWindow(window_name)
    if roi[2] > 10 and roi[3] > 10:
        minimap_offset = (int(roi[0]), int(roi[1]), int(roi[2]), int(roi[3]))
        lbl_minimap.config(text="✅ 미니맵 영역: 설정 완료", fg=C_POINT)
    else: messagebox.showwarning("경고", "❌ 드래그 실패.")

def select_hp_bar():
    global hp_bar_offset, max_detected_hp_pixel_ratio
    win = get_game_window()
    if not win:
        messagebox.showerror("오류", "❌ 게임 창을 찾을 수 없습니다.")
        return
    win.restore(); win.activate(); time.sleep(0.5)
    with mss.mss() as _sct:
        _raw = _sct.grab({"left": win.left, "top": win.top, "width": win.width, "height": win.height})
    img = cv2.cvtColor(np.array(_raw), cv2.COLOR_BGRA2BGR)
    window_name = "SELECT_HP_BAR"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    roi = cv2.selectROI(window_name, img, False)
    cv2.destroyWindow(window_name)
    if roi[2] > 5 and roi[3] > 2:
        hp_bar_offset = (int(roi[0]), int(roi[1]), int(roi[2]), int(roi[3]))
        lbl_hp_status.config(text="✅ HP 영역: 설정 완료", fg=C_POINT)
        time.sleep(0.1)
        raw_ratio = check_hp_raw_ratio()
        if raw_ratio > 5.0:
            max_detected_hp_pixel_ratio = raw_ratio
    else: messagebox.showwarning("경고", "❌ 드래그 실패.")

def select_mp_bar():
    global mp_bar_offset, max_detected_mp_pixel_ratio
    win = get_game_window()
    if not win:
        messagebox.showerror("오류", "❌ 게임 창을 찾을 수 없습니다.")
        return
    win.restore(); win.activate(); time.sleep(0.5)
    with mss.mss() as _sct:
        _raw = _sct.grab({"left": win.left, "top": win.top, "width": win.width, "height": win.height})
    img = cv2.cvtColor(np.array(_raw), cv2.COLOR_BGRA2BGR)
    window_name = "SELECT_MP_BAR"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    roi = cv2.selectROI(window_name, img, False)
    cv2.destroyWindow(window_name)
    if roi[2] > 5 and roi[3] > 2:
        mp_bar_offset = (int(roi[0]), int(roi[1]), int(roi[2]), int(roi[3]))
        lbl_mp_status.config(text="✅ MP 영역: 설정 완료", fg=C_POINT)
        time.sleep(0.1)
        raw_ratio = check_mp_raw_ratio()
        if raw_ratio > 5.0:
            max_detected_mp_pixel_ratio = raw_ratio
    else: messagebox.showwarning("경고", "❌ 드래그 실패.")

def set_left_limit():
    pos = get_pos()
    if pos: 
        global left_limit, floor_2_y
        left_limit = pos[0]; floor_2_y = pos[1]
        lbl_f5.config(text=f"X: {left_limit}", fg=C_POINT)

def set_right_limit():
    pos = get_pos()
    if pos: 
        global right_limit
        right_limit = pos[0]
        lbl_f6.config(text=f"X: {right_limit}", fg=C_POINT)

def set_return_x():
    pos = get_pos()
    if pos: 
        global return_x
        return_x = pos[0]
        lbl_f7.config(text=f"X: {return_x}", fg=C_POINT)

def set_right_limit_1f():
    pos = get_pos()
    if pos:
        global right_limit_1f
        right_limit_1f = pos[0]
        lbl_f8.config(text=f"X: {right_limit_1f}", fg=C_POINT)

def set_teleport_rect():
    global teleport_rect
    if not minimap_offset:
        messagebox.showerror("오류", "먼저 미니맵 영역을 지정해주세요."); return
    win = get_game_window()
    if not win:
        messagebox.showerror("오류", "게임 창을 찾을 수 없습니다."); return
    win.restore(); win.activate(); time.sleep(0.5)

    mx = win.left + minimap_offset[0]
    my = win.top  + minimap_offset[1]
    mw, mh = minimap_offset[2], minimap_offset[3]
    with mss.mss() as _sct:
        _raw = _sct.grab({"left": mx, "top": my, "width": mw, "height": mh})
    img_bgr = cv2.cvtColor(np.array(_raw), cv2.COLOR_BGRA2BGR)

    SCALE = 5
    img_big = cv2.resize(img_bgr, (mw * SCALE, mh * SCALE), interpolation=cv2.INTER_NEAREST)

    drawing = [False]
    pts = [None, None]  # [start, end]

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing[0] = True; pts[0] = (x, y); pts[1] = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and drawing[0]:
            pts[1] = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            drawing[0] = False; pts[1] = (x, y)

    wname = "미니맵 드래그: 윗텔포 범위 지정 (드래그 후 Enter / ESC 취소)"
    cv2.namedWindow(wname, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(wname, on_mouse)

    while True:
        display = img_big.copy()
        cv2.putText(display, "드래그로 범위 지정 후 Enter / ESC 취소", (5, 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        if pts[0] and pts[1]:
            x1 = min(pts[0][0], pts[1][0]); y1 = min(pts[0][1], pts[1][1])
            x2 = max(pts[0][0], pts[1][0]); y2 = max(pts[0][1], pts[1][1])
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.imshow(wname, display)
        key = cv2.waitKey(1)
        if key == 13 and pts[0] and pts[1] and not drawing[0]: break
        if key == 27: pts[0] = None; break

    cv2.destroyWindow(wname)
    if pts[0] and pts[1]:
        x1 = min(pts[0][0], pts[1][0]) // SCALE
        y1 = min(pts[0][1], pts[1][1]) // SCALE
        x2 = max(pts[0][0], pts[1][0]) // SCALE
        y2 = max(pts[0][1], pts[1][1]) // SCALE
        teleport_rect = (x1, y1, x2, y2)
        lbl_teleport.config(text=f"X:{x1}~{x2} Y:{y1}~{y2}", fg=C_POINT)

def capture_template(filename, label=None):
    win = get_game_window()
    if not win:
        messagebox.showerror("오류", "게임 창을 찾을 수 없습니다."); return
    win.restore(); win.activate(); time.sleep(0.5)
    with mss.mss() as _sct:
        _raw = _sct.grab({"left": win.left, "top": win.top, "width": win.width, "height": win.height})
    img = cv2.cvtColor(np.array(_raw), cv2.COLOR_BGRA2BGR)
    wname = f"드래그로 [{filename}] 영역 선택 후 Enter / ESC 취소"
    cv2.namedWindow(wname, cv2.WINDOW_AUTOSIZE)
    roi = cv2.selectROI(wname, img, False)
    cv2.destroyWindow(wname)
    if roi[2] > 5 and roi[3] > 5:
        cropped = img[int(roi[1]):int(roi[1]+roi[3]), int(roi[0]):int(roi[0]+roi[2])]
        if getattr(sys, 'frozen', False):
            save_dir = os.path.dirname(sys.executable)
        else:
            save_dir = os.path.abspath(".")
        save_path = os.path.join(save_dir, filename)
        cv2.imwrite(save_path, cropped)
        if label:
            label.config(text=f"✅ {filename} 등록 완료", fg=C_POINT)
        messagebox.showinfo("등록 완료", f"✅ {filename} 저장 완료!\n이제 이 이미지로 인식합니다.")
    else:
        messagebox.showwarning("취소", "드래그 실패. 다시 시도해주세요.")

def save_preset_to_file():
    from tkinter import simpledialog
    default_name = os.path.splitext(os.path.basename(current_preset_file[0]))[0] if current_preset_file[0] else "preset"
    name = simpledialog.askstring("프리셋 저장", "저장할 파일 이름을 입력하세요\n(.txt 자동 추가)", initialvalue=default_name, parent=root)
    if not name:
        return
    name = name.strip()
    if not name:
        return
    if not name.lower().endswith(".txt"):
        name += ".txt"
    path = os.path.join(get_preset_dir(), name)
    current_preset_file[0] = path
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"MINIMAP:{minimap_offset}\n")
            f.write(f"HP_BAR:{hp_bar_offset}\n")
            f.write(f"MP_BAR:{mp_bar_offset}\n")
            f.write(f"MAX_MP_RATIO:{max_detected_mp_pixel_ratio}\n")
            f.write(f"MP_POT_KEY:{ent_mp_pot_key.get().strip()}\n")
            f.write(f"MP_THRESHOLD:{int(scale_mp.get())}\n")
            f.write(f"LEFT_LIMIT:{left_limit}\n")
            f.write(f"RIGHT_LIMIT:{right_limit}\n")
            f.write(f"RETURN_X:{return_x}\n")
            f.write(f"RIGHT_LIMIT_1F:{right_limit_1f}\n")
            f.write(f"FLOOR_2_Y:{floor_2_y}\n")
            f.write(f"MAX_HP_RATIO:{max_detected_hp_pixel_ratio}\n")
            f.write(f"MAP_MODE:{map_mode.get()}\n")
            f.write(f"CUSTOM_KEY_NAME:{ent_custom_key.get().strip()}\n")
            f.write(f"CUSTOM_SEC:{ent_custom_sec.get().strip()}\n")
            f.write(f"CUSTOM_KEY_NAME_2:{ent_custom_key_2.get().strip()}\n")  
            f.write(f"CUSTOM_SEC_2:{ent_custom_sec_2.get().strip()}\n")      
            f.write(f"SKILL_KEY_1:{ent_skill_key1.get().strip()}\n")
            f.write(f"SKILL_MODE_1:{skill_mode1.get()}\n")
            f.write(f"SKILL_KEY_2:{ent_skill_key2.get().strip()}\n")
            f.write(f"SKILL_MODE_2:{skill_mode2.get()}\n")
            f.write(f"TELEPORT_RECT:{teleport_rect}\n")
            f.write(f"LOOT_SEC:{ent_loot_sec.get().strip()}\n")
            f.write(f"SELL_SEC:{ent_sell_sec.get().strip()}\n")
            f.write(f"PET_KEY:{ent_custom_key_3.get().strip()}\n")
            f.write(f"PET_SEC:{ent_custom_sec_3.get().strip()}\n")
            f.write(f"POT_KEY:{ent_pot_key.get().strip()}\n")
            f.write(f"HP_THRESHOLD:{int(scale_hp.get())}\n")
        messagebox.showinfo("저장 완료", f"⚙️ 프리셋 저장 완료!\n({os.path.basename(path)})")
    except Exception as e: messagebox.showerror("오류", f"저장 실패: {e}")

def load_preset_from_file(filepath=None):
    global minimap_offset, hp_bar_offset, mp_bar_offset, left_limit, right_limit, return_x, right_limit_1f, floor_2_y, max_detected_hp_pixel_ratio, max_detected_mp_pixel_ratio, teleport_rect
    if filepath is None:
        filepath = os.path.join(get_preset_dir(), PRESET_FILE)
    if not os.path.exists(filepath): return
    current_preset_file[0] = filepath
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f.readlines():  
                if ":" not in line: continue
                key, val = line.strip().split(":", 1)
                if val == "None" or val == "": continue
                if key == "MINIMAP": minimap_offset = eval(val)
                elif key == "HP_BAR": hp_bar_offset = eval(val)
                elif key == "LEFT_LIMIT": left_limit = int(val)
                elif key == "RIGHT_LIMIT": right_limit = int(val)
                elif key == "RETURN_X": return_x = int(val)
                elif key == "RIGHT_LIMIT_1F": right_limit_1f = int(val)
                elif key == "FLOOR_2_Y": floor_2_y = int(val)
                elif key == "MAX_HP_RATIO": max_detected_hp_pixel_ratio = float(val)
                elif key == "MAP_MODE": map_mode.set(val)
                elif key == "CUSTOM_KEY_NAME": ent_custom_key.delete(0, tk.END); ent_custom_key.insert(0, val)
                elif key == "CUSTOM_SEC": ent_custom_sec.delete(0, tk.END); ent_custom_sec.insert(0, val)
                elif key == "CUSTOM_KEY_NAME_2": ent_custom_key_2.delete(0, tk.END); ent_custom_key_2.insert(0, val)  
                elif key == "CUSTOM_SEC_2": ent_custom_sec_2.delete(0, tk.END); ent_custom_sec_2.insert(0, val)      
                elif key == "SKILL_KEY_1": ent_skill_key1.delete(0, tk.END); ent_skill_key1.insert(0, val)
                elif key == "SKILL_MODE_1": skill_mode1.set(val)
                elif key == "SKILL_KEY_2": ent_skill_key2.delete(0, tk.END); ent_skill_key2.insert(0, val)
                elif key == "SKILL_MODE_2": skill_mode2.set(val)
                elif key == "TELEPORT_RECT":
                    teleport_rect = eval(val)
                    root.after(0, lambda v=teleport_rect: lbl_teleport.config(text=f"X:{v[0]}~{v[2]} Y:{v[1]}~{v[3]}", fg=C_POINT))
                elif key == "LOOT_SEC": ent_loot_sec.delete(0, tk.END); ent_loot_sec.insert(0, val)
                elif key == "SELL_SEC": ent_sell_sec.delete(0, tk.END); ent_sell_sec.insert(0, val)
                elif key == "PET_KEY": ent_custom_key_3.delete(0, tk.END); ent_custom_key_3.insert(0, val)
                elif key == "PET_SEC": ent_custom_sec_3.delete(0, tk.END); ent_custom_sec_3.insert(0, val)
                elif key == "MP_BAR": mp_bar_offset = eval(val)
                elif key == "MAX_MP_RATIO": max_detected_mp_pixel_ratio = float(val)
                elif key == "MP_POT_KEY": ent_mp_pot_key.delete(0, tk.END); ent_mp_pot_key.insert(0, val)
                elif key == "MP_THRESHOLD":
                    try: scale_mp.set(int(val))
                    except: pass
                elif key == "POT_KEY": ent_pot_key.delete(0, tk.END); ent_pot_key.insert(0, val)
                elif key == "HP_THRESHOLD":
                    try: scale_hp.set(int(val))
                    except: pass
        
        if minimap_offset: lbl_minimap.config(text="✅ 미니맵 영역: 자동 로드 완료", fg=C_POINT)
        if hp_bar_offset: lbl_hp_status.config(text="✅ HP 영역: 자동 로드 완료", fg=C_POINT)
        if mp_bar_offset: lbl_mp_status.config(text="✅ MP 영역: 자동 로드 완료", fg=C_POINT)
        if left_limit: lbl_f5.config(text=f"X: {left_limit}", fg=C_POINT)
        if right_limit: lbl_f6.config(text=f"X: {right_limit}", fg=C_POINT)
        if return_x: lbl_f7.config(text=f"X: {return_x}", fg=C_POINT)
        if right_limit_1f: lbl_f8.config(text=f"X: {right_limit_1f}", fg=C_POINT)
        toggle_map_mode_ui()
    except Exception as e: print(f"⚠️ 프리셋 로드 에러: {e}")

# --- 💊 물약 오토 루프 ---
def check_hp_raw_ratio():
    if not hp_bar_offset: return 100.0
    win = get_game_window()
    if not win: return 100.0
    x = win.left + hp_bar_offset[0]; y = win.top + hp_bar_offset[1]
    w, h = hp_bar_offset[2], hp_bar_offset[3]
    with mss.mss() as sct:
        img = sct.grab({"left": x, "top": y, "width": w, "height": h})
    screen_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
    hsv = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 100, 100]); upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 100, 100]); upper_red2 = np.array([180, 255, 255])
    mask = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
    return (np.sum(mask > 0) / (w * h)) * 100

def get_normalized_hp_percentage():
    raw_ratio = check_hp_raw_ratio()
    if max_detected_hp_pixel_ratio <= 0: return 100.0
    return min(100.0, (raw_ratio / max_detected_hp_pixel_ratio) * 100.0)

def check_mp_raw_ratio():
    if not mp_bar_offset: return 100.0
    win = get_game_window()
    if not win: return 100.0
    x = win.left + mp_bar_offset[0]; y = win.top + mp_bar_offset[1]
    w, h = mp_bar_offset[2], mp_bar_offset[3]
    with mss.mss() as sct:
        img = sct.grab({"left": x, "top": y, "width": w, "height": h})
    screen_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
    hsv = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([100, 80, 80]); upper_blue = np.array([135, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    return (np.sum(mask > 0) / (w * h)) * 100

def get_normalized_mp_percentage():
    raw_ratio = check_mp_raw_ratio()
    if max_detected_mp_pixel_ratio <= 0: return 100.0
    return min(100.0, (raw_ratio / max_detected_mp_pixel_ratio) * 100.0)

def _pot_keydown(key_str):
    _sc_keydown(key_str)

def _pot_keyup(key_str):
    _sc_keyup(key_str)

def potion_loop():
    global POTION_KEY, HP_THRESHOLD, MP_POTION_KEY, MP_THRESHOLD
    hp_pressing = False; hp_press_start = 0
    mp_pressing = False; mp_press_start = 0
    while macro_running:
        if hp_bar_offset:
            current_hp = get_normalized_hp_percentage()
            if current_hp <= HP_THRESHOLD and not hp_pressing:
                _pot_keydown(POTION_KEY); hp_pressing = True; hp_press_start = time.time()
            elif hp_pressing:
                if current_hp >= 98.0 or (time.time() - hp_press_start >= random.uniform(1.6, 2.0)):
                    _pot_keyup(POTION_KEY); hp_pressing = False
        if mp_bar_offset and MP_POTION_KEY:
            current_mp = get_normalized_mp_percentage()
            if current_mp <= MP_THRESHOLD and not mp_pressing:
                _pot_keydown(MP_POTION_KEY); mp_pressing = True; mp_press_start = time.time()
            elif mp_pressing:
                if current_mp >= 98.0 or (time.time() - mp_press_start >= random.uniform(1.6, 2.0)):
                    _pot_keyup(MP_POTION_KEY); mp_pressing = False
        time.sleep(0.05)
    if hp_pressing: _pot_keyup(POTION_KEY)
    if mp_pressing and MP_POTION_KEY: _pot_keyup(MP_POTION_KEY)

# --- ⚔️ 매칭 및 마우스 클릭 제어 ---
def find_image_on_screen(template_path, threshold=0.35, debug_name=None):
    win = get_game_window()
    if not win: return None

    with mss.mss() as sct:
        raw = sct.grab(_get_primary_monitor(sct))
    screen_gray = cv2.cvtColor(np.array(raw), cv2.COLOR_BGRA2GRAY)

    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None: return None

    scales = [1.0, 0.5, 0.55, 0.6, 0.75, 1.25, 1.5, 0.8, 1.75, 0.67, 2.0, 1.1, 1.15, 1.35, 0.9]
    best_val = 0.0
    best_loc = None
    best_tw = template.shape[1]
    best_th = template.shape[0]

    def _save_debug(method, val, loc, tw, th, found):
        if debug_name is None: return
        try:
            debug_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(".")
            cv2.imwrite(os.path.join(debug_dir, f"debug_{debug_name}_screen.png"), screen_gray)
            cv2.imwrite(os.path.join(debug_dir, f"debug_{debug_name}_template.png"), template)
            vis = cv2.cvtColor(screen_gray, cv2.COLOR_GRAY2BGR)
            if loc:
                color = (0, 255, 0) if found else (0, 0, 255)
                cv2.rectangle(vis, (loc[0], loc[1]), (loc[0] + tw, loc[1] + th), color, 2)
                cv2.putText(vis, f"{val:.3f} [{method}]", (loc[0], max(loc[1] - 6, 12)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.imwrite(os.path.join(debug_dir, f"debug_{debug_name}_result.png"), vis)
            status = "발견" if found else "실패"
            print(f"[DEBUG:{debug_name}] {method} score={val:.4f} threshold={threshold} → {status}")
            print(f"[DEBUG] 저장 경로: {debug_dir}")
        except Exception as e:
            print(f"[DEBUG 저장 오류] {e}")

    # 1차: 픽셀 매칭 (기본, 좌표 정확)
    for scale in scales:
        tw = int(template.shape[1] * scale)
        th = int(template.shape[0] * scale)
        if tw < 5 or th < 5: continue
        if tw > screen_gray.shape[1] or th > screen_gray.shape[0]: continue
        scaled = cv2.resize(template, (tw, th), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
        res = cv2.matchTemplate(screen_gray, scaled, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val > best_val:
            best_val = max_val; best_loc = max_loc; best_tw = tw; best_th = th

    if best_val >= threshold:
        _save_debug("pixel", best_val, best_loc, best_tw, best_th, True)
        print(f"DEBUG: [pixel] 발견! {best_val:.4f} ({template_path})")
        return (best_loc[0] + best_tw // 2, best_loc[1] + best_th // 2)

    # 2차: Canny edge 매칭 fallback (DPI 차이로 픽셀 매칭 실패 시)
    px_val, px_loc, px_tw, px_th = best_val, best_loc, best_tw, best_th
    best_val = 0.0; best_loc = None; best_tw = template.shape[1]; best_th = template.shape[0]
    screen_edges = cv2.Canny(screen_gray, 30, 100)
    for scale in scales:
        tw = int(template.shape[1] * scale)
        th = int(template.shape[0] * scale)
        if tw < 5 or th < 5: continue
        if tw > screen_gray.shape[1] or th > screen_gray.shape[0]: continue
        scaled = cv2.resize(template, (tw, th), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
        tmpl_edges = cv2.Canny(scaled, 30, 100)
        res = cv2.matchTemplate(screen_edges, tmpl_edges, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val > best_val:
            best_val = max_val; best_loc = max_loc; best_tw = tw; best_th = th

    if best_val < threshold:
        if px_val >= best_val:
            _save_debug("pixel(fail)", px_val, px_loc, px_tw, px_th, False)
        else:
            _save_debug("edge(fail)", best_val, best_loc, best_tw, best_th, False)
        print(f"DEBUG: 매칭 실패! best={max(px_val, best_val):.4f} ({template_path})")
        return None
    _save_debug("edge", best_val, best_loc, best_tw, best_th, True)
    print(f"DEBUG: [edge] 발견! {best_val:.4f} ({template_path})")
    return (best_loc[0] + best_tw // 2, best_loc[1] + best_th // 2)

def click_image_helper(template_path, double=False, threshold=0.42, wait_after=0.15):
    if not macro_running and not test_running: return False
    paths = template_path if isinstance(template_path, (list, tuple)) else [template_path]
    for path in paths:
        full_path = resource_path(path)
        pos = find_image_on_screen(full_path, threshold)
        if pos:
            jx = random.randint(-2, 2)
            jy = random.randint(-2, 2)
            mx = int((pos[0] + jx) * _COORD_SCALE)
            my = int((pos[1] + jy) * _COORD_SCALE)
            time.sleep(random.uniform(0.07, 0.20))
            pydirectinput.moveTo(mx, my)
            time.sleep(random.uniform(0.06, 0.15))
            if double:
                pydirectinput.click(clicks=2, interval=random.uniform(0.07, 0.14))
            else:
                pydirectinput.click()
            time.sleep(wait_after + random.uniform(0.03, 0.10))
            return True
    return False

# 🌟 묘묘 정산 메인 엔진 (상태창 수정 완벽 제외)
# 🌟 [묘묘 인식률 극한 패치] 묘묘 찾기 및 정산 엔진
def check_and_sell_items():
    global SKILL_KEY_1, SKILL_KEY_2, state, transparent_scan_paused
    transparent_scan_paused = True
    try:
        _check_and_sell_items_inner()
    finally:
        transparent_scan_paused = False

def _check_and_sell_items_inner():
    global SKILL_KEY_1, SKILL_KEY_2, state
    
    # 1. 사냥 중이던 스킬/이동 키 해제
    _sc_keyup('left'); _sc_keyup('right')
    _sc_keyup(SKILL_KEY_1); _sc_keyup(SKILL_KEY_2)
    time.sleep(0.3) 
    
    if not macro_running and not test_running: return  
    
    _sc_press(INVENTORY_KEY)
    time.sleep(0.5) 
    
    # 2. 캐시탭 이동 및 묘묘 정산
    cash_images = ["cash_tab1.png", "cash_tab2.png", "cash_tab3.png", "cash_tab4.png"]
    if click_image_helper(cash_images, threshold=0.35, wait_after=0.4):
        if not macro_running and not test_running: return

        # 묘묘 더블클릭
        full_path = resource_path("miumiu.png")
        pos = find_image_on_screen(full_path, threshold=0.30, debug_name="miumiu" if test_running else None)
        if pos:
            time.sleep(random.uniform(0.08, 0.20))
            pydirectinput.moveTo(int((pos[0] + random.randint(-2, 2)) * _COORD_SCALE), int((pos[1] + random.randint(-2, 2)) * _COORD_SCALE))
            time.sleep(random.uniform(0.06, 0.14))
            pydirectinput.click(clicks=2, interval=random.uniform(0.08, 0.14))
            time.sleep(random.uniform(0.40, 0.65))

            # 판매 버튼 클릭
            sell_images = ["sell_btn.png", "sell_btn2.png", "sell_btn3.jpg"]
            for img in sell_images:
                pos_sell = find_image_on_screen(resource_path(img), threshold=0.35)
                if pos_sell:
                    time.sleep(random.uniform(0.08, 0.18))
                    pydirectinput.moveTo(int((pos_sell[0] + random.randint(-2, 2)) * _COORD_SCALE), int((pos_sell[1] + random.randint(-2, 2)) * _COORD_SCALE))
                    time.sleep(random.uniform(0.06, 0.13))
                    pydirectinput.click()
                    time.sleep(random.uniform(0.40, 0.65))
                    _sc_press('enter')
                    time.sleep(random.uniform(0.40, 0.65))
                    break

            pos_exit = find_image_on_screen(resource_path("exit_shop_btn.png"), threshold=0.35)
            if pos_exit:
                time.sleep(random.uniform(0.08, 0.18))
                pydirectinput.moveTo(int((pos_exit[0] + random.randint(-2, 2)) * _COORD_SCALE), int((pos_exit[1] + random.randint(-2, 2)) * _COORD_SCALE))
                time.sleep(random.uniform(0.06, 0.13))
                pydirectinput.click()
                time.sleep(random.uniform(0.40, 0.65))

            pos_x = find_image_on_screen(resource_path("x.png"), threshold=0.35)
            if pos_x:
                time.sleep(random.uniform(0.08, 0.18))
                pydirectinput.moveTo(int((pos_x[0] + random.randint(-2, 2)) * _COORD_SCALE), int((pos_x[1] + random.randint(-2, 2)) * _COORD_SCALE))
                time.sleep(random.uniform(0.06, 0.13))
                pydirectinput.click()
                time.sleep(random.uniform(0.40, 0.65))

    # 4. 마무리 및 복귀
    state = "HUNT"
    last_sell_time = time.time()


# --- 2층 끝단 d기동 후 도보 낙하 수거 엔진 ---
def perform_loot_cycle():
    global last_buff_time, SKILL_KEY_1, SKILL_KEY_2
    _sc_keyup('left'); _sc_keyup('right'); _sc_keyup('up'); _sc_keyup('down'); time.sleep(0.05)
    
    # [1] 텔포로 우측 한계선 근처까지 빠르게 이동
    _sc_keydown('right')
    stuck_counter, last_x = 0, -1
    while macro_running or test_running:
        if not macro_running and not test_running: break
        pos = get_pos()
        if not pos: time.sleep(0.01); continue
        cx = pos[0]

        if (right_limit is not None and cx >= (right_limit - 4)) or stuck_counter > 8:
            break
        if cx == last_x: stuck_counter += 1
        else: stuck_counter = 0; last_x = cx

        _sc_press(SKILL_KEY_2)
        time.sleep(random.uniform(0.12, 0.16))

    # [2] 텔포 멈추고 방향키로 걸어서 낙하 포인트까지 이동
    _sc_keyup(SKILL_KEY_1); _sc_keyup(SKILL_KEY_2)
    _sc_keydown('right')
    time.sleep(0.8)  # 걸어서 끝까지

    # [3] 낙하 대기
    fall_start = time.time()
    while macro_running or test_running:
        if not macro_running and not test_running: break
        if time.time() - fall_start > 1.8:
            break
        pos = get_pos()
        if pos and floor_2_y is not None:
            cy = pos[1]
            if cy >= (floor_2_y + 8):
                break
        time.sleep(0.05)

    _sc_keyup('right'); time.sleep(0.1)

    # 1층 낙하 확인 후 바로 왼쪽으로
    # 🎯 [정밀 저격 필터 수리] 좌측 한계선 지정구역 실시간 감속 추적
    _sc_keydown('left')
    stuck_counter, last_x = 0, -1
    while macro_running or test_running:
        if not macro_running and not test_running: break  
        pos = get_pos()
        if not pos: time.sleep(0.01); continue
        cx = pos[0]
        
        # 📌 사장님이 마우스로 지정해 놓은 '딱 그 지점 범위(마진 4픽셀 내외)'로 들어오면 수거 조기 종결 후 윗텔 도킹!
        if return_x is not None and cx <= (return_x + 4):
            _sc_keyup('left')
            break                       
            
        if cx == last_x: stuck_counter += 1
        else: stuck_counter = 0; last_x = cx
        
        _sc_keydown(SKILL_KEY_2)
        time.sleep(0.04)
        _sc_keyup(SKILL_KEY_2)
        time.sleep(random.uniform(0.25, 0.35)) 
        
        _sc_keydown(SKILL_KEY_1)
        time.sleep(0.04)
        _sc_keyup(SKILL_KEY_1)
        time.sleep(random.uniform(0.20, 0.30))
        
    _sc_keyup('left'); time.sleep(0.1)
    
    if macro_running or test_running:
        execute_upper_teleport() 
    
    if (macro_running or test_running) and (time.time() - last_buff_time >= BUFF_CYCLE_TIME):
        _sc_keyup('left'); _sc_keyup('right'); time.sleep(0.2)
        for _ in range(3): 
            if not macro_running and not test_running: break
            _sc_press('f'); time.sleep(random.uniform(0.55, 0.68))
        last_buff_time = time.time()
    return time.time()

def emergency_return_to_2f():
    global SKILL_KEY_1, SKILL_KEY_2
    if map_mode.get() in ["SINGLE", "STATIONARY"]: return  
    _sc_keyup('left'); _sc_keyup('right'); _sc_keyup(SKILL_KEY_1); _sc_keyup(SKILL_KEY_2); time.sleep(0.05)
    
    while macro_running or test_running:
        if not macro_running and not test_running: break 
        pos = get_pos()
        if not pos: time.sleep(0.01); continue
        cx = pos[0]
        if abs(cx - return_x) <= 12: break
        if cx < return_x:
            _sc_keyup('left'); _sc_keydown('right')
            _sc_press(SKILL_KEY_2); time.sleep(random.uniform(0.08, 0.12))
            _sc_press(SKILL_KEY_1); time.sleep(random.uniform(0.10, 0.15))
        else:
            _sc_keyup('right'); _sc_keydown('left')
            _sc_press(SKILL_KEY_2); time.sleep(random.uniform(0.08, 0.12))
            _sc_press(SKILL_KEY_1); time.sleep(random.uniform(0.10, 0.15))
    _sc_keyup('left'); _sc_keyup('right')
    if macro_running or test_running:
        execute_upper_teleport()

# 🌟 [요구사항 적극 반영] 사장님이 좌측에 찍어둔 '딱 그 장소'를 이탈하면 최대한 맞추고 윗텔 연사 때리는 순정 개조형
def execute_upper_teleport():
    global SKILL_KEY_2, SKILL_KEY_1, state
    if not macro_running and not test_running: return
    state = "UPPER"

    _sc_keyup('left'); _sc_keyup('right'); _sc_keyup('down')
    time.sleep(0.05)

    # 네모칸 범위 설정 (없으면 return_x 기준 ±5 폴백)
    if teleport_rect is not None:
        rx1, ry1, rx2, ry2 = teleport_rect
    elif return_x is not None:
        rx1, rx2 = return_x - 5, return_x + 5
        ry1, ry2 = None, None
    else:
        return

    rcx = (rx1 + rx2) // 2  # 네모칸 중심 X
    NEAR_ZONE = 15           # 이 범위 안을 한번이라도 지나치면 걷기 모드 고정
    walk_mode = False        # 한번 걷기 모드 진입하면 텔포 안 씀

    while macro_running or test_running:
        if not macro_running and not test_running: return
        pos = get_pos()
        if not pos: break
        cx, cy = pos
        diff = cx - rcx

        # ── [발동] 네모칸 안에 들어오면 즉시 윗텔포 ──
        if rx1 <= cx <= rx2:
            _sc_keyup('left'); _sc_keyup('right')
            _sc_keyup(SKILL_KEY_1); _sc_keyup(SKILL_KEY_2)
            time.sleep(0.05)
            _sc_keydown('up')
            _sc_keydown(SKILL_KEY_1)
            _sc_keydown(SKILL_KEY_2)
            time.sleep(1.0)
            _sc_keyup(SKILL_KEY_2)
            _sc_keyup(SKILL_KEY_1)
            _sc_keyup('up')
            time.sleep(0.15)
            pos2 = get_pos()
            if pos2 and floor_2_y is not None and pos2[1] <= (floor_2_y + 8):
                break
            # 2층 도달 실패 → walk_mode 유지, 걸어서 박스로 복귀
            walk_mode = True
            continue

        # 박스 근처 한 번이라도 지나치면 걷기 모드 고정
        if abs(diff) <= NEAR_ZONE:
            walk_mode = True

        # ── 걷기 모드: 방향키 꾹 + 10ms마다 박스 진입 감지 즉시 정지 ──
        if walk_mode:
            _sc_keyup(SKILL_KEY_1)
            _sc_keyup(SKILL_KEY_2)
            direction = 'right' if diff < 0 else 'left'
            opposite  = 'left'  if diff < 0 else 'right'
            _sc_keyup(opposite)
            _sc_keydown(direction)
            # 박스 진입할 때까지 10ms마다 위치 확인
            for _ in range(30):  # 최대 300ms
                time.sleep(0.01)
                chk = get_pos()
                if chk and rx1 <= chk[0] <= rx2:
                    _sc_keyup(direction)
                    break
            else:
                _sc_keyup(direction)

        # ── 텔포 모드: 아직 멀리 있음 → 텔포로 접근 ──
        else:
            _sc_keyup('left'); _sc_keyup('right')
            direction = 'right' if diff < 0 else 'left'
            _sc_keydown(direction)
            _sc_keydown(SKILL_KEY_1)
            _sc_keydown(SKILL_KEY_2)
            elapsed = 0.0
            while elapsed < 1.8:
                time.sleep(0.02); elapsed += 0.02
                chk = get_pos()
                if chk and abs(chk[0] - rcx) <= NEAR_ZONE:
                    walk_mode = True; break  # 근처 감지 → 걷기 모드로 전환
            _sc_keyup(SKILL_KEY_2)
            _sc_keyup(SKILL_KEY_1)
            _sc_keyup(direction)
            time.sleep(0.08)

    _sc_keyup('left'); _sc_keyup('right')
    _sc_keyup(SKILL_KEY_2); _sc_keyup('up')
    state = "HUNT"
    time.sleep(0.1)

def get_pos():
    if not minimap_offset: return None
    win = get_game_window()
    if not win: return None
    x = win.left + minimap_offset[0]; y = win.top + minimap_offset[1]
    w, h = minimap_offset[2], minimap_offset[3]
    try:
        with mss.mss() as sct:
            img = sct.grab({"left": x, "top": y, "width": w, "height": h})
        screen_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2HSV)
        lower_yellow = np.array([22, 160, 160]); upper_yellow = np.array([38, 255, 255])
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        char_x, char_y = None, None
        if cnts:
            m = cv2.moments(max(cnts, key=cv2.contourArea))
            if m["m00"] != 0: char_x = int(m["m10"] / m["m00"]); char_y = int(m["m01"] / m["m00"])
        return (char_x, char_y) if char_x is not None else None
    except: return None

def macro_loop():
    global state, last_loot_time, last_sell_time, current_direction, macro_running
    global last_custom_key_time, next_custom_delay, CUSTOM_KEY, CUSTOM_INTERVAL
    global last_custom_key_time_2, next_custom_delay_2, CUSTOM_KEY_2, CUSTOM_INTERVAL_2
    global last_custom_key_time_3, next_custom_delay_3, CUSTOM_KEY_3, CUSTOM_INTERVAL_3
    global SKILL_KEY_1, SKILL_MODE_1, SKILL_KEY_2, SKILL_MODE_2
    global center_x, skill_count
    global next_sell_delay, next_loot_delay, last_idle_time, next_idle_delay
    
    floor_1_y = floor_2_y
    last_dir = None

    # 매크로 시작 시점에 유저 설정값 기준으로 주기 재초기화
    next_sell_delay = random.uniform(SELL_CYCLE_TIME * 0.83, SELL_CYCLE_TIME * 1.18)
    next_loot_delay = random.uniform(LOOT_CYCLE_TIME * 0.83, LOOT_CYCLE_TIME * 1.18)
    last_idle_time = time.time()
    next_idle_delay = random.uniform(480, 900)

    if map_mode.get() == "STATIONARY":
        init_pos = get_pos()
        center_x = init_pos[0] if init_pos else None
        skill_count = 0

    while macro_running:
        if macro_paused:
            time.sleep(0.1)
            continue
        # 커스텀 키 1
        if time.time() - last_custom_key_time >= next_custom_delay:
            _sc_keyup('left'); _sc_keyup('right')
            _sc_keyup(SKILL_KEY_1); _sc_keyup(SKILL_KEY_2)
            time.sleep(0.15)
            if not macro_running: break
            send_hardware_key(CUSTOM_KEY)
            time.sleep(0.35)
            last_custom_key_time = time.time()
            random_offset = random.uniform(-CUSTOM_INTERVAL * 0.18, CUSTOM_INTERVAL * 0.18)
            next_custom_delay = max(1.0, CUSTOM_INTERVAL + random_offset)
            last_dir = None; continue
            
        # 커스텀 키 2
        if time.time() - last_custom_key_time_2 >= next_custom_delay_2:
            _sc_keyup('left'); _sc_keyup('right')
            _sc_keyup(SKILL_KEY_1); _sc_keyup(SKILL_KEY_2)
            time.sleep(0.15)
            if not macro_running: break
            send_hardware_key(CUSTOM_KEY_2)
            time.sleep(0.35)
            last_custom_key_time_2 = time.time()
            random_offset_2 = random.uniform(-CUSTOM_INTERVAL_2 * 0.18, CUSTOM_INTERVAL_2 * 0.18)
            next_custom_delay_2 = max(1.0, CUSTOM_INTERVAL_2 + random_offset_2)
            last_dir = None; continue

        # 펫먹이
        if CUSTOM_KEY_3 and time.time() - last_custom_key_time_3 >= next_custom_delay_3:
            _sc_keyup('left'); _sc_keyup('right')
            _sc_keyup(SKILL_KEY_1); _sc_keyup(SKILL_KEY_2)
            time.sleep(0.15)
            if not macro_running: break
            send_hardware_key(CUSTOM_KEY_3)
            time.sleep(0.35)
            last_custom_key_time_3 = time.time()
            random_offset_3 = random.uniform(-CUSTOM_INTERVAL_3 * 0.18, CUSTOM_INTERVAL_3 * 0.18)
            next_custom_delay_3 = max(1.0, CUSTOM_INTERVAL_3 + random_offset_3)
            last_dir = None; continue
            
        # 랜덤 휴식 (8~15분마다 3~10초 멈춤)
        if state == "HUNT" and (time.time() - last_idle_time >= next_idle_delay):
            _sc_keyup('left'); _sc_keyup('right')
            _sc_keyup(SKILL_KEY_1); _sc_keyup(SKILL_KEY_2)
            time.sleep(random.uniform(3.0, 10.0))
            last_idle_time = time.time()
            next_idle_delay = random.uniform(480, 900)
            last_dir = None; continue

        # 정산
        if state == "HUNT" and (time.time() - last_sell_time >= next_sell_delay):
            check_and_sell_items()
            last_sell_time = time.time()
            next_sell_delay = random.uniform(SELL_CYCLE_TIME * 0.83, SELL_CYCLE_TIME * 1.18)
            last_dir = None
            if map_mode.get() == "STATIONARY" and center_x:
                pos = get_pos()
                if pos: center_x = pos[0]
            continue

        # 제자리
        if state == "HUNT" and map_mode.get() == "STATIONARY":
            if skill_count >= 30:
                _sc_keyup(SKILL_KEY_1); time.sleep(random.uniform(0.9, 1.5))
                if not macro_running: break
                if current_direction == 'right':
                    _sc_keydown('right'); time.sleep(random.uniform(0.02, 0.06)); _sc_keyup('right')
                    current_direction = 'left'
                else:
                    _sc_keydown('left'); time.sleep(random.uniform(0.02, 0.06)); _sc_keyup('left')
                    current_direction = 'right'
                time.sleep(random.uniform(0.30, 0.60)); skill_count = 0; continue
            if not macro_running: break
            _sc_press(SKILL_KEY_1); skill_count += 1
            time.sleep(random.uniform(0.70, 1.05)); continue

        # 사냥
        elif state == "HUNT":
            if map_mode.get() == "DOUBLE" and (time.time() - last_loot_time >= next_loot_delay):
                _sc_keyup('left'); _sc_keyup('right')
                _sc_keyup(SKILL_KEY_1); _sc_keyup(SKILL_KEY_2)
                state = "LOOT"; last_dir = None; continue
                
            pos = get_pos()
            if pos:
                cx, cy = pos[0], pos[1]
                
                # 🎯 [2층 복귀 패치] SINGLE 모드여도 floor_2_y를 찍어두면 강제 낙하
                if map_mode.get() == "SINGLE" and floor_2_y is not None:
                    if cy < (floor_2_y - 10): 
                        _sc_keyup('left'); _sc_keyup('right')
                        _sc_keydown('down')
                        time.sleep(0.05)
                        _sc_press('c')
                        time.sleep(0.3)
                        _sc_keyup('down')
                        last_dir = None; continue

                # 지형 필터 로직
                if floor_2_y is not None:
                    y_diff = abs(cy - floor_2_y)
                    if map_mode.get() == "SINGLE" and y_diff > 15:
                        winsound.Beep(1500, 400); time.sleep(0.1); continue
                    elif map_mode.get() == "DOUBLE" and cy < (floor_2_y - 15):
                        winsound.Beep(1500, 400); time.sleep(0.1); continue
                
                if map_mode.get() == "SINGLE" and floor_1_y is not None:
                    if cy < floor_1_y - 5: 
                        _sc_keyup('left'); _sc_keyup('right'); _sc_keyup(SKILL_KEY_1); _sc_keyup(SKILL_KEY_2); time.sleep(random.uniform(0.04, 0.08))
                        if not macro_running: break
                        _sc_keydown('down'); time.sleep(random.uniform(0.04, 0.07)); _sc_press('c'); time.sleep(random.uniform(0.08, 0.13)); _sc_press('c'); time.sleep(random.uniform(0.04, 0.07)); _sc_keyup('down'); time.sleep(random.uniform(0.28, 0.35)) 
                        last_dir = None; continue
                
                if map_mode.get() == "DOUBLE" and floor_1_y is not None and cy > floor_1_y + 5: 
                    emergency_return_to_2f(); last_dir = None; continue 
                
                active_left = left_limit if map_mode.get() == "DOUBLE" else return_x
                active_right = right_limit if map_mode.get() == "DOUBLE" else right_limit_1f

                if current_direction == 'right' and active_right is not None and cx >= (active_right - random.randint(2, 7)): current_direction = 'left'; continue
                elif current_direction == 'left' and active_left is not None and cx <= (active_left + random.randint(2, 7)): current_direction = 'right'; continue
                    
                if current_direction != last_dir:
                    _sc_keyup('left'); _sc_keyup('right'); _sc_keyup(SKILL_KEY_1); _sc_keyup(SKILL_KEY_2); time.sleep(random.uniform(0.05, 0.14))
                    if not macro_running: break
                    _sc_keydown(current_direction)
                    if SKILL_MODE_1 == "HOLD": _sc_keydown(SKILL_KEY_1)
                    if SKILL_MODE_2 == "HOLD": _sc_keydown(SKILL_KEY_2)
                    last_dir = current_direction

                if not macro_running: break
                _sc_keydown(current_direction)
                if SKILL_MODE_1 == "HOLD": _sc_keydown(SKILL_KEY_1)
                if SKILL_MODE_2 == "HOLD": _sc_keydown(SKILL_KEY_2)

                if SKILL_MODE_1 == "TAP": _sc_press(SKILL_KEY_1); time.sleep(random.uniform(0.05, 0.20))
                if SKILL_MODE_2 == "TAP": _sc_press(SKILL_KEY_2); time.sleep(random.uniform(0.05, 0.20))
            else:
                winsound.Beep(2000, 300); _sc_keydown(current_direction)
                
        elif state == "LOOT" and map_mode.get() == "DOUBLE":
            last_loot_time = perform_loot_cycle()
            next_loot_delay = random.uniform(LOOT_CYCLE_TIME * 0.83, LOOT_CYCLE_TIME * 1.18)
            current_direction = 'left'; state = "HUNT"; last_dir = None
            
        time.sleep(random.uniform(0.02, 0.12))

    _sc_keyup('left'); _sc_keyup('right')
    _sc_keyup(SKILL_KEY_1); _sc_keyup(SKILL_KEY_2)

def test_loot_cycle():
    if map_mode.get() in ["SINGLE", "STATIONARY"]:
        messagebox.showinfo("안내", "현재 모드에서는 수거를 지원하지 않습니다.")
        return
    global test_running
    if macro_running or test_running: return
    win = get_game_window()
    if win: win.restore(); win.activate()
    def run():
        global test_running; test_running = True
        time.sleep(0.2)
        perform_loot_cycle(); test_running = False
    threading.Thread(target=run, daemon=True).start()

def test_sell_items():
    global test_running
    if macro_running or test_running: return
    win = get_game_window()
    if win: win.restore(); win.activate()
    def run():
        global test_running; test_running = True
        time.sleep(0.2)
        check_and_sell_items(); test_running = False
    threading.Thread(target=run, daemon=True).start()

def record_keyboard_key(event, entry_widget):
    key_name = event.keysym.lower()
    if key_name in ["backspace", "escape"]:
        entry_widget.delete(0, tk.END); return "break"
    if key_name in ["shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r", "meta_l", "meta_r"]:
        return "break"
        
    mapping = {'prior': 'page up', 'next': 'page down', 'insert': 'insert', 'delete': 'delete', 'home': 'home', 'end': 'end'}
    final_key = mapping.get(key_name, key_name)
    entry_widget.delete(0, tk.END); entry_widget.insert(0, final_key)
    return "break"

def toggle_map_mode_ui():
    try:
        if map_mode.get() == "SINGLE":
            lbl_loot_timer.config(text="🪙 수거 주기: 일자맵 제외")
            # btn_f5를 이제 normal로 바꿔서 클릭 가능하게 오픈!
            btn_f5.config(state="normal", bg=C_ENTRY_BG, fg=C_TEXT_MUTED)
            btn_f6.config(state="disabled", bg="#222222", fg="#555555")
            btn_f7.config(state="normal", bg=C_ENTRY_BG, fg=C_TEXT_MUTED)
            btn_f8.config(state="normal", bg=C_ENTRY_BG, fg=C_TEXT_MUTED)
        elif map_mode.get() == "STATIONARY":
            lbl_loot_timer.config(text="🪙 수거 주기: 제자리 제외")
            btn_f5.config(state="disabled", bg="#222222", fg="#555555")
            btn_f6.config(state="disabled", bg="#222222", fg="#555555")
            btn_f7.config(state="disabled", bg="#222222", fg="#555555")
            btn_f8.config(state="disabled", bg="#222222", fg="#555555")
        else:
            lbl_loot_timer.config(text=f"🪙 다음 메소 수거까지: {LOOT_CYCLE_TIME}초 남음")
            btn_f5.config(state="normal", bg=C_ENTRY_BG, fg=C_TEXT_MUTED)
            btn_f6.config(state="normal", bg=C_ENTRY_BG, fg=C_TEXT_MUTED)
            btn_f7.config(state="normal", bg=C_ENTRY_BG, fg=C_TEXT_MUTED)
            btn_f8.config(state="normal", bg=C_ENTRY_BG, fg=C_TEXT_MUTED)
    except NameError: pass

def update_gui_dashboard():
    global POTION_KEY, HP_THRESHOLD, MP_POTION_KEY, MP_THRESHOLD, CUSTOM_KEY, CUSTOM_INTERVAL, CUSTOM_KEY_2, CUSTOM_INTERVAL_2, SKILL_KEY_1, SKILL_MODE_1, SKILL_KEY_2, SKILL_MODE_2
    global LOOT_CYCLE_TIME, SELL_CYCLE_TIME, CUSTOM_KEY_3, CUSTOM_INTERVAL_3
    try:
        if macro_running:
            elapsed = int(time.time() - start_time)
            m, s = divmod(elapsed, 60); h, m = divmod(m, 60)
            lbl_runtime.config(text=f"⏱️ 총 가동 시간: {h:02d}시간 {m:02d}분 {s:02d}초")
            if map_mode.get() == "DOUBLE":
                loot_left = max(0, int(LOOT_CYCLE_TIME - (time.time() - last_loot_time)))
                lbl_loot_timer.config(text=f"🪙 다음 메소 수거까지: {loot_left}초 남음")
            sell_left = max(0, int(SELL_CYCLE_TIME - (time.time() - last_sell_time)))
            sm, ss = divmod(sell_left, 60)
            lbl_sell_timer.config(text=f"🎒 묘묘 장비 정산까지: {sm}분 {ss}초 남음")

            custom_left = max(0, int(next_custom_delay - (time.time() - last_custom_key_time)))
            lbl_custom_timer.config(text=f"⏱️ [SKILL 1] ({CUSTOM_KEY.upper()}) 실행까지: {custom_left}초")

            custom_left_2 = max(0, int(next_custom_delay_2 - (time.time() - last_custom_key_time_2)))
            lbl_custom_timer_2.config(text=f"⏱️ [SKILL 2] ({CUSTOM_KEY_2.upper()}) 실행까지: {custom_left_2}초")

            if CUSTOM_KEY_3:
                custom_left_3 = max(0, int(next_custom_delay_3 - (time.time() - last_custom_key_time_3)))
                lbl_custom_timer_3.config(text=f"⏱️ [펫먹이] ({CUSTOM_KEY_3.upper()}) 실행까지: {custom_left_3}초")
            else:
                lbl_custom_timer_3.config(text="⏱️ [펫먹이] 미설정")

            if hp_bar_offset:
                hp_val = get_normalized_hp_percentage()
                lbl_live_hp.config(text=f"❤️ 실시간 체력 감지: {hp_val:.1f}%")
            if mp_bar_offset:
                mp_val = get_normalized_mp_percentage()
                lbl_live_mp.config(text=f"💙 실시간 마나 감지: {mp_val:.1f}%")

            # 상태창
            if macro_paused:
                lbl_status.config(text="⏸ 일시정지", fg="#ffcc00")
            else:
                state_map = {
                    "HUNT": {"DOUBLE": "⚔️ 2층 사냥 중", "SINGLE": "⚔️ 1층 사냥 중", "STATIONARY": "⚔️ 제자리 사냥 중"}.get(map_mode.get(), "⚔️ 사냥 중"),
                    "LOOT": "📦 메소 회수 중",
                    "UPPER": "🔼 2층 복귀 중...",
                }
                lbl_status.config(text=state_map.get(state, "⚔️ 사냥 중"), fg=C_POINT)
        else:
            lbl_status.config(text="⚫ 대기 중", fg=C_TEXT_MUTED)

        POTION_KEY = ent_pot_key.get().strip().lower() if ent_pot_key.get() else 'insert'
        MP_POTION_KEY = ent_mp_pot_key.get().strip().lower() if ent_mp_pot_key.get().strip() else ''
        MP_THRESHOLD = int(scale_mp.get())
        CUSTOM_KEY = ent_custom_key.get().strip().lower() if ent_custom_key.get() else 'delete'
        CUSTOM_KEY_2 = ent_custom_key_2.get().strip().lower() if ent_custom_key_2.get() else 'page down'
        CUSTOM_KEY_3 = ent_custom_key_3.get().strip().lower() if ent_custom_key_3.get().strip() else ''
        SKILL_KEY_1 = ent_skill_key1.get().strip().lower() if ent_skill_key1.get() else 's'
        SKILL_KEY_2 = ent_skill_key2.get().strip().lower() if ent_skill_key2.get() else 'd'
        SKILL_MODE_1 = skill_mode1.get(); SKILL_MODE_2 = skill_mode2.get()

        try:
            CUSTOM_INTERVAL_3 = int(ent_custom_sec_3.get().strip())
            if CUSTOM_INTERVAL_3 <= 0: CUSTOM_INTERVAL_3 = 1
        except ValueError: CUSTOM_INTERVAL_3 = 180

        try:
            CUSTOM_INTERVAL = int(ent_custom_sec.get().strip())
            if CUSTOM_INTERVAL <= 0: CUSTOM_INTERVAL = 1
        except ValueError: CUSTOM_INTERVAL = 60

        try:
            CUSTOM_INTERVAL_2 = int(ent_custom_sec_2.get().strip())
            if CUSTOM_INTERVAL_2 <= 0: CUSTOM_INTERVAL_2 = 1
        except ValueError: CUSTOM_INTERVAL_2 = 120

        HP_THRESHOLD = int(scale_hp.get())

        try:
            val = int(ent_loot_sec.get().strip())
            if val > 0: LOOT_CYCLE_TIME = val
        except: pass
        try:
            val = int(ent_sell_sec.get().strip())
            if val > 0: SELL_CYCLE_TIME = val
        except: pass
    except Exception as e:
        print(f"[대시보드 오류] {e}")
    finally:
        root.after(500, update_gui_dashboard)

def start_macro_logic():
    global macro_running, last_loot_time, last_sell_time, last_buff_time, start_time, last_custom_key_time, next_custom_delay, last_custom_key_time_2, next_custom_delay_2, last_custom_key_time_3, next_custom_delay_3, max_detected_hp_pixel_ratio, transparent_detect_count
    transparent_detect_count = 0

    if map_mode.get() == "DOUBLE":
        if left_limit is None or right_limit is None or return_x is None or right_limit_1f is None:
            messagebox.showwarning("설정 미비", "⚠️ 복층모드는 지형 설정이 필수입니다."); stop_macro(); return
    elif map_mode.get() == "SINGLE":
        if return_x is None or right_limit_1f is None:
            messagebox.showwarning("설정 미비", "⚠️ 일자맵 모드는 1층 좌/우 한계선 설정이 필수입니다."); stop_macro(); return

    start_time = time.time(); last_loot_time = time.time(); last_sell_time = time.time(); last_buff_time = time.time(); last_custom_key_time = time.time(); last_custom_key_time_2 = time.time(); last_custom_key_time_3 = time.time()
    try:
        val = int(ent_custom_sec.get().strip())
        next_custom_delay = val if val > 0 else 60
    except: next_custom_delay = 60
        
    try:
        val_2 = int(ent_custom_sec_2.get().strip())
        next_custom_delay_2 = val_2 if val_2 > 0 else 120
    except: next_custom_delay_2 = 120

    try:
        val_3 = int(ent_custom_sec_3.get().strip())
        next_custom_delay_3 = val_3 if val_3 > 0 else 180
    except: next_custom_delay_3 = 180

    raw_ratio = check_hp_raw_ratio()
    if raw_ratio > 5.0: max_detected_hp_pixel_ratio = raw_ratio
    mp_raw_ratio = check_mp_raw_ratio()
    if mp_raw_ratio > 5.0: max_detected_mp_pixel_ratio = mp_raw_ratio

    load_transparent_template()
    threading.Thread(target=macro_loop, daemon=True).start()
    threading.Thread(target=potion_loop, daemon=True).start()
    threading.Thread(target=alert_loop, daemon=True).start()
    threading.Thread(target=map_guard_loop, daemon=True).start()

def toggle_pause():
    global macro_paused
    if not macro_running:
        return
    macro_paused = not macro_paused
    if macro_paused:
        _sc_keyup('left'); _sc_keyup('right')
        _sc_keyup(SKILL_KEY_1); _sc_keyup(SKILL_KEY_2)
        try: btn_pause.config(text="▶ 재개 (F4)", bg="#1a3a0a", fg=C_POINT)
        except: pass
    else:
        try: btn_pause.config(text="⏸ 일시정지 (F4)", bg="#2a2a0a", fg="#ffcc00")
        except: pass

def start_macro():
    global macro_running, macro_paused
    if not macro_running:
        root.focus_set(); macro_running = True; macro_paused = False
        btn_start.config(state="disabled"); btn_stop.config(state="normal")
        try: btn_pause.config(state="normal", text="⏸ 일시정지 (F4)", bg="#2a2a0a", fg="#ffcc00")
        except: pass
        threading.Thread(target=start_macro_logic, daemon=True).start()

def stop_macro():
    global macro_running, test_running, macro_paused
    macro_running = False; test_running = False; macro_paused = False

    def release_keys_async():
        try:
            _sc_keyup('left'); _sc_keyup('right'); _sc_keyup('up'); _sc_keyup('down'); _sc_keyup('c')
            try:
                k1 = ent_skill_key1.get().strip().lower()
                if k1: _sc_keyup(k1)
            except: pass
            try:
                k2 = ent_skill_key2.get().strip().lower()
                if k2: _sc_keyup(k2)
            except: pass
        except: pass
    threading.Thread(target=release_keys_async, daemon=True).start()
    try: btn_start.config(state="normal"); btn_stop.config(state="disabled")
    except: pass
    try: btn_pause.config(state="disabled", text="⏸ 일시정지 (F4)", bg="#2a2a0a", fg="#ffcc00")
    except: pass

def show_preset_selector():
    presets = get_all_presets()
    if not presets:
        messagebox.showinfo("알림", "프리셋 파일이 없습니다."); return
    if len(presets) == 1:
        load_preset_from_file(presets[0])
        messagebox.showinfo("로드 완료", f"프리셋 로드: {os.path.basename(presets[0])}"); return

    sel = tk.Toplevel(root)
    sel.title("프리셋 선택")
    sel.geometry("300x220")
    sel.resizable(False, False)
    sel.configure(bg=C_BG_MAIN)
    sel.grab_set(); sel.focus_set()

    tk.Label(sel, text="불러올 프리셋을 선택하세요",
             font=("맑은 고딕", 10, "bold"), fg=C_POINT, bg=C_BG_MAIN).pack(pady=12)

    lb = tk.Listbox(sel, font=("맑은 고딕", 10), bg=C_ENTRY_BG, fg=C_TEXT_MAIN,
                    selectbackground=C_POINT, selectforeground="#000000",
                    bd=0, height=6, activestyle="none")
    for f in presets:
        lb.insert(tk.END, os.path.basename(f))
    lb.pack(padx=20, fill="x")
    lb.select_set(0)

    def _load():
        idx = lb.curselection()
        if not idx: return
        load_preset_from_file(presets[idx[0]])
        sel.destroy()

    lb.bind("<Double-1>", lambda e: _load())
    tk.Button(sel, text="선택", font=("맑은 고딕", 10, "bold"),
              bg=C_BG_CARD, fg=C_POINT, bd=0, width=12, command=_load).pack(pady=12)

def _auto_load_preset():
    presets = get_all_presets()
    if len(presets) > 1:
        show_preset_selector()
    else:
        load_preset_from_file()

def snap_game_window():
    win = get_game_window()
    if not win:
        return
    try:
        win.restore()
        time.sleep(0.1)
        hwnd = win._hWnd
        # 클라이언트 영역이 정확히 1280x720이 되도록 프레임 크기 보정
        wr = win32gui.GetWindowRect(hwnd)
        cr = win32gui.GetClientRect(hwnd)
        border_w = (wr[2] - wr[0]) - cr[2]
        border_h = (wr[3] - wr[1]) - cr[3]
        win32gui.SetWindowPos(hwnd, None, 0, 0,
                              1280 + border_w, 720 + border_h,
                              win32con.SWP_NOZORDER)
    except Exception as e:
        print(f"[창 스냅] {e}")

def _on_insert_key(e):
    # 매크로 실행 중에는 Insert가 물약 키로 쓰이므로 창 정렬 스킵
    if not macro_running:
        threading.Thread(target=snap_game_window, daemon=True).start()

def setup_keyboard_hook():
    keyboard.on_press_key('f2', lambda e: root.after(0, start_macro), suppress=True)
    keyboard.on_press_key('f3', lambda e: root.after(0, stop_macro), suppress=True)
    keyboard.on_press_key('f4', lambda e: root.after(0, toggle_pause), suppress=True)
    keyboard.on_press_key('insert', _on_insert_key, suppress=False)

def get_windows_username(): return os.environ.get('USERNAME', '').strip().lower()

def check_license_and_login():
    user_key = ent_login_key.get().strip()
    my_pc_name = get_windows_username().replace(" ", "").lower()
    
    if user_key == "":
        messagebox.showerror("인증 오류", "🔒 라이선스 키가 입력되지 않았습니다.")
        return
        
    response_text = ""
    for attempt in range(3):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            cache_buster = f"cb={int(time.time())}{random.randint(100, 999)}"
            separator = "&" if "?" in GOOGLE_SHEET_CSV_URL else "?"
            nocache_url = f"{GOOGLE_SHEET_CSV_URL}{separator}{cache_buster}"
            
            response = requests.get(nocache_url, headers=headers, timeout=10)
            if response.status_code == 200 and response.text.strip():
                response.encoding = 'utf-8'
                response_text = response.text
                break
        except:
            pass
        time.sleep(0.3)
        
    if not response_text:
        messagebox.showerror("서버 트래픽 과부하", "🔒 구글 보안 서버가 일시적으로 요청을 거부했습니다.\n\n3초만 기다렸다가 다시 [가동] 버튼을 눌러주세요.")
        return
        
    raw_text = response_text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    login_success = False
    
    for line in lines:
        parts = [p.strip() for p in line.split(",")] if "," in line else [p.strip() for p in line.split("\t")]
        
        if len(parts) >= 2:
            sheet_key = parts[0]       
            sheet_status = parts[1]    
            
            sheet_pc_name = ""
            if len(parts) >= 3 and parts[2] != "":
                sheet_pc_name = parts[2].replace(" ", "").lower()
            
            if sheet_key == user_key:
                if sheet_status in ["차단", "만료"]:
                    messagebox.showerror("라이선스 제한", "❌ 인증 제한 계정입니다.")
                    return
                
                if sheet_status == "관리자":
                    login_success = True
                    break
                elif sheet_status == "무인증":
                    login_success = True
                    break
                elif sheet_status == "정상":
                    if sheet_pc_name == "":
                        messagebox.showinfo(
                            "기기 등록 필요", 
                            f"👋 처음 접속하신 기기입니다. 관리자 승인이 필요합니다.\n\n"
                            f"📌 아래의 [PC 인증 번호]를 복사해서 사장님께 보내주세요.\n"
                            f"----------------------------------------\n"
                            f"▶️ PC 인증 번호 : {my_pc_name}\n"
                            f"----------------------------------------\n"
                            f"⚠️ 확인을 누르면 인증 번호가 클립보드에 자동 복사됩니다."
                        )
                        login_window.clipboard_clear()
                        login_window.clipboard_append(my_pc_name)
                        return
                    elif sheet_pc_name == my_pc_name:
                        login_success = True
                        break
                    else:
                        messagebox.showerror(
                            "기기 잠금", 
                            f"🔒 승인되지 않은 PC 기기에서 접속했습니다.\n\n"
                            f"📌 다른 컴퓨터로 변경하셨다면 아래 인증 번호를 사장님께 전달해 주세요.\n"
                            f"----------------------------------------\n"
                            f"▶️ PC 인증 번호 : {my_pc_name}\n"
                            f"----------------------------------------\n"
                            f"⚠️ 확인을 누르면 인증 번호가 클립보드에 자동 복사됩니다."
                        )
                        login_window.clipboard_clear()
                        login_window.clipboard_append(my_pc_name)
                        return
                        
    if login_success:
        global _logged_in_key, _logged_in_pc
        _logged_in_key = user_key
        _logged_in_pc = my_pc_name
        login_window.destroy()
        show_main_macro_ui()
        return
    else:
        messagebox.showerror("인증 실패", "🚫 잘못된 인증키입니다. 시트 등록 상태를 다시 확인해 주세요.")

# --- 🖥️ 메인 UI 대시보드 ---
def show_main_macro_ui():
    global root, lbl_runtime, lbl_loot_timer, lbl_sell_timer, lbl_live_hp, lbl_live_mp, lbl_custom_timer, lbl_custom_timer_2, lbl_custom_timer_3
    global lbl_hp_status, lbl_mp_status, ent_pot_key, ent_mp_pot_key, scale_hp, scale_mp, ent_custom_key, ent_custom_sec, ent_custom_key_2, ent_custom_sec_2, lbl_minimap
    global lbl_f5, lbl_f6, lbl_f7, lbl_f8, lbl_teleport, btn_start, btn_stop, btn_pause, map_mode
    global ent_skill_key1, skill_mode1, ent_skill_key2, skill_mode2
    global btn_f5, btn_f6, btn_f7, btn_f8
    global ent_loot_sec, ent_sell_sec, ent_custom_key_3, ent_custom_sec_3
    global lbl_status

    root = tk.Tk()
    root.title("메이플 플래닛 프로 마스터 컨트롤러 V6.7")
    root.geometry("510x700")
    root.resizable(False, True)
    root.configure(bg=C_BG_MAIN)

    # ── 스크롤 가능한 메인 캔버스 설정 ──
    canvas = tk.Canvas(root, bg=C_BG_MAIN, highlightthickness=0)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    sf = tk.Frame(canvas, bg=C_BG_MAIN)
    sf_window = canvas.create_window((0, 0), window=sf, anchor="nw")

    def _on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        canvas.itemconfig(sf_window, width=event.width)

    sf.bind("<Configure>", _on_frame_configure)
    canvas.bind("<Configure>", _on_canvas_configure)
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))


    map_mode = tk.StringVar(value="DOUBLE")
    skill_mode1 = tk.StringVar(value="TAP"); skill_mode2 = tk.StringVar(value="TAP")

    # 🎯 [핵심 패치] 불필요한 상태 표시 텍스트창(lbl_status) 라인 완벽히 삭제 통편집

    # ── 현재 상태창 ──
    frame_status = tk.Frame(sf, bg="#0a2a1f", bd=1, relief="solid")
    frame_status.pack(pady=(12, 0), padx=15, fill="x")
    lbl_status = tk.Label(frame_status, text="⚫ 대기 중", font=("맑은 고딕", 12, "bold"), fg=C_TEXT_MUTED, bg="#0a2a1f", pady=8)
    lbl_status.pack()
    tk.Label(frame_status, text=f"🔑 {_logged_in_key}  |  💻 {_logged_in_pc}", font=("맑은 고딕", 8), fg="#555555", bg="#0a2a1f").pack(pady=(0, 5))

    lbl_hotkey_info = tk.Label(sf, text="⌨️ F2 시작  |  F3 정지  |  F4 일시정지", font=("맑은 고딕", 11, "bold"), fg=C_POINT, bg=C_BG_MAIN)
    lbl_hotkey_info.pack(pady=8)

    frame_mode = tk.LabelFrame(sf, text=" 🗺️ 사냥 모드 선택 ", font=("맑은 고딕", 10, "bold"), padx=15, pady=8, fg=C_POINT, bg=C_BG_CARD, bd=1, relief="solid")
    frame_mode.pack(pady=5, padx=15, fill="both")
    
    r1 = tk.Radiobutton(frame_mode, text="복층 지형 모드", variable=map_mode, value="DOUBLE", command=toggle_map_mode_ui, font=("맑은 고딕", 9, "bold"), fg=C_TEXT_MAIN, bg=C_BG_CARD, selectcolor=C_BG_MAIN, activebackground=C_BG_CARD)
    r1.pack(anchor="w", pady=2)
    r2 = tk.Radiobutton(frame_mode, text="일자 단순형 모드", variable=map_mode, value="SINGLE", command=toggle_map_mode_ui, font=("맑은 고딕", 9, "bold"), fg=C_TEXT_MAIN, bg=C_BG_CARD, selectcolor=C_BG_MAIN, activebackground=C_BG_CARD)
    r2.pack(anchor="w", pady=2)
    r3 = tk.Radiobutton(frame_mode, text="제자리 사냥 모드", variable=map_mode, value="STATIONARY", command=toggle_map_mode_ui, font=("맑은 고딕", 9, "bold"), fg=C_TEXT_MAIN, bg=C_BG_CARD, selectcolor=C_BG_MAIN, activebackground=C_BG_CARD)
    r3.pack(anchor="w", pady=2)

    frame_keys = tk.LabelFrame(sf, text=" ⚔️ 사냥 작동 키 세팅 ", font=("맑은 고딕", 10, "bold"), padx=15, pady=8, fg=C_POINT, bg=C_BG_CARD, bd=1, relief="solid")
    frame_keys.pack(pady=5, padx=15, fill="both")
    
    row_key1 = tk.Frame(frame_keys, bg=C_BG_CARD); row_key1.pack(fill="x", pady=3)
    tk.Label(row_key1, text="주력키 1 :", font=("맑은 고딕", 9), fg=C_TEXT_MAIN, bg=C_BG_CARD).pack(side="left")
    ent_skill_key1 = tk.Entry(row_key1, width=5, justify="center", font=("Consolas", 10, "bold"), bg=C_ENTRY_BG, fg=C_POINT, bd=0)
    ent_skill_key1.insert(0, "s"); ent_skill_key1.pack(side="left", padx=8)
    ent_skill_key1.bind("<Key>", lambda e: record_keyboard_key(e, ent_skill_key1))
    tk.Radiobutton(row_key1, text="연타", variable=skill_mode1, value="TAP", fg=C_TEXT_MUTED, bg=C_BG_CARD, selectcolor=C_BG_MAIN).pack(side="left", padx=5)
    tk.Radiobutton(row_key1, text="HOLD", variable=skill_mode1, value="HOLD", fg=C_TEXT_MUTED, bg=C_BG_CARD, selectcolor=C_BG_MAIN).pack(side="left", padx=5)

    row_key2 = tk.Frame(frame_keys, bg=C_BG_CARD); row_key2.pack(fill="x", pady=3)
    tk.Label(row_key2, text="기동키 2 :", font=("맑은 고딕", 9), fg=C_TEXT_MAIN, bg=C_BG_CARD).pack(side="left")
    ent_skill_key2 = tk.Entry(row_key2, width=5, justify="center", font=("Consolas", 10, "bold"), bg=C_ENTRY_BG, fg=C_POINT, bd=0)
    ent_skill_key2.insert(0, "d"); ent_skill_key2.pack(side="left", padx=8)
    ent_skill_key2.bind("<Key>", lambda e: record_keyboard_key(e, ent_skill_key2))
    tk.Radiobutton(row_key2, text="연타", variable=skill_mode2, value="TAP", fg=C_TEXT_MUTED, bg=C_BG_CARD, selectcolor=C_BG_MAIN).pack(side="left", padx=5)
    tk.Radiobutton(row_key2, text="HOLD", variable=skill_mode2, value="HOLD", fg=C_TEXT_MUTED, bg=C_BG_CARD, selectcolor=C_BG_MAIN).pack(side="left", padx=5)

    frame_dash = tk.LabelFrame(sf, text=" 📊 실시간 작동 대시보드 ", font=("맑은 고딕", 10, "bold"), padx=15, pady=8, fg=C_POINT, bg=C_BG_CARD, bd=1, relief="solid")
    frame_dash.pack(pady=5, padx=15, fill="both")

    lbl_runtime = tk.Label(frame_dash, text="⏱️ 총 가동 시간: 00시간 00분 00초", font=("맑은 고딕", 10, "bold"), fg=C_TEXT_MAIN, bg=C_BG_CARD, anchor="w")
    lbl_runtime.pack(fill="x", pady=3)

    row_loot_line = tk.Frame(frame_dash, bg=C_BG_CARD); row_loot_line.pack(fill="x", pady=2)
    lbl_loot_timer = tk.Label(row_loot_line, text=f"🪙 다음 메소 수거까지: {LOOT_CYCLE_TIME}초 남음", font=("맑은 고딕", 9), fg=C_TEXT_MUTED, bg=C_BG_CARD, anchor="w")
    lbl_loot_timer.pack(side="left")
    tk.Button(row_loot_line, text="수거 테스트", font=("맑은 고딕", 8, "bold"), command=test_loot_cycle, bg=C_ENTRY_BG, fg=C_POINT, bd=0, padx=6).pack(side="right")

    row_loot_sec = tk.Frame(frame_dash, bg=C_BG_CARD); row_loot_sec.pack(fill="x", pady=1)
    tk.Label(row_loot_sec, text="  └ 수거 주기 (초):", font=("맑은 고딕", 8), fg=C_TEXT_MUTED, bg=C_BG_CARD).pack(side="left")
    ent_loot_sec = tk.Entry(row_loot_sec, width=7, justify="center", font=("Consolas", 8, "bold"), bg=C_ENTRY_BG, fg=C_POINT, bd=0)
    ent_loot_sec.insert(0, str(LOOT_CYCLE_TIME)); ent_loot_sec.pack(side="left", padx=6)

    row_sell_line = tk.Frame(frame_dash, bg=C_BG_CARD); row_sell_line.pack(fill="x", pady=2)
    lbl_sell_timer = tk.Label(row_sell_line, text="🎒 묘묘 장비 정산까지: 10분 00초 남음", font=("맑은 고딕", 9), fg=C_TEXT_MUTED, bg=C_BG_CARD, anchor="w")
    lbl_sell_timer.pack(side="left")
    tk.Button(row_sell_line, text="묘묘 테스트", font=("맑은 고딕", 8, "bold"), command=test_sell_items, bg=C_ENTRY_BG, fg=C_POINT, bd=0, padx=6).pack(side="right")

    row_sell_sec = tk.Frame(frame_dash, bg=C_BG_CARD); row_sell_sec.pack(fill="x", pady=1)
    tk.Label(row_sell_sec, text="  └ 정산 주기 (초):", font=("맑은 고딕", 8), fg=C_TEXT_MUTED, bg=C_BG_CARD).pack(side="left")
    ent_sell_sec = tk.Entry(row_sell_sec, width=7, justify="center", font=("Consolas", 8, "bold"), bg=C_ENTRY_BG, fg=C_POINT, bd=0)
    ent_sell_sec.insert(0, str(SELL_CYCLE_TIME)); ent_sell_sec.pack(side="left", padx=6)

    lbl_live_hp = tk.Label(frame_dash, text="❤️ 실시간 체력 감지: HP 영역 지정 대기", font=("맑은 고딕", 9, "bold"), fg=C_TEXT_MUTED, bg=C_BG_CARD, anchor="w")
    lbl_live_hp.pack(fill="x", pady=2)
    lbl_live_mp = tk.Label(frame_dash, text="💙 실시간 마나 감지: MP 영역 지정 대기", font=("맑은 고딕", 9, "bold"), fg=C_TEXT_MUTED, bg=C_BG_CARD, anchor="w")
    lbl_live_mp.pack(fill="x", pady=2)

    lbl_custom_timer = tk.Label(frame_dash, text="⏱️ [SKILL 1] 다음 실행까지: 대기 중", font=("맑은 고딕", 9), fg=C_TEXT_MUTED, bg=C_BG_CARD, anchor="w")
    lbl_custom_timer.pack(fill="x", pady=2)

    lbl_custom_timer_2 = tk.Label(frame_dash, text="⏱️ [SKILL 2] 다음 실행까지: 대기 중", font=("맑은 고딕", 9), fg=C_TEXT_MUTED, bg=C_BG_CARD, anchor="w")
    lbl_custom_timer_2.pack(fill="x", pady=2)

    lbl_custom_timer_3 = tk.Label(frame_dash, text="⏱️ [펫먹이] 미설정", font=("맑은 고딕", 9), fg=C_TEXT_MUTED, bg=C_BG_CARD, anchor="w")
    lbl_custom_timer_3.pack(fill="x", pady=2)

    frame_potion = tk.LabelFrame(sf, text=" 💊 케어 및 SKILL 타이머 셋업 ", font=("맑은 고딕", 10, "bold"), padx=15, pady=8, fg=C_POINT, bg=C_BG_CARD, bd=1, relief="solid")
    frame_potion.pack(pady=5, padx=15, fill="both")

    row_hp = tk.Frame(frame_potion, bg=C_BG_CARD); row_hp.pack(fill="x", pady=3)
    lbl_hp_status = tk.Label(row_hp, text="❌ HP 바 영역: 미설정", fg=C_ACCENT, bg=C_BG_CARD, font=("맑은 고딕", 9, "bold"), anchor="w")
    lbl_hp_status.pack(side="left")
    tk.Button(row_hp, text="HP 영역 지정", font=("맑은 고딕", 8, "bold"), command=select_hp_bar, bg=C_ENTRY_BG, fg=C_TEXT_MAIN, bd=0, padx=8).pack(side="right")

    row_pot = tk.Frame(frame_potion, bg=C_BG_CARD); row_pot.pack(fill="x", pady=3)
    tk.Label(row_pot, text="HP 물약 단축키:", font=("맑은 고딕", 9), fg=C_TEXT_MAIN, bg=C_BG_CARD).pack(side="left")
    ent_pot_key = tk.Entry(row_pot, width=12, justify="center", font=("Consolas", 9, "bold"), bg=C_ENTRY_BG, fg=C_POINT, bd=0)
    ent_pot_key.insert(0, "insert"); ent_pot_key.pack(side="right")
    ent_pot_key.bind("<Key>", lambda e: record_keyboard_key(e, ent_pot_key))

    row_scale = tk.Frame(frame_potion, bg=C_BG_CARD); row_scale.pack(fill="x", pady=3)
    tk.Label(row_scale, text="HP 물약 기준 (%):", font=("맑은 고딕", 9), fg=C_TEXT_MAIN, bg=C_BG_CARD).pack(side="left")
    scale_hp = tk.Scale(row_scale, from_=10, to=90, orient="horizontal", width=10, length=140, bg=C_BG_CARD, fg=C_TEXT_MAIN, bd=0, highlightthickness=0, troughcolor=C_ENTRY_BG)
    scale_hp.set(50); scale_hp.pack(side="right")

    tk.Frame(frame_potion, bg="#444444", height=1).pack(fill="x", pady=4)

    row_mp = tk.Frame(frame_potion, bg=C_BG_CARD); row_mp.pack(fill="x", pady=3)
    lbl_mp_status = tk.Label(row_mp, text="❌ MP 바 영역: 미설정", fg=C_ACCENT, bg=C_BG_CARD, font=("맑은 고딕", 9, "bold"), anchor="w")
    lbl_mp_status.pack(side="left")
    tk.Button(row_mp, text="MP 영역 지정", font=("맑은 고딕", 8, "bold"), command=select_mp_bar, bg=C_ENTRY_BG, fg=C_TEXT_MAIN, bd=0, padx=8).pack(side="right")

    row_mp_pot = tk.Frame(frame_potion, bg=C_BG_CARD); row_mp_pot.pack(fill="x", pady=3)
    tk.Label(row_mp_pot, text="MP 물약 단축키:", font=("맑은 고딕", 9), fg=C_TEXT_MAIN, bg=C_BG_CARD).pack(side="left")
    ent_mp_pot_key = tk.Entry(row_mp_pot, width=12, justify="center", font=("Consolas", 9, "bold"), bg=C_ENTRY_BG, fg="#5599ff", bd=0)
    ent_mp_pot_key.pack(side="right")
    ent_mp_pot_key.bind("<Key>", lambda e: record_keyboard_key(e, ent_mp_pot_key))

    row_mp_scale = tk.Frame(frame_potion, bg=C_BG_CARD); row_mp_scale.pack(fill="x", pady=3)
    tk.Label(row_mp_scale, text="MP 물약 기준 (%):", font=("맑은 고딕", 9), fg=C_TEXT_MAIN, bg=C_BG_CARD).pack(side="left")
    scale_mp = tk.Scale(row_mp_scale, from_=10, to=90, orient="horizontal", width=10, length=140, bg=C_BG_CARD, fg=C_TEXT_MAIN, bd=0, highlightthickness=0, troughcolor=C_ENTRY_BG)
    scale_mp.set(30); scale_mp.pack(side="right")

    tk.Frame(frame_potion, bg="#444444", height=1).pack(fill="x", pady=4)

    row_sk1 = tk.Frame(frame_potion, bg=C_BG_CARD); row_sk1.pack(fill="x", pady=4)
    tk.Label(row_sk1, text="SKILL 1 키 / 주기:", font=("맑은 고딕", 9), fg=C_TEXT_MAIN, bg=C_BG_CARD).pack(side="left")
    ent_custom_sec = tk.Entry(row_sk1, width=6, justify="center", font=("Consolas", 9, "bold"), bg=C_ENTRY_BG, fg=C_POINT, bd=0)
    ent_custom_sec.insert(0, "60"); ent_custom_sec.pack(side="right", padx=(5,0))
    ent_custom_key = tk.Entry(row_sk1, width=10, justify="center", font=("Consolas", 9, "bold"), bg=C_ENTRY_BG, fg=C_POINT, bd=0)
    ent_custom_key.insert(0, "delete"); ent_custom_key.pack(side="right")
    ent_custom_key.bind("<Key>", lambda e: record_keyboard_key(e, ent_custom_key))

    row_sk2 = tk.Frame(frame_potion, bg=C_BG_CARD); row_sk2.pack(fill="x", pady=4)
    tk.Label(row_sk2, text="SKILL 2 키 / 주기:", font=("맑은 고딕", 9), fg=C_TEXT_MAIN, bg=C_BG_CARD).pack(side="left")
    ent_custom_sec_2 = tk.Entry(row_sk2, width=6, justify="center", font=("Consolas", 9, "bold"), bg=C_ENTRY_BG, fg=C_POINT, bd=0)
    ent_custom_sec_2.insert(0, "120"); ent_custom_sec_2.pack(side="right", padx=(5,0))
    ent_custom_key_2 = tk.Entry(row_sk2, width=10, justify="center", font=("Consolas", 9, "bold"), bg=C_ENTRY_BG, fg=C_POINT, bd=0)
    ent_custom_key_2.insert(0, "page down"); ent_custom_key_2.pack(side="right")
    ent_custom_key_2.bind("<Key>", lambda e: record_keyboard_key(e, ent_custom_key_2))

    row_pet = tk.Frame(frame_potion, bg=C_BG_CARD); row_pet.pack(fill="x", pady=4)
    tk.Label(row_pet, text="🐾 펫먹이 키 / 주기:", font=("맑은 고딕", 9), fg=C_TEXT_MAIN, bg=C_BG_CARD).pack(side="left")
    ent_custom_sec_3 = tk.Entry(row_pet, width=6, justify="center", font=("Consolas", 9, "bold"), bg=C_ENTRY_BG, fg=C_POINT, bd=0)
    ent_custom_sec_3.insert(0, "180"); ent_custom_sec_3.pack(side="right", padx=(5, 0))
    ent_custom_key_3 = tk.Entry(row_pet, width=10, justify="center", font=("Consolas", 9, "bold"), bg=C_ENTRY_BG, fg=C_POINT, bd=0)
    ent_custom_key_3.pack(side="right")
    ent_custom_key_3.bind("<Key>", lambda e: record_keyboard_key(e, ent_custom_key_3))

    frame_setup = tk.LabelFrame(sf, text=" 📍 사냥터 지형 환경 셋업 ", font=("맑은 고딕", 10, "bold"), padx=15, pady=8, fg=C_POINT, bg=C_BG_CARD, bd=1, relief="solid")
    frame_setup.pack(pady=5, padx=15, fill="both")

    row_map = tk.Frame(frame_setup, bg=C_BG_CARD); row_map.pack(fill="x", pady=3)
    lbl_minimap = tk.Label(row_map, text="❌ 미니맵 영역: 미설정", fg=C_ACCENT, bg=C_BG_CARD, font=("맑은 고딕", 9, "bold"), anchor="w")
    lbl_minimap.pack(side="left")
    tk.Button(row_map, text="영역 드래그", font=("맑은 고딕", 8, "bold"), command=select_minimap, bg=C_ENTRY_BG, fg=C_TEXT_MAIN, bd=0, padx=8).pack(side="right")

    def create_setup_row(parent, label_text, btn_cmd):
        row = tk.Frame(parent, bg=C_BG_CARD); row.pack(fill="x", pady=2)
        tk.Label(row, text=label_text, font=("맑은 고딕", 9), fg=C_TEXT_MAIN, bg=C_BG_CARD).pack(side="left")
        btn = tk.Button(row, text="위치 지정", font=("맑은 고딕", 8), command=btn_cmd, bg=C_ENTRY_BG, fg=C_TEXT_MUTED, bd=0, padx=6)
        btn.pack(side="right")
        lbl = tk.Label(row, text="미지정", font=("Consolas", 9), fg=C_TEXT_MUTED, bg=C_BG_CARD)
        lbl.pack(side="right", padx=10)
        return lbl, btn

    lbl_f5, btn_f5 = create_setup_row(frame_setup, "2층 사냥터 좌측 한계선:", set_left_limit)
    lbl_f6, btn_f6 = create_setup_row(frame_setup, "2층 사냥터 우측 한계선:", set_right_limit)
    lbl_f7, btn_f7 = create_setup_row(frame_setup, "1층 사냥터 좌측 한계선:", set_return_x)
    lbl_f8, btn_f8 = create_setup_row(frame_setup, "1층 사냥터 우측 한계선:", set_right_limit_1f)
    lbl_teleport, _ = create_setup_row(frame_setup, "🔼 윗텔포 범위 (드래그):", set_teleport_rect)

    # 이미지 인식 안 될 때 직접 등록 (접기/펼치기)
    frame_capture_outer = tk.Frame(sf, bg=C_BG_CARD, bd=1, relief="solid")
    frame_capture_outer.pack(pady=5, padx=15, fill="x")

    capture_open = [False]

    frame_capture_header = tk.Frame(frame_capture_outer, bg=C_BG_CARD)
    frame_capture_header.pack(fill="x", padx=15, pady=7)

    lbl_capture_toggle = tk.Label(
        frame_capture_header,
        text="▶  📸 이미지 직접 등록 (인식 안 될 때 클릭)",
        font=("맑은 고딕", 10, "bold"), fg="#ff9900", bg=C_BG_CARD, cursor="hand2"
    )
    lbl_capture_toggle.pack(side="left")

    frame_capture = tk.Frame(frame_capture_outer, bg=C_BG_CARD, padx=15, pady=4)

    def toggle_capture_section(e=None):
        if capture_open[0]:
            frame_capture.pack_forget()
            lbl_capture_toggle.config(text="▶  📸 이미지 직접 등록 (인식 안 될 때 클릭)")
            capture_open[0] = False
        else:
            frame_capture.pack(fill="x", pady=(0, 8))
            lbl_capture_toggle.config(text="▼  📸 이미지 직접 등록 (인식 안 될 때 클릭)")
            capture_open[0] = True

    lbl_capture_toggle.bind("<Button-1>", toggle_capture_section)
    frame_capture_header.bind("<Button-1>", toggle_capture_section)

    tk.Label(frame_capture, text="게임 화면에서 해당 이미지를 드래그로 직접 캡처해 등록하세요", font=("맑은 고딕", 8), fg=C_TEXT_MUTED, bg=C_BG_CARD).pack(anchor="w", pady=(0, 4))

    def _make_cap_row(parent, text, fname):
        row = tk.Frame(parent, bg=C_BG_CARD); row.pack(fill="x", pady=2)

        if getattr(sys, 'frozen', False):
            custom_p = os.path.join(os.path.dirname(sys.executable), fname)
            if os.path.exists(custom_p):
                status_text = f"[{fname}]  ✅ 직접 등록됨"
                status_fg = C_POINT
            else:
                status_text = f"[{fname}]  기본 이미지 사용 중"
                status_fg = "#ffcc00"
        else:
            p = os.path.join(os.path.abspath("."), fname)
            if os.path.exists(p):
                status_text = f"[{fname}]  ✅ 이미지 있음"
                status_fg = C_POINT
            else:
                status_text = f"[{fname}]  ❌ 미등록"
                status_fg = C_ACCENT

        lbl = tk.Label(row, text=status_text, font=("맑은 고딕", 8), fg=status_fg, bg=C_BG_CARD, anchor="w")
        lbl.pack(side="left", expand=True, fill="x")
        tk.Button(row, text=text, font=("맑은 고딕", 8, "bold"), bg=C_ENTRY_BG, fg=C_TEXT_MAIN, bd=0, padx=6,
                  command=lambda f=fname, l=lbl: capture_template(f, l)).pack(side="right")

    _make_cap_row(frame_capture, "묘묘 캡처", "miumiu.png")
    _make_cap_row(frame_capture, "캐시탭 캡처", "cash_tab1.png")
    _make_cap_row(frame_capture, "판매버튼 캡처", "sell_btn.png")
    _make_cap_row(frame_capture, "나가기 캡처", "exit_shop_btn.png")
    _make_cap_row(frame_capture, "닫기(X) 캡처", "x.png")

    frame_preset_ctrl = tk.Frame(sf, bg=C_BG_MAIN); frame_preset_ctrl.pack(pady=8)
    tk.Button(frame_preset_ctrl, text="💾 현재 모든 세팅값 프리셋 파일로 보존", font=("맑은 고딕", 9, "bold"), bg=C_BG_CARD, fg=C_POINT, bd=1, relief="solid", width=42, command=save_preset_to_file).pack()
    tk.Button(frame_preset_ctrl, text="📂 프리셋 선택 / 변경", font=("맑은 고딕", 9, "bold"), bg=C_BG_CARD, fg=C_TEXT_MUTED, bd=1, relief="solid", width=42, command=show_preset_selector).pack(pady=(4, 0))

    # 버튼 객체는 .config() 호출을 위해 생성만 하고 표시 안 함
    btn_start = tk.Button(root, command=start_macro)
    btn_pause = tk.Button(root, state="disabled", command=toggle_pause)
    btn_stop  = tk.Button(root, state="disabled", command=stop_macro)

    root.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
    setup_keyboard_hook(); root.after(200, _auto_load_preset); update_gui_dashboard(); root.mainloop()

if __name__ == '__main__':
    login_window = tk.Tk()
    login_window.title("🔒 SECURITY LOCK")
    login_window.geometry("360x190")
    login_window.resizable(False, False)
    login_window.configure(bg=C_BG_MAIN)

    tk.Label(login_window, text="메이플 플래닛 계정 권한 엔진", font=("맑은 고딕", 11, "bold"), fg=C_POINT, bg=C_BG_MAIN).pack(pady=15)
    frame_input = tk.Frame(login_window, bg=C_BG_MAIN); frame_input.pack(pady=5)
    tk.Label(frame_input, text="인증 키 : ", font=("맑은 고딕", 9), fg=C_TEXT_MAIN, bg=C_BG_MAIN).pack(side="left")
    ent_login_key = tk.Entry(frame_input, width=22, justify="center", font=("Consolas", 10, "bold"), bg=C_ENTRY_BG, fg=C_POINT, bd=0, insertbackground=C_POINT)
    ent_login_key.pack(side="left", padx=5); ent_login_key.focus_set()

    tk.Button(login_window, text="서버 라이선스 인증 및 가동", font=("맑은 고딕", 10, "bold"), bg=C_BG_CARD, fg=C_TEXT_MAIN, bd=0, width=24, height=2, command=check_license_and_login).pack(pady=20)
    login_window.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
    login_window.mainloop()