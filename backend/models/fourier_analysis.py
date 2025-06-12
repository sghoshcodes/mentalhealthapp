import numpy as np
from scipy.fft import fft, fftfreq
from scipy.signal import find_peaks
from typing import List, Dict, Tuple
import pandas as pd

class FourierAnalyzer:
    """
    Fourier analysis for detecting cyclical patterns in mood data
    """
    
    def __init__(self, min_period: float = 2.0, max_period: float = 60.0):
        self.min_period = min_period  # Minimum cycle length in days
        self.max_period = max_period  # Maximum cycle length in days
    
    def analyze_cycles(self, mood_data: np.ndarray, sampling_rate: float = 1.0) -> Dict:
        """
        Analyze cyclical patterns in mood data using Fourier Transform
        
        Args:
            mood_data: Array of mood values (time series)
            sampling_rate: Samples per day (default 1.0 for daily data)
        
        Returns:
            Dictionary containing analysis results
        """
        if len(mood_data) < 4:
            return {
                'peaks': [],
                'frequencies': [],
                'amplitudes': [],
                'dominant_period': None,
                'analysis_quality': 'insufficient_data'            }
        
        # Preprocess data
        processed_data = self._preprocess_data(mood_data)
        
        # Apply FFT
        fft_values = fft(processed_data)
        frequencies = fftfreq(len(processed_data), d=1/sampling_rate)
        
        # Calculate amplitudes (magnitude of complex numbers)
        amplitudes = np.abs(fft_values)
        
        # Convert frequencies to periods (days)
        periods = np.where(frequencies > 0, 1/frequencies, np.inf)
        
        # Filter for meaningful periods
        valid_mask = (periods >= self.min_period) & (periods <= self.max_period) & (frequencies > 0)
        valid_periods = periods[valid_mask]
        valid_amplitudes = amplitudes[valid_mask]
        valid_frequencies = frequencies[valid_mask]
        
        if len(valid_periods) == 0:
            return {
                'peaks': [],
                'frequencies': [],
                'amplitudes': [],
                'dominant_period': None,
                'analysis_quality': 'no_valid_periods'
            }
        
        # Find peaks in the amplitude spectrum
        peaks, properties = find_peaks(
            valid_amplitudes,
            height=np.max(valid_amplitudes) * 0.1,  # At least 10% of max amplitude
            distance=max(1, len(valid_amplitudes) // 20)  # Minimum distance between peaks
        )
        
        # Extract peak information
        peak_info = []
        for peak_idx in peaks:
            peak_info.append({
                'period': float(valid_periods[peak_idx]),
                'amplitude': float(valid_amplitudes[peak_idx]),
                'frequency': float(valid_frequencies[peak_idx]),
                'relative_strength': float(valid_amplitudes[peak_idx] / np.max(valid_amplitudes))
            })
        
        # Sort by amplitude (strongest first)
        peak_info.sort(key=lambda x: x['amplitude'], reverse=True)
        
        # Determine dominant period
        dominant_period = peak_info[0]['period'] if peak_info else None
        
        # Assess analysis quality
        quality = self._assess_analysis_quality(mood_data, peak_info)
        
        return {
            'peaks': peak_info,
            'frequencies': valid_frequencies.tolist(),
            'amplitudes': valid_amplitudes.tolist(),
            'periods': valid_periods.tolist(),
            'dominant_period': dominant_period,
            'analysis_quality': quality,
            'data_length': len(mood_data),
            'nyquist_period': 2.0  # Minimum detectable period for daily sampling
        }
    
    def _preprocess_data(self, data: np.ndarray) -> np.ndarray:
        """Preprocess mood data for Fourier analysis"""
        # Handle missing values
        data = np.array(data, dtype=float)
        
        # Remove NaN values by interpolation
        if np.any(np.isnan(data)):
            valid_indices = ~np.isnan(data)
            if np.sum(valid_indices) < len(data) * 0.5:
                # Too many missing values
                return data[valid_indices]
            
            # Linear interpolation for missing values
            data = pd.Series(data).interpolate().values
        
        # Remove linear trend (detrend)
        x = np.arange(len(data))
        coeffs = np.polyfit(x, data, 1)
        trend = np.polyval(coeffs, x)
        detrended = data - trend
        
        # Apply window function to reduce spectral leakage
        window = np.hanning(len(detrended))
        windowed = detrended * window
        
        return windowed
    
    def _assess_analysis_quality(self, original_data: np.ndarray, peaks: List[Dict]) -> str:
        """Assess the quality of the Fourier analysis"""
        data_length = len(original_data)
        
        if data_length < 14:
            return 'poor_short_series'
        elif data_length < 30:
            return 'fair_medium_series'
        
        if not peaks:
            return 'poor_no_peaks'
        
        # Check if strongest peak is significantly above noise
        if peaks[0]['relative_strength'] < 0.3:
            return 'fair_weak_signal'
        elif peaks[0]['relative_strength'] > 0.7:
            return 'excellent_strong_signal'
        else:
            return 'good_moderate_signal'
    
    def detect_phase_disruptions(self, mood_data: np.ndarray, dominant_period: float) -> List[Dict]:
        """
        Detect points where the dominant cycle is disrupted
        (e.g., depression spikes that break the normal pattern)
        """
        if dominant_period is None or len(mood_data) < dominant_period * 2:
            return []
        
        # Generate expected pattern based on dominant cycle
        x = np.arange(len(mood_data))
        expected_pattern = np.sin(2 * np.pi * x / dominant_period)
        
        # Normalize both signals
        mood_normalized = (mood_data - np.mean(mood_data)) / np.std(mood_data)
        expected_normalized = expected_pattern / np.std(expected_pattern)
        
        # Calculate residuals
        residuals = np.abs(mood_normalized - expected_normalized)
        
        # Find disruption points (residuals above threshold)
        threshold = np.mean(residuals) + 2 * np.std(residuals)
        disruption_indices = np.where(residuals > threshold)[0]
        
        disruptions = []
        for idx in disruption_indices:
            disruptions.append({
                'day_index': int(idx),
                'severity': float(residuals[idx]),
                'mood_value': float(mood_data[idx]),
                'expected_value': float(expected_pattern[idx] + np.mean(mood_data)),
                'deviation': float(mood_data[idx] - (expected_pattern[idx] + np.mean(mood_data)))
            })
        
        return disruptions
    
    def generate_cycle_insights(self, analysis_results: Dict) -> List[str]:
        """Generate human-readable insights from cycle analysis"""
        insights = []
        
        if analysis_results['analysis_quality'] in ['poor_short_series', 'poor_no_peaks']:
            insights.append("Not enough data to detect reliable patterns. Keep journaling!")
            return insights
        
        peaks = analysis_results['peaks']
        
        if not peaks:
            insights.append("No clear cyclical patterns detected in your mood data.")
            return insights
        
        # Dominant cycle insights
        dominant = peaks[0]
        period = dominant['period']
        strength = dominant['relative_strength']
        
        if 6 <= period <= 8:
            insights.append(f"Strong weekly pattern detected ({period:.1f} day cycle)")
            insights.append("Your mood follows a weekly rhythm - consider weekly planning")
        elif 13 <= period <= 15:
            insights.append(f"Bi-weekly pattern detected ({period:.1f} day cycle)")
            insights.append("You might benefit from bi-weekly goal setting")
        elif 28 <= period <= 32:
            insights.append(f"Monthly pattern detected ({period:.1f} day cycle)")
            insights.append("Consider tracking monthly external factors")
        else:
            insights.append(f"Unique {period:.1f}-day cycle detected in your mood")
        
        if strength > 0.7:
            insights.append("This pattern is very consistent and reliable")
        elif strength > 0.4:
            insights.append("This pattern is moderately consistent")
        else:
            insights.append("This pattern is weak but detectable")
        
        # Multiple cycles
        if len(peaks) > 1:
            insights.append(f"You have {len(peaks)} overlapping mood cycles")
            
            # Check for harmonic relationships
            for i, peak in enumerate(peaks[1:], 1):
                ratio = dominant['period'] / peak['period']
                if 1.8 <= ratio <= 2.2:
                    insights.append(f"Cycle {i+1} appears to be a harmonic of your main cycle")
        
        return insights
    
    def predict_mood_trend(self, mood_data: np.ndarray, days_ahead: int = 7) -> np.ndarray:
        """
        Predict mood trend based on detected cycles
        Simple prediction using dominant frequencies
        """
        analysis = self.analyze_cycles(mood_data)
        
        if not analysis['peaks']:
            # No pattern detected, return flat trend at recent average
            recent_avg = np.mean(mood_data[-7:]) if len(mood_data) >= 7 else np.mean(mood_data)
            return np.full(days_ahead, recent_avg)
        
        # Use top 3 cycles for prediction
        prediction = np.zeros(days_ahead)
        base_level = np.mean(mood_data)
        
        for peak in analysis['peaks'][:3]:
            period = peak['period']
            amplitude = peak['amplitude'] * 0.5  # Dampen amplitude for prediction
            
            # Generate future values for this cycle
            future_indices = np.arange(len(mood_data), len(mood_data) + days_ahead)
            cycle_component = amplitude * np.sin(2 * np.pi * future_indices / period)
            prediction += cycle_component
        
        # Add base level and ensure reasonable bounds
        prediction += base_level
        prediction = np.clip(prediction, 1, 10)  # Mood scale bounds
        
        return prediction