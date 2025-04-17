import numpy as np
import talib
import pandas as pd
from typing import Tuple, Dict
from src.utils.config import TRADING_CONFIG
from src.features.calculator import FeatureCalculator
from src.features.fractals import FractalAnalyzer
from src.features.technical import TechnicalAnalyzer

class SignalGenerator:
    def __init__(self, model):
        self.model = model
        self.config = TRADING_CONFIG
        self.fractal_analyzer = FractalAnalyzer(filter_bw=self.config['filter_bill_williams'])
        self.technical_analyzer = TechnicalAnalyzer()

    def prepare_combined_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare combined feature vector from all sources"""
        # Get original features
        orig_features = FeatureCalculator.calculate_all_features(df)
        if not orig_features:
            return None
            
        feature_vector = FeatureCalculator.prepare_feature_vector(
            orig_features, 
            -1, 
            self.config['feature_count']
        )
        
        # Get fractal features
        fractal_features = self.fractal_analyzer.get_fractal_features(df)
        fractal_vector = np.array([
            fractal_features['distance_to_top'][-1],
            fractal_features['distance_to_bottom'][-1],
            fractal_features['pattern_signals'][-1]
        ])
        
        # Get technical features
        tech_features = self.technical_analyzer.calculate_technical_features(df)
        tech_vector = np.array([
            tech_features['bb_position'][-1],
            tech_features['bb_width'][-1],
            tech_features['rsi'][-1],
            tech_features['tech_signal'][-1]
        ])
        
        # Combine all features
        combined_vector = np.concatenate([
            feature_vector,  # 4 features
            fractal_vector,  # 3 features
            tech_vector     # 4 features
        ])
        
        return combined_vector

    def get_trading_signal(self, df: pd.DataFrame, current_idx: int) -> int:
        """Generate trading signal based on all features"""
        if current_idx >= len(df):
            return 0
        
        df_slice = df.iloc[max(0, current_idx-self.config['max_bars_back']):current_idx+1]
        
        # Prepare combined features
        combined_features = self.prepare_combined_features(df_slice)
        if combined_features is None:
            print("❌ No features generated")
            return 0
        
        # Get predictions
        try:
            signal_pred, price_pred = self.model.predict(
                combined_features.reshape(1, -1), 
                verbose=0
            )
            
            print(f"📊 Signal prediction: {signal_pred:.3f}, Price prediction: {price_pred:.3f}")
            
            # Calculate confidence based on technical indicators
            _, confidence = self.technical_analyzer.predict_price_movement(df_slice)
            
            print(f"🎯 Confidence: {confidence:.3f}, Threshold: {self.config['confidence_threshold']}")
            
            # Only generate signal if confidence meets threshold
            if confidence < self.config['confidence_threshold']:
                print("❌ Confidence below threshold")
                return 0
            
            # Generate final signal with more sensitivity
            signal = 1 if signal_pred > 0.45 else (-1 if signal_pred < 0.55 else 0)
            
            if signal != 0:
                print(f"🔔 Initial signal generated: {signal}")
                
                if not self.apply_filters(df, current_idx, signal):
                    print("❌ Signal rejected by filters")
                    return 0
                    
                print(f"✅ Final signal confirmed: {signal}")
                return signal
            else:
                print("❌ No clear signal direction")
                return 0
            
        except Exception as e:
            print(f"❌ Error in prediction: {str(e)}")
            print(f"Feature vector shape: {combined_features.shape}")
            return 0

    def _get_lorentzian_signal(self, df: pd.DataFrame) -> float:
        """Get signal from Lorentzian model"""
        if not self.config['use_lorentzian']:
            return 0.5
            
        features = FeatureCalculator.calculate_all_features(df)
        if not features:
            return 0.5
            
        feature_vector = FeatureCalculator.prepare_feature_vector(
            features, 
            -1, 
            self.config['feature_count']
        )
        
        return self.model.predict(feature_vector.reshape(1, -1), verbose=0)[0][0]

    def _get_fractal_signal(self, df: pd.DataFrame) -> float:
        """Get signal from fractal analysis"""
        if not self.config['use_fractal_filter']:
            return 0.5
            
        fractal_features = self.fractal_analyzer.get_fractal_features(df)
        
        # Combine fractal signals
        signal = 0.5  # Neutral base
        
        if fractal_features['bottom_fractals'][-1]:
            signal += 0.25
        elif fractal_features['top_fractals'][-1]:
            signal -= 0.25
            
        pattern_signal = fractal_features['pattern_signals'][-1]
        signal += pattern_signal * 0.25
        
        return max(0, min(1, signal))  # Normalize between 0 and 1

    def _get_technical_signal(self, df: pd.DataFrame) -> float:
        """Get signal from technical analysis"""
        if not self.config['use_technical_filter']:
            return 0.5
            
        tech_features = self.technical_analyzer.calculate_technical_features(df)
        
        # Normalize technical signal to [0, 1] range
        signal = tech_features['tech_signal'][-1]
        normalized_signal = 0.5 + (signal / 4)  # Assuming signal range is [-2, 2]
        
        return max(0, min(1, normalized_signal))

    def apply_filters(self, df: pd.DataFrame, current_idx: int, prediction: int) -> bool:
        """Apply trading filters to validate the signal"""
        if self.config['use_adx_filter']:
            adx = talib.ADX(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
            if current_idx < len(adx) and not np.isnan(adx[current_idx]):
                current_adx = adx[current_idx]
                print(f"📏 ADX value: {current_adx:.2f}, threshold: {self.config['adx_threshold']}")
                if current_adx < self.config['adx_threshold']:
                    return False

        if self.config['use_regime_filter']:
            lookback = 20
            if current_idx >= lookback:
                y = df['close'].values[current_idx-lookback:current_idx+1]
                x = np.arange(lookback+1)
                slope, _ = np.polyfit(x, y, 1)
                regime_threshold = -0.05  # Less restrictive threshold
                print(f"📈 Trend slope: {slope:.4f}, threshold: {regime_threshold}")
                if prediction > 0 and slope < regime_threshold:
                    return False
                elif prediction < 0 and slope > -regime_threshold:
                    return False

        return True

    def get_trade_levels(self, current_price: float, signal: int) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels"""
        if signal > 0:  # Long position
            stop_loss = current_price * (1 - self.config['stop_loss'])
            take_profit = current_price * (1 + self.config['take_profit'])
        else:  # Short position
            stop_loss = current_price * (1 + self.config['stop_loss'])
            take_profit = current_price * (1 - self.config['take_profit'])
        
        return stop_loss, take_profit