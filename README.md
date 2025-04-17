# 🤖 Lorentzian Trading Bot

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.0%2B-orange)
![Capital.com](https://img.shields.io/badge/Capital.com-API-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

A sophisticated cryptocurrency trading bot that implements the Lorentzian strategy with real-time market data from Capital.com. This bot uses advanced machine learning techniques and technical analysis to identify trading opportunities in the crypto market.

## ✨ Features

- 🧠 Neural network-based trading decisions using TensorFlow
- 📊 Real-time market data processing with WebSocket connection
- 📈 Advanced technical indicators calculation (RSI, ADX, CCI, WaveTrend)
- 💹 Risk management and position sizing
- 🔄 Automated trade execution through Capital.com API
- 📱 Beautiful console-based UI with real-time updates
- 📝 Detailed trading session reports and analytics
- ⚡ High-performance data processing with NumPy and Pandas

## 🛠️ Technologies

- **Python 3.8+**: Core programming language
- **TensorFlow**: Deep learning framework for price prediction
- **Pandas & NumPy**: Data manipulation and numerical computations
- **TA-Lib**: Technical analysis indicators
- **Capital.com API**: Market data and trading execution
- **WebSocket**: Real-time market data streaming
- **Colorama & Termcolor**: Terminal UI styling

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Capital.com API credentials
- TA-Lib installed on your system

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ignaciocorball/loretzian-bot.git
cd loretzian-bot
```

2. **Create and activate virtual environment**
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure your Capital.com API credentials**
Create a `.env` file in the project root:
```env
CAPITAL_API_KEY=your_api_key
CAPITAL_API_SECRET=your_api_secret
```

### 🏃‍♂️ Running the Bot

```bash
python src/main.py
```

## 📊 Trading Strategy

The Lorentzian Trading Bot implements a sophisticated trading strategy that combines multiple components:

### Technical Indicators
- RSI (Relative Strength Index)
- ADX (Average Directional Index)
- CCI (Commodity Channel Index)
- WaveTrend Oscillator

### Filters
- ✅ Volatility Filter
- ✅ Regime Filter
- ✅ ADX Filter
- ✅ EMA Filter
- ✅ SMA Filter

### Risk Management
- Dynamic position sizing based on account balance
- Configurable risk per trade (default: 5%)
- Automatic stop-loss and take-profit levels
- Maximum drawdown protection

## 📈 Sample Output

```
╔═══════════════ 🤖 Lorentzian Bot ═══════════════╗
║ 2024-01-20 15:30:45                             ║
║ Price: $41,235.75                               ║
╚══════════════════════════════════════════════════╝

=== 📊 Market Data ===
Pair         BTC/USD
Price        $41,235.75
Bid          $41,234.50
Ask          $41,237.00
Spread       $2.50

=== 📈 Active Positions ===
ID    Type      Size        Entry       SL          TP          P&L
#123  🟢 LONG   0.1 BTC    $41,000.00  $40,795.00  $41,410.00  +$23.57
```

## 📝 Configuration

The bot's behavior can be customized through the `config.py` file:

```python
TRADING_CONFIG = {
    "risk_per_trade": 0.05,    # 5% risk per trade
    "take_profit": 0.01,       # 1% take profit
    "stop_loss": 0.005,        # 0.5% stop loss
    "max_bars_back": 2000,     # Historical data bars
    "feature_count": 5,        # Number of features
    "adx_threshold": 20,       # ADX filter threshold
}
```

## 📊 Trading Reports

The bot generates detailed Excel reports after each session, including:
- Trade history
- Win/Loss statistics
- Profit/Loss analysis
- Risk metrics
- Performance charts

## ⚠️ Disclaimer

Trading cryptocurrencies carries a high level of risk and may not be suitable for all investors. The high degree of leverage can work against you as well as for you. Before deciding to trade cryptocurrencies, you should carefully consider your investment objectives, level of experience, and risk appetite.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions and support, please open an issue in the GitHub repository.
