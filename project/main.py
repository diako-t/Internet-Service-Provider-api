from fastapi import FastAPI
from . import models
from .database import engine
from .routers import auth, categories, services, ServicePlans, orders, transactions

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(categories.router)
app.include_router(auth.router)
app.include_router(services.router)
app.include_router(ServicePlans.router)
app.include_router(orders.router)
app.include_router(transactions.router)

@app.get("/")
def root():
    return {"message": "hello user"}