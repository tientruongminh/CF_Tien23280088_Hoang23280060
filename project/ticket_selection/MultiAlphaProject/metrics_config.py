"""
Metrics Configuration & Explanations
====================================
Comprehensive metrics framework with explanations and thresholds.
"""

# Metrics organized by category
METRICS_CONFIG = {
    'return': {
        'Total_Return': {
            'name': 'Total Return',
            'formula': '(Final Value - Initial Value) / Initial Value',
            'explanation': 'Overall profitability over the entire period',
            'why_important': 'Shows absolute performance - did you make money?',
            'interpretation': 'Higher is better. Compare against benchmarks (S&P500 ~10%/year)',
            'thresholds': {
                'excellent': 1.0,  # 100%+
                'good': 0.3,       # 30%+
                'poor': 0.0        # Break-even
            },
            'unit': '%',
            'multiply': 100
        },
        'Annual_Return_CAGR': {
            'name': 'Annual Return (CAGR)',
            'formula': '(Total Return + 1)^(1/years) - 1',
            'explanation': 'Annualized return for fair comparison across timeframes',
            'why_important': 'Allows comparing strategies with different durations',
            'interpretation': 'Industry standard. >15% = excellent, >10% = good, <5% = poor',
            'thresholds': {
                'excellent': 0.15,
                'good': 0.10,
                'poor': 0.05
            },
            'unit': '%',
            'multiply': 100
        },
        'Annual_Volatility': {
            'name': 'Annual Volatility',
            'formula': 'StdDev(daily returns) × √252',
            'explanation': 'Annualized standard deviation of returns',
            'why_important': 'Measures risk magnitude - how bumpy the ride is',
            'interpretation': 'Lower is safer. <20% = stable, 20-40% = moderate, >40% = high risk',
            'thresholds': {
                'excellent': 0.20,  # Low vol
                'good': 0.35,
                'poor': 0.50        # High vol
            },
            'unit': '%',
            'multiply': 100,
            'inverse': True  # Lower is better
        }
    },
    
    'risk_adjusted': {
        'Sharpe_Ratio': {
            'name': 'Sharpe Ratio',
            'formula': '(Return - Risk-Free Rate) / Volatility',
            'explanation': 'Return per unit of total risk (volatility)',
            'why_important': 'THE industry standard for risk-adjusted performance. Used by all institutional investors.',
            'interpretation': '>1.5 = excellent (top quartile), >1.0 = good, >0.5 = acceptable, <0 = losing money after risk adjustment',
            'thresholds': {
                'excellent': 1.5,
                'good': 1.0,
                'poor': 0.5
            },
            'unit': '',
            'multiply': 1
        },
        'Sortino_Ratio': {
            'name': 'Sortino Ratio',
            'formula': 'Return / Downside Deviation',
            'explanation': 'Return per unit of downside risk only',
            'why_important': 'Better than Sharpe because it only penalizes BAD volatility (losses), not good volatility (gains)',
            'interpretation': 'Always higher than Sharpe. >2.0 = excellent, >1.5 = good',
            'thresholds': {
                'excellent': 2.0,
                'good': 1.5,
                'poor': 0.8
            },
            'unit': '',
            'multiply': 1
        },
        'Calmar_Ratio': {
            'name': 'Calmar Ratio',
            'formula': 'Annual Return / |Max Drawdown|',
            'explanation': 'Return per unit of maximum loss',
            'why_important': 'Focuses on worst-case scenario. Critical for investors who fear large losses.',
            'interpretation': '>1.0 = excellent (return exceeds max loss), >0.5 = acceptable',
            'thresholds': {
                'excellent': 1.0,
                'good': 0.5,
                'poor': 0.2
            },
            'unit': '',
            'multiply': 1
        }
    },
    
    'drawdown': {
        'Max_Drawdown': {
            'name': 'Maximum Drawdown',
            'formula': 'Max[(Peak - Trough) / Peak]',
            'explanation': 'Largest peak-to-trough decline',
            'why_important': 'CRITICAL: This is the maximum you would have lost if you bought at the worst time. Most investors withdraw after -30% DD.',
            'interpretation': '<-20% = excellent, <-35% = good, <-50% = acceptable, >-50% = too risky for most',
            'thresholds': {
                'excellent': -0.20,
                'good': -0.35,
                'poor': -0.50
            },
            'unit': '%',
            'multiply': 100,
            'inverse': True
        },
        'Avg_Drawdown': {
            'name': 'Average Drawdown',
            'formula': 'Mean(all drawdown periods)',
            'explanation': 'Typical depth when underwater',
            'why_important': 'Max DD might be a one-time event. Avg DD shows typical pain.',
            'interpretation': '<-10% = excellent, <-20% = good',
            'thresholds': {
                'excellent': -0.10,
                'good': -0.20,
                'poor': -0.30
            },
            'unit': '%',
            'multiply': 100,
            'inverse': True
        }
    },
    
    'trade': {
        'Win_Rate': {
            'name': 'Win Rate',
            'formula': 'Winning Days / Total Days',
            'explanation': 'Percentage of profitable trading days',
            'why_important': 'Psychological comfort metric. BUT: 40% win rate with big wins > 60% win rate with small wins!',
            'interpretation': '>55% = excellent, >50% = good (slight edge is enough)',
            'thresholds': {
                'excellent': 0.55,
                'good': 0.50,
                'poor': 0.45
            },
            'unit': '%',
            'multiply': 100,
            'note': '⚠️ Can be misleading! Focus on Profit Factor instead.'
        },
        'Profit_Factor': {
            'name': 'Profit Factor',
            'formula': 'Gross Profit / Gross Loss',
            'explanation': 'Total gains divided by total losses',
            'why_important': 'MOST IMPORTANT trade metric. Shows actual profitability efficiency after costs.',
            'interpretation': '>2.0 = very profitable, >1.5 = good, >1.0 = barely profitable, <1.0 = losing',
            'thresholds': {
                'excellent': 2.0,
                'good': 1.5,
                'poor': 1.0
            },
            'unit': '',
            'multiply': 1
        },
        'Win_Loss_Ratio': {
            'name': 'Win/Loss Ratio',
            'formula': 'Average Win Size / Average Loss Size',
            'explanation': 'Quality of wins vs losses',
            'why_important': 'Shows if you cut losses small and let winners run',
            'interpretation': '>1.5 = excellent (wins 50% bigger than losses), >1.0 = good',
            'thresholds': {
                'excellent': 1.5,
                'good': 1.0,
                'poor': 0.8
            },
            'unit': '',
            'multiply': 1
        }
    }
}

def get_metric_category(metric_name):
    """Get category for a metric"""
    for category, metrics in METRICS_CONFIG.items():
        if metric_name in metrics:
            return category
    return None

def get_metric_config(metric_name):
    """Get full config for a metric"""
    category = get_metric_category(metric_name)
    if category:
        return METRICS_CONFIG[category][metric_name]
    return None

def evaluate_metric(metric_name, value):
    """Evaluate if metric value is good/bad"""
    config = get_metric_config(metric_name)
    if not config:
        return 'unknown', '⚪'
    
    thresholds = config['thresholds']
    inverse = config.get('inverse', False)
    
    if inverse:
        # For metrics where lower is better (volatility, drawdown)
        if value >= thresholds['excellent']:
            return 'excellent', '🟢'
        elif value >= thresholds['good']:
            return 'good', '🟡'
        else:
            return 'poor', '🔴'
    else:
        # For metrics where higher is better
        if value >= thresholds['excellent']:
            return 'excellent', '🟢'
        elif value >= thresholds['good']:
            return 'good', '🟡'
        else:
            return 'poor', '🔴'

def format_metric_value(metric_name, value):
    """Format metric value with proper unit"""
    config = get_metric_config(metric_name)
    if not config:
        return f"{value:.2f}"
    
    formatted = value * config.get('multiply', 1)
    unit = config.get('unit', '')
    
    if unit == '%':
        return f"{formatted:.2f}%"
    else:
        return f"{formatted:.2f}"

# Category display names
CATEGORY_NAMES = {
    'return': '📈 Return Metrics',
    'risk_adjusted': '⚖️ Risk-Adjusted Metrics',
    'drawdown': '📉 Drawdown Metrics',
    'trade': '🎯 Trade Metrics'
}

CATEGORY_DESCRIPTIONS = {
    'return': 'Raw performance without risk adjustment',
    'risk_adjusted': 'Performance adjusted for risk taken',
    'drawdown': 'Downside risk and maximum losses',
    'trade': 'Trading consistency and efficiency'
}
