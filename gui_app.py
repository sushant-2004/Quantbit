import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from datetime import datetime
from enum import Enum
import os

DB_FILE = "stock_monitor_db.json"

if not os.path.exists(DB_FILE):
    sample_data = {
        "inventory_items": [
            {
                "id": 1,
                "name": "Steel Sheets",
                "sku": "STL-001",
                "current_quantity": 150,
                "min_quantity": 50,
                "unit": "pc",
                "supplier": "MetalWorks Inc.",
                "warehouse": "Main Warehouse"
            },
            {
                "id": 2,
                "name": "Plastic Pellets",
                "sku": "PLA-001",
                "current_quantity": 500,
                "min_quantity": 200,
                "unit": "kg",
                "supplier": "Plastico",
                "warehouse": "Main Warehouse"
            }
        ],
        "stock_movements": []
    }
    with open(DB_FILE, 'w') as f:
        json.dump(sample_data, f, indent=2)

class StockStatus(Enum):
    NORMAL = "green"
    WARNING = "yellow"
    CRITICAL = "red"

class StockMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Raw Material Stock Monitor")
        self.root.geometry("1000x600")
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_widgets()
        
        self.load_data()
        self.update_inventory_list()
    
    def create_widgets(self):
        title_label = ttk.Label(
            self.main_frame, 
            text="Raw Material Stock Monitor", 
            font=('Helvetica', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            button_frame, 
            text="Add New Item", 
            command=self.add_item_dialog
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Update Stock", 
            command=self.update_stock_dialog
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="View Alerts", 
            command=self.show_alerts
        ).pack(side=tk.LEFT, padx=5)
        
        self.tree = ttk.Treeview(
            self.main_frame,
            columns=("ID", "Name", "SKU", "Current Qty", "Min Qty", "Unit", "Status", "Supplier", "Warehouse"),
            show="headings",
            selectmode="browse"
        )
        
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("SKU", text="SKU")
        self.tree.heading("Current Qty", text="Current Qty")
        self.tree.heading("Min Qty", text="Min Qty")
        self.tree.heading("Unit", text="Unit")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Supplier", text="Supplier")
        self.tree.heading("Warehouse", text="Warehouse")
        
        self.tree.column("ID", width=50, anchor=tk.CENTER)
        self.tree.column("Name", width=150)
        self.tree.column("SKU", width=100)
        self.tree.column("Current Qty", width=80, anchor=tk.CENTER)
        self.tree.column("Min Qty", width=80, anchor=tk.CENTER)
        self.tree.column("Unit", width=60, anchor=tk.CENTER)
        self.tree.column("Status", width=80, anchor=tk.CENTER)
        self.tree.column("Supplier", width=150)
        self.tree.column("Warehouse", width=120)
        
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(
            self.main_frame, 
            textvariable=self.status_var,
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_data(self):
        try:
            with open(DB_FILE, 'r') as f:
                self.data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            self.data = {"inventory_items": [], "stock_movements": []}
    
    def save_data(self):
        try:
            with open(DB_FILE, 'w') as f:
                json.dump(self.data, f, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")
            return False
    
    def get_stock_status(self, current, min_qty):
        if current <= 0:
            return StockStatus.CRITICAL
        elif current <= min_qty * 1.5:
            return StockStatus.WARNING
        return StockStatus.NORMAL
    
    def update_inventory_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for item in self.data["inventory_items"]:
            status = self.get_stock_status(item["current_quantity"], item["min_quantity"])
            
            self.tree.insert("", tk.END, values=(
                item["id"],
                item["name"],
                item["sku"],
                f"{item['current_quantity']:.2f}",
                f"{item['min_quantity']:.2f}",
                item["unit"],
                status.value.upper(),
                item["supplier"],
                item["warehouse"]
            ), tags=(status.value,))
        
        self.tree.tag_configure("red", background='#ffdddd')
        self.tree.tag_configure("yellow", background='#ffffcc')
        self.tree.tag_configure("green", background='#ddffdd')
    
    def add_item_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Item")
        dialog.geometry("400x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Name:").pack(pady=(10, 0))
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=(0, 10))
        
        ttk.Label(dialog, text="SKU:").pack(pady=(0, 0))
        sku_entry = ttk.Entry(dialog, width=40)
        sku_entry.pack(pady=(0, 10))
        
        ttk.Label(dialog, text="Current Quantity:").pack(pady=(0, 0))
        current_qty_entry = ttk.Spinbox(dialog, from_=0, to=100000, width=37)
        current_qty_entry.pack(pady=(0, 10))
        
        ttk.Label(dialog, text="Minimum Quantity:").pack(pady=(0, 0))
        min_qty_entry = ttk.Spinbox(dialog, from_=0, to=100000, width=37)
        min_qty_entry.pack(pady=(0, 10))
        
        ttk.Label(dialog, text="Unit:").pack(pady=(0, 0))
        unit_entry = ttk.Combobox(dialog, values=["pc", "kg", "g", "L", "mL"], width=37)
        unit_entry.pack(pady=(0, 10))
        
        ttk.Label(dialog, text="Supplier:").pack(pady=(0, 0))
        supplier_entry = ttk.Entry(dialog, width=40)
        supplier_entry.pack(pady=(0, 10))
        
        ttk.Label(dialog, text="Warehouse:").pack(pady=(0, 0))
        warehouse_entry = ttk.Entry(dialog, width=40)
        warehouse_entry.pack(pady=(0, 20))
        
        def save_item():
            try:
                item_id = max([item["id"] for item in self.data["inventory_items"]], default=0) + 1
                
                new_item = {
                    "id": item_id,
                    "name": name_entry.get(),
                    "sku": sku_entry.get(),
                    "current_quantity": float(current_qty_entry.get()),
                    "min_quantity": float(min_qty_entry.get()),
                    "unit": unit_entry.get(),
                    "supplier": supplier_entry.get(),
                    "warehouse": warehouse_entry.get()
                }
                
                self.data["inventory_items"].append(new_item)
                if self.save_data():
                    self.update_inventory_list()
                    dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", "Please enter valid numbers for quantities")
        
        ttk.Button(dialog, text="Save", command=save_item).pack(pady=(0, 10))
    
    def update_stock_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to update")
            return
            
        item_id = int(self.tree.item(selected[0], "values")[0])
        item = next((i for i in self.data["inventory_items"] if i["id"] == item_id), None)
        
        if not item:
            messagebox.showerror("Error", "Selected item not found")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Update Stock - {item['name']}")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Current Quantity: {item['current_quantity']} {item['unit']}").pack(pady=10)
        
        ttk.Label(dialog, text="Movement Type:").pack()
        movement_type = tk.StringVar(value="in")
        ttk.Radiobutton(dialog, text="Add Stock", variable=movement_type, value="in").pack()
        ttk.Radiobutton(dialog, text="Remove Stock", variable=movement_type, value="out").pack()
        ttk.Radiobutton(dialog, text="Set New Quantity", variable=movement_type, value="adjust").pack()
        
        ttk.Label(dialog, text="Quantity:").pack()
        qty_entry = ttk.Spinbox(dialog, from_=0, to=100000, width=10)
        qty_entry.pack(pady=5)
        
        def update_item():
            try:
                qty = float(qty_entry.get())
                movement = movement_type.get()
                
                if movement == "in":
                    item["current_quantity"] += qty
                elif movement == "out":
                    item["current_quantity"] = max(0, item["current_quantity"] - qty)
                else:  
                    item["current_quantity"] = qty
                
                movement_id = max([m.get("id", 0) for m in self.data["stock_movements"]], default=0) + 1
                self.data["stock_movements"].append({
                    "id": movement_id,
                    "item_id": item_id,
                    "quantity": qty,
                    "movement_type": movement,
                    "timestamp": datetime.now().isoformat()
                })
                
                if self.save_data():
                    self.update_inventory_list()
                    dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
        
        ttk.Button(dialog, text="Update", command=update_item).pack(pady=10)
    
    def show_alerts(self):
        alerts = []
        for item in self.data["inventory_items"]:
            status = self.get_stock_status(item["current_quantity"], item["min_quantity"])
            if status != StockStatus.NORMAL:
                alerts.append(
                    f"{item['name']} ({item['sku']}) - "
                    f"Current: {item['current_quantity']} {item['unit']}, "
                    f"Min: {item['min_quantity']} {item['unit']} - "
                    f"Status: {status.value.upper()}"
                )
        
        if not alerts:
            messagebox.showinfo("Stock Alerts", "No stock alerts at this time.")
        else:
            alert_text = "\n\n".join(alerts)
            messagebox.showwarning("Stock Alerts", f"The following items need attention:\n\n{alert_text}")

def main():
    root = tk.Tk()
    app = StockMonitorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
