import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime as dt
import uuid
import os

# Try to import pymongo; handle gracefully if not installed
try:
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
except Exception:
    PYMONGO_AVAILABLE = False

# ---------------------------- CONFIG ---------------------------- #
TAX_SGST = 0.09  # 9%
TAX_CGST = 0.09  # 9%
CURRENCY = "₹"
RESTAURANT_NAME = "Café Aura"

# Replace with your MongoDB URI if using Atlas or remote DB
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "cafe_aura"
COLLECTION_NAME = "orders"

# Extended Menu
MENU = {
    "Pizza": [
        ("Volcano Pizza", 200),
        ("Corn Pizza", 150),
        ("Onion Pizza", 180),
        ("Cheese Pizza", 250),
        ("Veg Pizza", 120),
    ],
    "Maggie": [
        ("Masala Maggie", 50),
        ("Cheese Maggie", 70),
        ("Veg Maggie", 60),
        ("Special Maggie", 80),
        ("Spicy Maggie", 90),
    ],
    "Burger": [
        ("Veg Burger", 99),
        ("Cheese Burger", 220),
        ("Chicken Burger", 250),
        ("Spicy Burger", 180),
        ("Double Cheese Burger", 300),
    ],
    "Sandwich": [
        ("Veg Sandwich", 120),
        ("Cheese Sandwich", 199),
        ("Grilled Sandwich", 150),
        ("Club Sandwich", 180),
        ("Special Sandwich", 250),
    ],
    "Drinks": [
        ("Cold Coffee", 120),
        ("Masala Chaas", 60),
        ("Fresh Lime Soda", 80),
        ("Iced Tea", 110),
        ("Mineral Water", 30),
    ],
    "Desserts": [
        ("Brownie", 140),
        ("Gulab Jamun", 90),
        ("Ice Cream", 100),
        ("Cheesecake", 220),
        ("Fruit Salad", 120),
    ],
    "Coffee & Shakes": [
        ("Espresso", 80),
        ("Cold Coffee (Large)", 160),
        ("Cappuccino", 130),
        ("Vanilla Shake", 140),
        ("Chocolate Shake", 150),
    ],
    "Fries & Sides": [
        ("Classic Fries", 90),
        ("Cheese Fries", 140),
        ("Garlic Bread", 80),
        ("Onion Rings", 100),
    ],
    "Pasta": [
        ("White Sauce Pasta", 180),
        ("Red Sauce Pasta", 160),
        ("Pesto Pasta", 200),
    ],
}

# ---------------------------- DB HELPERS ---------------------------- #
mongo_client = None
mongo_collection = None
mongo_connected = False

def connect_mongo():
    global mongo_client, mongo_collection, mongo_connected
    if not PYMONGO_AVAILABLE:
        mongo_connected = False
        return
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        mongo_client.server_info()  # force connection check
        db = mongo_client[DB_NAME]
        mongo_collection = db[COLLECTION_NAME]
        mongo_connected = True
    except Exception:
        mongo_client = None
        mongo_collection = None
        mongo_connected = False

def save_order_to_mongo(order_doc):
    """Return True if saved, False otherwise."""
    if not mongo_connected or mongo_collection is None:
        return False
    try:
        mongo_collection.insert_one(order_doc)
        return True
    except Exception:
        return False

def fetch_orders_from_mongo(limit=200):
    """Fetch recent orders sorted by datetime desc. Returns list of dicts."""
    if not mongo_connected or mongo_collection is None:
        return []
    try:
        cursor = mongo_collection.find().sort("datetime", -1).limit(limit)
        return list(cursor)
    except Exception:
        return []

# initial attempt to connect
connect_mongo()

# ---------------------------- APP ---------------------------- #
class CafeAuraApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{RESTAURANT_NAME} - POS")
        self.geometry("1150x720")
        self.minsize(1024, 640)

        self.order_id = self._new_order_id()
        self.cart = []  # list of dicts {name, price, qty}

        self._build_header()
        self._build_left()
        self._build_middle()
        self._build_right()

        first_cat = list(MENU.keys())[0]
        self.show_items(first_cat)
        self.category_list.selection_set(0)

    # ---------- UI BUILDERS ----------
    def _build_header(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill=tk.X)

        lbl = ttk.Label(top, text=f"{RESTAURANT_NAME} - ORDERING", font=("Segoe UI", 18, "bold"))
        lbl.pack(side=tk.LEFT)

        right = ttk.Frame(top)
        right.pack(side=tk.RIGHT)
        ttk.Label(right, text="Customer Name:").grid(row=0, column=0, sticky="e", padx=4)
        self.customer_name = ttk.Entry(right, width=22)
        self.customer_name.grid(row=0, column=1)
        ttk.Label(right, text="Phone:").grid(row=0, column=2, sticky="e", padx=4)
        self.customer_phone = ttk.Entry(right, width=16)
        self.customer_phone.grid(row=0, column=3)

        # Mongo status indicator
        self.mongo_status = ttk.Label(right, text=("DB: Connected" if mongo_connected else "DB: Not connected"),
                                      foreground=("green" if mongo_connected else "red"))
        self.mongo_status.grid(row=0, column=4, padx=8)

    def _build_left(self):
        left = ttk.Frame(self, padding=(10,0,10,10))
        left.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left, text="Categories", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.category_list = tk.Listbox(left, height=18)
        for cat in MENU.keys():
            self.category_list.insert(tk.END, cat)
        self.category_list.pack(fill=tk.Y, pady=6)
        self.category_list.bind("<<ListboxSelect>>", self.on_category_select)

        actions = ttk.Frame(left)
        actions.pack(fill=tk.X, pady=(10,0))
        ttk.Button(actions, text="New Order", command=self.new_order).pack(fill=tk.X, pady=3)
        ttk.Button(actions, text="Clear Cart", command=self.clear_cart).pack(fill=tk.X, pady=3)
        ttk.Button(actions, text="Checkout / Save Bill", command=self.checkout).pack(fill=tk.X, pady=3)
        ttk.Button(actions, text="View Old Orders", command=self.view_old_orders).pack(fill=tk.X, pady=6)

    def _build_middle(self):
        middle_wrap = ttk.Frame(self, padding=(0,0,10,10))
        middle_wrap.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(middle_wrap, text="Items", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        self.middle_canvas = tk.Canvas(middle_wrap, borderwidth=0)
        self.items_frame = ttk.Frame(self.middle_canvas)
        vsb = ttk.Scrollbar(middle_wrap, orient="vertical", command=self.middle_canvas.yview)
        self.middle_canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        self.middle_canvas.pack(side="left", fill="both", expand=True)

        self.middle_canvas.create_window((0,0), window=self.items_frame, anchor="nw")
        self.items_frame.bind("<Configure>", lambda e: self.middle_canvas.configure(scrollregion=self.middle_canvas.bbox("all")))

    def _build_right(self):
        right = ttk.Frame(self, padding=(0,0,10,10))
        right.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(right, text="Cart", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        columns = ("item","qty","price","total")
        self.cart_table = ttk.Treeview(right, columns=columns, show="headings", height=20)
        self.cart_table.heading("item", text="Item")
        self.cart_table.heading("qty", text="Qty")
        self.cart_table.heading("price", text=f"Price ({CURRENCY})")
        self.cart_table.heading("total", text=f"Total ({CURRENCY})")

        self.cart_table.column("item", width=220)
        self.cart_table.column("qty", width=50, anchor="center")
        self.cart_table.column("price", width=90, anchor="e")
        self.cart_table.column("total", width=100, anchor="e")

        self.cart_table.pack(fill=tk.Y, pady=6)

        btns = ttk.Frame(right)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="Remove Selected", command=self.remove_selected).pack(fill=tk.X, pady=3)
        ttk.Button(btns, text="Checkout / Save Bill", command=self.checkout).pack(fill=tk.X, pady=3)

        self.summary = ttk.LabelFrame(right, text="Bill Summary")
        self.summary.pack(fill=tk.X, pady=8)

        self.var_subtotal = tk.StringVar(value=f"{CURRENCY} 0.00")
        self.var_sgst = tk.StringVar(value=f"{CURRENCY} 0.00")
        self.var_cgst = tk.StringVar(value=f"{CURRENCY} 0.00")
        self.var_total = tk.StringVar(value=f"{CURRENCY} 0.00")

        self._row_summary(self.summary, 0, "Subtotal:", self.var_subtotal)
        self._row_summary(self.summary, 1, f"SGST ({int(TAX_SGST*100)}%):", self.var_sgst)
        self._row_summary(self.summary, 2, f"CGST ({int(TAX_CGST*100)}%):", self.var_cgst)
        ttk.Separator(self.summary).grid(row=3, column=0, columnspan=2, sticky="ew", pady=6)
        self._row_summary(self.summary, 4, "Grand Total:", self.var_total, bold=True)

    def _row_summary(self, parent, r, label, var, bold=False):
        ttk.Label(parent, text=label, font=("Segoe UI", 10, "bold" if bold else "normal")).grid(row=r, column=0, sticky="w", padx=8, pady=4)
        ttk.Label(parent, textvariable=var, font=("Segoe UI", 10, "bold" if bold else "normal")).grid(row=r, column=1, sticky="e", padx=8, pady=4)

    # ---------- Events ----------
    def on_category_select(self, event):
        selection = event.widget.curselection()
        if not selection:
            return
        idx = selection[0]
        category = event.widget.get(idx)
        self.show_items(category)

    def show_items(self, category):
        # Clear previous
        for child in self.items_frame.winfo_children():
            child.destroy()

        ttk.Label(self.items_frame, text=f"{category} Menu", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,6))
        ttk.Label(self.items_frame, text="Item").grid(row=1, column=0, sticky="w", padx=4)
        ttk.Label(self.items_frame, text="Price").grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(self.items_frame, text="Qty").grid(row=1, column=2, sticky="w", padx=4)
        ttk.Label(self.items_frame, text="Add").grid(row=1, column=3, sticky="w", padx=4)

        for r, (name, price) in enumerate(MENU[category], start=2):
            ttk.Label(self.items_frame, text=name, font=("Segoe UI", 10)).grid(row=r, column=0, sticky="w", padx=4, pady=2)
            ttk.Label(self.items_frame, text=f"{CURRENCY} {price}").grid(row=r, column=1, sticky="w", padx=4)

            qty_var = tk.IntVar(value=1)
            spin = ttk.Spinbox(self.items_frame, from_=1, to=50, width=5, textvariable=qty_var, justify="center")
            spin.grid(row=r, column=2, padx=4)

            def make_add_cmd(name=name, price=price, qty_var=qty_var):
                return lambda: self.add_to_cart(name, price, int(qty_var.get()))

            add_btn = ttk.Button(self.items_frame, text="Add", command=make_add_cmd())
            add_btn.grid(row=r, column=3, padx=4)

    # ---------- Cart Ops ----------
    def add_to_cart(self, name, price, qty):
        try:
            qty = int(qty)
        except ValueError:
            messagebox.showerror("Invalid Quantity", "Please enter a valid number.")
            return
        if qty < 1:
            messagebox.showwarning("Quantity", "Minimum quantity is 1.")
            return

        # merge if already exists
        for item in self.cart:
            if item['name'] == name and item['price'] == price:
                item['qty'] += qty
                break
        else:
            self.cart.append({"name": name, "price": price, "qty": qty})

        self._refresh_cart_table()
        self._update_totals()

    def remove_selected(self):
        sel = self.cart_table.selection()
        if not sel:
            messagebox.showinfo("Remove", "Please select an item in cart.")
            return
        index = int(sel[0])
        if 0 <= index < len(self.cart):
            del self.cart[index]
            self._refresh_cart_table()
            self._update_totals()

    def clear_cart(self):
        if not self.cart:
            return
        if messagebox.askyesno("Clear Cart", "Remove all items from cart?"):
            self.cart.clear()
            self._refresh_cart_table()
            self._update_totals()

    def _refresh_cart_table(self):
        for row in self.cart_table.get_children():
            self.cart_table.delete(row)
        for i, item in enumerate(self.cart):
            total = item['qty'] * item['price']
            self.cart_table.insert('', 'end', iid=str(i), values=(item['name'], item['qty'], f"{item['price']:.2f}", f"{total:.2f}"))

    def _update_totals(self):
        subtotal = sum(i['qty'] * i['price'] for i in self.cart)
        sgst = subtotal * TAX_SGST
        cgst = subtotal * TAX_CGST
        grand = subtotal + sgst + cgst

        self.var_subtotal.set(f"{CURRENCY} {subtotal:.2f}")
        self.var_sgst.set(f"{CURRENCY} {sgst:.2f}")
        self.var_cgst.set(f"{CURRENCY} {cgst:.2f}")
        self.var_total.set(f"{CURRENCY} {grand:.2f}")

    # ---------- Order Ops ----------
    def new_order(self):
        if self.cart and not messagebox.askyesno("New Order", "Start a new order? Current cart will be cleared."):
            return
        self.cart.clear()
        self._refresh_cart_table()
        self._update_totals()
        self.order_id = self._new_order_id()
        self.customer_name.delete(0, tk.END)
        self.customer_phone.delete(0, tk.END)
        messagebox.showinfo("New Order", f"New Order ID: {self.order_id}")

    def checkout(self):
        if not self.cart:
            messagebox.showwarning("Checkout", "Your cart is empty.")
            return

        subtotal = sum(i['qty'] * i['price'] for i in self.cart)
        sgst = subtotal * TAX_SGST
        cgst = subtotal * TAX_CGST
        grand = subtotal + sgst + cgst

        name = self.customer_name.get().strip() or "Guest"
        phone = self.customer_phone.get().strip() or "-"

        if not messagebox.askyesno("Confirm Order", f"Place order {self.order_id} for {name}?\nTotal: {CURRENCY} {grand:.2f}"):
            return

        receipt_text = self._build_receipt_text(name, phone, subtotal, sgst, cgst, grand)

        # Save order to MongoDB (best-effort)
        order_doc = {
            "order_id": self.order_id,
            "datetime": dt.datetime.now(),
            "customer_name": name,
            "phone": phone,
            "items": self.cart.copy(),
            "subtotal": subtotal,
            "sgst": sgst,
            "cgst": cgst,
            "grand_total": grand,
        }
        saved = save_order_to_mongo(order_doc)
        if saved:
            messagebox.showinfo("Order Saved", "Order saved to database.")
        else:
            if PYMONGO_AVAILABLE:
                messagebox.showwarning("DB", "Could not save order to DB (connection failed).")
            else:
                messagebox.showwarning("DB", "pymongo not installed; order not saved to DB.")

        # Show receipt window with Save option only (print removed)
        self._show_receipt_window(receipt_text)

    def _build_receipt_text(self, customer_name, phone, subtotal, sgst, cgst, grand):
        now = dt.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        lines = []
        lines.append("*" * 54)
        lines.append(f"\t\t{RESTAURANT_NAME.upper()}")
        lines.append("*" * 54)
        lines.append(f"Order ID : {self.order_id}")
        lines.append(f"Date/Time: {now}")
        lines.append(f"Customer : {customer_name}")
        lines.append(f"Phone    : {phone}")
        lines.append("-" * 54)
        lines.append(f"{'Item':28} {'Qty':>3} {'Price':>8} {'Total':>10}")
        lines.append("-" * 54)
        for item in self.cart:
            total = item['qty'] * item['price']
            name = (item['name'][:25] + '...') if len(item['name']) > 28 else item['name']
            lines.append(f"{name:28} {item['qty']:>3} {item['price']:>8.2f} {total:>10.2f}")
        lines.append("-" * 54)
        lines.append(f"Subtotal: {CURRENCY} {subtotal:.2f}")
        lines.append(f"SGST (9%): {CURRENCY} {sgst:.2f}")
        lines.append(f"CGST (9%): {CURRENCY} {cgst:.2f}")
        lines.append("=" * 54)
        lines.append(f"Grand Total: {CURRENCY} {grand:.2f}")
        lines.append("=" * 54)
        lines.append("Thank you for your order! Please visit again.")
        return "\n".join(lines)

    def _show_receipt_window(self, receipt_text):
        win = tk.Toplevel(self)
        win.title("Order Receipt")
        win.geometry("720x560")

        txt = tk.Text(win, wrap="word", font=("Consolas", 11))
        txt.insert("1.0", receipt_text)
        txt.config(state="disabled")
        txt.pack(fill=tk.BOTH, expand=True)

        btns = ttk.Frame(win)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="Save Receipt", command=lambda: self._save_receipt(receipt_text)).pack(side=tk.LEFT, padx=6, pady=6)
        ttk.Button(btns, text="New Order", command=lambda: [win.destroy(), self.new_order()]).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Close", command=win.destroy).pack(side=tk.RIGHT, padx=6)

    def _save_receipt(self, text):
        default_name = f"receipt_{self.order_id}.txt"
        file = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=default_name,
                                            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not file:
            return
        try:
            with open(file, "w", encoding="utf-8") as f:
                f.write(text)
            messagebox.showinfo("Saved", f"Receipt saved to:\n{file}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file.\n{e}")

    # ---------- Old Orders Viewer ----------
    def view_old_orders(self):
        if not PYMONGO_AVAILABLE:
            messagebox.showwarning("pymongo missing", "pymongo not installed; cannot fetch orders.\nInstall with: pip install pymongo")
            return
        if not mongo_connected:
            messagebox.showwarning("DB", "Not connected to MongoDB; cannot fetch orders.")
            return

        orders = fetch_orders_from_mongo(limit=500)
        win = tk.Toplevel(self)
        win.title("Old Orders - Cafe Aura")
        win.geometry("900x520")

        frame = ttk.Frame(win, padding=8)
        frame.pack(fill=tk.BOTH, expand=True)

        cols = ("order_id", "datetime", "customer_name", "phone", "grand_total")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        tree.heading("order_id", text="Order ID")
        tree.heading("datetime", text="Date/Time")
        tree.heading("customer_name", text="Customer")
        tree.heading("phone", text="Phone")
        tree.heading("grand_total", text=f"Total ({CURRENCY})")

        tree.column("order_id", width=120)
        tree.column("datetime", width=180)
        tree.column("customer_name", width=180)
        tree.column("phone", width=120)
        tree.column("grand_total", width=100, anchor="e")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill=tk.BOTH, expand=True)

        # Insert rows
        for o in orders:
            dt_val = o.get("datetime")
            if isinstance(dt_val, dt.datetime):
                dt_str = dt_val.strftime("%d-%m-%Y %H:%M:%S")
            else:
                dt_str = str(dt_val)
            tree.insert("", "end", values=(o.get("order_id", "-"), dt_str, o.get("customer_name", "-"), o.get("phone", "-"), f"{o.get('grand_total', 0):.2f}"))

        # Double-click to view details
        def on_double(ev):
            sel = tree.selection()
            if not sel: return
            item = tree.item(sel[0])["values"]
            order_id = item[0]
            # fetch full order doc
            doc = mongo_collection.find_one({"order_id": order_id})
            if doc:
                self._show_order_details(doc)
            else:
                messagebox.showinfo("Order", "Order details not found.")

        tree.bind("<Double-1>", on_double)

    def _show_order_details(self, doc):
        win = tk.Toplevel(self)
        win.title(f"Order {doc.get('order_id', '')}")
        win.geometry("600x520")

        txt = tk.Text(win, wrap="word", font=("Consolas", 11))
        lines = []
        lines.append("*" * 54)
        lines.append(f"\t\t{RESTAURANT_NAME.upper()}")
        lines.append("*" * 54)
        lines.append(f"Order ID : {doc.get('order_id', '-')}")
        dt_val = doc.get("datetime")
        if isinstance(dt_val, dt.datetime):
            lines.append(f"Date/Time: {dt_val.strftime('%d-%m-%Y %H:%M:%S')}")
        else:
            lines.append(f"Date/Time: {dt_val}")
        lines.append(f"Customer : {doc.get('customer_name', '-')}")
        lines.append(f"Phone    : {doc.get('phone', '-')}")
        lines.append("-" * 54)
        lines.append(f"{'Item':28} {'Qty':>3} {'Price':>8} {'Total':>10}")
        lines.append("-" * 54)
        for item in doc.get("items", []):
            total = item.get("qty", 0) * item.get("price", 0)
            name = item.get("name", "")
            name_short = (name[:25] + '...') if len(name) > 28 else name
            lines.append(f"{name_short:28} {item.get('qty',0):>3} {item.get('price',0):>8.2f} {total:>10.2f}")
        lines.append("-" * 54)
        lines.append(f"Subtotal: {CURRENCY} {doc.get('subtotal', 0):.2f}")
        lines.append(f"SGST (9%): {CURRENCY} {doc.get('sgst', 0):.2f}")
        lines.append(f"CGST (9%): {CURRENCY} {doc.get('cgst', 0):.2f}")
        lines.append("=" * 54)
        lines.append(f"Grand Total: {CURRENCY} {doc.get('grand_total', 0):.2f}")
        lines.append("=" * 54)
        txt.insert("1.0", "\n".join(lines))
        txt.config(state="disabled")
        txt.pack(fill=tk.BOTH, expand=True)

    def _new_order_id(self):
        return uuid.uuid4().hex[:8].upper()

# ---------------------------- RUN ---------------------------- #
if __name__ == "__main__":
    # Optional: nicer ttk defaults
    try:
        from tkinter import font
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Treeview", rowheight=26)
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=10)
    except Exception:
        pass

    # Early warnings about pymongo / DB connection
    if not PYMONGO_AVAILABLE:
        root_warn = tk.Tk()
        root_warn.withdraw()
        messagebox.showwarning("pymongo missing", "pymongo not installed. Orders will not be saved to MongoDB.\nInstall with: pip install pymongo")
        root_warn.destroy()
    elif not mongo_connected:
        root_warn = tk.Tk()
        root_warn.withdraw()
        messagebox.showwarning("DB Conn", f"Could not connect to MongoDB at {MONGO_URI}. Orders will not be saved until connection is available.")
        root_warn.destroy()

    app = CafeAuraApp()
    app.mainloop()
