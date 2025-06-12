from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from routers import sentiment, score, trend
import uvicorn

app = FastAPI(title="Mental Health Journal API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["sentiment"])
app.include_router(score.router, prefix="/api/score", tags=["score"])
app.include_router(trend.router, prefix="/api/trends", tags=["trends"])

@app.get("/")
async def root():
    return {"message": "Mental Health Journal API", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "mental-health-api"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)