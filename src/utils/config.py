import os
from typing import Dict, Any

# Environment configuration
ENV_CONFIG = {
    'TF_CPP_MIN_LOG_LEVEL': '3',
    'TF_ENABLE_ONEDNN_OPTS': '0'
}

# Data paths
DATA_DIR = './data'
os.makedirs(DATA_DIR, exist_ok=True)

# Trading pairs
DEFAULT_PAIR = "BTC/USD"
DEFAULT_TIMEFRAME = '5m'

# Trading configuration
TRADING_CONFIG: Dict[str, Any] = {
    "risk_per_trade": 0.05,
    "take_profit": 0.005,
    "stop_loss": 0.003,
    "neighbors_count": 10,
    "max_bars_back": 1000,
    "feature_count": 4,
    "total_features": 11,
    "adx_threshold": 15,
    "ema_period": 9,
    "use_volatility_filter": False,
    "use_regime_filter": False,
    "use_adx_filter": True,
    "use_ema_filter": False,
    "use_sma_filter": False,
    "min_time_between_trades": 5,
    # New fractal configuration
    "use_fractal_filter": True,
    "filter_bill_williams": True,
    "fractal_weight": 0.3,
    "pattern_weight": 0.3,
    # Strategy weights for combined model
    "lorentzian_weight": 0.4,
    "technical_weight": 0.3,
    # Technical indicators parameters
    "bollinger_length": 20,
    "bollinger_std": 2,
    "rsi_length": 14,
    # Strategy selection
    "use_lorentzian": True,
    "use_technical_filter": True,
    # Prediction parameters
    "prediction_horizon": 5,
    "confidence_threshold": 0.45,
    # New parameters for volatility management
    'high_volatility_threshold': 0.25,  # 25% annualized volatility
    'low_volatility_threshold': 0.10,   # 10% annualized volatility
    # Position management parameters
    'trend_strength_threshold': 0.002,   # 0.2% change in EMAs
    'recovery_time_minimum': 1,          # Minimum hours to evaluate recovery
    'max_loss_threshold': -0.02,         # -2% maximum allowed loss
    'volatility_exit_threshold': 0.20,   # 20% volatility for exit
    # Parameters adapted by timeframe
    'timeframe_params': {
        '1m': {
            'volatility_high': 0.05,    # 5% daily volatility
            'volatility_low': 0.02,     # 2% daily volatility
            'trend_strength': 0.0005,   # 0.05% change in EMAs
            'min_hold_time': 5,         # 5 minutes
            'max_loss': -0.015,         # -1.5% maximum loss
            'adx_period': 30,           # Periods for ADX
            'momentum_period': 20,      # Periods for momentum
            'ema_fast': 10,             # Fast EMA (10 minutes)
            'ema_slow': 30              # Slow EMA (30 minutes)
        },
        '5m': {
            'volatility_high': 0.08,    # 8% daily volatility
            'volatility_low': 0.03,     # 3% daily volatility
            'trend_strength': 0.001,    # 0.1% change in EMAs
            'min_hold_time': 15,        # 15 minutes
            'max_loss': -0.02,          # -2% maximum loss
            'adx_period': 14,           # Periods for ADX
            'momentum_period': 10,      # Periods for momentum
            'ema_fast': 6,              # Fast EMA (30 minutes)
            'ema_slow': 12              # Slow EMA (1 hour)
        }
    }
}

# Feature parameters
FEATURE_PARAMS: Dict[str, Dict[str, Any]] = {
    'f1': {'type': 'RSI', 'param_a': 9,  'param_b': 1},
    'f2': {'type': 'WT',  'param_a': 10, 'param_b': 12},  # WaveTrend
    'f3': {'type': 'CCI', 'param_a': 20, 'param_b': 1},
    'f4': {'type': 'ADX', 'param_a': 20, 'param_b': 2},
    'f5': {'type': 'BB',  'param_a': 200, 'param_b': 2},  # Bollinger Bands
    #'f5': {'type': 'RSI', 'param_a': 9,  'param_b': 1}
}

# Fractal parameters
FRACTAL_PARAMS: Dict[str, Any] = {
    'show_patterns': True,
    'show_bar_colors': False,
    'timeframe': "240",
    'show_channels': False,
    'pattern_types': [
        'Bat', 'Butterfly', 'Gartley', 'Crab',
        'Shark', '5-0', 'Wolf', 'Head and Shoulders',
        'Contracting Triangle', 'Expanding Triangle'
    ]
}