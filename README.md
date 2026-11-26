# MinZ Network v2.5

![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue)
![Engine](https://img.shields.io/badge/Engine-Socket%20%7C%20mss%20%7C%20tkinter-orange)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![Status](https://img.shields.io/badge/Status-Active%20%26%20Maintained-green)
![License](https://img.shields.io/badge/License-MIT-green)

**LAN Classroom Management & Remote Control Tool**

Quản lý và điều khiển các máy tính trong cùng mạng LAN nội bộ. Có khả năng xem màn hình trực tiếp (Live View), khóa chuột/phím (Lock Input), tự động quét thiết bị trong mạng.

---

### ⚠️ Cảnh báo bảo mật — Đọc trước khi chạy

- Công cụ này cho phép chiếm quyền điều khiển máy tính khác.
- **Chỉ sử dụng trong môi trường bạn sở hữu hoặc có sự cho phép** (như lớp học, phòng máy).
- Không sử dụng cho mục đích xâm nhập trái phép.
- Yêu cầu quyền **Administrator** trên cả máy Master và Agent.

---

### Yêu cầu hệ thống

| OS | Ghi chú | Trạng thái |
|---|---|---|
| **Windows 10 / 11** | Chạy bằng CMD (Run as Administrator) | Hỗ trợ đầy đủ |
| **Python** | 3.10 – 3.12+ | Cần thiết |
| **Thư viện** | `rich`, `pillow`, `mss`, `opencv-python` | Cài qua `requirements.txt` |

---

### Cài đặt

```bash
pip install -r requirements.txt
