# minz_network.py — MinZ Network v2.5 (Full UI + Auto Scan + Lock Input)
# pip install rich pillow mss opencv-python
# Run as Administrator on both Master and Agent!

import os
import sys
import socket
import threading
import time
import struct
import ctypes
import io
import mss
import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()
PORT = 9998
SCAN_PORT = 9997

BANNER = """
[bold cyan]
███╗   ███╗██╗███╗   ██╗███████╗    ███╗   ██╗███████╗████████╗██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗
████╗ ████║██║████╗  ██║╚══███╔╝    ████╗  ██║██╔════╝╚══██╔══╝██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝
██╔████╔██║██║██╔██╗ ██║  ███╔╝     ██╔██╗ ██║█████╗     ██║   ██║ █╗ ██║██║   ██║██████╔╝█████╔╝ 
██║╚██╔╝██║██║██║╚██╗██║ ███╔╝      ██║╚██╗██║██╔══╝     ██║   ██║███╗██║██║   ██║██╔══██╗██╔═██╗ 
██║ ╚═╝ ██║██║██║ ╚████║███████╗    ██║ ╚████║███████╗   ██║   ╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗
╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝    ╚═╝  ╚═══╝╚══════╝   ╚═╝    ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
[/bold cyan]
[dim]                  LAN Classroom Management & Remote Control Tool[/dim]
"""

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# ============================================================
# AGENT (Client)
# ============================================================
class MinZAgent:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        self.locked = False
        self.sct = mss.mss()
        self.ping_server = True

    def lock_input(self, state):
        try:
            ctypes.windll.user32.BlockInput(state)
            self.locked = state
        except Exception:
            pass

    def capture_screen(self):
        monitor = self.sct.monitors[1]
        sct_img = self.sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        img = img.resize((640, 360))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=40)
        return img_byte_arr.getvalue()

    def listen_udp(self):
        # Lắng nghe tín hiệu quét LAN từ Master
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.bind(('0.0.0.0', SCAN_PORT))
        while self.running:
            try:
                data, addr = udp_sock.recvfrom(1024)
                if data == b"MINZ_DISCOVER":
                    udp_sock.sendto(b"MINZ_HERE", addr)
            except:
                pass

    def start(self):
        try:
            threading.Thread(target=self.listen_udp, daemon=True).start()
            self.client.connect((self.server_ip, PORT))
            console.print(f"[bold green]✔ Đã kết nối tới Master {self.server_ip}[/]")
            
            def listen_cmd():
                while self.running:
                    try:
                        cmd = self.client.recv(1024).decode().strip()
                        if cmd == "LOCK": self.lock_input(True)
                        elif cmd == "UNLOCK": self.lock_input(False)
                        elif cmd == "QUIT":
                            self.running = False
                            break
                    except:
                        break

            threading.Thread(target=listen_cmd, daemon=True).start()

            while self.running:
                frame = self.capture_screen()
                self.client.sendall(struct.pack(">I", len(frame)) + frame)
                time.sleep(0.05)
                
        except Exception as e:
            console.print(f"[bold red]✖ Mất kết nối: {e}[/]")
        finally:
            self.lock_input(False)
            self.client.close()

# ============================================================
# MASTER (Server + UI)
# ============================================================
class MinZMasterUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MinZ Network - Master Control")
        self.root.geometry("1100x750")
        self.root.configure(bg="#1e1e1e")
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('0.0.0.0', PORT))
        self.server.listen(20)
        
        self.agents = {}
        self.frames = {}
        self.running = True
        
        self.setup_ui()
        threading.Thread(target=self.accept_loop, daemon=True).start()
        threading.Thread(target=self.update_frames, daemon=True).start()

    def setup_ui(self):
        top_frame = tk.Frame(self.root, bg="#2d2d2d", height=60)
        top_frame.pack(fill=tk.X)
        
        tk.Label(top_frame, text="MinZ Network", font=("Segoe UI", 18, "bold"), bg="#2d2d2d", fg="#00d2ff").pack(side=tk.LEFT, padx=20)
        
        local_ip = get_local_ip()
        tk.Label(top_frame, text=f"IP: {local_ip}", font=("Segoe UI", 10), bg="#2d2d2d", fg="#aaa").pack(side=tk.LEFT, padx=10)
        
        self.btn_scan = tk.Button(top_frame, text="Quét LAN", bg="#0078d7", fg="white", font=("Segoe UI", 10, "bold"), command=self.scan_lan)
        self.btn_scan.pack(side=tk.RIGHT, padx=10, pady=10)
        
        main_frame = tk.Frame(self.root, bg="#1e1e1e")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        left_frame = tk.Frame(main_frame, bg="#252526", width=250)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(left_frame, text="Danh sách thiết bị", bg="#252526", fg="white", font=("Segoe UI", 12)).pack(pady=10)
        self.device_listbox = tk.Listbox(left_frame, bg="#1e1e1e", fg="#ccc", font=("Consolas", 11), selectbackground="#0078d7", borderwidth=0)
        self.device_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.right_frame = tk.Frame(main_frame, bg="#1e1e1e")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.lbl_screen = tk.Label(self.right_frame, bg="black", text="Chọn 1 thiết bị để xem màn hình", fg="grey", font=("Segoe UI", 14))
        self.lbl_screen.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        bottom_frame = tk.Frame(self.root, bg="#2d2d2d", height=60)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.btn_lock = tk.Button(bottom_frame, text="🔒 Khóa Chuột/Phím", bg="#d32f2f", fg="white", font=("Segoe UI", 10, "bold"), command=lambda: self.send_cmd("LOCK"))
        self.btn_lock.pack(side=tk.LEFT, padx=20, pady=10)
        
        self.btn_unlock = tk.Button(bottom_frame, text="🔓 Mở Khóa", bg="#388e3c", fg="white", font=("Segoe UI", 10, "bold"), command=lambda: self.send_cmd("UNLOCK"))
        self.btn_unlock.pack(side=tk.LEFT, padx=10, pady=10)

    def scan_lan(self):
        self.btn_scan.config(text="Đang quét...", state=tk.DISABLED)
        self.root.update()
        
        try:
            # Gửi UDP Broadcast để tìm Agent
            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            udp_sock.settimeout(2)
            
            broadcast_ip = ".".join(get_local_ip().split(".")[:3]) + ".255"
            udp_sock.sendto(b"MINZ_DISCOVER", (broadcast_ip, SCAN_PORT))
            
            found_ips = []
            while True:
                try:
                    data, addr = udp_sock.recvfrom(1024)
                    if data == b"MINZ_HERE":
                        found_ips.append(addr[0])
                except socket.timeout:
                    break
            udp_sock.close()
            
            count = 0
            for ip in found_ips:
                if ip not in self.device_listbox.get(0, tk.END):
                    self.device_listbox.insert(tk.END, ip)
                    count += 1
            messagebox.showinfo("Quét LAN", f"Tìm thấy {count} thiết bị có cài Agent.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi quét: {e}")
            
        self.btn_scan.config(text="Quét LAN", state=tk.NORMAL)

    def send_cmd(self, cmd):
        selected = self.device_listbox.curselection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một thiết bị.")
            return
        ip = self.device_listbox.get(selected[0])
        if ip in self.agents:
            try:
                self.agents[ip].sendall(cmd.encode())
            except:
                messagebox.showerror("Lỗi", "Mất kết nối tới thiết bị.")
        else:
            messagebox.showerror("Lỗi", f"Thiết bị {ip} chưa kết nối Agent.")

    def accept_loop(self):
        while self.running:
            try:
                conn, addr = self.server.accept()
                ip = addr[0]
                self.agents[ip] = conn
                if ip not in self.device_listbox.get(0, tk.END):
                    self.device_listbox.insert(tk.END, ip)
                threading.Thread(target=self.handle_agent, args=(conn, ip), daemon=True).start()
            except:
                break

    def recv_exact(self, sock, n):
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet: return None
            data += packet
        return data

    def handle_agent(self, conn, ip):
        while self.running:
            try:
                raw_msglen = self.recv_exact(conn, 4)
                if not raw_msglen: break
                msglen = struct.unpack(">I", raw_msglen)[0]
                frame_data = self.recv_exact(conn, msglen)
                if not frame_data: break
                self.frames[ip] = frame_data
            except:
                break

    def update_frames(self):
        while self.running:
            selected = self.device_listbox.curselection()
            if selected:
                ip = self.device_listbox.get(selected[0])
                if ip in self.frames:
                    try:
                        img_data = self.frames[ip]
                        nparr = np.frombuffer(img_data, np.uint8)
                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(img)
                        img = ImageTk.PhotoImage(img)
                        
                        self.lbl_screen.config(image=img, text="")
                        self.lbl_screen.image = img
                    except:
                        pass
            time.sleep(0.05)

if __name__ == "__main__":
    if os.name == 'nt' and not ctypes.windll.shell32.IsUserAnAdmin():
        console.print("[bold red]LỖI: Tool yêu cầu quyền Administrator![/]")
        console.print("Vui lòng chuột phải CMD -> Run as Administrator.")
        sys.exit(1)

    os.system('cls' if os.name == 'nt' else 'clear')
    console.print(BANNER)
    
    mode = Prompt.ask("\n[bold cyan]Chọn chế độ chạy[/]", choices=["master", "agent"], default="master")
    
    if mode == "master":
        local_ip = get_local_ip()
        console.print("\n" + "="*50)
        console.print(f"[bold green]IP MASTER CỦA BẠN LÀ: {local_ip}[/]")
        console.print("[yellow]Hãy nhập IP này vào máy Agent để kết nối.[/]")
        console.print("="*50)
        
        Prompt.ask("\n[dim]Nhấn Enter để mở giao diện điều khiển...[/]")
        
        root = tk.Tk()
        app = MinZMasterUI(root)
        root.mainloop()
    else:
        console.print("\n[bold cyan]Nhập IP của Master (máy quản lý)[/]")
        console.print("[dim]Bạn có thể xem IP này trên màn hình của máy Master.[/]")
        ip = Prompt.ask("[bold cyan]IP Master[/]")
        agent = MinZAgent(ip)
        agent.start()
