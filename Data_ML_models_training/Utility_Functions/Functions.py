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
# We'll be using MACD_ratio which is MACD / Signal. We will multiply it by -1 if MACD is lesser than 0. 
# So the MACD ratio will range from:
    # ratio < -1, when the MACD is below 0 and MACD is below Signal line 
    # -1 > ratio > 0, when the MACD is above Signal line but below 0
    # 0 < ratio < 1, when MACD is below signal but above 0 
    # 1 < ratio, when MACD is above 0 and above the signal line 
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

#---------------------------------------------------------------------
# Volume Indicators
#---------------------------------------------------------------------
# # SMA indicators fast and slow
    sma_vol_fast = ta.SMA(df['Volume'], timeperiod=fast )
    sma_vol_slow = ta.SMA(df['Volume'], timeperiod=slow )
    df['SMA_vol_agg'] = sma_vol_fast / sma_vol_slow 

    return df