from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd

from . import models, schemas, crud, auth
from .database import SessionLocal, engine
from .config import settings


models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Raw Material Stock Monitor API",
    description="API for monitoring raw material stock levels in manufacturing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Raw Material Stock Monitor API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.post("/api/items/", response_model=schemas.InventoryItem, status_code=status.HTTP_201_CREATED)
def create_item(item: schemas.InventoryItemCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    return crud.create_inventory_item(db=db, item=item, user_id=current_user.id)

@app.get("/api/items/", response_model=List[schemas.InventoryItem])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_inventory_items(db, skip=skip, limit=limit)
    return items

@app.get("/api/items/{item_id}", response_model=schemas.InventoryItem)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_inventory_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.post("/api/stock-movements/", response_model=schemas.StockMovement, status_code=status.HTTP_201_CREATED)
def create_stock_movement(movement: schemas.StockMovementCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    return crud.create_stock_movement(db=db, movement=movement, user_id=current_user.id)

@app.get("/api/stock-alerts/", response_model=List[schemas.StockAlert])
def get_stock_alerts(
    status: Optional[models.StockStatus] = None, 
    supplier_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    return crud.get_stock_alerts(
        db, 
        status=status, 
        supplier_id=supplier_id, 
        warehouse_id=warehouse_id
    )

@app.get("/api/reports/stock-levels/")
def generate_stock_levels_report(
    format: str = "json",
    db: Session = Depends(get_db)
):
    items = crud.get_inventory_items(db)
    
    if format == "csv":
        df = pd.DataFrame([{
            'id': item.id,
            'name': item.name,
            'sku': item.sku,
            'current_quantity': item.current_quantity,
            'min_quantity': item.min_quantity,
            'status': item.stock_status.value,
            'warehouse': item.warehouse.name if item.warehouse else None,
            'supplier': item.supplier.name if item.supplier else None
        } for item in items])
        
        return {"content": df.to_csv(index=False), "media_type": "text/csv"}
    
    return items

@app.get("/api/predictions/shortage-dates/")
def predict_shortage_dates(
    days_lookback: int = 30,
    db: Session = Depends(get_db)
):
    """Predict shortage dates for all inventory items based on recent usage"""
    return crud.calculate_shortage_predictions(db, days_lookback=days_lookback)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
