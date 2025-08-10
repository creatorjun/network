import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import psutil
import subprocess
import os
import re
import sys # sys 모듈 추가 (pyinstaller 경로 탐색에 필요)

class NetworkInfoApp:
    """
    네트워크 정보를 표시하고 IP를 재할당하는 GUI 애플리케이션 클래스.
    (Windows 전용, 콘솔 창 숨김 처리)
    """
    FONT_BOLD = ("Malgun Gothic", 10, "bold")
    FONT_NORMAL = ("Malgun Gothic", 10)
    FONT_MONO = ("Consolas", 10)

    def __init__(self, root):
        self.root = root
        self.root.title("Simple Network Info")
        self.set_icon('C:/SEPR/network/icon/kdic.ico')
        self.center_window(480, 280)
        self.root.resizable(False, False)

        self.info_vars = {
            "어댑터 정보": ttk.StringVar(),
            "MAC 주소": ttk.StringVar(),
            "IP 주소": ttk.StringVar()
        }
        self.status_var = ttk.StringVar()

        self.create_widgets()
        self.refresh_info()

    def resource_path(self, relative_path):
        """ 리소스의 절대 경로를 반환합니다. (개발, PyInstaller 모두 호환) """
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.argv[0])))
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def set_icon(self, icon_path):
        abs_icon_path = self.resource_path(icon_path)
        if os.path.exists(abs_icon_path):
            self.root.iconbitmap(abs_icon_path)

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=BOTH, expand=True)
        self._create_info_frame(main_frame)
        self._create_button_frame(main_frame)
        self._create_status_bar(main_frame)

    def _create_info_frame(self, parent):
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=X, padx=10, pady=10)
        info_frame.columnconfigure(1, weight=1)
        labels = ["어댑터 정보", "MAC 주소", "IP 주소"]
        for i, text in enumerate(labels):
            key_label = ttk.Label(info_frame, text=text, font=self.FONT_BOLD)
            key_label.grid(row=i, column=0, sticky="w", pady=8)
            font = self.FONT_NORMAL if text == "어댑터 정보" else self.FONT_MONO
            value_label = ttk.Label(info_frame, textvariable=self.info_vars[text], font=font)
            value_label.grid(row=i, column=1, sticky="w", padx=10)

    def _create_button_frame(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=X, padx=10, pady=20)
        button_frame.columnconfigure((0, 1), weight=1)
        refresh_button = ttk.Button(
            button_frame, text="🔄 정보 새로고침", command=self.refresh_info, bootstyle="secondary-outline"
        )
        refresh_button.grid(row=0, column=0, sticky="ew", padx=5)
        self.reassign_button = ttk.Button(
            button_frame, text="⚡ IP 재할당 받기", command=self.reassign_ip, bootstyle="success"
        )
        self.reassign_button.grid(row=0, column=1, sticky="ew", padx=5)

    def _create_status_bar(self, parent):
        status_label = ttk.Label(
            parent, textvariable=self.status_var, font=("Malgun Gothic", 9), bootstyle="secondary"
        )
        status_label.pack(side=BOTTOM, fill=X, padx=10)

    def _is_dhcp_enabled(self, mac_address):
        if not mac_address:
            return False
        try:
            # 콘솔 창이 나타나지 않도록 creationflags 추가
            output = subprocess.check_output(
                ["ipconfig", "/all"],
                encoding='cp949',
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            adapter_sections = output.split('\n\n')
            for section in adapter_sections:
                if mac_address in section and "DHCP 사용" in section:
                    dhcp_line = re.search(r"DHCP 사용.*?: (네|예|Yes)", section, re.IGNORECASE)
                    if dhcp_line:
                        return True
            return False
        except (FileNotFoundError, subprocess.CalledProcessError, UnicodeDecodeError):
            return False

    def get_network_info(self):
        all_stats = psutil.net_if_stats()
        all_addrs = psutil.net_if_addrs()
        adapter_candidates = []
        for name, stats in all_stats.items():
            if not (stats.isup and name in all_addrs):
                continue
            addrs = all_addrs[name]
            ip_addr, mac_addr = None, None
            for addr in addrs:
                if addr.family == psutil.AF_LINK: mac_addr = addr.address
                elif addr.family == 2: ip_addr = addr.address
            if ip_addr and mac_addr:
                adapter_info = {'name': name, 'ip': ip_addr, 'mac': mac_addr, 'status': '활성화'}
                name_lower = name.lower()
                if 'ethernet' in name_lower or '이더넷' in name_lower:
                    adapter_candidates.append((0, adapter_info))
                elif 'wi-fi' in name_lower or '무선' in name_lower:
                    adapter_candidates.append((1, adapter_info))
                elif name != 'Loopback Pseudo-Interface 1':
                    adapter_candidates.append((2, adapter_info))
        if adapter_candidates:
            adapter_candidates.sort(key=lambda x: x[0])
            chosen_adapter = adapter_candidates[0][1]
            chosen_adapter['dhcp_enabled'] = self._is_dhcp_enabled(chosen_adapter['mac'])
            return chosen_adapter
        return None

    def refresh_info(self):
        info = self.get_network_info()
        if info:
            self.info_vars["어댑터 정보"].set(f"{info.get('name', 'N/A')} ({info.get('status', 'N/A')})")
            self.info_vars["MAC 주소"].set(info.get('mac', 'N/A'))
            self.info_vars["IP 주소"].set(info.get('ip', 'N/A'))
            if info.get('dhcp_enabled'):
                self.reassign_button.config(state=NORMAL)
                self.status_var.set("정보를 성공적으로 새로고침했습니다.")
            else:
                self.reassign_button.config(state=DISABLED)
                self.status_var.set("고정 IP가 감지되었습니다. (IP 재할당 불가)")
        else:
            self.status_var.set("활성화된 네트워크 연결을 찾을 수 없습니다.")
            self.reassign_button.config(state=DISABLED)
            for key in self.info_vars:
                self.info_vars[key].set("N/A")

    def reassign_ip(self):
        self.status_var.set("IP 주소 재할당 중...")
        self.root.update_idletasks()
        try:
            # 콘솔 창이 나타나지 않도록 creationflags 추가
            creation_flags = subprocess.CREATE_NO_WINDOW
            subprocess.run(["ipconfig", "/release"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creation_flags)
            subprocess.run(["ipconfig", "/renew"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creation_flags)
            self.status_var.set("IP 재할당 완료! 잠시 후 정보가 업데이트됩니다.")
        except FileNotFoundError:
            self.status_var.set("오류: 'ipconfig' 명령을 찾을 수 없습니다.")
        except subprocess.CalledProcessError:
            self.status_var.set("오류 발생: 관리자 권한으로 프로그램을 실행해야 합니다.")
        except Exception as e:
            self.status_var.set(f"알 수 없는 오류 발생: {e}")
        finally:
            self.root.after(2000, self.refresh_info)

if __name__ == "__main__":
    app = ttk.Window(themename="litera")
    network_app = NetworkInfoApp(app)
    app.mainloop()