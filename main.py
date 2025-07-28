from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from routers import auth, staff, alerts, geofence, cattle, dashboard

# Single FastAPI app instance
app = FastAPI(title="Cattle Monitor API", description="FastAPI backend for cattle monitoring system with Firebase integration")

# CORS configuration - update for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(staff.router)
app.include_router(alerts.router)
app.include_router(geofence.router)
app.include_router(cattle.router)
app.include_router(dashboard.router)

@app.get("/")
def read_root():
    return {"message": "Cattle Monitor API is running!", "status": "healthy", "version": "1.0.0"}
