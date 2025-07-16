import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import psutil
import subprocess
import os
import sys


# --- 함수 정의 ---

def resource_path(relative_path):
    """ 리소스의 절대 경로를 반환합니다. (개발, PyInstaller 모두 호환) """
    try:
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.argv[0])))
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def center_window(window, width, height):
    """주어진 너비와 높이로 창을 화면 중앙에 배치합니다."""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')


def get_network_info():
    """우선순위에 따라 최적의 네트워크 어댑터 정보를 찾아 반환합니다."""
    adapters = {'ethernet': [], 'wifi': [], 'other': []}
    all_addrs = psutil.net_if_addrs()
    all_stats = psutil.net_if_stats()

    for name, stats in all_stats.items():
        if stats.isup and name in all_addrs:
            addrs = all_addrs[name]
            for addr in addrs:
                if addr.family == 2:
                    adapter_info = {'name': name, 'ip': addr.address, 'status': '활성화'}
                    for addr_mac in addrs:
                        if addr_mac.family == psutil.AF_LINK:
                            adapter_info['mac'] = addr_mac.address
                            break

                    name_lower = name.lower()
                    if 'ethernet' in name_lower or '이더넷' in name_lower:
                        adapters['ethernet'].append(adapter_info)
                    elif 'wi-fi' in name_lower or 'wi–fi' in name_lower or '무선' in name_lower:
                        adapters['wifi'].append(adapter_info)
                    elif name != 'Loopback Pseudo-Interface 1':
                        adapters['other'].append(adapter_info)
                    break

    chosen_adapter = None
    if adapters['ethernet']:
        chosen_adapter = adapters['ethernet'][0]
    elif adapters['wifi']:
        chosen_adapter = adapters['wifi'][0]
    elif adapters['other']:
        chosen_adapter = adapters['other'][0]

    return chosen_adapter


def refresh_info():
    """GUI의 레이블 정보를 업데이트합니다."""
    info = get_network_info()
    if info:
        status_var.set("정보를 성공적으로 새로고침했습니다.")
        info_vars["어댑터 정보"].set(f"{info.get('name', 'N/A')} ({info.get('status', 'N/A')})")
        info_vars["MAC 주소"].set(info.get('mac', 'N/A'))
        info_vars["IP 주소"].set(info.get('ip', 'N/A'))
    else:
        status_var.set("활성화된 네트워크 연결을 찾을 수 없습니다.")
        for key in info_vars: info_vars[key].set("N/A")


def reassign_ip():
    """IP 주소를 재할당합니다."""
    status_var.set("IP 주소 재할당 중...")
    app.update_idletasks()
    try:
        subprocess.run(["ipconfig", "/release"], check=True, capture_output=True)
        subprocess.run(["ipconfig", "/renew"], check=True, capture_output=True)
        status_var.set("IP 재할당 완료! 정보를 새로고침하세요.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        status_var.set(f"오류 발생: {e} (관리자 권한으로 실행 필요)")

    app.after(1000, refresh_info)


# --- GUI 설정 ---
app = ttk.Window(themename="litera")
app.title("Simple Network Info")

# 절대 경로로 아이콘 설정
app.iconbitmap(resource_path('icon/kdic.ico'))

center_window(app, 480, 280)
app.resizable(False, False)

main_frame = ttk.Frame(app, padding="20")
main_frame.pack(fill=BOTH, expand=True)

info_frame = ttk.Frame(main_frame)
info_frame.pack(fill=X, padx=10, pady=10)
info_frame.columnconfigure(1, weight=1)

info_labels = ["어댑터 정보", "MAC 주소", "IP 주소"]
info_vars = {label: ttk.StringVar() for label in info_labels}

for i, label_text in enumerate(info_labels):
    key_label = ttk.Label(info_frame, text=label_text, font=("Malgun Gothic", 10, "bold"))
    key_label.grid(row=i, column=0, sticky="w", pady=8)

    value_label_font = ("Consolas", 10)
    if label_text == "어댑터 정보":
        value_label_font = ("Malgun Gothic", 10)

    value_label = ttk.Label(info_frame, textvariable=info_vars[label_text], font=value_label_font)
    value_label.grid(row=i, column=1, sticky="w", padx=10)

button_frame = ttk.Frame(main_frame)
button_frame.pack(fill=X, padx=10, pady=20)
button_frame.columnconfigure((0, 1), weight=1)

refresh_button = ttk.Button(
    button_frame,
    text="🔄 정보 새로고침",
    command=refresh_info,
    bootstyle="secondary-outline"
)
refresh_button.grid(row=0, column=0, sticky="ew", padx=5)

reassign_button = ttk.Button(
    button_frame,
    text="⚡ IP 재할당 받기",
    command=reassign_ip,
    bootstyle="success"
)
reassign_button.grid(row=0, column=1, sticky="ew", padx=5)

status_var = ttk.StringVar()
status_label = ttk.Label(main_frame, textvariable=status_var, font=("Malgun Gothic", 9), bootstyle="secondary")
status_label.pack(side=BOTTOM, fill=X, padx=10)

# --- 프로그램 시작 ---
refresh_info()
app.mainloop()