import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import pymysql
from decimal import Decimal
import os, hashlib, binascii, csv

# ------------------- DATABASE CONFIG -------------------
DB_SETTINGS = {
    "host": "localhost",
    "user": "root",
    "passwd": "260604",
    "database": "FinanceProDB"
}

SALT_SIZE = 16
HASH_ITER = 120000


# ------------------- UTILITY FUNCTIONS -------------------
def db_connect():
    """Establish connection to MySQL database."""
    return pymysql.connect(**DB_SETTINGS, autocommit=True)


def hash_password(password, salt=None):
    """Hash password securely using PBKDF2."""
    if salt is None:
        salt = os.urandom(SALT_SIZE)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, HASH_ITER)
    return f"{binascii.hexlify(salt).decode()}:{binascii.hexlify(key).decode()}"


def verify_password(stored, provided):
    """Verify a password against the stored hash."""
    try:
        salt_hex, key_hex = stored.split(":")
        salt = binascii.unhexlify(salt_hex)
        expected = binascii.unhexlify(key_hex)
        test = hashlib.pbkdf2_hmac("sha256", provided.encode(), salt, HASH_ITER)
        return hashlib.compare_digest(test, expected)
    except Exception:
        return False


# ------------------- INITIAL SETUP -------------------
def init_database():
    """Create database and tables if not exist."""
    con = pymysql.connect(host="localhost", user="root", passwd="260604", autocommit=True)
    cur = con.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS FinanceProDB")
    cur.execute("USE FinanceProDB")

    # Create accounts table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            accid VARCHAR(40) PRIMARY KEY,
            holder VARCHAR(150),
            acc_type VARCHAR(50),
            balance DECIMAL(18,2),
            status VARCHAR(20),
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create transactions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            txid BIGINT AUTO_INCREMENT PRIMARY KEY,
            accid VARCHAR(40),
            action VARCHAR(50),
            amount DECIMAL(18,2),
            balance DECIMAL(18,2),
            remarks VARCHAR(255),
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (accid) REFERENCES accounts(accid) ON DELETE CASCADE
        )
    """)

    # Create users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            userid INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE,
            password VARCHAR(512),
            role VARCHAR(50),
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert default admin if none exist
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            ("Hritik", hash_password("260604"), "Manager")
        )

    con.commit()
    con.close()


# ------------------- DATABASE OPERATIONS -------------------
def add_account(accid, holder, acc_type, balance, status):
    con = db_connect()
    cur = con.cursor()
    cur.execute("INSERT INTO accounts VALUES (%s,%s,%s,%s,%s,DEFAULT)",
                (accid, holder, acc_type, Decimal(balance), status))
    cur.execute("INSERT INTO transactions (accid, action, amount, balance, remarks) VALUES (%s,%s,%s,%s,%s)",
                (accid, "Account Created", Decimal(balance), Decimal(balance), "Initial Deposit"))
    con.commit()
    con.close()


def fetch_accounts():
    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT accid, holder, acc_type, balance, status, created FROM accounts ORDER BY created DESC")
    data = cur.fetchall()
    con.close()
    return data


def fetch_transactions(accid):
    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT txid, action, amount, balance, remarks, created FROM transactions WHERE accid=%s ORDER BY created DESC", (accid,))
    data = cur.fetchall()
    con.close()
    return data


def deposit_money(accid, amount):
    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT balance, status FROM accounts WHERE accid=%s", (accid,))
    row = cur.fetchone()
    if not row: return False, "Account not found"
    if row[1].lower() == "closed": return False, "Account closed"
    new_bal = Decimal(row[0]) + Decimal(amount)
    cur.execute("UPDATE accounts SET balance=%s WHERE accid=%s", (new_bal, accid))
    cur.execute("INSERT INTO transactions (accid, action, amount, balance, remarks) VALUES (%s,%s,%s,%s,%s)",
                (accid, "Deposit", Decimal(amount), new_bal, "Money Deposited"))
    con.commit()
    con.close()
    return True, new_bal


def withdraw_money(accid, amount):
    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT balance, status FROM accounts WHERE accid=%s", (accid,))
    row = cur.fetchone()
    if not row: return False, "Account not found"
    if row[1].lower() == "closed": return False, "Account closed"
    if Decimal(row[0]) < Decimal(amount): return False, "Insufficient funds"
    new_bal = Decimal(row[0]) - Decimal(amount)
    cur.execute("UPDATE accounts SET balance=%s WHERE accid=%s", (new_bal, accid))
    cur.execute("INSERT INTO transactions (accid, action, amount, balance, remarks) VALUES (%s,%s,%s,%s,%s)",
                (accid, "Withdrawal", Decimal(amount), new_bal, "Money Withdrawn"))
    con.commit()
    con.close()
    return True, new_bal


def transfer_money(src, dst, amount):
    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT balance, status FROM accounts WHERE accid=%s", (src,))
    s = cur.fetchone()
    cur.execute("SELECT balance, status FROM accounts WHERE accid=%s", (dst,))
    d = cur.fetchone()
    if not s or not d: return False, "Source or destination not found"
    if s[1].lower() == "closed" or d[1].lower() == "closed": return False, "Account closed"
    if Decimal(s[0]) < Decimal(amount): return False, "Insufficient balance"

    new_s = Decimal(s[0]) - Decimal(amount)
    new_d = Decimal(d[0]) + Decimal(amount)
    cur.execute("UPDATE accounts SET balance=%s WHERE accid=%s", (new_s, src))
    cur.execute("UPDATE accounts SET balance=%s WHERE accid=%s", (new_d, dst))
    cur.execute("INSERT INTO transactions (accid, action, amount, balance, remarks) VALUES (%s,%s,%s,%s,%s)",
                (src, "Transfer Out", Decimal(amount), new_s, f"To {dst}"))
    cur.execute("INSERT INTO transactions (accid, action, amount, balance, remarks) VALUES (%s,%s,%s,%s,%s)",
                (dst, "Transfer In", Decimal(amount), new_d, f"From {src}"))
    con.commit()
    con.close()
    return True, (new_s, new_d)


def update_status(accid, status):
    con = db_connect()
    cur = con.cursor()
    cur.execute("UPDATE accounts SET status=%s WHERE accid=%s", (status, accid))
    con.commit()
    rows = cur.rowcount
    con.close()
    return rows


def delete_account(accid):
    con = db_connect()
    cur = con.cursor()
    cur.execute("DELETE FROM transactions WHERE accid=%s", (accid,))
    cur.execute("DELETE FROM accounts WHERE accid=%s", (accid,))
    con.commit()
    rows = cur.rowcount
    con.close()
    return rows


def export_to_csv(filepath):
    data = fetch_accounts()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Account ID", "Holder", "Type", "Balance", "Status", "Created"])
        writer.writerows(data)


# ------------------- GUI CLASS -------------------
class FinanceProApp(tk.Tk):
    def init(self):
        super().init()
        init_database()
        self.title("🏦 FinancePro Bank Manager")
        self.geometry("1180x720")
        self.configure(bg="#f0f6fb")
        self.create_ui()
        self.refresh_table()

    def create_ui(self):
        header = tk.Label(self, text="💼 FinancePro Bank Manager", font=("Segoe UI", 22, "bold"), bg="#1b4f72", fg="white")
        header.pack(fill="x")

        sidebar = tk.Frame(self, bg="#d6eaf8", width=220)
        sidebar.pack(side="left", fill="y")

        buttons = [
            ("➕ Create Account", self.create_account),
            ("💰 Deposit", self.deposit_action),
            ("💸 Withdraw", self.withdraw_action),
            ("🔁 Transfer", self.transfer_action),
            ("🟢 Change Status", self.status_action),
            ("❌ Delete Account", self.delete_action),
            ("📊 Export CSV", self.export_action),
            ("🔄 Refresh", self.refresh_table)
        ]
        for text, cmd in buttons:
            ttk.Button(sidebar, text=text, command=cmd).pack(fill="x", pady=5, padx=12)

        self.tree = ttk.Treeview(self, columns=("accid", "holder", "acc_type", "balance", "status", "created"), show="headings")
        for col, width in (("accid", 130), ("holder", 200), ("acc_type", 120), ("balance", 120), ("status", 100), ("created", 160)):
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.open_transactions)

    def refresh_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for rec in fetch_accounts():
            self.tree.insert("", "end", values=rec)

    # --- Actions ---
    def create_account(self):
        w = tk.Toplevel(self)
        w.title("New Account")
        labels = ["Account ID", "Holder", "Type", "Balance", "Status"]
        entries = {}
        for i, label in enumerate(labels):
            tk.Label(w, text=label).grid(row=i, column=0, padx=6, pady=6)
            if label == "Type":
                combo = ttk.Combobox(w, values=["Savings", "Current", "Fixed Deposit"], state="readonly")
                combo.set("Savings")
                combo.grid(row=i, column=1)
                entries[label] = combo
            elif label == "Status":
                combo = ttk.Combobox(w, values=["Active", "Dormant", "Closed"], state="readonly")
                combo.set("Active")
                combo.grid(row=i, column=1)
                entries[label] = combo
            else:
                e = tk.Entry(w)
                e.grid(row=i, column=1)
                entries[label] = e

        def save_acc():
            try:
                add_account(entries["Account ID"].get(), entries["Holder"].get(), entries["Type"].get(),
                            Decimal(entries["Balance"].get()), entries["Status"].get())
                messagebox.showinfo("Success", "Account created successfully!")
                w.destroy()
                self.refresh_table()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(w, text="Create Account", command=save_acc).grid(row=6, columnspan=2, pady=10)

    def deposit_action(self):
        acc = simpledialog.askstring("Deposit", "Enter Account ID:")
        amt = simpledialog.askfloat("Deposit", "Enter Amount:")
        if not acc or not amt: return
        ok, res = deposit_money(acc, amt)
        messagebox.showinfo("Deposit", f"New Balance: ₹{res}" if ok else res)
        self.refresh_table()

    def withdraw_action(self):
        acc = simpledialog.askstring("Withdraw", "Enter Account ID:")
        amt = simpledialog.askfloat("Withdraw", "Enter Amount:")
        if not acc or not amt: return
        ok, res = withdraw_money(acc, amt)
        messagebox.showinfo("Withdraw", f"New Balance: ₹{res}" if ok else res)
        self.refresh_table()

    def transfer_action(self):
        src = simpledialog.askstring("Transfer", "From Account ID:")
        dst = simpledialog.askstring("Transfer", "To Account ID:")
        amt = simpledialog.askfloat("Transfer", "Amount:")
        if not src or not dst or not amt: return
        ok, res = transfer_money(src, dst, amt)
        messagebox.showinfo("Transfer", f"Transfer Complete!\nSrc: ₹{res[0]}\nDst: ₹{res[1]}" if ok else res)
        self.refresh_table()

    def status_action(self):
        acc = simpledialog.askstring("Change Status", "Enter Account ID:")
        new = simpledialog.askstring("Change Status", "Enter New Status (Active/Dormant/Closed):")
        if not acc or not new: return
        res = update_status(acc, new)
        messagebox.showinfo("Status", "Status updated" if res else "Account not found")
        self.refresh_table()

    def delete_action(self):
        acc = simpledialog.askstring("Delete Account", "Enter Account ID:")
        if not acc: return
        if messagebox.askyesno("Confirm", f"Delete account {acc}?"):
            res = delete_account(acc)
            messagebox.showinfo("Delete", "Deleted successfully!" if res else "Account not found")
            self.refresh_table()

    def open_transactions(self, event):
        sel = self.tree.selection()
        if not sel: return
        acc = self.tree.item(sel[0], "values")[0]
        rows = fetch_transactions(acc)
        w = tk.Toplevel(self)
        w.title(f"Transactions - {acc}")
        t = ttk.Treeview(w, columns=("txid", "action", "amount", "balance", "remarks", "created"), show="headings")
        for c, width in (("txid", 80), ("action", 120), ("amount", 100), ("balance", 100), ("remarks", 220), ("created", 160)):
            t.heading(c, text=c.title())
            t.column(c, width=width, anchor="center")
        t.pack(fill="both", expand=True)
        for r in rows:
            t.insert("", "end", values=r)

    def export_action(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path: return
        export_to_csv(path)
        messagebox.showinfo("Export", "Accounts exported successfully!")


if name == "main":
    FinanceProApp().mainloop()
