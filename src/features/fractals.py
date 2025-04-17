import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass

@dataclass
class HarmonicPattern:
    name: str
    direction: int  # 1 for bullish, -1 for bearish
    probability: float

class FractalAnalyzer:
    def __init__(self, filter_bw: bool = False):
        self.filter_bw = filter_bw
        
    def is_regular_fractal(self, data: pd.DataFrame, idx: int, mode: int) -> bool:
        """Regular fractal pattern recognition"""
        if idx < 4:
            return False
            
        if mode == 1:  # Bullish fractal
            return (data['high'].iloc[idx-4] < data['high'].iloc[idx-3] and 
                   data['high'].iloc[idx-3] < data['high'].iloc[idx-2] and 
                   data['high'].iloc[idx-2] > data['high'].iloc[idx-1] and 
                   data['high'].iloc[idx-1] > data['high'].iloc[idx])
        else:  # Bearish fractal
            return (data['low'].iloc[idx-4] > data['low'].iloc[idx-3] and 
                   data['low'].iloc[idx-3] > data['low'].iloc[idx-2] and 
                   data['low'].iloc[idx-2] < data['low'].iloc[idx-1] and 
                   data['low'].iloc[idx-1] < data['low'].iloc[idx])

    def is_bw_fractal(self, data: pd.DataFrame, idx: int, mode: int) -> bool:
        """Bill Williams fractal pattern recognition"""
        if idx < 4:
            return False
            
        if mode == 1:  # Bullish fractal
            return (data['high'].iloc[idx-4] < data['high'].iloc[idx-2] and 
                   data['high'].iloc[idx-3] <= data['high'].iloc[idx-2] and 
                   data['high'].iloc[idx-2] >= data['high'].iloc[idx-1] and 
                   data['high'].iloc[idx-2] > data['high'].iloc[idx])
        else:  # Bearish fractal
            return (data['low'].iloc[idx-4] > data['low'].iloc[idx-2] and 
                   data['low'].iloc[idx-3] >= data['low'].iloc[idx-2] and 
                   data['low'].iloc[idx-2] <= data['low'].iloc[idx-1] and 
                   data['low'].iloc[idx-2] < data['low'].iloc[idx])

    def identify_fractals(self, data: pd.DataFrame) -> Tuple[List[bool], List[bool]]:
        """Identify both bullish and bearish fractals in the data"""
        length = len(data)
        top_fractals = [False] * length
        bottom_fractals = [False] * length
        
        for i in range(4, length):
            if self.filter_bw:
                top_fractals[i] = self.is_regular_fractal(data, i, 1)
                bottom_fractals[i] = self.is_regular_fractal(data, i, -1)
            else:
                top_fractals[i] = self.is_bw_fractal(data, i, 1)
                bottom_fractals[i] = self.is_bw_fractal(data, i, -1)
                
        return top_fractals, bottom_fractals

    def calculate_ratios(self, points: List[float]) -> Tuple[float, float, float, float]:
        """Calculate harmonic pattern ratios"""
        x, a, b, c, d = points
        xab = abs(b-a)/abs(x-a) if abs(x-a) > 0 else 0
        xad = abs(a-d)/abs(x-a) if abs(x-a) > 0 else 0
        abc = abs(b-c)/abs(a-b) if abs(a-b) > 0 else 0
        bcd = abs(c-d)/abs(b-c) if abs(b-c) > 0 else 0
        return xab, xad, abc, bcd

    def identify_harmonic_patterns(self, data: pd.DataFrame, idx: int) -> List[HarmonicPattern]:
        """Identify harmonic patterns at the current index"""
        patterns = []
        if idx < 4:
            return patterns

        # Get the last 5 significant points
        points = self._get_significant_points(data, idx)
        if not points:
            return patterns

        xab, xad, abc, bcd = self.calculate_ratios(points)
        
        # Check for various harmonic patterns
        for direction in [1, -1]:  # 1 for bullish, -1 for bearish
            if self._is_bat_pattern(xab, xad, abc, bcd, direction):
                patterns.append(HarmonicPattern("Bat", direction, 0.8))
            if self._is_butterfly_pattern(xab, xad, abc, bcd, direction):
                patterns.append(HarmonicPattern("Butterfly", direction, 0.8))
            if self._is_gartley_pattern(xab, xad, abc, bcd, direction):
                patterns.append(HarmonicPattern("Gartley", direction, 0.7))
            if self._is_crab_pattern(xab, xad, abc, bcd, direction):
                patterns.append(HarmonicPattern("Crab", direction, 0.9))

        return patterns

    def _is_bat_pattern(self, xab: float, xad: float, abc: float, bcd: float, mode: int) -> bool:
        return (0.382 <= xab <= 0.5 and
                abc >= 0.382 and abc <= 0.886 and
                bcd >= 1.618 and bcd <= 2.618 and
                xad <= 0.886 and
                (mode == 1 and bcd > 0 or mode == -1 and bcd < 0))

    def _is_butterfly_pattern(self, xab: float, xad: float, abc: float, bcd: float, mode: int) -> bool:
        return (xab <= 0.786 and
                abc >= 0.382 and abc <= 0.886 and
                bcd >= 1.618 and bcd <= 2.618 and
                xad >= 1.27 and xad <= 1.618 and
                (mode == 1 and bcd > 0 or mode == -1 and bcd < 0))

    def _is_gartley_pattern(self, xab: float, xad: float, abc: float, bcd: float, mode: int) -> bool:
        return (0.5 <= xab <= 0.618 and
                abc >= 0.382 and abc <= 0.886 and
                bcd >= 1.13 and bcd <= 2.618 and
                xad >= 0.75 and xad <= 0.875 and
                (mode == 1 and bcd > 0 or mode == -1 and bcd < 0))

    def _is_crab_pattern(self, xab: float, xad: float, abc: float, bcd: float, mode: int) -> bool:
        return (0.75 <= xab <= 0.875 and
                abc >= 0.382 and abc <= 0.886 and
                bcd >= 2.0 and bcd <= 3.618 and
                xad >= 1.5 and xad <= 1.625 and
                (mode == 1 and bcd > 0 or mode == -1 and bcd < 0))

    def _get_significant_points(self, data: pd.DataFrame, idx: int) -> Optional[List[float]]:
        """Get the last 5 significant price points for pattern recognition"""
        if idx < 4:
            return None
            
        # Simplified version - using last 5 points
        points = []
        for i in range(idx-4, idx+1):
            points.append(data['close'].iloc[i])
        return points

    def get_fractal_features(self, data: pd.DataFrame) -> Dict[str, List[float]]:
        """Generate fractal-based features for the neural network"""
        top_fractals, bottom_fractals = self.identify_fractals(data)
        
        features = {
            'top_fractals': top_fractals,
            'bottom_fractals': bottom_fractals,
            'distance_to_top': [],
            'distance_to_bottom': [],
            'pattern_signals': []
        }
        
        last_top_idx = -1
        last_bottom_idx = -1
        
        for i in range(len(data)):
            if top_fractals[i]:
                last_top_idx = i
            if bottom_fractals[i]:
                last_bottom_idx = i
                
            features['distance_to_top'].append(i - last_top_idx if last_top_idx != -1 else -1)
            features['distance_to_bottom'].append(i - last_bottom_idx if last_bottom_idx != -1 else -1)
            
            # Add harmonic pattern signals
            patterns = self.identify_harmonic_patterns(data, i)
            pattern_signal = sum(p.direction * p.probability for p in patterns)
            features['pattern_signals'].append(pattern_signal)
        
        return features
