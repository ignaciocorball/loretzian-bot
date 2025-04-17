import numpy as np
import pandas as pd
import talib
from typing import Dict, List, Tuple
from src.utils.config import TRADING_CONFIG

class TechnicalAnalyzer:
    def __init__(self):
        self.config = TRADING_CONFIG

    def calculate_technical_features(self, df: pd.DataFrame) -> Dict[str, List[float]]:
        """Calculate technical indicators and their signals"""
        features = {}
        
        # Calculate Bollinger Bands
        upper, middle, lower = talib.BBANDS(
            df['close'],
            timeperiod=self.config['bollinger_length'],
            nbdevup=self.config['bollinger_std'],
            nbdevdn=self.config['bollinger_std']
        )
        
        # Calculate BB position
        bb_position = (df['close'] - lower) / (upper - lower)
        features['bb_position'] = bb_position.tolist()
        
        # Calculate BB width
        bb_width = (upper - lower) / middle
        features['bb_width'] = bb_width.tolist()
        
        # Calculate RSI
        rsi = talib.RSI(df['close'], timeperiod=self.config['rsi_length'])
        features['rsi'] = rsi.tolist()
        
        # Generate technical signals
        features['tech_signal'] = self._generate_technical_signals(
            df['close'].values,
            bb_position.values,
            rsi.values
        )
        
        return features

    def _generate_technical_signals(self, 
                                  prices: np.ndarray, 
                                  bb_position: np.ndarray, 
                                  rsi: np.ndarray) -> List[float]:
        """Generate combined technical signals"""
        signals = []
        
        for i in range(len(prices)):
            signal = 0
            
            # RSI signals
            if rsi[i] < 30:
                signal += 1
            elif rsi[i] > 70:
                signal -= 1
                
            # Bollinger Bands signals
            if bb_position[i] < 0.2:  # Price near lower band
                signal += 1
            elif bb_position[i] > 0.8:  # Price near upper band
                signal -= 1
                
            signals.append(signal)
            
        return signals

    def predict_price_movement(self, df: pd.DataFrame) -> Tuple[float, float]:
        """Predict price movement using technical indicators"""
        features = self.calculate_technical_features(df)
        
        # Simple prediction based on technical signals
        last_signal = features['tech_signal'][-1]
        last_price = df['close'].iloc[-1]
        
        # Calculate predicted movement
        bb_width = features['bb_width'][-1]
        predicted_move = last_price * bb_width * 0.1 * np.sign(last_signal)
        
        confidence = min(abs(last_signal) / 2, 1.0)  # Scale confidence between 0 and 1
        
        return predicted_move, confidence
