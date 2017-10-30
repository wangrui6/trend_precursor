#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 29 23:37:50 2017

@author: ruiwang
"""

mport numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# called once per simulation
def initialize(context):
    # random.seed(None)
    fetch_csv('https://www.dropbox.com/s/czhlnw8zycgxdfj/data.csv?dl=0', 
              date_column = 'Date',
              date_format = '%y-%m-%d',
              mask=False)    
    context.leverage_factor = 1.0
    context.number_of_positions_ratio = 0.8 #len(context.stocks)
    context.long_short_ratios = []
    
    schedule_function(weekly_market_open, date_rule=date_rules.week_start(), time_rule=time_rules.market_open(minutes=60))
                
def weekly_market_open(context, data): 
    long_buys = []
    short_buys = []
    
    df = data.current(data.fetcher_assets, ['probability', 'predictiveness', 'prediction'])
    df.sort_values(by='probability', ascending=True, inplace=True)
    
    df_high_predictiveness = df[-1*int(context.number_of_positions_ratio*len(df)):]
                
    for stock in df_high_predictiveness.index:        
        if df_high_predictiveness.loc[stock, 'prediction'] > 0:
            long_buys.append(stock)
        else:
            short_buys.append(stock)    
    
    # removing untradable stocks.
    for stock in long_buys:
        if not data.can_trade(stock):
            long_buys.remove(stock)

    for stock in short_buys:
        if not data.can_trade(stock):
            short_buys.remove(stock)
            
    # sell stocks that are in portfolio but were not selected for this coming week.
    for stock in context.portfolio.positions:
        if stock.sid not in [x.sid for x in long_buys] and stock.sid not in [x.sid for x in short_buys]:
            order_target_percent(stock, 0)
     #################################
        
    long_calls = len(long_buys)
    short_calls = len(short_buys)
    
    for stock in long_buys:
        order_target_percent(stock, context.leverage_factor/(long_calls+short_calls))
            
    for stock in short_buys:
        order_target_percent(stock, -1*context.leverage_factor/(long_calls+short_calls))
        
    try:
        long_short_ratio = float(long_calls - short_calls)/(short_calls + long_calls)
    except:
        long_short_ratio = 0
        
    # beta edge the whole thing.
    if long_short_ratio > 0.5:
        order_target_percent(sid(8554), -1.1*long_short_ratio*context.leverage_factor)    
        
    context.long_short_ratios.append(long_short_ratio)
       
    record(long_short_ratio=long_short_ratio)