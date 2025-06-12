import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from utils.text_cleaning import TextCleaner
from typing import List, Dict
import re

class JournalClusterer:
    """
    Cluster journal entries to identify themes and patterns in content
    """
    
    def __init__(self, max_clusters: int = 8, min_cluster_size: int = 3):
        self.max_clusters = max_clusters
        self.min_cluster_size = min_cluster_size
        self.text_cleaner = TextCleaner()
        self.vectorizer = None
        self.clustering_model = None
        self.clustering_quality = None
    
    def cluster_entries(self, texts: List[str]) -> List[Dict]:
        """
        Cluster journal entries and extract themes
        
        Args:
            texts: List of journal entry texts
            
        Returns:
            List of cluster information dictionaries
        """
        if len(texts) < 6:
            return [{
                'cluster_id': 0,
                'theme': 'Insufficient data',
                'keywords': [],
                'entry_indices': list(range(len(texts))),
                'description': 'Need more entries for meaningful clustering'
            }]
        
        # Preprocess texts
        processed_texts = [self.text_cleaner.preprocess_for_analysis(text) for text in texts]
        
        # Remove empty texts
        valid_indices = [i for i, text in enumerate(processed_texts) if text.strip()]
        valid_texts = [processed_texts[i] for i in valid_indices]
        
        if len(valid_texts) < 3:
            return [{
                'cluster_id': 0,
                'theme': 'Processing error',
                'keywords': [],
                'entry_indices': valid_indices,
                'description': 'Unable to process texts for clustering'
            }]
        
        # Vectorize texts
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        
        try:
            tfidf_matrix = self.vectorizer.fit_transform(valid_texts)
        except ValueError:
            # Fallback for very small datasets
            self.vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                min_df=1
            )
            tfidf_matrix = self.vectorizer.fit_transform(valid_texts)
        
        # Determine optimal number of clusters
        optimal_clusters = self._find_optimal_clusters(tfidf_matrix)
        
        # Perform clustering
        self.clustering_model = KMeans(
            n_clusters=optimal_clusters,
            random_state=42,
            n_init=10
        )
        cluster_labels = self.clustering_model.fit_predict(tfidf_matrix)
        
        # Calculate clustering quality
        if optimal_clusters > 1:
            self.clustering_quality = silhouette_score(tfidf_matrix, cluster_labels)
        else:
            self.clustering_quality = 0.0
        
        # Extract cluster information
        clusters = []
        feature_names = self.vectorizer.get_feature_names_out()
        
        for cluster_id in range(optimal_clusters):
            cluster_indices = [valid_indices[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
            
            if len(cluster_indices) < self.min_cluster_size and optimal_clusters > 1:
                continue
            
            # Get cluster theme and keywords
            theme, keywords, description = self._extract_cluster_theme(
                cluster_id, tfidf_matrix, cluster_labels, feature_names, texts, cluster_indices
            )
            
            clusters.append({
                'cluster_id': cluster_id,
                'theme': theme,
                'keywords': keywords,
                'entry_indices': cluster_indices,
                'description': description,
                'size': len(cluster_indices)
            })
        
        return clusters
    
    def _find_optimal_clusters(self, tfidf_matrix) -> int:
        """Find optimal number of clusters using silhouette analysis"""
        n_samples = tfidf_matrix.shape[0]
        
        if n_samples < 6:
            return 1
        
        max_k = min(self.max_clusters, n_samples // 2)
        if max_k < 2:
            return 1
        
        best_score = -1
        best_k = 2
        
        for k in range(2, max_k + 1):
            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(tfidf_matrix)
                score = silhouette_score(tfidf_matrix, labels)
                
                if score > best_score:
                    best_score = score
                    best_k = k
            except:
                continue
        
        return best_k if best_score > 0.2 else 1
    
    def _extract_cluster_theme(self, cluster_id: int, tfidf_matrix, cluster_labels, 
                              feature_names, original_texts: List[str], 
                              cluster_indices: List[int]) -> tuple:
        """Extract theme, keywords, and description for a cluster"""
        
        # Get cluster centroid
        cluster_mask = cluster_labels == cluster_id
        cluster_center = np.mean(tfidf_matrix[cluster_mask].toarray(), axis=0)
        
        # Get top keywords
        top_indices = np.argsort(cluster_center)[-10:][::-1]
        keywords = [feature_names[i] for i in top_indices if cluster_center[i] > 0]
        
        # Generate theme based on keywords
        theme = self._generate_theme_name(keywords, original_texts, cluster_indices)
        
        # Generate description
        description = self._generate_cluster_description(keywords, len(cluster_indices))
        
        return theme, keywords[:5], description
    
    def _generate_theme_name(self, keywords: List[str], original_texts: List[str], 
                           cluster_indices: List[int]) -> str:
        """Generate a human-readable theme name"""
        
        # Predefined theme patterns
        theme_patterns = {
            'work': ['work', 'job', 'office', 'meeting', 'project', 'boss', 'colleague'],
            'family': ['family', 'mom', 'dad', 'parent', 'child', 'sister', 'brother'],
            'relationships': ['relationship', 'partner', 'boyfriend', 'girlfriend', 'love', 'date'],
            'health': ['health', 'doctor', 'pain', 'sick', 'medical', 'exercise', 'tired'],
            'anxiety': ['anxious', 'worry', 'nervous', 'stress', 'panic', 'fear'],
            'depression': ['sad', 'depressed', 'down', 'hopeless', 'empty', 'lonely'],
            'happiness': ['happy', 'joy', 'excited', 'good', 'great', 'wonderful'],
            'social': ['friends', 'social', 'party', 'people', 'conversation', 'event'],
            'personal_growth': ['learn', 'grow', 'improve', 'goal', 'achievement', 'progress'],
            'daily_life': ['day', 'morning', 'evening', 'routine', 'daily', 'normal']
        }
        
        # Score each theme
        keyword_str = ' '.join(keywords).lower()
        theme_scores = {}
        
        for theme, pattern_words in theme_patterns.items():
            score = sum(1 for word in pattern_words if word in keyword_str)
            if score > 0:
                theme_scores[theme] = score
        
        # Return best matching theme or generate from keywords
        if theme_scores:
            best_theme = max(theme_scores, key=theme_scores.get)
            return best_theme.replace('_', ' ').title()
        
        # Fallback: use most common keyword
        if keywords:
            return f"{keywords[0].title()} Related"
        
        return "General Thoughts"
    
    def _generate_cluster_description(self, keywords: List[str], size: int) -> str:
        """Generate a description for the cluster"""
        if not keywords:
            return f"A group of {size} entries with similar themes"
        
        keyword_str = ', '.join(keywords[:3])
        return f"Entries focusing on {keyword_str} and related topics ({size} entries)"
    
    def get_clustering_quality(self) -> float:
        """Get the quality score of the last clustering operation"""
        return self.clustering_quality or 0.0
    
    def analyze_cluster_emotions(self, clusters: List[Dict], mood_ratings: List[float], 
                                sentiment_scores: List[float]) -> List[Dict]:
        """Add emotional analysis to clusters"""
        
        for cluster in clusters:
            indices = cluster['entry_indices']
            
            # Calculate average mood and sentiment for this cluster
            cluster_moods = [mood_ratings[i] for i in indices if i < len(mood_ratings)]
            cluster_sentiments = [sentiment_scores[i] for i in indices if i < len(sentiment_scores) and sentiment_scores[i] is not None]
            
            cluster['avg_mood'] = np.mean(cluster_moods) if cluster_moods else None
            cluster['avg_sentiment'] = np.mean(cluster_sentiments) if cluster_sentiments else None
            
            # Determine emotional category
            if cluster['avg_mood'] is not None:
                if cluster['avg_mood'] >= 7:
                    cluster['emotional_category'] = 'positive'
                elif cluster['avg_mood'] <= 4:
                    cluster['emotional_category'] = 'negative'
                else:
                    cluster['emotional_category'] = 'neutral'
            else:
                cluster['emotional_category'] = 'unknown'
            
            # Add insights based on cluster characteristics
            cluster['insights'] = self._generate_cluster_insights(cluster)
        
        return clusters
    
    def _generate_cluster_insights(self, cluster: Dict) -> List[str]:
        """Generate insights for a specific cluster"""
        insights = []
        
        theme = cluster['theme'].lower()
        avg_mood = cluster.get('avg_mood')
        size = cluster['size']
        
        # Size-based insights
        if size >= 5:
            insights.append(f"This is a recurring theme in your journal ({size} entries)")
        
        # Mood-based insights
        if avg_mood is not None:
            if avg_mood >= 7 and 'work' in theme:
                insights.append("Work seems to be a positive aspect of your life")
            elif avg_mood <= 4 and 'work' in theme:
                insights.append("Work appears to be a source of stress")
            elif avg_mood >= 7:
                insights.append(f"{cluster['theme']} entries tend to be positive")
            elif avg_mood <= 4:
                insights.append(f"{cluster['theme']} entries tend to be negative")
        
        # Theme-specific insights
        if 'anxiety' in theme or 'stress' in theme:
            insights.append("Consider stress management techniques for this area")
        elif 'relationship' in theme:
            insights.append("Relationships are an important focus in your journaling")
        elif 'health' in theme:
            insights.append("Health and wellness are key concerns for you")
        
        return insights