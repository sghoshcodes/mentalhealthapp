import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

class MentalHealthIndex:
    """
    Calculate a comprehensive Mental Health Index based on multiple factors:
    - Mood ratings
    - Sentiment scores
    - Consistency of journaling
    - Emotional variance
    - Trend direction
    """
    
    def __init__(self):
        self.weights = {
            'mood_average': 0.3,
            'mood_stability': 0.2,
            'sentiment_average': 0.2,
            'consistency': 0.15,
            'trend': 0.15
        }
    
    def calculate_index(self, entries: List[Dict]) -> Tuple[float, Dict]:
        """
        Calculate Mental Health Index from journal entries
        Returns: (index_score, components)
        """
        if not entries:
            return 0.0, {}
        
        # Calculate individual components
        mood_avg = self._calculate_mood_average(entries)
        mood_stability = self._calculate_mood_stability(entries)
        sentiment_avg = self._calculate_sentiment_average(entries)
        consistency = self._calculate_consistency(entries)
        trend = self._calculate_trend(entries)
        
        # Calculate weighted index
        index = (
            mood_avg * self.weights['mood_average'] +
            mood_stability * self.weights['mood_stability'] +
            sentiment_avg * self.weights['sentiment_average'] +
            consistency * self.weights['consistency'] +
            trend * self.weights['trend']
        )
        
        # Normalize to 0-10 scale
        index = max(0, min(10, index))
        
        components = {
            'mood_average': mood_avg,
            'mood_stability': mood_stability,
            'sentiment_average': sentiment_avg,
            'consistency': consistency,
            'trend': trend,
            'weights': self.weights
        }
        
        return index, components
    
    def _calculate_mood_average(self, entries: List[Dict]) -> float:
        """Calculate average mood rating (0-10 scale)"""
        moods = [entry['mood_rating'] for entry in entries if entry.get('mood_rating')]
        return np.mean(moods) if moods else 5.0
    
    def _calculate_mood_stability(self, entries: List[Dict]) -> float:
        """Calculate mood stability (lower variance = higher stability)"""
        moods = [entry['mood_rating'] for entry in entries if entry.get('mood_rating')]
        if len(moods) < 2:
            return 5.0
        
        variance = np.var(moods)
        # Convert variance to stability score (invert and normalize)
        # Variance of 0 = stability of 10, variance of 9 = stability of 1
        stability = max(1, 10 - variance)
        return stability
    
    def _calculate_sentiment_average(self, entries: List[Dict]) -> float:
        """Calculate average sentiment score (convert to 0-10 scale)"""
        sentiments = [
            entry['sentiment_score'] for entry in entries 
            if entry.get('sentiment_score') is not None
        ]
        
        if not sentiments:
            return 5.0
        
        # Convert from 0-1 scale to 0-10 scale
        avg_sentiment = np.mean(sentiments) * 10
        return avg_sentiment
    
    def _calculate_consistency(self, entries: List[Dict]) -> float:
        """Calculate journaling consistency score"""
        if not entries:
            return 0.0
        
        # Get date range
        dates = [datetime.fromisoformat(entry['created_at'].replace('Z', '+00:00')) for entry in entries]
        dates.sort()
        
        if len(dates) < 2:
            return 5.0
        
        # Calculate expected vs actual entries
        date_range = (dates[-1] - dates[0]).days + 1
        actual_entries = len(entries)
        consistency_ratio = min(1.0, actual_entries / date_range)
        
        # Convert to 0-10 scale
        return consistency_ratio * 10
    
    def _calculate_trend(self, entries: List[Dict]) -> float:
        """Calculate recent trend direction"""
        if len(entries) < 4:
            return 5.0
        
        # Sort by date
        sorted_entries = sorted(entries, key=lambda x: x['created_at'])
        
        # Compare recent half vs older half
        mid_point = len(sorted_entries) // 2
        recent_moods = [e['mood_rating'] for e in sorted_entries[mid_point:]]
        older_moods = [e['mood_rating'] for e in sorted_entries[:mid_point]]
        
        recent_avg = np.mean(recent_moods)
        older_avg = np.mean(older_moods)
        
        # Calculate trend score
        trend_diff = recent_avg - older_avg
        
        # Convert to 0-10 scale (0 = declining, 5 = stable, 10 = improving)
        trend_score = 5 + (trend_diff * 2)  # Scale the difference
        return max(0, min(10, trend_score))
    
    def get_interpretation(self, index: float) -> str:
        """Get human-readable interpretation of the index"""
        if index >= 8:
            return "Excellent mental health"
        elif index >= 6.5:
            return "Good mental health"
        elif index >= 5:
            return "Moderate mental health"
        elif index >= 3.5:
            return "Concerning mental health"
        else:
            return "Poor mental health - consider seeking support"
    
    def get_recommendations(self, components: Dict) -> List[str]:
        """Get personalized recommendations based on components"""
        recommendations = []
        
        if components['mood_average'] < 5:
            recommendations.append("Focus on activities that boost your mood")
        
        if components['mood_stability'] < 5:
            recommendations.append("Work on developing emotional regulation techniques")
        
        if components['sentiment_average'] < 5:
            recommendations.append("Practice positive self-talk and gratitude")
        
        if components['consistency'] < 6:
            recommendations.append("Try to journal more regularly for better insights")
        
        if components['trend'] < 4:
            recommendations.append("Your mood trend is declining - consider seeking support")
        elif components['trend'] > 7:
            recommendations.append("Great job! Your mood is trending upward")
        
        return recommendations