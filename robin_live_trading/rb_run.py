from rb_login import robin_login


## --------------------------------------------------------------------------------------------------------------------
## set parameters
parameters = {'short_window':60,'long_window':120,'signal_window':60,'dollar_amt':100,}
## ----------------------------------------------------------------------------------------------------------------

## initialization 
rb_client = robin_login(username='xxxxxx', password='xxxxxx')
rb_client.data.get_crypto_historicals_df()

## --------------------------------------------------------------------------------------------------------------------

## stock visualization
rb_client.data.live_plot_start('NIO',span='month',bound='regular')