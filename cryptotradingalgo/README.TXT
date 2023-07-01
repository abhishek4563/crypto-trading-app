## README.TXT


### Fetching data, calcs and genning trades functions: Usage

#### for BTC
btc_hist_prices=adt.get_daily_prices("bitcoin")
adt.create_indicators(btc_hist_prices)
adt.calc_signals(btc_hist_prices)
adt.gen_trades(btc_hist_prices)

#### for ETH
eth_hist_prices=adt.get_daily_prices("ethereum")
adt.create_indicators(eth_hist_prices)
adt.calc_signals(eth_hist_prices)
adt.gen_trades(eth_hist_prices)


### Plotting Functions: Function signatures

#### Plot an indicator
plot_inds(coin_hist_prices,inds=[],start_date='2001-01-01',end_date='2001-01-01', num_days=180 ):
plotly_inds(coin_hist_prices,inds=[],start_date='2001-01-01',end_date='2001-01-01', num_days=180 ):

#### Plot price vs upto 3 indicators
plot_price_vs_inds (coin_hist_prices,vs_inds=[],start_date='2001-01-01',end_date='2001-01-01', num_days=180,colors=['red','blue','green']): # or inds_on_price?
plotly_price_vs_inds (coin_hist_prices,vs_inds=[],start_date='2001-01-01',end_date='2001-01-01', num_days=180,colors=['red','blue','green']): # or inds_on_price?

#### Plot buy/sell signals as well as inds
plot_signals(coin_hist_prices,inds=[],start_date='2001-01-01',end_date='2001-01-01', num_days=180,colors=['orange','purple','grey'] ):   
plotly_signals (coin_hist_prices,start_date='2001-01-01',end_date='2001-01-01', num_days=180,colors=['red','blue','green']): # or inds_on_price?
