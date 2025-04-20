# 🤖 Lorentzian Trading Bot

An advanced trading bot that uses technical analysis, machine learning, and harmonic patterns to trade financial markets through Capital.com.

## 🌟 Key Features

### 📊 Multi-Timeframe Analysis
- Support for 1-minute and 5-minute timeframes
- Adaptive analysis based on time interval
- Optimized parameters for intraday trading

### 🎯 Advanced Signal System
- Adaptive volatility analysis
- Custom technical indicators
- Harmonic pattern detection
- Machine learning integration (Lorentzian Model)

### 📈 Intelligent Position Management
- Dynamic trend evaluation
- Adaptive stop-loss and take-profit
- High volatility protection system
- Recovery analysis for losing positions

### ⚡ Technical Features
- Capital.com API integration
- Demo and live trading support
- PostgreSQL database for trade tracking
- Detailed logging system

## 🛠️ Setup

### Prerequisites
- Python 3.8+
- PostgreSQL
- Capital.com Account (Demo or Live)

### Environment Variables
Create a `.env` file with the following variables:
```env
# Capital.com API
CAPITAL_API_KEY=your_api_key
CAPITAL_DEMO_MODE=true
CAPITAL_API_IDENTIFIER=your_email
CAPITAL_API_PASSWORD=your_password

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=trading_bot
```

### Installation
```bash
# Clone repository
git clone https://github.com/your-username/loretzian-bot.git

# Install dependencies
pip install -r requirements.txt

# Setup database
python setup_database.py
```

## ⚙️ Trading Parameters

### 1-Minute Timeframe
- High volatility: 5% (daily)
- Low volatility: 2% (daily)
- Minimum trend strength: 0.05%
- Minimum hold time: 5 minutes
- Maximum allowed loss: -1.5%

### 5-Minute Timeframe
- High volatility: 8% (daily)
- Low volatility: 3% (daily)
- Minimum trend strength: 0.1%
- Minimum hold time: 15 minutes
- Maximum allowed loss: -2%

## 🚀 Usage

```bash
# Start the bot
python main.py

# Start with specific configuration
python main.py --timeframe 5m --pair BTCUSD
```

## 📊 Risk Management System

### Volatility Analysis
- Timeframe-adapted historical volatility calculation
- Dynamic parameter adjustment based on market conditions
- Protection against sudden market movements

### Position Management
- Continuous trend evaluation using EMAs
- Momentum analysis for signal confirmation
- Adaptive trailing stop system
- Profit protection in volatile conditions

### Exit Criteria
- Early exit in unfavorable conditions
- Position holding with recovery signals
- Volatility-based dynamic stop-loss
- Adaptive take-profit based on market conditions

## 📈 Performance Analysis

The bot includes a complete tracking and analysis system:
- Detailed trade logging
- Real-time performance metrics
- Drawdown analysis
- Statistics by trade type

## 🔒 Security

- Encrypted API Keys support
- Safe demo mode testing
- Trade validation
- Audit logging system

## 🤝 Contributing

Contributions are welcome. Please open an issue to discuss major changes before creating a pull request.

### Development Guidelines
- Use English for code, comments, and documentation
- Follow PEP 8 style guide
- Write unit tests for new features
- Update documentation when adding features

## 📝 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## ⚠️ Disclaimer

Trading involves risk. This bot is an automated trading tool and does not guarantee profits. Use at your own risk.

## 🔧 Technical Architecture

### Core Components
- `src/core/`: Main trading logic and position management
- `src/features/`: Technical analysis and signal generation
- `src/api/`: Capital.com API integration
- `src/database/`: Database management
- `src/utils/`: Utility functions and configurations

### Key Classes
- `LorentzianTrader`: Main trading bot class
- `SignalGenerator`: Trading signal generation
- `ActivePositions`: Position management
- `TechnicalAnalyzer`: Technical analysis tools
- `CapitalAPI`: API integration

### Data Flow
1. Market data collection
2. Technical analysis
3. Signal generation
4. Position management
5. Trade execution
6. Performance tracking

## 📊 Monitoring and Logging

### Performance Metrics
- Win rate
- Profit factor
- Maximum drawdown
- Average win/loss ratio
- Risk-adjusted return

### Logging Levels
- INFO: Regular trading operations
- WARNING: Risk management alerts
- ERROR: Trading errors
- DEBUG: Detailed system information

## 🔄 Updates and Maintenance

### Version Control
- Semantic versioning
- Release notes for each version
- Migration guides for updates

### Regular Maintenance
- Daily performance review
- Weekly parameter optimization
- Monthly strategy evaluation
