import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings
from app.schemas import PostingRequest, PostingResponse
from app.services.posting_service import PostingService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.posting_service = PostingService()
    yield


app = FastAPI(
    title="Automated Multi-Platform Posting System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        if msg.startswith("Value error, "):
            msg = msg.replace("Value error, ", "")
        errors.append(f"{loc}: {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "success": False,
            "error_type": "ValidationError",
            "message": "Input validation failed. Please review the constraints.",
            "details": errors
        }
    )


@app.get("/", tags=["Health"], include_in_schema=False)
async def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept and not accept.startswith("*/*"):
        return RedirectResponse(url="/docs", status_code=status.HTTP_303_SEE_OTHER)

    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs",
        "endpoint": "POST /posting"
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


@app.post(
    "/posting",
    response_model=PostingResponse,
    status_code=status.HTTP_200_OK,
    tags=["Posting"],
    summary="Publish short message across integrated platforms"
)
async def create_posting(payload: PostingRequest) -> PostingResponse:
    posting_service: PostingService = app.state.posting_service
    return await posting_service.broadcast_message(payload.message)
