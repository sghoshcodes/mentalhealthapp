from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.supabase_client import get_supabase_client
from models.mh_index import MentalHealthIndex
from datetime import datetime, timedelta
import numpy as np

router = APIRouter()
supabase = get_supabase_client()
mh_calculator = MentalHealthIndex()

class ScoreRequest(BaseModel):
    user_id: str

class ScoreResponse(BaseModel):
    mh_index: float
    trend: str
    last_updated: datetime
    components: dict

@router.post("/calculate", response_model=ScoreResponse)
async def calculate_mental_health_score(request: ScoreRequest):
    try:
        # Fetch recent entries for the user
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        response = supabase.table('journal_entries').select(
            'created_at, mood_rating, sentiment_score, emotions'
        ).eq('user_id', request.user_id).gte(
            'created_at', start_date.isoformat()
        ).order('created_at', desc=True).execute()
        
        entries = response.data
        
        if not entries:
            raise HTTPException(status_code=404, detail="No entries found for user")
        
        # Calculate MH Index
        mh_index, components = mh_calculator.calculate_index(entries)
        
        # Determine trend
        if len(entries) >= 7:
            recent_scores = [entry['mood_rating'] for entry in entries[:7]]
            older_scores = [entry['mood_rating'] for entry in entries[7:14]] if len(entries) >= 14 else []
            
            if older_scores:
                recent_avg = np.mean(recent_scores)
                older_avg = np.mean(older_scores)
                
                if recent_avg > older_avg + 0.5:
                    trend = "improving"
                elif recent_avg < older_avg - 0.5:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
        else:
            trend = "insufficient_data"
        
        # Store the calculated score
        score_data = {
            'user_id': request.user_id,
            'mh_index': mh_index,
            'trend': trend,
            'components': components,
            'calculated_at': datetime.now().isoformat()
        }
        
        supabase.table('mh_scores').upsert(score_data).execute()
        
        return ScoreResponse(
            mh_index=mh_index,
            trend=trend,
            last_updated=datetime.now(),
            components=components
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Score calculation failed: {str(e)}")

@router.get("/{user_id}")
async def get_mental_health_score(user_id: str):
    try:
        response = supabase.table('mh_scores').select('*').eq(
            'user_id', user_id
                ).order('calculated_at', desc=True).limit(1).execute()
        
        if not response.data:
            # Calculate score if it doesn't exist
            return await calculate_mental_health_score(ScoreRequest(user_id=user_id))
        
        score_data = response.data[0]
        return ScoreResponse(
            mh_index=score_data['mh_index'],
            trend=score_data['trend'],
            last_updated=datetime.fromisoformat(score_data['calculated_at']),
            components=score_data['components']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve score: {str(e)}")

@router.get("/history/{user_id}")
async def get_score_history(user_id: str, days: int = 30):
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        response = supabase.table('mh_scores').select('*').eq(
            'user_id', user_id
        ).gte('calculated_at', start_date.isoformat()).order(
            'calculated_at', desc=False
        ).execute()
        
        return {"history": response.data, "count": len(response.data)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve score history: {str(e)}")