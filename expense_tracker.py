
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from pathlib import Path

DB_FILE = Path(__file__).with_name("expenses.db")

CATEGORIES = ["Food", "Transport", "Bills", "Shopping", "Education", "Health", "Entertainment", "Other"]
ICONS = {
    "Food": "🍔", "Transport": "🚗", "Bills": "🧾", "Shopping": "🛍",
    "Education": "📚", "Health": "💊", "Entertainment": "🎮", "Other": "📦"
}

class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Monthly Expense Tracker")
        self.root.geometry("1000x650")
        self.root.minsize(900, 600)

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.setup_db()
        self.build_ui()
        self.refresh()

    def setup_db(self):
        with sqlite3.connect(DB_FILE) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_date TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    amount REAL NOT NULL
                )
            """)

    def build_ui(self):
        self.root.configure(bg="#f4f6f8")

        # Header
        header = tk.Frame(self.root, bg="#17202a", height=82)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="💰  Monthly Expense Tracker",
                 font=("Segoe UI", 22, "bold"), fg="white", bg="#17202a").pack(
                     side="left", padx=25, pady=18)

        # Main container
        main = tk.Frame(self.root, bg="#f4f6f8")
        main.pack(fill="both", expand=True, padx=20, pady=18)

        # Summary cards
        cards = tk.Frame(main, bg="#f4f6f8")
        cards.pack(fill="x", pady=(0, 15))

        self.total_var = tk.StringVar(value="PKR 0.00")
        self.count_var = tk.StringVar(value="0")
        self.avg_var = tk.StringVar(value="PKR 0.00")

        self.make_card(cards, "💵", "This Month", self.total_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.make_card(cards, "🧮", "Expenses", self.count_var).pack(side="left", fill="x", expand=True, padx=8)
        self.make_card(cards, "📊", "Average", self.avg_var).pack(side="left", fill="x", expand=True, padx=(8, 0))

        # Form
        form = tk.LabelFrame(main, text="  ➕ Add Expense  ", font=("Segoe UI", 11, "bold"),
                             bg="white", fg="#17202a", padx=12, pady=10)
        form.pack(fill="x", pady=(0, 15))

        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.desc_var = tk.StringVar()
        self.amount_var = tk.StringVar()

        tk.Label(form, text="Date", bg="white").grid(row=0, column=0, sticky="w", padx=6)
        tk.Entry(form, textvariable=self.date_var, width=15).grid(row=1, column=0, padx=6, pady=5)

        tk.Label(form, text="Category", bg="white").grid(row=0, column=1, sticky="w", padx=6)
        ttk.Combobox(form, textvariable=self.category_var, values=CATEGORIES,
                     state="readonly", width=18).grid(row=1, column=1, padx=6, pady=5)

        tk.Label(form, text="Description", bg="white").grid(row=0, column=2, sticky="w", padx=6)
        tk.Entry(form, textvariable=self.desc_var, width=30).grid(row=1, column=2, padx=6, pady=5)

        tk.Label(form, text="Amount (PKR)", bg="white").grid(row=0, column=3, sticky="w", padx=6)
        tk.Entry(form, textvariable=self.amount_var, width=16).grid(row=1, column=3, padx=6, pady=5)

        tk.Button(form, text="  💾 Add Expense  ", command=self.add_expense,
                  bg="#1f8f5f", fg="white", activebackground="#176b47",
                  activeforeground="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=12, pady=7).grid(row=1, column=4, padx=12)

        # Table
        table_frame = tk.Frame(main, bg="white")
        table_frame.pack(fill="both", expand=True)

        toolbar = tk.Frame(table_frame, bg="white")
        toolbar.pack(fill="x", padx=12, pady=10)

        tk.Label(toolbar, text="📋 Expense History",
                 font=("Segoe UI", 13, "bold"), bg="white", fg="#17202a").pack(side="left")

        tk.Button(toolbar, text="🗑 Delete Selected", command=self.delete_selected,
                  bg="#c0392b", fg="white", relief="flat", padx=10, pady=5).pack(side="right")

        self.month_var = tk.StringVar(value=date.today().strftime("%Y-%m"))
        tk.Label(toolbar, text="Month:", bg="white").pack(side="right", padx=(0, 5))
        month_entry = tk.Entry(toolbar, textvariable=self.month_var, width=9)
        month_entry.pack(side="right", padx=5)
        tk.Button(toolbar, text="🔄 Refresh", command=self.refresh,
                  bg="#34495e", fg="white", relief="flat", padx=10, pady=5).pack(side="right", padx=5)

        columns = ("id", "date", "category", "description", "amount")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        headings = {"id":"ID", "date":"Date", "category":"Category", "description":"Description", "amount":"Amount (PKR)"}
        widths = {"id":55, "date":110, "category":150, "description":350, "amount":140}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center" if col != "description" else "w")
        self.tree.pack(side="left", fill="both", expand=True, padx=(12,0), pady=(0,12))

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y", padx=(0,12), pady=(0,12))
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.tag_configure("odd", background="#f8f9fa")

    def make_card(self, parent, icon, title, variable):
        card = tk.Frame(parent, bg="white", height=105, bd=0, highlightthickness=1, highlightbackground="#e1e5e8")
        tk.Label(card, text=icon, font=("Segoe UI Emoji", 25), bg="white").pack(side="left", padx=16)
        body = tk.Frame(card, bg="white")
        body.pack(side="left", pady=16)
        tk.Label(body, text=title, font=("Segoe UI", 10), fg="#68737d", bg="white").pack(anchor="w")
        tk.Label(body, textvariable=variable, font=("Segoe UI", 17, "bold"), fg="#17202a", bg="white").pack(anchor="w")
        return card

    def add_expense(self):
        d = self.date_var.get().strip()
        cat = self.category_var.get().strip()
        desc = self.desc_var.get().strip()
        amount_text = self.amount_var.get().strip()

        try:
            date.fromisoformat(d)
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Enter a valid date (YYYY-MM-DD) and a positive amount.")
            return

        with sqlite3.connect(DB_FILE) as con:
            con.execute(
                "INSERT INTO expenses (expense_date, category, description, amount) VALUES (?, ?, ?, ?)",
                (d, cat, desc, amount)
            )

        self.desc_var.set("")
        self.amount_var.set("")
        self.month_var.set(d[:7])
        self.refresh()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Nothing Selected", "Please select an expense first.")
            return

        item = self.tree.item(selected[0])
        expense_id = item["values"][0]

        if messagebox.askyesno("Delete Expense", "Delete the selected expense?"):
            with sqlite3.connect(DB_FILE) as con:
                con.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            self.refresh()

    def refresh(self):
        month = self.month_var.get().strip()

        for item in self.tree.get_children():
            self.tree.delete(item)

        with sqlite3.connect(DB_FILE) as con:
            rows = con.execute("""
                SELECT id, expense_date, category, description, amount
                FROM expenses
                WHERE substr(expense_date, 1, 7) = ?
                ORDER BY expense_date DESC, id DESC
            """, (month,)).fetchall()

        total = sum(row[4] for row in rows)
        count = len(rows)
        average = total / count if count else 0

        self.total_var.set(f"PKR {total:,.2f}")
        self.count_var.set(str(count))
        self.avg_var.set(f"PKR {average:,.2f}")

        for i, row in enumerate(rows):
            category_display = f"{ICONS.get(row[2], '📦')} {row[2]}"
            self.tree.insert("", "end",
                             values=(row[0], row[1], category_display, row[3] or "—", f"{row[4]:,.2f}"),
                             tags=("odd",) if i % 2 else ())

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
