from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
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
        json.dump(sample_data, f)

def load_db():
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

class StockStatus(str, Enum):
    NORMAL = "green"
    WARNING = "yellow"
    CRITICAL = "red"

class InventoryItem(BaseModel):
    id: int
    name: str
    sku: str
    current_quantity: float
    min_quantity: float
    unit: str
    supplier: str
    warehouse: str
    
    @property
    def status(self) -> StockStatus:
        if self.current_quantity <= 0:
            return StockStatus.CRITICAL
        elif self.current_quantity <= self.min_quantity * 1.5:
            return StockStatus.WARNING
        return StockStatus.NORMAL

class StockMovement(BaseModel):
    id: int
    item_id: int
    quantity: float
    movement_type: str  # 'in', 'out', 'adjustment'
    reference: Optional[str] = None
    notes: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

app = FastAPI(
    title="Raw Material Stock Monitor",
    description="Simple API for monitoring raw material stock levels",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Raw Material Stock Monitor API", "docs": "/docs"}

@app.get("/api/items/", response_model=List[dict])
async def get_items():
    db = load_db()
    return db["inventory_items"]

@app.get("/api/items/{item_id}", response_model=dict)
async def get_item(item_id: int):
    db = load_db()
    for item in db["inventory_items"]:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.post("/api/items/{item_id}/update-quantity")
async def update_quantity(item_id: int, quantity: float, movement_type: str = "adjustment", notes: str = None):
    db = load_db()
    item_found = False
    
    for item in db["inventory_items"]:
        if item["id"] == item_id:
            item_found = True
            if movement_type == "in":
                item["current_quantity"] += quantity
            elif movement_type == "out":
                item["current_quantity"] = max(0, item["current_quantity"] - quantity)
            else:  # adjustment
                item["current_quantity"] = quantity
            break
    
    if not item_found:
        raise HTTPException(status_code=404, detail="Item not found")
    
    movement_id = max([m.get("id", 0) for m in db["stock_movements"]], default=0) + 1
    db["stock_movements"].append({
        "id": movement_id,
        "item_id": item_id,
        "quantity": quantity,
        "movement_type": movement_type,
        "notes": notes,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    save_db(db)
    return {"message": "Quantity updated successfully"}

@app.get("/api/stock-alerts/")
async def get_stock_alerts():
    db = load_db()
    alerts = []
    
    for item in db["inventory_items"]:
        item_obj = InventoryItem(**item)
        if item_obj.status != StockStatus.NORMAL:
            alerts.append({
                "item_id": item_obj.id,
                "item_name": item_obj.name,
                "current_quantity": item_obj.current_quantity,
                "min_quantity": item_obj.min_quantity,
                "status": item_obj.status,
                "warehouse": item_obj.warehouse
            })
    
    return alerts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)