import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import uuid

class BillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ritesh Billing System for GST")
        self.root.geometry("1200x700")
        self.items = []
        self.tax_percent = tk.StringVar(value="18")
        self.gst_id = tk.StringVar()
        self.bill_data = {}
        
        self.setup_ui()

    def setup_ui(self):
        # Title with border
        title_frame = tk.Frame(self.root, bd=2, relief=tk.RIDGE, bg="lightblue")
        title_frame.pack(fill=tk.X)
        title = tk.Label(title_frame, text="Ritesh Billing System For GST", font=("Arial", 24, "bold"), bg="lightblue", pady=10)
        title.pack()

        # GST and Tax Entry Centered Below Title
        top_frame = tk.Frame(self.root, bd=2, relief=tk.RIDGE)
        top_frame.pack(pady=5, fill=tk.X)

        tax_gst_frame = tk.Frame(top_frame)
        tax_gst_frame.pack(anchor=tk.CENTER)

        tk.Label(tax_gst_frame, text="Tax %:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        tk.Entry(tax_gst_frame, textvariable=self.tax_percent, width=5).pack(side=tk.LEFT)
        tk.Label(tax_gst_frame, text="GST ID:", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)
        tk.Entry(tax_gst_frame, textvariable=self.gst_id, width=20).pack(side=tk.LEFT)

        # Main Panels
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left Panel (50%)
        left_frame = tk.Frame(main_frame, width=400, bg="#f8f8f8", bd=2, relief=tk.RIDGE)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_frame.pack_propagate(False)

        # Bill Output Area
        tk.Label(left_frame, text="Bill Output", font=("Arial", 14)).pack(pady=5)
        self.bill_text = scrolledtext.ScrolledText(left_frame, height=18, width=48, bd=2, relief=tk.SUNKEN)
        self.bill_text.pack(pady=5, padx=5)

        # Buttons frame (Open, Search, Clear) below bill text
        bill_btn_frame = tk.Frame(left_frame, bd=2, relief=tk.RIDGE, bg="#e0e0e0")
        bill_btn_frame.pack(fill=tk.X, pady=10, padx=5)
        
        # Buttons frame (Open, Search, Clear) below bill text
        bill_btn_frame = tk.Frame(left_frame, bd=2, relief=tk.RIDGE, bg="#e0e0e0")
        bill_btn_frame.pack(fill=tk.X, pady=10, padx=5)
        
        # Add Item / Calculate / Save Bill buttons at bottom (optional if needed)
        control_frame =  tk.Frame(left_frame, bd=2, relief=tk.RIDGE, bg="#e0e0e0")
        control_frame.pack(fill=tk.X, pady=10, padx=10)
        tk.Button(control_frame, text="Add Item",font=("Arial",12), command=self.add_item, bg="#ADD8E6", height=2).pack(side=tk.LEFT, padx=10)
        tk.Button(control_frame, text="Calculate", font=("Arial", 12), bg="lightgreen", command=self.calculate_total, height=2).pack(side=tk.LEFT, padx=10)
        self.save_button = tk.Button(control_frame, text="Save Bill", font=("Arial", 12), bg="lightblue", command=self.save_bill, height=2)
        self.save_button.pack(side=tk.LEFT, padx=10)
        # self.save_button.config(state=tk.DISABLED)

        # Open Bill Button
        open_btn = tk.Button(bill_btn_frame, text="Open Bill", bg="#87CEEB", width=12, height=2, command=lambda: self.open_bill(self.search_id.get()))



        open_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Search Entry
        search_label = tk.Label(bill_btn_frame, text="Search Bill:", font=("Arial", 10), bg="#e0e0e0")
        search_label.pack(side=tk.LEFT, padx=5)
        self.search_id = tk.StringVar()
        search_entry = tk.Entry(bill_btn_frame, textvariable=self.search_id, width=15)
        search_entry.pack(side=tk.LEFT, padx=5)

        # Clear Bill Button
        clear_btn = tk.Button(bill_btn_frame, text="Clear Bill", bg="#FFA07A", width=12, height=2, command=self.clear_bill_text)
        clear_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Right Panel (50%)
        right_frame = tk.Frame(main_frame, bg="#f5f5f5", bd=2, relief=tk.RIDGE)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Items Frame (40% Height)
        items_panel = tk.Frame(right_frame, height=300, bg="#ffffff", bd=2, relief=tk.RIDGE)
        items_panel.pack(fill=tk.X, padx=5, pady=5)

        # Scrollable Items Section
        canvas = tk.Canvas(items_panel, bg="#ffffff")
        scrollbar = ttk.Scrollbar(items_panel, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="#ffffff")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


        # Calculator Section
        calc_frame = tk.Frame(right_frame, bd=4, relief=tk.RIDGE, bg="#f9f9f9")
        calc_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(calc_frame, text="Calculator", font=("Arial", 14, "bold"), bg="#f9f9f9").pack(pady=5)

        self.calc_entry = tk.Entry(calc_frame, font=("Arial", 16), width=30, bd=4, relief=tk.SUNKEN, justify=tk.RIGHT)
        self.calc_entry.pack(pady=5, padx=10)

        btns = [
            ('7', '8', '9', '/'),
            ('4', '5', '6', '*'),
            ('1', '2', '3', '-'),
            ('0', '.', '=', '+')
        ]

        for row in btns:
            row_frame = tk.Frame(calc_frame, bg="#f9f9f9")
            row_frame.pack(pady=2)
            for btn in row:
                tk.Button(
                    row_frame,
                    text=btn,
                    font=("Arial", 12),
                    width=6,
                    height=2,
                    bg="#dcdcdc",
                    relief=tk.RAISED,
                    command=lambda b=btn: self.calculate(b)
                ).pack(side=tk.LEFT, padx=3, pady=3)

        # Add Item / Calculate / Save Bill buttons at bottom (optional if needed)
        control_frame = tk.Frame(right_frame)
        control_frame.pack(fill=tk.X, pady=10, padx=10)
        tk.Button(control_frame, text="Add Item",font=("Arial",12), command=self.add_item, bg="#ADD8E6", height=2).pack(side=tk.LEFT, padx=10)
        tk.Button(control_frame, text="Calculate", font=("Arial", 12), bg="lightgreen", command=self.calculate_total, height=2).pack(side=tk.LEFT, padx=10)
        self.save_button = tk.Button(control_frame, text="Save Bill", font=("Arial", 12), bg="lightblue", command=self.save_bill, height=2)
        self.save_button.pack(side=tk.LEFT, padx=10)
        # self.save_button.config(state=tk.DISABLED)
        
    # Example of how to bind the bill_id to the button click event
    def on_open_button_click(self, bill_id):
        self.open_bill(bill_id)



    # Dummy clear function – add real logic as needed
    def clear_bill_text(self):
        self.bill_text.delete('1.0', tk.END)

    def open_bill(self):
        # Get the bill ID from the search entry
        bill_id = self.search_id.get()
        
        if bill_id in self.bill_data:
            # Display the saved bill in the bill text area
            self.bill_text.delete(1.0, tk.END)
            self.bill_text.insert(tk.END, self.bill_data[bill_id])
        else:
            # Show an error message if the bill ID doesn't exist
            tk.messagebox.showerror("Error", "Bill not found.")

    def calculate(self, key):
        if key == "=":
            try:
                result = eval(self.calc_entry.get())
                self.calc_entry.delete(0, tk.END)
                self.calc_entry.insert(tk.END, str(result))
            except:
                self.calc_entry.delete(0, tk.END)
                self.calc_entry.insert(tk.END, "Error")
        else:
            self.calc_entry.insert(tk.END, key)

    def add_item(self):
        frame = tk.Frame(self.scrollable_frame, pady=2)
        frame.pack(fill=tk.X, padx=0,pady=0)

        name = tk.Entry(frame)
        name.grid(row=0, column=0, padx=5)
        price = tk.Entry(frame)
        price.grid(row=0, column=1, padx=5)
        qty = tk.Entry(frame)
        qty.grid(row=0, column=2, padx=5)

        tk.Label(frame, text="Name").grid(row=1, column=0)
        tk.Label(frame, text="Price/kg").grid(row=1, column=1)
        tk.Label(frame, text="Qty").grid(row=1, column=2)

        self.items.append((name, price, qty))

    def calculate_total(self):
        self.bill_text.delete(1.0, tk.END)
        total = 0
        bill_id = str(uuid.uuid4())[:8]

        self.bill_text.insert(tk.END, f"Ritesh Billing System\n")
        self.bill_text.insert(tk.END, f"Bill ID: {bill_id}\n")
        self.bill_text.insert(tk.END, f"GST ID: {self.gst_id.get()}\n")
        self.bill_text.insert(tk.END, f"{'-'*30}\n")

        for name, price, qty in self.items:
            try:
                item_name = name.get().strip()
                item_price = float(price.get())
                item_qty = float(qty.get())
                item_total = item_price * item_qty
                total += item_total
                self.bill_text.insert(tk.END, f"{item_name} - {item_qty} x Rupees{item_price:.2f} = Rupee{item_total:.2f}\n")
            except:
                pass

        self.bill_text.insert(tk.END, f"{'-'*30}\n")
        self.bill_text.insert(tk.END, f"Subtotal: ₹{total:.2f}\n")
        try:
            tax = float(self.tax_percent.get())
        except:
            tax = 0
        tax_amount = total * (tax / 100)
        grand_total = total + tax_amount
        self.bill_text.insert(tk.END, f"GST ({tax}%): ₹{tax_amount:.2f}\n")
        self.bill_text.insert(tk.END, f"Grand Total: ₹{grand_total:.2f}\n")
        self.bill_text.insert(tk.END, f"{'='*30}\n")

        # Save this bill temporarily in memory
        self.bill_data[bill_id] = self.bill_text.get(1.0, tk.END)

        # ✅ Enable save button
        # self.save_button.config(state=tk.NORMAL)

        
    def save_bill(self):
        bill_content = self.bill_text.get(1.0, tk.END).strip()
        if not bill_content:
            messagebox.showwarning("Empty Bill", "There is nothing to save!")
            return

        # Extract bill ID from the text (assuming it is the second line)
        lines = bill_content.splitlines()
        bill_id = None
        for line in lines:
            if line.startswith("Bill ID:"):
                bill_id = line.split(":", 1)[1].strip()
                break

        if not bill_id:
            messagebox.showerror("Error", "Bill ID not found. Cannot save.")
            return

        # Save to internal dict
        self.bill_data[bill_id] = bill_content

        # Save to file with utf-8 encoding
        folder = "bills"
        if not os.path.exists(folder):
            os.makedirs(folder)

        file_path = os.path.join(folder, f"{bill_id}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(bill_content)

        messagebox.showinfo("Saved", f"Bill saved successfully with ID: {bill_id}")

    def open_bill(self, bill_id):
        # Make sure the bill_id is provided correctly
        if bill_id not in self.bill_data:
            messagebox.showerror("Error", f"Bill ID: {bill_id} not found.")
            return

        bill_content = self.bill_data[bill_id]

        # Optionally, you can load the content from the file using utf-8 encoding
        # file_path = os.path.join("bills", f"{bill_id}.txt")
        # with open(file_path, "r", encoding="utf-8") as f:
        #     bill_content = f.read()

        self.bill_text.delete(1.0, tk.END)  # Clear current content
        self.bill_text.insert(tk.END, bill_content)  # Insert loaded content

        messagebox.showinfo("Loaded", f"Bill with ID: {bill_id} loaded successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()
