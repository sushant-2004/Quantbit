from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from .database import Base
import enum

class StockStatus(str, enum.Enum):
    NORMAL = "green"
    WARNING = "yellow"
    CRITICAL = "red"

class MaterialCategory(str, enum.Enum):
    RAW_MATERIAL = "raw_material"
    PACKAGING = "packaging"
    CHEMICAL = "chemical"
    COMPONENT = "component"
    OTHER = "other"

class UnitType(str, enum.Enum):
    KILOGRAM = "kg"
    GRAM = "g"
    LITER = "L"
    MILLILITER = "mL"
    PIECE = "pc"
    METER = "m"
    CENTIMETER = "cm"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    inventory_items = relationship("InventoryItem", back_populates="created_by")
    stock_movements = relationship("StockMovement", back_populates="user")

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    contact_person = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    address = Column(String)
    lead_time_days = Column(Integer, default=7)  
    
    inventory_items = relationship("InventoryItem", back_populates="supplier")

class Warehouse(Base):
    __tablename__ = "warehouses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    location = Column(String)
    contact_person = Column(String)
    contact_phone = Column(String)
   
    inventory_items = relationship("InventoryItem", back_populates="warehouse")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    sku = Column(String, unique=True, index=True)
    category = Column(Enum(MaterialCategory), nullable=False)
    unit = Column(Enum(UnitType), nullable=False)
    current_quantity = Column(Float, default=0.0)
    min_quantity = Column(Float, default=0.0)
    reorder_quantity = Column(Float)
    unit_cost = Column(Float, default=0.0)
    
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    s
    supplier = relationship("Supplier", back_populates="inventory_items")
    warehouse = relationship("Warehouse", back_populates="inventory_items")
    created_by = relationship("User", back_populates="inventory_items")
    stock_movements = relationship("StockMovement", back_populates="item")
    
    @property
    def stock_status(self) -> StockStatus:
        """Calculate stock status based on current and minimum quantity"""
        if self.current_quantity <= 0:
            return StockStatus.CRITICAL
        elif self.current_quantity <= self.min_quantity * 1.5:  
            return StockStatus.WARNING
        return StockStatus.NORMAL
    
    def predict_shortage_date(self, avg_daily_usage: float = None) -> datetime:
        """
        Predict when the stock will run out based on average daily usage
        If avg_daily_usage is not provided, it will be calculated from historical data
        """
        if avg_daily_usage is None or avg_daily_usage <= 0:
            return datetime.utcnow() + timedelta(days=30)
            
        if self.current_quantity <= 0:
            return datetime.utcnow()
            
        days_remaining = self.current_quantity / avg_daily_usage
        return datetime.utcnow() + timedelta(days=days_remaining)

class StockMovement(Base):
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    movement_type = Column(String, nullable=False) 
    quantity = Column(Float, nullable=False)
    reference = Column(String) 
    notes = Column(String)
   
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    item = relationship("InventoryItem", back_populates="stock_movements")
    user = relationship("User", back_populates="stock_movements")
