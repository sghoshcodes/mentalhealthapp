from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.supabase_client import get_supabase_client
from models.fourier_analysis import FourierAnalyzer
from models.journal_cluster import JournalClusterer
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

router = APIRouter()
supabase = get_supabase_client()
fourier_analyzer = FourierAnalyzer()
clusterer = JournalClusterer()

class TrendResponse(BaseModel):
    mh_index: float = None
    weekly_pattern: dict = None
    dominant_cycle: dict = None
    fourier_peaks: list = []
    fourier_analysis: dict = None
    recommendations: list = []
    insights: list = []

@router.get("/{user_id}")
async def get_user_trends(user_id: str):
    try:
        # Fetch user data (last 60 days for better pattern detection)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        response = supabase.table('journal_entries').select(
            'created_at, mood_rating, sentiment_score, emotions, content'
        ).eq('user_id', user_id).gte(
            'created_at', start_date.isoformat()
        ).order('created_at', desc=False).execute()
        
        entries = response.data
        
        if len(entries) < 7:
            return TrendResponse(
                recommendations=["Keep journaling daily to unlock pattern insights!"],
                insights=["Need at least 7 days of data to detect patterns"]
            )
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(entries)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['day_of_week'] = df['created_at'].dt.dayofweek  # 0=Monday, 6=Sunday
        
        # Create time series data
        mood_series = df.set_index('created_at')['mood_rating'].resample('D').mean().fillna(method='forward')
        sentiment_series = df.set_index('created_at')['sentiment_score'].resample('D').mean().fillna(method='forward')
        
        # Weekly pattern analysis
        weekly_pattern = analyze_weekly_pattern(df)
        
        # Fourier analysis for cycle detection
        fourier_results = fourier_analyzer.analyze_cycles(mood_series.values)
        
        # Get dominant cycle
        dominant_cycle = None
        if fourier_results['peaks']:
            dominant_cycle = {
                'period': fourier_results['peaks'][0]['period'],
                'strength': fourier_results['peaks'][0]['amplitude']
            }
        
        # Generate recommendations
        recommendations = generate_recommendations(df, weekly_pattern, fourier_results)
        
        # Generate insights
        insights = generate_insights(df, weekly_pattern, fourier_results)
        
        # Get latest MH index
        mh_score_response = supabase.table('mh_scores').select('mh_index').eq(
            'user_id', user_id
        ).order('calculated_at', desc=True).limit(1).execute()
        
        mh_index = mh_score_response.data[0]['mh_index'] if mh_score_response.data else None
        
        return TrendResponse(
            mh_index=mh_index,
            weekly_pattern=weekly_pattern,
            dominant_cycle=dominant_cycle,
            fourier_peaks=fourier_results['peaks'][:5],  # Top 5 peaks
            fourier_analysis=fourier_results,
            recommendations=recommendations,
            insights=insights
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")

def analyze_weekly_pattern(df):
    """Analyze weekly mood patterns"""
    weekly_mood = df.groupby('day_of_week')['mood_rating'].mean()
    
    worst_day = weekly_mood.idxmin()
    best_day = weekly_mood.idxmax()
    
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    return {
        'worst_day': int(worst_day),
        'worst_day_name': day_names[worst_day],
        'worst_day_avg': float(weekly_mood[worst_day]),
        'best_day': int(best_day),
        'best_day_name': day_names[best_day],
        'best_day_avg': float(weekly_mood[best_day]),
        'weekly_variation': float(weekly_mood.std())
    }

def generate_recommendations(df, weekly_pattern, fourier_results):
    """Generate personalized recommendations"""
    recommendations = []
    
    # Weekly pattern recommendations
    if weekly_pattern:
        if weekly_pattern['weekly_variation'] > 1.5:
            recommendations.append(
                f"You show significant mood variation throughout the week. "
                f"Consider planning lighter activities on {weekly_pattern['worst_day_name']}s."
            )
        
        if weekly_pattern['worst_day'] < 5:  # Weekday
            recommendations.append(
                "Your mood tends to dip during weekdays. Try incorporating stress-relief activities during work."
            )
    
    # Cycle-based recommendations
    if fourier_results['peaks']:
        dominant_period = fourier_results['peaks'][0]['period']
        
        if 6 <= dominant_period <= 8:  # Weekly cycle
            recommendations.append(
                "You have a strong weekly mood cycle. Consider establishing consistent weekly routines."
            )
        elif 13 <= dominant_period <= 15:  # Bi-weekly cycle
            recommendations.append(
                "You show bi-weekly mood patterns. This might relate to work schedules or social activities."
            )
        elif dominant_period >= 28:  # Monthly cycle
            recommendations.append(
                "Monthly mood cycles detected. Consider tracking external factors like hormones or seasonal changes."
            )
    
    # General recommendations
    avg_mood = df['mood_rating'].mean()
    if avg_mood < 5:
        recommendations.append("Consider speaking with a mental health professional for additional support.")
    elif avg_mood > 7:
        recommendations.append("Great job maintaining positive mental health! Keep up your current practices.")
    
    recent_trend = df.tail(7)['mood_rating'].mean() - df.head(7)['mood_rating'].mean()
    if recent_trend > 1:
        recommendations.append("Your mood has been improving recently - you're on the right track!")
    elif recent_trend < -1:
        recommendations.append("Your mood has been declining. Consider reaching out for support or adjusting your routine.")
    
    return recommendations

def generate_insights(df, weekly_pattern, fourier_results):
    """Generate data-driven insights"""
    insights = []
    
    # Mood stability insights
    mood_std = df['mood_rating'].std()
    if mood_std < 1:
        insights.append("Your mood is very stable day-to-day")
    elif mood_std > 2:
        insights.append("You experience significant mood fluctuations")
    
    # Sentiment vs mood correlation
    if 'sentiment_score' in df.columns and df['sentiment_score'].notna().sum() > 5:
        correlation = df['mood_rating'].corr(df['sentiment_score'])
        if correlation > 0.7:
            insights.append("Your written sentiment strongly matches your mood ratings")
        elif correlation < 0.3:
            insights.append("Your written sentiment often differs from your mood ratings")
    
    # Pattern insights
    if fourier_results['peaks']:
        peak_count = len([p for p in fourier_results['peaks'] if p['amplitude'] > 0.1])
        if peak_count > 3:
            insights.append("You have multiple overlapping mood cycles")
        elif peak_count == 1:
            insights.append("You have one dominant mood cycle")
    
    # Consistency insights
    entry_frequency = len(df) / 60  # entries per day over 60 days
    if entry_frequency > 0.8:
        insights.append("You're very consistent with journaling")
    elif entry_frequency < 0.3:
        insights.append("More frequent journaling could provide better insights")
    
    return insights

@router.get("/cluster/{user_id}")
async def get_journal_clusters(user_id: str):
    """Get journal entry clusters and themes"""
    try:
        response = supabase.table('journal_entries').select(
            'content, mood_rating, sentiment_score, created_at'
        ).eq('user_id', user_id).execute()
        
        entries = response.data
        
        if len(entries) < 10:
            return {"message": "Need at least 10 entries for clustering analysis"}
        
        # Extract text content
        texts = [entry['content'] for entry in entries]
        
        # Perform clustering
        clusters = clusterer.cluster_entries(texts)
        
        # Add metadata to clusters
        for i, cluster in enumerate(clusters):
            cluster_indices = cluster['entry_indices']
            cluster_entries = [entries[j] for j in cluster_indices]
            
            cluster['avg_mood'] = np.mean([e['mood_rating'] for e in cluster_entries])
            cluster['avg_sentiment'] = np.mean([e['sentiment_score'] for e in cluster_entries if e['sentiment_score']])
            cluster['entry_count'] = len(cluster_entries)
            cluster['date_range'] = {
                'start': min(e['created_at'] for e in cluster_entries),
                'end': max(e['created_at'] for e in cluster_entries)
            }
        
        return {
            "clusters": clusters,
            "summary": {
                "total_clusters": len(clusters),
                "total_entries": len(entries),
                "clustering_quality": clusterer.get_clustering_quality()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clustering analysis failed: {str(e)}")