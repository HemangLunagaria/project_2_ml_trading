import pandas as pd
import numpy as np
import talib as ta 

def add_tech_indicators(df, fast, slow):
    
#---------------------------------------------------------------------
# Momentum Indicators
#---------------------------------------------------------------------
# SMA indicators fast and slow
    sma_fast = ta.SMA(df['Close'], timeperiod=fast )
    sma_slow = ta.SMA(df['Close'], timeperiod=slow )
    df['SMA_agg'] = sma_fast / sma_slow 

# RSI Ratio
    rsi_fast = ta.RSI(df['Close'], fast)
    rsi_slow = ta.RSI(df['Close'], slow)
    df['RSI_ratio'] = rsi_fast / rsi_slow

# CCI
    df['CCI'] = ta.CCI(df['High'], df['Low'], df['Close'], fast)

# MACD
    df['MACD'], df['Signal'], hist = ta.MACD(df['Close'], fastperiod=6, slowperiod=12, signalperiod=5) 
    df['MACD_ratio'] =  df['MACD'] / df['Signal']
    df['MACD_ratio'] = df['MACD_ratio'] * df['MACD'] / abs(df['MACD'])

    df.drop(columns= ['MACD', 'Signal'], inplace = True)

#---------------------------------------------------------------------
# Trend Strength Indicators
#---------------------------------------------------------------------
# ADX
    df['ADX'] = ta.ADX(df['High'], df['Low'], df['Close'], timeperiod= fast)
    df['plus_DI'] = ta.PLUS_DI(df['High'], df['Low'], df['Close'], timeperiod= fast)
    df['minus_DI'] = ta.MINUS_DI(df['High'], df['Low'], df['Close'], timeperiod= fast)
    df['ADX_dirn'] = np.where(df['plus_DI'] > df['minus_DI'], 1.0, 0.0)

    df.drop(columns=['plus_DI', 'minus_DI'], inplace=True)

#---------------------------------------------------------------------
# Volatility Indicators
#---------------------------------------------------------------------
# ATR Ratio: fast / slow. if value is less than 1, the price volatility is slowing
    atr_fast = ta.ATR(df['High'], df['Low'], df['Close'], timeperiod= fast)
    atr_slow = ta.ATR(df['High'], df['Low'], df['Close'], timeperiod= slow)
    df['ATR_ratio'] = atr_fast / atr_slow

# Bollinger Bands: periods = fast; Std.Dev = 1
    df['BBands_high'], middle, df['BBands_low']  = ta.BBANDS(df['Close'], timeperiod= fast, nbdevup= 1, nbdevdn= 1)

    df['BBands_high'] = df['BBands_high'] / df['Close']             # Value lesser than 1 will mean price has crossed above upper band
    df['BBands_low'] = df['Close'] / df['BBands_low']               # Value lesser than 1 will mean price has crossed below lower band

    return df