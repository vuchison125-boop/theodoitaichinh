import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter import ttk

class BillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rental Billing - Admin UI (Prototype)")

        # Danh sách phòng
        self.rooms = ["Phòng 101", "Phòng 102", "Phòng 103"]

        # Dữ liệu cho mỗi phòng: items, total_amount, total_paid, payment_status
        self.rooms_data = {
            room: {"items": [], "total_amount": 0.0, "total_paid": 0.0, "payment_status": "Unpaid"}
            for room in self.rooms
        }

        # Phòng đang làm việc
        self.current_room = tk.StringVar(value=self.rooms[0])

        # Giao diện chọn phòng
        top = tk.Frame(root)
        top.pack(pady=8)
        tk.Label(top, text="Chọn phòng thuê để thanh toán:").pack(side='left')
        self.room_combo = ttk.Combobox(top, values=self.rooms, textvariable=self.current_room, state='readonly', width=18)
        self.room_combo.pack(side='left', padx=5)
        self.room_combo.bind("<<ComboboxSelected>>", self.on_room_changed)

        # Badge trạng thái thanh toán cạnh danh sách phòng
        self.status_badge = tk.Label(top, text="", width=14, relief="ridge", bd=2)
        self.status_badge.pack(side='left', padx=(8,0))

        # Khung nút hành động (6 nút)
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=6)

        # Icons (emoji) làm "icon" cho từng nút
        self.btn_rent = tk.Button(btn_frame, text="💼 Tiền thuê/phòng/tháng", width=22, command=self.add_rent)
        self.btn_rent.grid(row=0, column=0, padx=5, pady=5)

        self.btn_edit_rent = tk.Button(btn_frame, text="🛠️ Sửa giá thuê", width=22, command=self.edit_rent)
        self.btn_edit_rent.grid(row=0, column=1, padx=5, pady=5)

        self.btn_electric = tk.Button(btn_frame, text="⚡ Tiền điện", width=22, command=self.add_electric)
        self.btn_electric.grid(row=0, column=2, padx=5, pady=5)

        self.btn_water = tk.Button(btn_frame, text="💧 Tiền nước", width=22, command=self.add_water)
        self.btn_water.grid(row=1, column=0, padx=5, pady=5)

        self.btn_service = tk.Button(btn_frame, text="🧰 Dịch vụ khác", width=22, command=self.add_service)
        self.btn_service.grid(row=1, column=1, padx=5, pady=5)

        self.btn_update = tk.Button(btn_frame, text="🧾 Cập nhật trạng thái thanh toán", width=22, command=self.update_payment_window)
        self.btn_update.grid(row=1, column=2, padx=5, pady=5)

        self.reset_btn = tk.Button(root, text="Reset", command=self.reset, width=20)
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

        self.refresh_display()

    def on_room_changed(self, event):
        self.refresh_display()

    def _status_and_color_from(self, data):
        # Xác định trạng thái và màu dựa trên dữ liệu phòng
        if data['total_amount'] == 0:
            return "No charges yet", "#f1c40f"  # vàng
        if data.get('payment_status') == "Paid":
            return "Paid", "#28a745"  # xanh lá
        if data.get('payment_status') == "Unpaid":
            return "Unpaid", "#dc3545"  # đỏ
        # Partial sẽ là màu cam/ vàng đậm
        if data['total_paid'] > 0 and data['total_paid'] < data['total_amount']:
            return "Partially Paid", "#f0ad4e"  # cam
        return "Unpaid", "#dc3545"

    # 1) Thêm Tiền thuê/phòng (nhập một lần)
    def add_rent(self):
        room = self.current_room.get()
        data = self.rooms_data[room]
        if any(it['type'] == 'Rent' for it in data['items']):
            messagebox.showinfo("Thông báo", "Rent đã được thiết lập cho phòng này. Sử dụng 'Sửa giá thuê' để chỉnh sửa.")
            return
        amount = simpledialog.askfloat("Nhập Tiền thuê/phòng", "Nhập tiền thuê/phòng theo tháng (VND):", minvalue=0.0)
        if amount is None:
            return
        self._add_item(room, "Rent", amount, "Monthly rent")

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
        self.refresh_display()

    # 3) Tiền điện: nhập tiêu thụ -> *4
    def add_electric(self):
        room = self.current_room.get()
        consumption = simpledialog.askfloat("Nhập Tiền điện", "Nhập số điện tiêu thụ (kWh):", minvalue=0.0)
        if consumption is None:
            return
        amount = consumption * 4
        self._add_item(room, "Electricity", amount, f"Điện ({consumption} kWh)")

    # 4) Tiền nước: nhập tiêu thụ -> *30
    def add_water(self):
        room = self.current_room.get()
        consumption = simpledialog.askfloat("Nhập Tiền nước", "Nhập số nước tiêu thụ (m3):", minvalue=0.0)
        if consumption is None:
            return
        amount = consumption * 30
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
        self.refresh_display()

    # 6) Cập nhật trạng thái thanh toán
    def update_payment_window(self):
        room = self.current_room.get()
        data = self.rooms_data[room]
        types_present = {it['type'] for it in data['items']}
        required = {'Rent','Electricity','Water','OtherService'}
        if not required.issubset(types_present):
            messagebox.showinfo("Thông báo", "Cần nhập đủ 4 loại phí: Rent, Electricity, Water, OtherService.")
            return

        remaining = data['total_amount'] - data['total_paid']
        if remaining <= 0 and data.get('payment_status') == "Paid":
            messagebox.showinfo("Thông báo", f"Phòng {room} đã thanh toán đầy đủ.")
            return

        win = tk.Toplevel(self.root)
        win.title("Cập nhật trạng thái thanh toán")
        win.geometry("360x210")

        tk.Label(win, text=f"Cập nhật trạng thái thanh toán cho {room}", font=('Arial', 12, 'bold')).pack(pady=6)

        # Thay vì nhập số tiền, hiện hai nút để đặt trạng thái
        status_frame = tk.Frame(win)
        status_frame.pack(pady=8)
        tk.Label(status_frame, text="Chọn trạng thái thanh toán:").pack()

        def set_paid():
            data['total_paid'] = max(data['total_paid'], data['total_amount'])
            data['payment_status'] = "Paid"
            win.destroy()
            self.refresh_display()
            messagebox.showinfo("Thông báo", f"Phòng {room} thanh toán thành công.")

        def set_unpaid():
            data['payment_status'] = "Unpaid"
            win.destroy()
            self.refresh_display()
            messagebox.showinfo("Thông báo", f"Phòng {room} đã được chuyển sang trạng thái chưa thanh toán.")

        btn_paid = tk.Button(win, text="✅ Đã thanh toán", width=16, command=set_paid)
        btn_paid.pack(pady=6)

        btn_unpaid = tk.Button(win, text="❌ Chưa thanh toán", width=16, command=set_unpaid)
        btn_unpaid.pack(pady=6)

    # Reset toàn bộ dữ liệu
    def reset(self):
        for r in self.rooms:
            self.rooms_data[r] = {"items": [], "total_amount": 0.0, "total_paid": 0.0, "payment_status": "Unpaid"}
        self.refresh_display()

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
                self.items_text.insert(tk.END, f"{idx}. {item['type']}: {item['amount']:.0f} VND - {item['description']}\n")
        self.items_text.config(state='disabled')

        # Cập nhật trạng thái tổng quan và màu badge
        status, color = self._status_and_color_from(data)
        self.status_badge.config(text=status, bg=color)

        balance = data['total_amount'] - data['total_paid']
        summary = (
            f"Total amount: {data['total_amount']:.0f} VND\n"
            f"Total paid:   {data['total_paid']:.0f} VND\n"
            f"Balance:      {max(balance,0):.0f} VND\n"
            f"Trạng thái:   {status}"
        )
        self.status_label.config(text=summary)

if __name__ == "__main__":
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()