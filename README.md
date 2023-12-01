# Project 2: The T-1000 Tradinator
![image](https://github.com/HemangLunagaria/project_2_ml_trading/blob/main/images/t1000.jpg)
## Overview

The T-1000 Tradinator is a sophisticated Machine Learning Algoritmic Trading Bot, sent back through time to help crypto humans successfully trade.

We decided to create an Algorithmic trading bot that users can interact with through Amazon Lex and recieve signal updates through slack and telegram. The bot will then gather the data on the crypto currency previously specifided by the users and use technical analysis indicators to prepare the data. The bot will then use these signals to run multiple Machine Learning models and compare the results of these models to determine the most accurate Buy/Sell/Hold signal for the user. 

Using Amazon Lex, the bot will then be instructed to either execute a Buy or Sell trade in a live trading account or do nothing by holding the position. 

![image](https://github.com/HemangLunagaria/project_2_ml_trading/blob/main/images/mindmap.png)

## Models Used
* Decision Tree
* Random Forrest
* Linear Recession 

### Model Performance

## Dependencies

To run this code, users will need the following libraries
* Pandas
* ccxt
* yfinance
* coinspot
* Keras
* Tensorflow
* scikit learn
* matplotlib
* dash
* talib

## Team
* Hemang
* Siddhesh
* Edward
* Richard
