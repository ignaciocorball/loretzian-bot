import tensorflow as tf
from src.utils.config import TRADING_CONFIG
from typing import Dict, Any

class LorentzianModel:
    def __init__(self):
        self.model = self._build_model()

    def _build_model(self):
        """Build enhanced neural network model"""
        # Define exact feature counts
        lorentzian_features = TRADING_CONFIG['feature_count']  # 4
        fractal_features = 3  # distance_to_top, distance_to_bottom, pattern_signal
        technical_features = 4  # bb_position, bb_width, rsi, tech_signal
        total_features = lorentzian_features + fractal_features + technical_features  # 11
        
        inputs = tf.keras.Input(shape=(total_features,))
        
        # Lorentzian branch
        x1 = tf.keras.layers.Dense(64, activation='relu')(
            inputs[:, :lorentzian_features]
        )
        x1 = tf.keras.layers.Dropout(0.2)(x1)
        
        # Fractal branch
        x2 = tf.keras.layers.Dense(32, activation='relu')(
            inputs[:, lorentzian_features:lorentzian_features+fractal_features]
        )
        x2 = tf.keras.layers.Dropout(0.2)(x2)
        
        # Technical branch
        x3 = tf.keras.layers.Dense(32, activation='relu')(
            inputs[:, -technical_features:]
        )
        x3 = tf.keras.layers.Dropout(0.2)(x3)
        
        # Combine all branches
        combined = tf.keras.layers.Concatenate()([x1, x2, x3])
        
        # Common hidden layers
        x = tf.keras.layers.Dense(64, activation='relu')(combined)
        x = tf.keras.layers.Dropout(0.2)(x)
        x = tf.keras.layers.Dense(32, activation='relu')(x)
        
        # Price prediction branch
        price_output = tf.keras.layers.Dense(1, name='price_prediction')(x)
        
        # Signal prediction branch
        signal_output = tf.keras.layers.Dense(1, activation='sigmoid', name='signal_prediction')(x)
        
        model = tf.keras.Model(
            inputs=inputs, 
            outputs=[signal_output, price_output]  # Note the order change to match predict usage
        )
        
        model.compile(
            optimizer='adam',
            loss={
                'price_prediction': 'mse',
                'signal_prediction': 'binary_crossentropy'
            },
            metrics={
                'price_prediction': 'mae',
                'signal_prediction': 'accuracy'
            }
        )
        
        return model

    def predict(self, features, verbose=0):
        """Make predictions for both signal and price"""
        if features.shape[1] != 11:
            raise ValueError(f"Expected 11 features, but got {features.shape[1]}")
            
        predictions = self.model.predict(features, verbose=verbose)
        return predictions[0][0][0], predictions[1][0][0]  # signal_pred, price_pred

    def train(self, X_train, y_train_signal, y_train_price, epochs=10, batch_size=32, validation_split=0.2):
        """Train the model with both signal and price targets"""
        return self.model.fit(
            X_train,
            {
                'signal_prediction': y_train_signal,
                'price_prediction': y_train_price
            },
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split
        )

    def save_weights(self, filepath):
        """Save model weights to file"""
        self.model.save_weights(filepath)

    def load_weights(self, filepath):
        """Load model weights from file"""
        self.model.load_weights(filepath) 