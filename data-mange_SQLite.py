import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import re
from datetime import datetime
from collections import Counter
import random
from tkcalendar import DateEntry
import sqlite3

def create_phone_data_tables():
    conn = sqlite3.connect("phone_data.db")
    cursor = conn.cursor()

    for i in range(1, 16):
        table_name = f"phone_data_set_{i}"
        cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT,
                    dataset_name TEXT,
                    receive_date TEXT,
                    source TEXT,
                    detail TEXT,
                    data_type TEXT,
                    is_exported INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    conn.commit()
    conn.close()

class PhoneDataManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Phone Data Manager")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f2f5")

        self.setup_styles()
        self.create_tabs()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TLabel", background="#f0f2f5", font=("Kanit", 10))
        style.configure("TButton", font=("Kanit", 10), padding=6)
        style.configure("TEntry", padding=6)
        style.configure("TCombobox", padding=6)

    def create_tabs(self):
        tab_control = ttk.Notebook(self.root)

        self.tab_import = ttk.Frame(tab_control)
        self.tab_manage = ttk.Frame(tab_control)
        self.tab_move = ttk.Frame(tab_control)
        self.tab_export = ttk.Frame(tab_control)
        self.tab_combine = ttk.Frame(tab_control)

        self.setup_manage_tab()
        self.setup_move_tab()
        self.setup_export_tab()
        # ฟังก์ชันนี้จะตั้งค่า UI สำหรับ tab "รวม 2 ไฟล์" โดยไม่มีคำสั่ง add()
        self.create_combine_tab(tab_control)

        # เรียงลำดับแท็บตามที่ต้องการ
        tab_control.add(self.tab_import, text="นำเข้าข้อมูล")
        tab_control.add(self.tab_manage, text="จัดการข้อมูล")
        tab_control.add(self.tab_move, text="ย้ายข้อมูล")
        tab_control.add(self.tab_export, text="ส่งออกข้อมูล")
        tab_control.add(self.tab_combine, text="รวม 2 ไฟล์")

        tab_control.pack(expand=1, fill='both')

        self.setup_import_tab()

    def create_combine_tab(self, tab_control):
        frame = tk.Frame(self.tab_combine, bg="#f0f2f5")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.combine_file1 = tk.StringVar()
        self.combine_file2 = tk.StringVar()

        def browse_file(var):
            path = filedialog.askopenfilename(
                filetypes=[("Text Files", "*.txt")])
            if path:
                var.set(path)

        def combine_and_save():
            if not self.combine_file1.get() or not self.combine_file2.get():
                messagebox.showerror("Error", "กรุณาเลือกไฟล์ทั้งสองไฟล์ก่อน")
                return
            save_path = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
            if not save_path:
                return
            try:
                with open(self.combine_file1.get(), 'r', encoding='utf-8') as f1, \
                        open(self.combine_file2.get(), 'r', encoding='utf-8') as f2:
                    lines = [line.strip() for line in f1 if line.strip()] + \
                        [line.strip() for line in f2 if line.strip()]
                random.shuffle(lines)
                with open(save_path, 'w', encoding='utf-8') as fout:
                    fout.write('\n'.join(lines))
                messagebox.showinfo(
                    "Success", f"รวมไฟล์เรียบร้อยแล้ว\nบันทึกที่: {save_path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Label(frame, text="เลือกไฟล์ที่ 1:", bg="#f0f2f5",
                 font=("Kanit", 10)).pack(pady=(10, 0), anchor='w')
        tk.Entry(frame, textvariable=self.combine_file1, width=80).pack()
        ttk.Button(frame, text="เลือกไฟล์ที่ 1", command=lambda: browse_file(
            self.combine_file1)).pack(pady=(0, 10))

        tk.Label(frame, text="เลือกไฟล์ที่ 2:", bg="#f0f2f5",
                 font=("Kanit", 10)).pack(anchor='w')
        tk.Entry(frame, textvariable=self.combine_file2, width=80).pack()
        ttk.Button(frame, text="เลือกไฟล์ที่ 2", command=lambda: browse_file(
            self.combine_file2)).pack(pady=(0, 10))

        ttk.Button(frame, text="รวมและบันทึก",
                   command=combine_and_save).pack(pady=20)

    def setup_move_tab(self):
        frame = tk.Frame(self.tab_move, bg="#f0f2f5")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Source table dropdown
        top_frame = tk.Frame(frame, bg="#f0f2f5")
        top_frame.pack(fill=tk.X, pady=10)

        tk.Label(top_frame, text="เลือก Table ต้นทาง:",
                 bg="#f0f2f5", font=("Kanit", 10)).pack(side=tk.LEFT)
        self.move_source_table_var = tk.StringVar()
        self.move_source_combo = ttk.Combobox(top_frame, textvariable=self.move_source_table_var, state="readonly",
                                              values=[f"phone_data_set_{i}" for i in range(1, 16)], width=25)
        self.move_source_combo.pack(side=tk.LEFT, padx=10)
        self.move_source_combo.bind(
            "<<ComboboxSelected>>", self.load_datasets_from_source)

        # Dataset list (checkboxes)
        self.dataset_checkbox_frame = tk.Frame(
            frame, bg="#ffffff", bd=1, relief="solid")
        self.dataset_checkbox_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Destination table dropdown
        dest_frame = tk.Frame(frame, bg="#f0f2f5")
        dest_frame.pack(fill=tk.X)

        tk.Label(dest_frame, text="เลือก Table ปลายทาง:",
                 bg="#f0f2f5", font=("Kanit", 10)).pack(side=tk.LEFT)
        self.move_dest_table_var = tk.StringVar()
        self.move_dest_combo = ttk.Combobox(dest_frame, textvariable=self.move_dest_table_var, state="readonly",
                                            values=[f"phone_data_set_{i}" for i in range(1, 16)], width=25)
        self.move_dest_combo.pack(side=tk.LEFT, padx=10)

        # Checkbox: ลบข้อมูลต้นทางหลังย้าย
        self.delete_after_move_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            frame,
            text="ลบข้อมูลต้นทางหลังย้าย",
            variable=self.delete_after_move_var,
            bg="#f0f2f5",
            font=("Kanit", 10)
        ).pack(pady=(0, 10))

        ttk.Button(frame, text="ย้ายข้อมูลที่เลือก",
                   command=self.move_selected_datasets).pack(pady=10)
        
    def get_db_connection(self):
        return sqlite3.connect("phone_data.db")

    def load_datasets_from_source(self, event=None):
        for widget in self.dataset_checkbox_frame.winfo_children():
            widget.destroy()

        table = self.move_source_table_var.get()
        if not table:
            return

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT DISTINCT dataset_name FROM {table}")
            dataset_names = [row[0] for row in cursor.fetchall()]
            conn.close()

            self.dataset_vars = {}
            for name in dataset_names:
                var = tk.BooleanVar()
                cb = tk.Checkbutton(self.dataset_checkbox_frame, text=name, variable=var,
                                    bg="#ffffff", font=("Kanit", 10), anchor='w', justify='left')
                cb.pack(fill=tk.X, padx=10, pady=2, anchor='w')
                self.dataset_vars[name] = var

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def move_selected_datasets(self):
        source_table = self.move_source_table_var.get()
        dest_table = self.move_dest_table_var.get()

        if not source_table or not dest_table:
            messagebox.showerror("Error", "กรุณาเลือก Table ต้นทางและปลายทาง")
            return
        if source_table == dest_table:
            messagebox.showerror(
                "Error", "ต้นทางและปลายทางต้องไม่ใช่ Table เดียวกัน")
            return

        selected_datasets = [name for name,
                             var in self.dataset_vars.items() if var.get()]
        if not selected_datasets:
            messagebox.showerror("Error", "กรุณาเลือกชุดข้อมูลที่ต้องการย้าย")
            return

        delete_after_move = self.delete_after_move_var.get()

        # Progress Window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("กำลังย้ายข้อมูล...")
        progress_window.geometry("400x100")
        tk.Label(progress_window, text="กำลังย้ายข้อมูลระหว่าง Table...",
                 font=("Kanit", 10)).pack(pady=(10, 5))
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_window, maximum=100, variable=progress_var)
        progress_bar.pack(fill=tk.X, padx=20, pady=5)
        status_label = tk.Label(progress_window, text="", font=("Kanit", 9))
        status_label.pack()
        progress_window.update()

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            total_moved = 0
            for idx, dataset in enumerate(selected_datasets):
                cursor.execute(f"""
                    SELECT phone_number, dataset_name, receive_date, source, detail, data_type, created_at, is_exported
                    FROM {source_table} WHERE dataset_name = ?
                """, (dataset,))
                records = cursor.fetchall()

                if records:
                    insert_query = f"""
                        INSERT INTO {dest_table}
                        (phone_number, dataset_name, receive_date, source, detail, data_type, created_at, is_exported)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """

                    batch_size = 1000
                    for i in range(0, len(records), batch_size):
                        batch = records[i:i+batch_size]
                        cursor.executemany(insert_query, batch)
                        conn.commit()
                        total_moved += len(batch)

                    # ลบต้นทางเฉพาะเมื่อเลือกให้ลบ
                    if delete_after_move:
                        cursor.execute(
                            f"DELETE FROM {source_table} WHERE dataset_name = ?", (dataset,))
                        conn.commit()

                percent = ((idx + 1) / len(selected_datasets)) * 100
                progress_var.set(percent)
                status_label.config(
                    text=f"ย้าย {dataset} แล้ว ({idx+1}/{len(selected_datasets)})")
                progress_window.update()

            conn.close()
            progress_window.destroy()

            if delete_after_move:
                messagebox.showinfo(
                    "Success", f"ย้ายข้อมูลเรียบร้อยแล้ว ({total_moved} เบอร์)")
            else:
                messagebox.showinfo(
                    "Success", f"คัดลอกข้อมูลเรียบร้อยแล้ว ({total_moved} เบอร์)")

            self.load_datasets_from_source()

        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("Database Error", str(e))

    def reset_manage_filters(self):
        self.search_phone_var.set("")
        self.search_dataset_var.set("")
        self.load_manage_data()

    def load_manage_data(self):
        table = self.manage_table_var.get()
        phone_filter = self.search_phone_var.get().strip()
        dataset_filter = self.search_dataset_var.get().strip()
        date_from = self.search_date_from_var.get().strip()
        date_to = self.search_date_to_var.get().strip()

        # ปรับวันที่ให้อยู่ในรูปแบบที่ MySQL ต้องการ (YYYY-MM-DD)
        try:
            if date_from:
                date_from = datetime.strptime(
                    date_from, "%m/%d/%y").strftime("%Y-%m-%d")
            if date_to:
                date_to = datetime.strptime(
                    date_to, "%m/%d/%y").strftime("%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "กรุณากรอกวันที่ในรูปแบบ MM/DD/YY")
            return

        if not table:
            return

        # Progress Window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("กำลังค้นหาข้อมูล...")
        progress_window.geometry("400x100")
        progress_window.resizable(False, False)
        tk.Label(progress_window, text="กำลังดึงข้อมูลจากฐานข้อมูล...",
                 font=("Kanit", 10)).pack(pady=(10, 5))

        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_window, maximum=100, variable=progress_var)
        progress_bar.pack(fill=tk.X, padx=20, pady=5)

        progress_status = tk.Label(progress_window, text="", font=("Kanit", 9))
        progress_status.pack()
        progress_window.update()

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            query = f"""
                SELECT id, phone_number, dataset_name, receive_date, source, data_type, created_at
                FROM {table} WHERE 1
            """
            params = []

            if phone_filter:
                query += " AND phone_number LIKE ?"
                params.append(f"%{phone_filter}%")
            if dataset_filter:
                query += " AND dataset_name LIKE ?"
                params.append(f"%{dataset_filter}%")
            if date_from:
                query += " AND receive_date >= ?"
                params.append(date_from)
            if date_to:
                query += " AND receive_date <= ?"
                params.append(date_to)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            progress_var.set(50)
            progress_status.config(text="กำลังแสดงข้อมูล...")
            progress_window.update()

            for i in self.tree.get_children():
                self.tree.delete(i)

            for row in rows:
                self.tree.insert("", "end", values=row)

            progress_var.set(80)
            progress_status.config(text="กำลังตรวจสอบเบอร์ซ้ำ...")
            progress_window.update()

            # ตรวจสอบเบอร์ซ้ำ
            phone_numbers = [row[1] for row in rows]
            duplicate_count = sum(
                count > 1 for count in Counter(phone_numbers).values())

            total_count = len(rows)
            self.count_label.config(
                text=f"แสดงทั้งหมด {total_count} รายการ, ซ้ำ {duplicate_count} รายการ"
            )

            progress_var.set(100)
            progress_status.config(text="เสร็จสิ้น")
            progress_window.update()
            progress_window.destroy()

            conn.close()

        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("Database Error", str(e))

    def setup_export_tab(self):
        frame = tk.Frame(self.tab_export, bg="#f0f2f5")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # เลือก table
        top_frame = tk.Frame(frame, bg="#f0f2f5")
        top_frame.pack(fill=tk.X, pady=10)
        tk.Label(top_frame, text="เลือก Table:", bg="#f0f2f5",
                 font=("Kanit", 10)).pack(side=tk.LEFT)
        self.export_table_var = tk.StringVar()
        table_combo = ttk.Combobox(top_frame, textvariable=self.export_table_var, state="readonly",
                                   values=[f"phone_data_set_{i}" for i in range(1, 16)], width=25)
        table_combo.pack(side=tk.LEFT, padx=10)
        table_combo.bind("<<ComboboxSelected>>", self.load_export_datasets)

        # กรอบชุดข้อมูล
        self.export_dataset_frame = tk.Frame(
            frame, bg="#ffffff", bd=1, relief="solid")
        self.export_dataset_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        ttk.Button(frame, text="ส่งออก",
                   command=self.export_selected_datasets).pack(pady=(5, 5))

        # แทรกเบอร์สุ่ม
        self.inject_extra_var = tk.BooleanVar(value=False)
        inject_check = tk.Checkbutton(
            frame, text="สุ่มแทรกเบอร์จากไฟล์อื่นเข้าไปด้วย",
            variable=self.inject_extra_var, bg="#f0f2f5", font=("Kanit", 10),
            command=self.toggle_inject_extra_file
        )
        inject_check.pack(anchor="w")

        self.inject_file_path = None
        ttk.Button(frame, text="เลือกไฟล์เบอร์ที่จะสุ่มแทรก",
                   command=self.choose_inject_file).pack(anchor="w", pady=(5, 10))

    def export_selected_datasets(self):
        selected_data = []
        for name, var in self.export_dataset_vars.items():
            if var.get():
                entry, entry_var, exportable = self.export_entry_vars[name]
                try:
                    requested = int(entry_var.get())
                except:
                    requested = 0

                if requested <= 0:
                    continue

                if requested > exportable:
                    self.export_warnings[name].config(
                        text="จำนวนที่ต้องการนำออกเยอะเกิน จะนำข้อมูลที่เคยนำออกไปแล้วนำออกไปด้วย")
                else:
                    self.export_warnings[name].config(text="")

                selected_data.append((name, requested))

        if not selected_data:
            messagebox.showwarning(
                "ไม่พบข้อมูล", "กรุณาเลือกชุดข้อมูลและระบุจำนวนที่ต้องการส่งออก")
            return

        table = self.export_table_var.get()
        if not table:
            messagebox.showerror("Error", "กรุณาเลือก Table")
            return

        total = sum(r for _, r in selected_data)

        # เลือก path สำหรับบันทึก .txt
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")],
            title="บันทึกไฟล์ส่งออก"
        )
        if not file_path:
            return

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            all_numbers = []

            for dataset_name, limit in selected_data:
                cursor.execute(f"""
                    SELECT id, phone_number FROM {table}
                    WHERE dataset_name = ?
                    ORDER BY is_exported ASC, id ASC
                    LIMIT ?
                """, (dataset_name, limit))
                results = cursor.fetchall()
                ids = [row[0] for row in results]
                numbers = [row[1] for row in results]
                all_numbers.extend(numbers)

                # อัปเดต is_exported = 1
                if ids:
                    cursor.execute(
                        f"UPDATE {table} SET is_exported = 1 WHERE id IN ({','.join(['?'] * len(ids))})", ids
                    )
                    conn.commit()

            conn.close()

            # หากเปิดใช้งานแทรกเบอร์เพิ่มเติม
            if self.inject_extra_var.get() and self.inject_file_path:
                try:
                    with open(self.inject_file_path, "r", encoding="utf-8") as f:
                        injected_numbers = [line.strip()
                                            for line in f if line.strip()]
                    import random
                    for num in injected_numbers:
                        insert_index = random.randint(0, len(all_numbers))
                        all_numbers.insert(insert_index, num)
                except Exception as e:
                    messagebox.showerror(
                        "Error", f"เกิดข้อผิดพลาดขณะโหลดเบอร์เพิ่มเติม: {str(e)}")
                    return

            # บันทึกเป็นไฟล์ .txt
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(all_numbers))

            messagebox.showinfo(
                "สำเร็จ", f"ส่งออกทั้งหมด {len(all_numbers):,} เบอร์เรียบร้อยแล้ว\n\nบันทึกไว้ที่:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def load_export_datasets(self, event=None):
        for widget in self.export_dataset_frame.winfo_children():
            widget.destroy()

        table = self.export_table_var.get()
        if not table:
            return

        self.export_dataset_vars = {}
        self.export_entry_vars = {}
        self.export_warnings = {}

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT dataset_name,
                    COUNT(*) AS total,
                    SUM(CASE WHEN is_exported = 0 THEN 1 ELSE 0 END) AS exportable
                FROM {table}
                GROUP BY dataset_name
            """)
            results = cursor.fetchall()
            conn.close()

            for name, total, exportable in results:
                row = tk.Frame(self.export_dataset_frame, bg="#ffffff")
                row.pack(fill=tk.X, padx=10, pady=3)

                var = tk.BooleanVar()
                cb = tk.Checkbutton(row, text=f"{name} (ทั้งหมด {total:,}/นำออกได้ {exportable:,})",
                                    variable=var, bg="#ffffff", font=("Kanit", 10),
                                    command=lambda n=name: self.toggle_export_input(n))
                cb.pack(side=tk.LEFT)

                entry_var = tk.StringVar()
                entry = ttk.Entry(
                    row, width=10, textvariable=entry_var, state='disabled')
                entry.pack(side=tk.LEFT, padx=10)

                warning = tk.Label(row, text="", fg="red",
                                   bg="#ffffff", font=("Kanit", 9))
                warning.pack(side=tk.LEFT)

                self.export_dataset_vars[name] = var
                self.export_entry_vars[name] = (entry, entry_var, exportable)
                self.export_warnings[name] = warning

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def toggle_export_input(self, name):
        var = self.export_dataset_vars[name]
        entry, entry_var, _ = self.export_entry_vars[name]
        if var.get():
            entry.configure(state='normal')
        else:
            entry.configure(state='disabled')
            entry_var.set("")
            self.export_warnings[name].config(text="")

    def export_selected_data(self):
        selected = self.export_table.get_children()
        data_type = self.export_data_type_var.get()
        only_new = self.only_new_export_var.get()
        export_results = []

        for row in selected:
            dataset_name, table, total, export_count = self.export_table.item(row)[
                "values"]
            try:
                export_count = int(export_count)
            except:
                continue
            if export_count <= 0:
                continue

            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                # ดึงเบอร์ที่ต้องการ
                query = f"""
                    SELECT id, phone_number FROM {table}
                    WHERE dataset_name = ? AND data_type = ?
                """
                params = [dataset_name, data_type]
                if only_new:
                    query += " AND is_exported = 0"
                query += f" LIMIT {export_count}"
                params.append(export_count)
                cursor.execute(query, params)
                rows = cursor.fetchall()

                # update is_exported = 1
                ids = [row[0] for row in rows]
                if ids:
                    id_str = ",".join(str(i) for i in ids)
                    cursor.execute(
                        f"UPDATE {table} SET is_exported = 1 WHERE id IN ({id_str})")
                    conn.commit()
                    export_results.extend([row[1] for row in rows])

                conn.close()
            except Exception as e:
                messagebox.showerror("Export Error", str(e))
                return

        # บันทึกเป็นไฟล์ .txt
        if export_results:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(export_results))
                messagebox.showinfo(
                    "Success", f"ส่งออก {len(export_results)} เบอร์เรียบร้อยแล้ว")

        else:
            messagebox.showwarning(
                "ไม่มีข้อมูล", "ไม่มีข้อมูลที่ตรงตามเงื่อนไขที่ต้องการส่งออก")

    def toggle_inject_extra_file(self):
        if not self.inject_extra_var.get():
            self.inject_file_path = None

    def choose_inject_file(self):
        if self.inject_extra_var.get():
            path = filedialog.askopenfilename(
                filetypes=[("Text Files", "*.txt")])
            if path:
                self.inject_file_path = path

    def setup_manage_tab(self):
        frame = tk.Frame(self.tab_manage, bg="#f0f2f5")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        filter_frame = tk.Frame(frame, bg="#f0f2f5")
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(filter_frame, text="เลือกชุดข้อมูล (Table):",
                 bg="#f0f2f5", font=("Kanit", 10)).pack(side=tk.LEFT)
        self.manage_table_var = tk.StringVar()
        self.manage_table_combo = ttk.Combobox(filter_frame, textvariable=self.manage_table_var, state="readonly",
                                               values=[f"phone_data_set_{i}" for i in range(1, 16)], width=25)
        self.manage_table_combo.set("")  # ไม่เลือกค่าเริ่มต้น
        self.manage_table_combo.pack(side=tk.LEFT, padx=5)

        tk.Label(filter_frame, text="ค้นหาเบอร์:", bg="#f0f2f5",
                 font=("Kanit", 10)).pack(side=tk.LEFT, padx=(10, 0))
        self.search_phone_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.search_phone_var,
                  width=20).pack(side=tk.LEFT, padx=5)

        tk.Label(filter_frame, text="ชื่อชุดข้อมูล:", bg="#f0f2f5",
                 font=("Kanit", 10)).pack(side=tk.LEFT, padx=(10, 0))
        self.search_dataset_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.search_dataset_var,
                  width=20).pack(side=tk.LEFT, padx=5)

        # เพิ่มฟิลด์สำหรับเลือกวันที่
        tk.Label(filter_frame, text="เลือกวันที่ (ตั้งแต่):", bg="#f0f2f5",
                 font=("Kanit", 10)).pack(side=tk.LEFT, padx=(10, 0))
        self.search_date_from_var = tk.StringVar()
        self.search_date_from_entry = DateEntry(filter_frame, textvariable=self.search_date_from_var,
                                                width=20, background='darkblue', foreground='white', borderwidth=2)
        self.search_date_from_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(filter_frame, text="ถึงวันที่:", bg="#f0f2f5",
                 font=("Kanit", 10)).pack(side=tk.LEFT, padx=(10, 0))
        self.search_date_to_var = tk.StringVar()
        self.search_date_to_entry = DateEntry(filter_frame, textvariable=self.search_date_to_var,
                                              width=20, background='darkblue', foreground='white', borderwidth=2)
        self.search_date_to_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(filter_frame, text="ค้นหา", command=self.load_manage_data).pack(
            side=tk.LEFT, padx=10)
        ttk.Button(filter_frame, text="รีเซ็ต",
                   command=self.reset_manage_filters).pack(side=tk.LEFT)

        columns = ("id", "phone_number", "dataset_name",
                   "receive_date", "source", "data_type", "created_at")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=120)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.count_label = tk.Label(
            frame, text="แสดงทั้งหมด 0 รายการ, ซ้ำ 0 รายการ", bg="#f0f2f5", font=("Kanit", 10, "italic"))
        self.count_label.pack(anchor='w', pady=(5, 0))

        self.load_manage_data()

    def setup_import_tab(self):
        main_frame = tk.Frame(self.tab_import, bg="#f0f2f5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        left_frame = tk.Frame(main_frame, bg="#ffffff",
                              bd=1, relief="solid", width=300)
        center_frame = tk.Frame(main_frame, bg="#ffffff", bd=1, relief="solid")
        right_frame = tk.Frame(main_frame, bg="#ffffff",
                               bd=1, relief="solid", width=300)

        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Left: Split into top and bottom
        top_left_frame = tk.Frame(left_frame, bg="#ffffff")
        bottom_left_frame = tk.Frame(left_frame, bg="#ffffff")

        top_left_frame.pack(fill=tk.BOTH, expand=True)
        bottom_left_frame.pack(fill=tk.BOTH, expand=True)

        # Top Left: เบอร์ซ้ำในฐานข้อมูล
        tk.Label(top_left_frame, text="เบอร์ซ้ำในฐานข้อมูล", bg="#ffffff",
                 fg="#1877f2", font=("Kanit", 12, "bold")).pack(pady=5)
        self.duplicate_box = ScrolledText(
            top_left_frame, width=35, height=17, font=("Kanit", 9))
        self.duplicate_box.pack(padx=5, pady=(0, 10))

        # Bottom Left: เบอร์ซ้ำในไฟล์
        tk.Label(bottom_left_frame, text="เบอร์ซ้ำกันเองในไฟล์", bg="#ffffff",
                 fg="#dc3545", font=("Kanit", 12, "bold")).pack(pady=5)
        self.file_duplicate_box = ScrolledText(
            bottom_left_frame, width=35, height=17, font=("Kanit", 9))
        self.file_duplicate_box.pack(padx=5, pady=(0, 10))

        # Right: All Numbers
        tk.Label(right_frame, text="เบอร์ที่จะนำเข้า", bg="#ffffff",
                 fg="#1877f2", font=("Kanit", 12, "bold")).pack(pady=10)
        self.preview_box = ScrolledText(
            right_frame, width=35, height=35, font=("Kanit", 9))
        self.preview_box.pack(padx=5, pady=(0, 10))

        # Center: Form
        tk.Label(center_frame, text="รายละเอียดข้อมูล", bg="#ffffff",
                 fg="#1877f2", font=("Kanit", 14, "bold")).pack(pady=15)

        self.create_labeled_entry(
            center_frame, "ชื่อชุดข้อมูล", "entry_dataset")

        # ใช้ DateEntry สำหรับเลือกวันที่ได้รับเบอร์
        tk.Label(center_frame, text="วันที่ได้รับเบอร์:", bg="#ffffff",
                 font=("Kanit", 10)).pack(pady=(0, 2))
        self.entry_date = DateEntry(center_frame, width=20,
                                    background='darkblue', foreground='white', borderwidth=2)
        self.entry_date.pack(pady=(0, 10))

        self.create_labeled_entry(
            center_frame, "แหล่งที่มาของข้อมูล", "entry_source")
        self.create_labeled_textarea(center_frame, "รายละเอียด", "text_detail")
        self.create_labeled_combobox(
            center_frame, "ประเภทข้อมูล", "data_type_var", ['องค์กร', 'ภายนอก'])
        self.create_labeled_combobox(center_frame, "เลือกชุดข้อมูล (Table)", "table_var", [
            f"phone_data_set_{i}" for i in range(1, 16)])

        ttk.Button(center_frame, text="เลือกไฟล์เบอร์โทร (.txt)",
                   command=self.load_files).pack(pady=(10, 5))
        ttk.Button(center_frame, text="บันทึกลงฐานข้อมูล",
                   command=self.save_to_database).pack(pady=(5, 10))

    def create_labeled_entry(self, parent, label_text, attr_name, default=""):
        tk.Label(parent, text=label_text, bg="#ffffff",
                 font=("Kanit", 10)).pack(pady=(0, 2))
        entry = ttk.Entry(parent, width=50)
        entry.insert(0, default)
        entry.pack(pady=(0, 10))
        setattr(self, attr_name, entry)

    def create_labeled_combobox(self, parent, label_text, attr_name, values):
        tk.Label(parent, text=label_text, bg="#ffffff",
                 font=("Kanit", 10)).pack(pady=(0, 2))
        var = tk.StringVar()
        dropdown = ttk.Combobox(parent, textvariable=var,
                                state="readonly", values=values, width=47)
        dropdown.current(0)
        dropdown.pack(pady=(0, 10))
        setattr(self, attr_name, var)

    def create_labeled_textarea(self, parent, label_text, attr_name):
        tk.Label(parent, text=label_text, bg="#ffffff",
                 font=("Kanit", 10)).pack(pady=(0, 2))
        textarea = ScrolledText(parent, width=50, height=4, font=("Kanit", 10))
        textarea.pack(pady=(0, 10))
        setattr(self, attr_name, textarea)

    def load_files(self):
        self.file_paths = filedialog.askopenfilenames(
            filetypes=[("Text Files", "*.txt")])
        self.phone_numbers = []

        self.preview_box.delete("1.0", tk.END)
        self.duplicate_box.delete("1.0", tk.END)
        self.file_duplicate_box.delete("1.0", tk.END)

        if not self.file_paths:
            return

        # Progress Window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("กำลังโหลดไฟล์เบอร์โทร...")
        progress_window.geometry("400x100")
        progress_window.resizable(False, False)
        tk.Label(progress_window, text="กำลังอ่านและวิเคราะห์ไฟล์...",
                 font=("Kanit", 10)).pack(pady=(10, 5))

        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_window, maximum=100, variable=progress_var)
        progress_bar.pack(fill=tk.X, padx=20, pady=5)

        progress_status = tk.Label(progress_window, text="", font=("Kanit", 9))
        progress_status.pack()
        progress_window.update()

        # Step 1: Load and normalize numbers
        raw_numbers = []
        total_lines = sum(
            1 for path in self.file_paths for _ in open(path, encoding='utf-8'))

        count = 0
        for file_path in self.file_paths:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    phone = line.strip()
                    phone = self.normalize_phone(phone)
                    if phone:
                        raw_numbers.append(phone)
                    count += 1
                    progress_percent = (count / total_lines) * 30  # 30% weight
                    progress_var.set(progress_percent)
                    progress_status.config(
                        text=f"กำลังโหลด {count} / {total_lines} บรรทัด")
                    progress_window.update()

        self.phone_numbers = raw_numbers
        self.preview_box.insert(tk.END, "\n".join(self.phone_numbers))

        # Step 2: Check duplicates in file (weight 20%)
        progress_status.config(text="กำลังตรวจสอบเบอร์ซ้ำในไฟล์...")
        progress_window.update()
        self.find_internal_duplicates()
        progress_var.set(50)
        progress_window.update()

        # Step 3: Check duplicates in DB (weight 50%)
        table = self.table_var.get()
        if table:
            progress_status.config(text="กำลังตรวจสอบเบอร์ซ้ำในฐานข้อมูล...")
            progress_window.update()
            self.duplicate_box.delete("1.0", tk.END)
            duplicates = []

            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()

                total = len(self.phone_numbers)
                batch_size = 1000
                for i in range(0, total, batch_size):
                    batch = self.phone_numbers[i:i+batch_size]
                    if not batch:
                        continue
                    format_strings = ','.join(['?'] * len(batch))
                    query = f'SELECT phone_number FROM "{table}" WHERE phone_number IN ({format_strings})'
                    cursor.execute(query, batch)
                    result = cursor.fetchall()
                    duplicates.extend([row[0] for row in result])

                    percent = 50 + ((i + len(batch)) / total) * \
                        50  # จาก 50 ถึง 100
                    progress_var.set(percent)
                    progress_status.config(
                        text=f"ตรวจสอบแล้ว {i + len(batch)} / {total} เบอร์")
                    progress_window.update()

                conn.close()
                self.duplicate_box.insert(tk.END, "\n".join(duplicates))
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("Database Error", str(e))
                return

        progress_window.destroy()

    def find_internal_duplicates(self):
        self.file_duplicate_box.delete("1.0", tk.END)
        counter = Counter(self.phone_numbers)
        internal_duplicates = [num for num,
                               count in counter.items() if count > 1]
        self.file_duplicate_box.insert(tk.END, "\n".join(internal_duplicates))

    def show_duplicates_preview(self):
        table = self.table_var.get()
        self.duplicate_box.delete("1.0", tk.END)
        duplicates = []

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            for phone in self.phone_numbers:
                cursor.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE phone_number = ?", (phone,))
                if cursor.fetchone()[0] > 0:
                    duplicates.append(phone)

            conn.close()
            self.duplicate_box.insert(tk.END, "\n".join(duplicates))
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def normalize_phone(self, phone):
        phone = re.sub(r'[^\d+]', '', phone)
        if phone.startswith('+66'):
            phone = '0' + phone[3:]
        elif phone.startswith('66'):
            phone = '0' + phone[2:]
        elif not phone.startswith('0'):
            phone = '0' + phone[-9:]
        return phone if re.match(r'^0\d{9}$', phone) else None

    def save_to_database(self):
        if not hasattr(self, 'phone_numbers') or not self.phone_numbers:
            messagebox.showerror("Error", "กรุณาเลือกไฟล์และโหลดเบอร์ก่อน")
            return

        table = self.table_var.get()
        dataset_name = self.entry_dataset.get().strip()

        receive_date = self.entry_date.get()
        if not receive_date:
            messagebox.showerror("Error", "กรุณากรอกวันที่ได้รับเบอร์")
            return

        try:
            receive_date = datetime.strptime(receive_date, "%m/%d/%y").strftime("%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "กรุณากรอกวันที่ในรูปแบบ MM/DD/YY")
            return

        source = self.entry_source.get().strip()
        detail = self.text_detail.get("1.0", tk.END).strip()
        data_type = self.data_type_var.get()

        if not dataset_name:
            messagebox.showerror("Error", "กรุณากรอกชื่อชุดข้อมูล")
            return

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            progress_window = tk.Toplevel(self.root)
            progress_window.title("กำลังบันทึกข้อมูล...")
            progress_window.geometry("400x100")
            progress_window.resizable(False, False)
            tk.Label(progress_window, text="กำลังนำเข้าข้อมูล กรุณารอสักครู่...", font=("Kanit", 10)).pack(pady=(10, 5))

            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_window, maximum=100, variable=progress_var)
            progress_bar.pack(fill=tk.X, padx=20, pady=5)

            progress_status = tk.Label(progress_window, text="", font=("Kanit", 9))
            progress_status.pack()
            progress_window.update()

            cursor.execute(f'SELECT phone_number FROM "{table}"')
            existing_numbers = set(row[0] for row in cursor.fetchall())

            new_entries = []
            duplicates = []
            times = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for phone in self.phone_numbers:
                if phone in existing_numbers:
                    duplicates.append(phone)
                else:
                    new_entries.append((
                        phone, dataset_name, receive_date, source, detail, data_type, times, 0
                    ))

            total = len(new_entries)
            batch_size = 1000

            for i in range(0, total, batch_size):
                batch = new_entries[i:i + batch_size]
                cursor.executemany(f"""
                    INSERT INTO {table} 
                    (phone_number, dataset_name, receive_date, source, detail, data_type, created_at, is_exported)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                conn.commit()

                percent = ((i + len(batch)) / total) * 100
                progress_var.set(percent)
                progress_status.config(text=f"นำเข้าแล้ว {i + len(batch)} / {total} เบอร์")
                progress_window.update()

            conn.close()
            progress_window.destroy()

            messagebox.showinfo(
                "Success",
                f"บันทึกข้อมูลเรียบร้อยแล้ว\nนำเข้า {len(new_entries)} เบอร์\nพบเบอร์ซ้ำ {len(duplicates)} รายการ"
            )

            self.preview_box.delete("1.0", tk.END)
            self.duplicate_box.delete("1.0", tk.END)
            self.file_duplicate_box.delete("1.0", tk.END)

        except Exception as e:
            messagebox.showerror("Database Error", str(e))



if __name__ == "__main__":
    create_phone_data_tables()
    root = tk.Tk()
    app = PhoneDataManager(root)
    root.mainloop()
