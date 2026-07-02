import time
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from model import ToxicClassifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GuardianAI-Backend")

app = FastAPI(
    title="GuardianAI API",
    description="FastAPI Backend for BERT Multi-Label Toxicity Classification",
    version="1.0.0"
)

# Enable CORS for frontend web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Classifier
classifier = ToxicClassifier()

@app.on_event("startup")
def startup_event():
    """Warm up the classifier by loading the BERT model weights on server start."""
    try:
        logger.info("Initializing BERT Classifier and loading weights...")
        start_time = time.time()
        classifier.load_model()
        logger.info(f"Classifier weights loaded successfully in {time.time() - start_time:.2f} seconds.")
    except Exception as e:
        logger.error(f"Error loading model during startup: {str(e)}")
        logger.warning("The model directory might be missing. The API will fall back to lazy-loading or error reporting on demand.")

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Comment text to analyze")
    threshold: float = Field(0.4, ge=0.05, le=0.95, description="Classification confidence threshold")

class LabelScore(BaseModel):
    probability: float
    flagged: bool

@app.post("/api/analyze", response_model=dict[str, LabelScore])
def analyze_text(request: AnalyzeRequest):
    """
    Analyzes the input text for 6 toxic dimensions:
    - toxic, severe_toxic, obscene, threat, insult, identity_hate
    """
    if not classifier.is_loaded:
        try:
            logger.info("Model was not loaded on startup. Attempting on-demand load...")
            classifier.load_model()
        except FileNotFoundError as fnf:
            raise HTTPException(status_code=503, detail=str(fnf))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load classifier: {str(e)}")

    try:
        results = classifier.predict(request.text, threshold=request.threshold)
        return results
    except Exception as e:
        logger.error(f"Inference error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Inference engine error: {str(e)}")

@app.get("/api/health")
def health_check():
    """Endpoint for checking api server health and model loaded status."""
    return {
        "status": "online",
        "model_loaded": classifier.is_loaded,
        "device": str(classifier.device),
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    # Launch uvicorn programmatically when executed directly
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
