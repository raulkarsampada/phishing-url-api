import json
import os

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.features import FEATURE_NAMES, explain, extract_features

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model = joblib.load(os.path.join(BASE, "model.joblib"))
with open(os.path.join(BASE, "metrics.json")) as f:
    metrics = json.load(f)

app = FastAPI(title="Phishing URL Risk Scoring API", version="1.0.0")


class URLRequest(BaseModel):
    url: str = Field(..., min_length=4, max_length=2048, examples=["http://192.168.1.5/secure-login"])

    @field_validator("url")
    @classmethod
    def no_blank_or_spaces(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 4 or " " in v:
            raise ValueError("Provide a valid URL without spaces")
        return v


class URLResponse(BaseModel):
    url: str
    risk_score: float
    verdict: str
    red_flags: list[str]


def verdict_for(score: float) -> str:
    if score < 0.35:
        return "likely safe"
    if score < 0.65:
        return "suspicious"
    return "likely phishing"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/model-info")
def model_info():
    return metrics


@app.post("/check-url", response_model=URLResponse)
def check_url(req: URLRequest):
    try:
        feats = extract_features(req.url)
    except ValueError:
        raise HTTPException(status_code=422, detail="Malformed URL")
    score = float(model.predict_proba([[feats[n] for n in FEATURE_NAMES]])[0][1])
    return URLResponse(url=req.url, risk_score=round(score, 3),
                       verdict=verdict_for(score), red_flags=explain(feats))