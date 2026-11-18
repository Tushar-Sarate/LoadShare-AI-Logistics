from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database import engine

# Import all models (needed so SQLAlchemy can resolve relationships)
from app.models.user import User
from app.models.customer import Customer
from app.models.delivery_partner import DeliveryPartner
from app.models.order import Order
from app.models.payment import Payment
from app.models.tracking import Tracking
from app.models.complaint import Complaint
from app.models.restaurant import Restaurant, MenuItem
from app.models.order_item import OrderItem
from app.models.review import Review

# Import routers
from app.routers.auth import router as auth_router
from app.routers.users import router as user_router
from app.routers.customer import router as customer_router
from app.routers.partners import router as partner_router
from app.routers import orders
from app.routers.payments import router as payment_router
from app.routers.tracking import router as tracking_router
from app.routers.complaints import router as complaint_router
from app.routers.chatbot import router as chatbot_router
from app.routers.restaurants import router as restaurant_router
from app.routers.food_orders import router as food_order_router
from app.routers.events import router as events_router
from app.routers.analytics import router as analytics_router
from app.routers.live import router as live_router
from app.routers.reviews import router as review_router
from app.routers.public import router as public_router

from app.services.email_inbox import start_inbox_worker


# Tables are created by Alembic migrations:  alembic upgrade head


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start reading the support inbox in the background
    start_inbox_worker()
    yield


# Initialize FastAPI
app = FastAPI(
    title="LoadShare AI Logistics",
    description="AI Powered Logistics and Delivery Management System",
    version="2.0.0",
    lifespan=lifespan
)


# Register routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(customer_router)
app.include_router(partner_router)
app.include_router(orders.router)
app.include_router(payment_router)
app.include_router(tracking_router)
app.include_router(complaint_router)
app.include_router(chatbot_router)
app.include_router(restaurant_router)
app.include_router(food_order_router)
app.include_router(events_router)
app.include_router(analytics_router)
app.include_router(live_router)
app.include_router(review_router)
app.include_router(public_router)


# Home API
@app.get("/")
def home():
    return {
        "message": "Welcome to LoadShare AI Logistics",
        "status": "Running Successfully"
    }


# Database health check
@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "database": "Connected",
            "status": "Healthy"
        }

    except Exception:
        return {
            "database": "Disconnected",
            "status": "Unhealthy"
        }


# Serve the frontend pages
app.mount("/site", StaticFiles(directory="frontend", html=True), name="site")