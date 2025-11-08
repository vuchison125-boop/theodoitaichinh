import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter import ttk
import json
import os

class BillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hóa đơn thanh toán")

        # Đường dẫn lưu dữ liệu (billing_data.json cùng thư mục script)
        self.data_file = os.path.join(os.path.dirname(__file__), "billing_data.json")

        # Danh sách phòng
        self.rooms = ["Phòng 101", "Phòng 102", "Phòng 103"]

        # Dữ liệu cho mỗi phòng: items, total_amount, total_paid, payment_status
        self.rooms_data = {
            room: {"items": [], "total_amount": 0.0, "total_paid": 0.0, "payment_status": "Unpaid"}
            for room in self.rooms
        }

        # Phòng đang làm việc
        self.current_room = tk.StringVar(value=self.rooms[0])

        # Tải dữ liệu từ file (nếu có)
        self.load_data()

        # Giao diện chọn phòng
        top = tk.Frame(root)
        top.pack(pady=8)

        # Nút "Quay lại" ở phía bên trái màn hình
        self.back_btn = tk.Button(top, text="🔙 Quay lại", width=12, command=self.close_interface, bg="white")
        self.back_btn.pack(side='left', padx=(5, 0))

        tk.Label(top, text="Chọn phòng thuê để thanh toán:").pack(side='left', padx=(10, 0))
        self.room_combo = ttk.Combobox(top, values=self.rooms, textvariable=self.current_room, state='readonly', width=18)
        self.room_combo.pack(side='left', padx=5)
        self.room_combo.bind("<<ComboboxSelected>>", self.on_room_changed)

        # Badge trạng thái thanh toán cạnh danh sách phòng
        self.status_badge = tk.Label(top, text="", width=14, relief="ridge", bd=2, bg="white")
        self.status_badge.pack(side='left', padx=(8,0))

        # Khung nút hành động (6 nút)
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=6)

        self.btn_rent = tk.Button(btn_frame, text="💼 Tiền thuê/phòng/tháng", width=22, command=self.add_rent, bg="white")
        self.btn_rent.grid(row=0, column=0, padx=5, pady=5)

        self.btn_edit_rent = tk.Button(btn_frame, text="🛠️ Sửa giá thuê", width=22, command=self.edit_rent, bg="white")
        self.btn_edit_rent.grid(row=0, column=1, padx=5, pady=5)

        self.btn_electric = tk.Button(btn_frame, text="⚡ Tiền điện", width=22, command=self.add_electric, bg="white")
        self.btn_electric.grid(row=0, column=2, padx=5, pady=5)

        self.btn_water = tk.Button(btn_frame, text="💧 Tiền nước", width=22, command=self.add_water, bg="white")
        self.btn_water.grid(row=1, column=0, padx=5, pady=5)

        self.btn_service = tk.Button(btn_frame, text="🧰 Dịch vụ khác", width=22, command=self.add_service, bg="white")
        self.btn_service.grid(row=1, column=1, padx=5, pady=5)

        self.btn_update = tk.Button(btn_frame, text="🧾 Cập nhật trạng thái thanh toán", width=22, command=self.update_payment_window, bg="white")
        self.btn_update.grid(row=1, column=2, padx=5, pady=5)

        self.reset_btn = tk.Button(root, text="Reset", command=self.reset, width=20, bg="white")
        self.reset_btn.pack(pady=5)

        # Khung hiển thị chi tiết và tổng quan
        summary_frame = tk.Frame(root)
        summary_frame.pack(padx=10, pady=10, fill='both', expand=True)

        self.items_text = tk.Text(summary_frame, height=12, width=70)
        self.items_text.pack(side='left', fill='both', expand=True)

        self.scroll = tk.Scrollbar(summary_frame, command=self.items_text.yview)
        self.scroll.pack(side='right', fill='y')
        self.items_text.config(yscrollcommand=self.scroll.set)

        self.status_label = tk.Label(root, text="", anchor='w', justify='left')
        self.status_label.pack(fill='x', padx=10, pady=5)

        # Đăng ký xử lý đóng cửa sổ để lưu lại
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.refresh_display()

    def close_interface(self):
        self.on_close()

    def on_close(self):
        # Lưu dữ liệu và đóng
        self.save_data()
        self.root.destroy()

    def on_room_changed(self, event):
        self.refresh_display()

    def _status_and_color_from(self, data):
        if data['total_amount'] == 0:
            return "Chưa tính toán", "#f1c40f"  # vàng
        if data.get('payment_status') == "Paid":
            return "Đã thanh toán", "#28a745"  # xanh lá
        if data.get('payment_status') == "Unpaid":
            return "Chưa thanh toán", "#dc3545"  # đỏ

    # 1) Thêm Tiền thuê/phòng (nhập một lần)
    def add_rent(self):
        room = self.current_room.get()
        data = self.rooms_data[room]
        if any(it['type'] == 'Rent' for it in data['items']):
            messagebox.showinfo("Thông báo", "Tiền thuê/phòng/tháng đã được thiết lập cho phòng này. Sử dụng 'Sửa giá thuê' để chỉnh sửa.")
            return
        amount = simpledialog.askfloat("Nhập Tiền thuê/phòng", "Nhập tiền thuê/phòng theo tháng (VND):", minvalue=0.0)
        if amount is None:
            return
        self._add_item(room, "Rent", amount, "Thuê/phòng theo tháng")

    # 2) Sửa giá thuê (chỉ khi Rent đã có)
    def edit_rent(self):
        room = self.current_room.get()
        data = self.rooms_data[room]
        rent_item = next((it for it in data['items'] if it['type'] == "Rent"), None)
        if not rent_item:
            messagebox.showinfo("Thông báo", "Chưa thiết lập giá thuê. Vui lòng nhấn 'Tiền thuê/phòng/tháng' trước.")
            return
        old = rent_item['amount']
        new = simpledialog.askfloat("Sửa giá thuê", f"Nhập lại giá thuê/phòng (VND) hiện tại {old:.0f}:", minvalue=0.0)
        if new is None:
            return
        delta = new - old
        rent_item['amount'] = new
        self.rooms_data[room]['total_amount'] += delta
        self.save_data()
        self.refresh_display()

    # 3) Tiền điện: nhập tiêu thụ -> *4000
    def add_electric(self):
        room = self.current_room.get()
        consumption = simpledialog.askfloat("Nhập Tiền điện", "Nhập số điện tiêu thụ (kWh):", minvalue=0.0)
        if consumption is None:
            return
        amount = consumption * 4000
        self._add_item(room, "Electricity", amount, f"Điện ({consumption} kWh)")

    # 4) Tiền nước: nhập tiêu thụ -> *30000
    def add_water(self):
        room = self.current_room.get()
        consumption = simpledialog.askfloat("Nhập Tiền nước", "Nhập số nước tiêu thụ (m3):", minvalue=0.0)
        if consumption is None:
            return
        amount = consumption * 30000
        self._add_item(room, "Water", amount, f"Nước ({consumption} m3)")

    # 5) Tiền dịch vụ khác: cố định 100000
    def add_service(self):
        room = self.current_room.get()
        amount = 100000
        self._add_item(room, "OtherService", amount, "Dịch vụ khác")

    # Thêm item vào phòng
    def _add_item(self, room, item_type, amount, description):
        item = {"type": item_type, "amount": amount, "description": description}
        self.rooms_data[room]['items'].append(item)
        self.rooms_data[room]['total_amount'] += amount
        self.save_data()
        self.refresh_display()

    # 6) Cập nhật trạng thái thanh toán
    def update_payment_window(self):
        room = self.current_room.get()
        data = self.rooms_data[room]
        types_present = {it['type'] for it in data['items']}
        required = {'Rent','Electricity','Water','OtherService'}
        if not required.issubset(types_present):
            messagebox.showinfo("Thông báo", "Cần nhập đủ 4 loại phí: Tiền thuê/phòng, Tiền điện, Tiền nước, Dịch vụ khác.")
            return

        remaining = data['total_amount'] - data['total_paid']
        if remaining <= 0 and data.get('payment_status') == "Paid":
            messagebox.showinfo("Thông báo", f"Phòng {room} đã thanh toán đầy đủ.")
            return

        win = tk.Toplevel(self.root)
        win.title("Cập nhật trạng thái thanh toán")
        win.geometry("360x210")

        tk.Label(win, text=f"Cập nhật trạng thái thanh toán cho {room}", font=('Arial', 12, 'bold')).pack(pady=6)

        status_frame = tk.Frame(win)
        status_frame.pack(pady=8)
        tk.Label(status_frame, text="Chọn trạng thái thanh toán:").pack()

        def set_paid():
            data['total_paid'] = max(data['total_paid'], data['total_amount'])
            data['payment_status'] = "Paid"
            win.destroy()
            self.save_data()
            self.refresh_display()
            messagebox.showinfo("Thông báo", f"Phòng {room} thanh toán thành công.")

        def set_unpaid():
            data['payment_status'] = "Unpaid"
            win.destroy()
            self.save_data()
            self.refresh_display()
            messagebox.showinfo("Thông báo", f"Phòng {room} đã được chuyển sang trạng thái chưa thanh toán.")

        btn_paid = tk.Button(win, text="✅ Đã thanh toán", width=16, command=set_paid, bg="white")
        btn_paid.pack(pady=6)

        btn_unpaid = tk.Button(win, text="❌ Chưa thanh toán", width=16, command=set_unpaid, bg="white")
        btn_unpaid.pack(pady=6)

    # Reset toàn bộ dữ liệu
    def reset(self):
        for r in self.rooms:
            self.rooms_data[r] = {"items": [], "total_amount": 0.0, "total_paid": 0.0, "payment_status": "Unpaid"}
        self.save_data()
        self.refresh_display()

    # Lưu dữ liệu ra file
    def save_data(self):
        data = {
            "rooms_data": self.rooms_data,
            "current_room": self.current_room.get()
        }
        try:
            dirpath = os.path.dirname(self.data_file)
            if dirpath and not os.path.exists(dirpath):
                os.makedirs(dirpath, exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Lưu dữ liệu thất bại:", e)

    # Nạp dữ liệu từ file (nếu có)
    def load_data(self):
        if not os.path.exists(self.data_file):
            return
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            rooms_data = saved.get("rooms_data")
            if isinstance(rooms_data, dict):
                for r in self.rooms:
                    if r in rooms_data:
                        self.rooms_data[r] = rooms_data[r]
            current = saved.get("current_room")
            if current in self.rooms:
                self.current_room.set(current)
        except Exception as e:
            print("Khởi tạo dữ liệu từ file thất bại:", e)

    # Hiển thị danh sách và trạng thái cho phòng đang chọn
    def refresh_display(self):
        room = self.current_room.get()
        data = self.rooms_data[room]
        self.items_text.config(state='normal')
        self.items_text.delete('1.0', tk.END)
        self.items_text.insert(tk.END, f"Phòng: {room}\n")
        self.items_text.insert(tk.END, "Danh sách khoản phí:\n")
        if not data['items']:
            self.items_text.insert(tk.END, "Chưa có khoản phí nào được thêm cho phòng này.\n")
        else:
            for idx, item in enumerate(data['items'], start=1):
                type_name_map = {
                    'Rent': 'Tiền thuê/phòng',
                    'Electricity': 'Tiền điện',
                    'Water': 'Tiền nước',
                    'OtherService': 'Dịch vụ khác'
                }
                display_type = type_name_map.get(item['type'], item['type'])
                self.items_text.insert(tk.END, f"{idx}. {display_type}: {item['amount']:.0f} VND - {item['description']}\n")
        self.items_text.config(state='disabled')

        status, color = self._status_and_color_from(data)
        self.status_badge.config(text=status, bg=color)

        balance = data['total_amount'] - data['total_paid']
        summary = (
            f"Tổng số tiền: {data['total_amount']:.0f} VND\n"
            f"Đã thanh toán:   {data['total_paid']:.0f} VND\n"
            f"Số nợ:      {max(balance,0):.0f} VND\n"
            f"Trạng thái:   {status}"
        )
        self.status_label.config(text=summary)

if __name__ == "__main__":
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()
