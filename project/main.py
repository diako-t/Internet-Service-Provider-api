from .logging_config import setup_logging
setup_logging()

from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app:FastAPI):
    print("Application startup")
    yield
    print("Application shutdown")

from fastapi import FastAPI
app = FastAPI(lifespan=lifespan, title="internet service provider", version="1.0.0")

from .middleware import log_requests
app.middleware("http")(log_requests)


from .routers import auth, categories, services, ServicePlans, orders, transactions, subscriptions
app.include_router(categories.router)
app.include_router(auth.router)
app.include_router(services.router)
app.include_router(ServicePlans.router)
app.include_router(orders.router)
app.include_router(transactions.router)
app.include_router(subscriptions.router)

@app.get("/")
def root():
    return {"message": "hello user"}