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
    ind_name = 'Ind_SMA_agg_'+ str(fast) 
    df[ind_name] = sma_fast / sma_slow 

# RSI Ratio
    rsi_fast = ta.RSI(df['Close'], fast)
    rsi_slow = ta.RSI(df['Close'], slow)
    ind_name = 'Ind_RSI_'  + str(fast)
    df[ind_name] = rsi_fast / rsi_slow

# CCI
    ind_name = 'Ind_CCI_' + str(fast)
    df[ind_name] = ta.CCI(df['High'], df['Low'], df['Close'], fast)

# MACD
# We'll be using MACD_ratio which is MACD / Signal. We will multiply it by -1 if MACD is lesser than 0. 
# So the MACD ratio will range from:
    # ratio < -1, when the MACD is below 0 and MACD is below Signal line 
    # -1 > ratio > 0, when the MACD is above Signal line but below 0
    # 0 < ratio < 1, when MACD is below signal but above 0 
    # 1 < ratio, when MACD is above 0 and above the signal line 
    df['MACD'], df['Signal'], hist = ta.MACD(df['Close'], fastperiod=fast, slowperiod=slow, signalperiod=8) 
    ind_name = 'Ind_MACD_ratio_' + str(fast)
    df[ind_name] =  df['MACD'] / df['Signal']
    df[ind_name] = df[ind_name] * df['MACD'] / abs(df['MACD'])          

    df.drop(columns= ['MACD', 'Signal'], inplace = True)

#---------------------------------------------------------------------
# Trend Strength Indicators
#---------------------------------------------------------------------
# ADX
    ind_name = 'Ind_ADX_' + str(fast)
    df[ind_name] = ta.ADX(df['High'], df['Low'], df['Close'], timeperiod= fast)
    df['plus_DI'] = ta.PLUS_DI(df['High'], df['Low'], df['Close'], timeperiod= fast)
    df['minus_DI'] = ta.MINUS_DI(df['High'], df['Low'], df['Close'], timeperiod= fast)
    ind_name = 'Ind_ADX_dirn_' + str(fast)
    df[ind_name] = np.where(df['plus_DI'] > df['minus_DI'], 1.0, 0.0)

    df.drop(columns=['plus_DI', 'minus_DI'], inplace=True)

#---------------------------------------------------------------------
# Volatility Indicators
#---------------------------------------------------------------------
# ATR Ratio: fast / slow. if value is less than 1, the price volatility is slowing
    atr_fast = ta.ATR(df['High'], df['Low'], df['Close'], timeperiod= fast)
    atr_slow = ta.ATR(df['High'], df['Low'], df['Close'], timeperiod= slow)
    ind_name = 'Ind_ATR_ratio_' + str(fast)
    df[ind_name] = atr_fast / atr_slow

# Bollinger Bands: periods = fast; Std.Dev = 1
    ind_high = 'Ind_BBands_high_' + str(fast)
    ind_low = 'Ind_BBands_low_' + str(fast)
    df[ind_high], middle, df[ind_low]  = ta.BBANDS(df['Close'], timeperiod= fast, nbdevup= 1, nbdevdn= 1)

    df[ind_high] = df[ind_high] / df['Close']             # Value lesser than 1 will mean price has crossed above upper band
    df[ind_low] = df['Close'] / df[ind_low]               # Value lesser than 1 will mean price has crossed below lower band

#---------------------------------------------------------------------
# Volume Indicators
#---------------------------------------------------------------------
# # SMA indicators fast and slow
    sma_vol_fast = ta.SMA(df['Volume'], timeperiod=fast )
    sma_vol_slow = ta.SMA(df['Volume'], timeperiod=slow )
    ind_name = 'Ind_SMA_vol_agg_' + str(fast)
    df[ind_name] = sma_vol_fast / sma_vol_slow 

    return df