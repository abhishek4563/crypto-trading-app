import pandas as pd
import json 
import matplotlib.pyplot as plt
import seaborn as sns
import random
import datetime as dt

#All necessary plotly libraries
import plotly as py
import plotly.io as pio
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

from pycoingecko import CoinGeckoAPI # API docs are here: https://www.coingecko.com/en/api/documentation 
cg = CoinGeckoAPI()

def get_daily_prices(coin,days=3500):
    
    hist_prices_json= cg.get_coin_market_chart_by_id(id=coin, 
                                                           vs_currency="usd",days=days, interval="daily")
    hist_prices=pd.DataFrame(hist_prices_json['prices'], columns =['date','price']).merge(
    pd.DataFrame(hist_prices_json['market_caps'], columns =['date','market_cap']), on="date").merge(
    pd.DataFrame(hist_prices_json['total_volumes'], columns =['date','volume']), on="date")
    hist_prices['coin']=["btc"]*len(hist_prices.index)
    hist_prices['date'] = list (map( lambda n: int(float(n)/1000), hist_prices['date'])) # fixing date
    hist_prices['date']=pd.to_datetime(hist_prices['date'],unit='s')
    return hist_prices

def perc_diff (col1, col2):
    return (col1-col2)/col2

def calc_diff_trend (col,coin_hist_prices) :
    col_diff=col+'_diff'
    col_trend=col+'_trend'
    coin_hist_prices[col_diff] = None
    coin_hist_prices[col_trend] = None
    coin_hist_prices[col_diff]=coin_hist_prices[col].diff()
    coin_hist_prices.loc[coin_hist_prices[col_diff]>0,col_trend] = 'UP'
    coin_hist_prices.loc[coin_hist_prices[col_diff]<=0,col_trend] = 'DOWN'
    coin_hist_prices.loc[((coin_hist_prices[col_trend] == 'UP') & (
        coin_hist_prices[col_trend].shift()=='DOWN')),col_trend] = 'REV_UP'
    coin_hist_prices.loc[((coin_hist_prices[col_trend] == 'DOWN') & (
        coin_hist_prices[col_trend].shift()=='UP')),col_trend] = 'REV_DOWN'

def create_indicators(coin_hist_prices):
    coin_hist_prices['price_sma_7']= coin_hist_prices['price'].rolling(7).mean()
    coin_hist_prices['price_sma_30']= coin_hist_prices['price'].rolling(30).mean()
    coin_hist_prices['price_sma_90']= coin_hist_prices['price'].rolling(90).mean()
    coin_hist_prices['price_sma_180']= coin_hist_prices['price'].rolling(180).mean()
    coin_hist_prices['vol_sma_7']= coin_hist_prices['volume'].rolling(7).mean()
    coin_hist_prices['vol_sma_30']= coin_hist_prices['volume'].rolling(30).mean()
    coin_hist_prices['vol_sma_90']= coin_hist_prices['volume'].rolling(90).mean()
    coin_hist_prices['vol_sma_180']= coin_hist_prices['volume'].rolling(180).mean()
    coin_hist_prices['dev_price_sma_7'] = perc_diff(coin_hist_prices['price'],
                                                     coin_hist_prices['price_sma_7'])
    coin_hist_prices['dev_price_sma_30'] = perc_diff(coin_hist_prices['price'],
                                                     coin_hist_prices['price_sma_30'])
    coin_hist_prices['dev_price_sma_90'] = perc_diff(coin_hist_prices['price'],
                                                     coin_hist_prices['price_sma_90'])
    coin_hist_prices['dev_price_sma_180'] = perc_diff(coin_hist_prices['price'],
                                                     coin_hist_prices['price_sma_180'])
    coin_hist_prices['dev_vol_sma_7'] = perc_diff(coin_hist_prices['volume'],
                                                   coin_hist_prices['vol_sma_7'])
    coin_hist_prices['dev_vol_sma_30'] = perc_diff(coin_hist_prices['volume'],
                                                         coin_hist_prices['vol_sma_30'])
    coin_hist_prices['dev_vol_sma_90'] = perc_diff(coin_hist_prices['volume'],
                                                         coin_hist_prices['vol_sma_90'])
    coin_hist_prices['dev_vol_sma_180'] = perc_diff(coin_hist_prices['volume'],
                                                         coin_hist_prices['vol_sma_180'])
    coin_hist_prices['dev_vol_7_30'] = perc_diff(coin_hist_prices['vol_sma_7'],
                                                     coin_hist_prices['vol_sma_30'])
    coin_hist_prices['dev_price_7_30'] = perc_diff(coin_hist_prices['price_sma_7'],
                                                     coin_hist_prices['price_sma_30'])
    calc_diff_trend ('dev_price_7_30',coin_hist_prices)
    calc_diff_trend ('dev_vol_7_30',coin_hist_prices)
    calc_diff_trend ('dev_price_sma_7',coin_hist_prices)
    
    #FOR LATER: maybe do this with map function later? and lambda?

    ## Functions for calculating and generating trading signals and recos 

def isBuyorSell(coin_hist_prices,date):
    return (coin_hist_prices[coin_hist_prices.date==date]['signal'].iloc[0])

def create_trade(coin_hist_prices,buy_date):
    
    if(type(buy_date)==str):
        buy_date=datetime.datetime.strptime(buy_date, format)
    
    sell_date=buy_date 
    coin_hist_prices.loc[coin_hist_prices.date ==buy_date,'trade_reco'] ='BUY'
    
    for idate in coin_hist_prices.date:
        if (idate <= buy_date):
            continue # skip the rest of the loop until we are past the buy_date
        elif (isBuyorSell(coin_hist_prices,idate)=='SELL'):
            coin_hist_prices.loc[coin_hist_prices.date ==idate,'trade_reco'] ='SELL'
            sell_date=idate
            break # if SELL found, break the loop
    
    return sell_date

def calc_signals(coin_hist_prices):
    
    coin_hist_prices['signal'] = None 
    
    # Calculate BUY signals
    for index, row in coin_hist_prices.iterrows():
         if ((row['dev_price_7_30_trend'] =='UP') & (row['dev_vol_7_30_trend'] =='UP')):
            coin_hist_prices.at[index,'signal'] ='BUY'
    #      if ((row['dev_price_7_30'] <0)& (row['dev_price_7_30_trend']=='REV_UP')& ((row['dev_vol_7_30_trend']=='REV_UP')|(row['dev_vol_7_30_trend']=='UP'))):
    #          coin_hist_prices.at[index,'signal'] ='BUY'

    # Calculate SELL signals 
    for index, row in coin_hist_prices.iterrows():
        if (row['dev_price_7_30_trend']=='REV_DOWN'):
             coin_hist_prices.at[index,'signal'] ='SELL'
        elif ((row['dev_price_7_30'] <0)& (row['dev_price_7_30_trend']=='DOWN')):
            coin_hist_prices.at[index,'signal'] ='SELL'

    #### HAVe REVISED SELL SIGNAL to add a condition that dev price 7 30 trend != REV_UP to signal a sell when its -ve

def gen_trades(coin_hist_prices):
    
    coin_hist_prices.trade_reco = None
    start_date= coin_hist_prices.loc[0]['date']
    
    for idate in coin_hist_prices.date : 
        if (idate<=start_date):
            continue # skip the code below if this date was already scanned for a trade signal
        elif (isBuyorSell(coin_hist_prices,idate)=='BUY'):
            start_date=create_trade(coin_hist_prices,idate) # record the trade and scan next 

# plot n number of idnicators on the same axis 
def plot_inds(coin_hist_prices,inds=[],start_date='2001-01-01',end_date='2001-01-01', num_days=180 ):
    start_date = dt.datetime.strptime(start_date, '%Y-%m-%d') # https://www.digitalocean.com/community/tutorials/python-string-to-datetime-strptimea
    end_date = dt.datetime.strptime(end_date, '%Y-%m-%d')
    default_date=dt.datetime.strptime('2001-01-01', '%Y-%m-%d')
  
    # set the dates
    if (start_date==default_date) & (end_date==default_date):
            end_date=coin_hist_prices.iloc[len(coin_hist_prices)-2]['date']
            start_date=end_date - dt.timedelta(days=num_days)

    elif start_date==default_date:
        start_date= end_date - dt.timedelta(days=num_days) # https://www.geeksforgeeks.org/how-to-add-and-subtract-days-using-datetime-in-python/
    elif end_date==default_date:
        end_date=start_date + dt.timedelta(days=num_days)
    
    print('start date:',start_date,'end date:',end_date)
    for ind in inds:
        sns.lineplot(x='date', y=ind,data=coin_hist_prices.loc[((coin_hist_prices['date']>=start_date)&(coin_hist_prices['date']<=end_date)),['date',ind]])

  # plot UPTO 3 indicators vs price
def plot_price_vs_inds (coin_hist_prices,vs_inds=[],start_date='2001-01-01',end_date='2001-01-01', num_days=180,colors=['red','blue','green']): # or inds_on_price?
    
    start_date = dt.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = dt.datetime.strptime(end_date, '%Y-%m-%d')
    default_date=dt.datetime.strptime('2001-01-01', '%Y-%m-%d')
    
  
    # set the dates
    if (start_date==default_date) & (end_date==default_date):
            end_date=coin_hist_prices.iloc[len(coin_hist_prices)-2]['date']
            start_date=end_date - dt.timedelta(days=num_days)

    elif start_date==default_date:
        start_date= end_date - dt.timedelta(days=num_days) 
    elif end_date==default_date:
        end_date=start_date + dt.timedelta(days=num_days)
    print('start date:',start_date,'end date:',end_date)
    
    plot_data=data=coin_hist_prices.loc[((coin_hist_prices['date']>=start_date)&(coin_hist_prices['date']<=end_date))]
    
    # plot price
    sns.set_theme(style="darkgrid")

    sns.lineplot(x='date', y='price',
                     data=plot_data[['date','price']],color='black', alpha=0.2)

        # plot other inds on different axis
    ax2=plt.twinx() 
    
    for (i,ind) in enumerate(vs_inds):
        sns.lineplot(x='date', y=ind,data=plot_data[['date',ind]],ax=ax2,color=colors[i])

def plot_signals(coin_hist_prices,inds=[],start_date='2001-01-01',end_date='2001-01-01', num_days=180,colors=['orange','purple','grey'] ):
    
    start_date = dt.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = dt.datetime.strptime(end_date, '%Y-%m-%d')
    default_date=dt.datetime.strptime('2001-01-01', '%Y-%m-%d')
    
    # set the dates
    if (start_date==default_date) & (end_date==default_date):
            end_date=coin_hist_prices.iloc[len(coin_hist_prices)-2]['date']
            start_date=end_date - dt.timedelta(days=num_days)
    elif start_date==default_date:
        start_date= end_date - dt.timedelta(days=num_days) 
    elif end_date==default_date:
        end_date=start_date + dt.timedelta(days=num_days)
    
    print('start date:',start_date,'end date:',end_date)
    
    plot_data=data=coin_hist_prices.loc[((coin_hist_prices['date']>=start_date)&(coin_hist_prices['date']<=end_date))]
    
    # plot price
    sns.set_theme(style="darkgrid")
    sns.lineplot(x='date', y='price', data=plot_data[['date','price']],color='b')
    
    # setting the x and y offset 
    (y_lim1,y_lim2)=plt.ylim()
    y_off= 0.1* (y_lim2-y_lim1)
    (x_lim1,x_lim2)=plt.xlim()
    x_off= 0.025* (x_lim2-x_lim1)

    # plot signals
    for index, row in plot_data.iterrows():
        if (row['trade_reco'] == 'BUY'):
            plt.annotate(row['trade_reco'],xy=(row['date'], row['price']),xytext=((row['date']+dt.timedelta(days=5), (row['price']-y_off))),
                         color='green', arrowprops=dict(facecolor='grey', width=2.5,headwidth=7.5))
        elif (row['trade_reco'] == 'SELL'):
            plt.annotate(row['trade_reco'],xy=(row['date'], row['price']),xytext=((row['date']+dt.timedelta(days=5), (row['price']+y_off))),
                         color='red', arrowprops=dict(facecolor='grey', width=2.5,headwidth=7.5))

    # plot other inds on different axis
    ax2=plt.twinx() 
    
    for (i,ind) in enumerate(inds):
        sns.lineplot(x='date', y=ind,data=plot_data[['date',ind]],ax=ax2,color=colors[i])

#plot n number of idnicators on the same axis 
def plotly_inds(coin_hist_prices,inds=[],start_date='2001-01-01',end_date='2001-01-01', num_days=180 ):
    start_date = dt.datetime.strptime(start_date, '%Y-%m-%d') # https://www.digitalocean.com/community/tutorials/python-string-to-datetime-strptimea
    end_date = dt.datetime.strptime(end_date, '%Y-%m-%d')
    default_date=dt.datetime.strptime('2001-01-01', '%Y-%m-%d')
  
    # set the dates
    if (start_date==default_date) & (end_date==default_date):
            end_date=coin_hist_prices.iloc[len(coin_hist_prices)-2]['date']
            start_date=end_date - dt.timedelta(days=num_days)

    elif start_date==default_date:
        start_date= end_date - dt.timedelta(days=num_days) # https://www.geeksforgeeks.org/how-to-add-and-subtract-days-using-datetime-in-python/
    elif end_date==default_date:
        end_date=start_date + dt.timedelta(days=num_days)
    
    print('start date:',start_date,'end date:',end_date)
    plot_data=coin_hist_prices.loc[((coin_hist_prices['date']>=start_date)&(coin_hist_prices['date']<=end_date))]

    
    fig =go.Figure()
    
    for ind in inds:
        fig.add_trace(go.Scatter(x=plot_data['date'],y=plot_data[ind],name=ind,mode='lines'))
    
    fig.update_layout(autosize=False, width=1000, height=700,margin=go.layout.Margin(
        l=20, r=20, b=20, t=20, pad = 1),
        xaxis=dict(rangeselector=dict( buttons=list([
                dict(count=1,label="1m", step="month", stepmode="backward"),
                dict(count=6,label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        ), rangeslider=dict(visible=True), type="date"), legend_orientation='h' )
    fig.update_yaxes({'fixedrange':False})
    return fig.show()
# we have to return fig.show() if we want the function to actualluy plot!

# plot UPTO 3 indicators vs price
# LATER: add LEGEND
def plotly_price_vs_inds (coin_hist_prices,vs_inds=[],start_date='2001-01-01',end_date='2001-01-01', num_days=180,colors=['red','blue','green']): # or inds_on_price?
    
    start_date = dt.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = dt.datetime.strptime(end_date, '%Y-%m-%d')
    default_date=dt.datetime.strptime('2001-01-01', '%Y-%m-%d')
    
  
    # set the dates
    if (start_date==default_date) & (end_date==default_date):
            end_date=coin_hist_prices.iloc[len(coin_hist_prices)-2]['date']
            start_date=end_date - dt.timedelta(days=num_days)

    elif start_date==default_date:
        start_date= end_date - dt.timedelta(days=num_days) 
    elif end_date==default_date:
        end_date=start_date + dt.timedelta(days=num_days)
    print('start date:',start_date,'end date:',end_date)
    
    plot_data=data=coin_hist_prices.loc[((coin_hist_prices['date']>=start_date)&(coin_hist_prices['date']<=end_date))]
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Plot price
    fig.add_trace(go.Scatter(x=plot_data['date'],y=plot_data['price'],name='Price',mode='lines', 
                             opacity=0.2, line_color='black'),secondary_y=False)
    # changing line opacity and color
    # https://stackoverflow.com/questions/50488894/plotly-py-change-line-opacity-leave-markers-opaque
    #https://stackoverflow.com/questions/58188816/how-to-set-line-color
    
    # plot vs indicators 
    for (i,ind) in enumerate(vs_inds):
            fig.add_trace(go.Scatter(x=plot_data['date'],y=plot_data[ind],name=ind,mode='lines', 
                             line_color=colors[i]),secondary_y=True)
    
    fig.update_layout(autosize=False, width=1200, height=700,margin=go.layout.Margin(
        l=20, r=20, b=20, t=20, pad = 1),
        xaxis=dict(rangeselector=dict( buttons=list([
                dict(count=1,label="1m", step="month", stepmode="backward"),
                dict(count=6,label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        ), rangeslider=dict(visible=True), type="date"), legend_orientation='h' )
    
    fig.update_yaxes({'fixedrange':False})

    return fig.show()
# plot UPTO 3 indicators vs price
# LATER: add LEGEND
# adding annotations and text to charts
# https://plotly.com/python/text-and-annotations/
#https://stackoverflow.com/questions/62716521/plotly-how-to-add-text-to-existing-figure

def plotly_signals (coin_hist_prices,start_date='2001-01-01',end_date='2001-01-01', num_days=180,colors=['red','blue','green']): # or inds_on_price?
    
    start_date = dt.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = dt.datetime.strptime(end_date, '%Y-%m-%d')
    default_date=dt.datetime.strptime('2001-01-01', '%Y-%m-%d')
    
  
    # set the dates
    if (start_date==default_date) & (end_date==default_date):
            end_date=coin_hist_prices.iloc[len(coin_hist_prices)-2]['date']
            start_date=end_date - dt.timedelta(days=num_days)

    elif start_date==default_date:
        start_date= end_date - dt.timedelta(days=num_days) 
    elif end_date==default_date:
        end_date=start_date + dt.timedelta(days=num_days)
    print('start date:',start_date,'end date:',end_date)
    
    plot_data=data=coin_hist_prices.loc[((coin_hist_prices['date']>=start_date)&(coin_hist_prices['date']<=end_date))]
    
    fig = go.Figure()
    
    # Plot price
    fig.add_trace(go.Scatter(x=plot_data['date'],y=plot_data['price'],name='Price',mode='lines', 
                             opacity=0.2, line_color='black'))
    # changing line opacity and color
    # https://stackoverflow.com/questions/50488894/plotly-py-change-line-opacity-leave-markers-opaque
    #https://stackoverflow.com/questions/58188816/how-to-set-line-color
    
     # plot signals
    for index, row in plot_data.iterrows():
        if (row['trade_reco'] == 'BUY'):
            fig.add_annotation(x=row['date'], y=row['price'],text="BUY", font={'color':'green','size':12},showarrow=True, arrowhead=2)
        elif (row['trade_reco'] == 'SELL'):
            fig.add_annotation(x=row['date'], y=row['price'],text="SELL", font={'color':'red','size':12},showarrow=True, arrowhead=2)

    fig.update_layout(autosize=False, width=1400, height=700,margin=go.layout.Margin(
        l=20, r=20, b=20, t=20, pad = 1),
        xaxis=dict(rangeselector=dict( buttons=list([
                dict(count=1,label="1m", step="month", stepmode="backward"),
                dict(count=6,label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        ), rangeslider=dict(visible=True), type="date"), legend_orientation='h' )
   
    fig.update_yaxes({'fixedrange':False})

    
    return fig.show()

# plot signals as well as upto 3 signals 

def plotly_signals_and_inds (coin_hist_prices,vs_inds=[],start_date='2001-01-01',end_date='2001-01-01', num_days=180,colors=['orange','purple','cyan']): # or inds_on_price?
    
    start_date = dt.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = dt.datetime.strptime(end_date, '%Y-%m-%d')
    default_date=dt.datetime.strptime('2001-01-01', '%Y-%m-%d')
    
  
    # set the dates
    if (start_date==default_date) & (end_date==default_date):
            end_date=coin_hist_prices.iloc[len(coin_hist_prices)-2]['date']
            start_date=end_date - dt.timedelta(days=num_days)

    elif start_date==default_date:
        start_date= end_date - dt.timedelta(days=num_days) 
    elif end_date==default_date:
        end_date=start_date + dt.timedelta(days=num_days)
    print('start date:',start_date,'end date:',end_date)
    
    plot_data=data=coin_hist_prices.loc[((coin_hist_prices['date']>=start_date)&(coin_hist_prices['date']<=end_date))]
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Plot price
    fig.add_trace(go.Scatter(x=plot_data['date'],y=plot_data['price'],name='Price',mode='lines', 
                             opacity=0.2, line_color='black'),secondary_y=False)

    # plot vs indicators 
    for (i,ind) in enumerate(vs_inds):
            fig.add_trace(go.Scatter(x=plot_data['date'],y=plot_data[ind],name=ind,mode='lines', 
                             line_color=colors[i]),secondary_y=True)
     # plot signals
    for index, row in plot_data.iterrows():
        if (row['trade_reco'] == 'BUY'):
            fig.add_annotation(x=row['date'], y=row['price'],text="BUY", font={'color':'green','size':12},showarrow=True, arrowhead=2)
        elif (row['trade_reco'] == 'SELL'):
            fig.add_annotation(x=row['date'], y=row['price'],text="SELL", font={'color':'red','size':12},showarrow=True, arrowhead=2)

    fig.update_layout(autosize=False, width=1400, height=700,margin=go.layout.Margin(
        l=20, r=20, b=20, t=20, pad = 1),
        xaxis=dict(rangeselector=dict( buttons=list([
                dict(count=1,label="1m", step="month", stepmode="backward"),
                dict(count=6,label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        ), rangeslider=dict(visible=True), type="date"), legend_orientation='h' )
   
    fig.update_yaxes({'fixedrange':False})
    
    return fig.show()