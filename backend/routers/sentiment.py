from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from utils.text_cleaning import TextCleaner
import torch

router = APIRouter()

# Initialize models
sentiment_analyzer = pipeline(
    "sentiment-analysis", 
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    return_all_scores=True
)

emotion_analyzer = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    return_all_scores=True
)

text_cleaner = TextCleaner()

class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    sentiment_score: float
    sentiment_label: str
    emotions: dict
    confidence: float
    text_metrics: dict

@router.post("/", response_model=SentimentResponse)
async def analyze_sentiment(request: SentimentRequest):
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Clean text
        cleaned_text = text_cleaner.clean_text(request.text)
        
        # Sentiment analysis
        sentiment_results = sentiment_analyzer(cleaned_text)
        
        # Convert to normalized score (0-1, where 1 is most positive)
        sentiment_scores = {result['label']: result['score'] for result in sentiment_results[0]}
        
        # Calculate normalized sentiment score
        if 'LABEL_2' in sentiment_scores:  # Positive
            positive_score = sentiment_scores['LABEL_2']
        elif 'positive' in sentiment_scores:
            positive_score = sentiment_scores['positive']
        else:
            positive_score = 0.5
            
        if 'LABEL_0' in sentiment_scores:  # Negative
            negative_score = sentiment_scores['LABEL_0']
        elif 'negative' in sentiment_scores:
            negative_score = sentiment_scores['negative']
        else:
            negative_score = 0.5
        
        # Normalize to 0-1 scale
        sentiment_score = (positive_score - negative_score + 1) / 2
        
        # Determine label
        if sentiment_score > 0.6:
            sentiment_label = "positive"
        elif sentiment_score < 0.4:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        # Emotion analysis
        emotion_results = emotion_analyzer(cleaned_text)
        emotions = {result['label']: result['score'] for result in emotion_results[0]}
        
        # Get confidence (highest emotion score)
        confidence = max(emotions.values())
        
        # Extract text metrics
        text_metrics = text_cleaner.extract_emotional_indicators(request.text)
        
        return SentimentResponse(
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            emotions=emotions,
            confidence=confidence,
            text_metrics=text_metrics
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/batch")
async def analyze_batch_sentiment(texts: list[str]):
    """Analyze sentiment for multiple texts"""
    results = []
    
    for text in texts:
        try:
            request = SentimentRequest(text=text)
            result = await analyze_sentiment(request)
            results.append(result.dict())
        except Exception as e:
            results.append({
                "error": str(e),
                "text": text[:50] + "..." if len(text) > 50 else text
            })
    
    return {"results": results, "count": len(results)}