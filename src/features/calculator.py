import numpy as np
import talib
import pandas as pd
from typing import Dict, Optional
from src.utils.config import FEATURE_PARAMS

class FeatureCalculator:
    @staticmethod
    def calculate_feature(df: pd.DataFrame, feature_type: str, param_a: int, param_b: int) -> Optional[np.ndarray]:
        """Calculate a single technical feature"""
        try:
            if feature_type == 'RSI':
                values = talib.RSI(df['close'].values, timeperiod=param_a)
            elif feature_type == 'CCI':
                values = talib.CCI(df['high'].values, df['low'].values, df['close'].values, timeperiod=param_a)
            elif feature_type == 'ADX':
                values = talib.ADX(df['high'].values, df['low'].values, df['close'].values, timeperiod=param_a)
            elif feature_type == 'WT':
                hlc3 = (df['high'] + df['low'] + df['close']) / 3
                esa = talib.EMA(hlc3, timeperiod=param_a)
                d = talib.EMA(abs(hlc3 - esa), timeperiod=param_a)
                ci = (hlc3 - esa) / (0.015 * d)
                wt1 = talib.EMA(ci, timeperiod=param_b)
                wt2 = talib.EMA(wt1, timeperiod=4)
                values = wt1 - wt2
            else:
                return None
            
            values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
            
            # Normalize values based on feature type
            if feature_type in ['RSI', 'CCI', 'WT']:
                min_val = np.min(values)
                max_val = np.max(values)
                if max_val != min_val:
                    values = (values - min_val) / (max_val - min_val)
                else:
                    values = np.zeros_like(values)
            elif feature_type == 'ADX':
                values = values / 100.0
            
            return values
            
        except Exception as e:
            print(f"Error calculating feature {feature_type}: {str(e)}")
            return None

    @staticmethod
    def calculate_all_features(df: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Calculate all technical features defined in config"""
        features = {}
        try:
            for feature_name, params in FEATURE_PARAMS.items():
                feature_values = FeatureCalculator.calculate_feature(
                    df,
                    params['type'],
                    params['param_a'],
                    params['param_b']
                )
                if feature_values is not None:
                    features[feature_name] = feature_values
        except Exception as e:
            print(f"Error calculating features: {e}")
        return features

    @staticmethod
    def prepare_feature_vector(features: Dict[str, np.ndarray], index: int, feature_count: int) -> np.ndarray:
        """Prepare feature vector for model prediction"""
        return np.array([features[f'f{i+1}'][index] for i in range(feature_count)]) 