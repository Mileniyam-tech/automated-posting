import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.APP_NAME} on http://localhost:{settings.APP_PORT}...")
    print(f"Interactive Swagger Documentation: http://localhost:{settings.APP_PORT}/docs")
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True
    )
