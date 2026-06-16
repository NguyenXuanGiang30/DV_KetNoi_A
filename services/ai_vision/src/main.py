"""
A4: AI Vision Service — Smart Campus
Cung cấp API phát hiện vật thể và face-match cho Camera Stream (cặp 1) và Core Business (cặp 2).
"""

import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

SERVICE_NAME = os.getenv("SERVICE_NAME", "ai-vision")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "smart-campus-dev-token-2026")

app = FastAPI(
    title="Smart Campus — AI Vision Service",
    version=SERVICE_VERSION,
    description="Dịch vụ AI phân tích hình ảnh: phát hiện vật thể (detect) và đối chiếu khuôn mặt (face-match).",
)

# ── In-memory storage ──
DETECTIONS: dict = {}


# ── Models ──
class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    version: str
    time: str


class DetectionRequest(BaseModel):
    camera_id: str = Field(..., min_length=3, examples=["cam-gate-a"])
    image_url: Optional[str] = Field(default=None, examples=["https://example.com/frame.jpg"])
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded image")
    timestamp: Optional[str] = None
    motion_score: Optional[float] = None


class BBox(BaseModel):
    x: int = 120
    y: int = 80
    width: int = 210
    height: int = 430


class DetectionItem(BaseModel):
    label: str
    confidence: float
    bbox: BBox


class DetectionResponse(BaseModel):
    detection_id: str
    request_id: Optional[str] = None
    camera_id: str
    timestamp: str
    detections: List[DetectionItem]
    unknown_person: bool
    risk_level: str  # low, medium, high


class FaceMatchRequest(BaseModel):
    camera_id: str = Field(..., min_length=3)
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    reference_face_id: Optional[str] = None


class FaceMatchResponse(BaseModel):
    match_id: str
    camera_id: str
    matched: bool
    confidence: float
    model_version: str
    timestamp: str


class ModelInfo(BaseModel):
    model_name: str
    model_version: str
    supported_labels: List[str]
    max_image_size_mb: int


class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: Optional[str] = None


# ── Auth ──
def verify_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "https://smart-campus.local/problems/unauthorized",
                    "title": "Unauthorized", "status": 401,
                    "detail": "Missing Authorization header"},
        )
    expected = f"Bearer {AUTH_TOKEN}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "https://smart-campus.local/problems/unauthorized",
                    "title": "Unauthorized", "status": 401,
                    "detail": "Invalid bearer token"},
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── Endpoints ──

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok", service=SERVICE_NAME, version=SERVICE_VERSION, time=now_iso()
    )


@app.post("/detect", response_model=DetectionResponse, dependencies=[Depends(verify_token)])
def detect_image(req: DetectionRequest):
    """Cặp 1: Camera Stream gọi — phát hiện vật thể trong ảnh."""
    if not req.image_url and not req.image_base64:
        raise HTTPException(
            status_code=400,
            detail={"type": "https://smart-campus.local/problems/invalid-image",
                    "title": "Invalid image", "status": 400,
                    "detail": "image_url or image_base64 is required",
                    "instance": "/detect"},
        )

    detection_id = f"DET-{uuid.uuid4().hex[:8].upper()}"
    ts = req.timestamp or now_iso()

    # Mock detection logic — giả lập kết quả nhận diện
    import random
    labels = ["person", "vehicle", "unknown"]
    label = random.choice(labels)
    confidence = round(random.uniform(0.70, 0.99), 2)
    unknown_person = label == "person" and confidence < 0.85
    risk_level = "high" if unknown_person else ("medium" if label == "unknown" else "low")

    result = DetectionResponse(
        detection_id=detection_id,
        camera_id=req.camera_id,
        timestamp=ts,
        detections=[
            DetectionItem(
                label=label,
                confidence=confidence,
                bbox=BBox(x=120, y=80, width=210, height=430),
            )
        ],
        unknown_person=unknown_person,
        risk_level=risk_level,
    )

    DETECTIONS[detection_id] = result.model_dump()
    return result


@app.post("/vision/face-match", response_model=FaceMatchResponse, dependencies=[Depends(verify_token)])
def face_match(req: FaceMatchRequest):
    """Cặp 2: Core Business gọi — đối chiếu khuôn mặt."""
    import random

    match_id = f"FM-{uuid.uuid4().hex[:8].upper()}"
    matched = random.choice([True, True, True, False])  # 75% match
    confidence = round(random.uniform(0.80, 0.99), 2) if matched else round(random.uniform(0.20, 0.50), 2)

    return FaceMatchResponse(
        match_id=match_id,
        camera_id=req.camera_id,
        matched=matched,
        confidence=confidence,
        model_version="mock-v1.0",
        timestamp=now_iso(),
    )


@app.get("/vision/detections/{detection_id}", dependencies=[Depends(verify_token)])
def get_detection(detection_id: str):
    """Truy vấn kết quả phát hiện theo ID."""
    if detection_id not in DETECTIONS:
        raise HTTPException(
            status_code=404,
            detail={"type": "https://smart-campus.local/problems/not-found",
                    "title": "Not Found", "status": 404,
                    "detail": f"Detection {detection_id} does not exist",
                    "instance": f"/vision/detections/{detection_id}"},
        )
    return DETECTIONS[detection_id]


@app.get("/vision/models/info", response_model=ModelInfo, dependencies=[Depends(verify_token)])
def model_info():
    """Thông tin mô hình AI đang sử dụng."""
    return ModelInfo(
        model_name="smart-campus-detector-mock",
        model_version="mock-v1.0",
        supported_labels=["person", "vehicle", "unknown"],
        max_image_size_mb=10,
    )
