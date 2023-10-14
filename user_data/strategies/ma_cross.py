# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame

from freqtrade.strategy import (IStrategy)

# --------------------------------
# Add your lib to import here
import freqtrade.vendor.qtpylib.indicators as qtpylib
import talib.abstract as ta
import numpy as np
from scipy.ndimage import label, sum
from shared.custom_classes import CustomSender


# This class is a sample. Feel free to customize it.
class MACross(IStrategy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_notif = CustomSender()
    """
    This is a sample strategy to inspire you.
    More information in https://www.freqtrade.io/en/latest/strategy-customization/

    You can:
        :return: a Dataframe with all mandatory indicators for the strategies
    - Rename the class name (Do not forget to update class_name)
    - Add any methods you want to build your strategy
    - Add any lib you need to build your strategy

    You must keep:
    - the lib in the section "Do not remove these libs"
    - the methods: populate_indicators, populate_entry_trend, populate_exit_trend
    You should keep:
    - timeframe, minimal_roi, stoploss, trailing_*
    """
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # Can this strategy go short?
    can_short: bool = True

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "60": 0.01,
        "30": 0.02,
        "0": 0.04
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.10

    # Trailing stoploss
    trailing_stop = False
    # trailing_only_offset_is_reached = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured

    # Optimal timeframe for the strategy.
    timeframe = '1m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = False
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    short_ma_len = 3
    long_ma_len = 6

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = long_ma_len + short_ma_len

    # Plot Length
    plot_candle_count = 30

    # Optional order type mapping.
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'entry': 'GTC',
        'exit': 'GTC'
    }

    plot_config = {
        'main_plot': {
            'tenkan_sen': {'color': 'orange'},
            'kijun_sen': {'color': 'blue'},
            'senkou_span_b': {'color': 'red'},
            'leading_senkou_span_b': {'color': 'green'},
        }
    }

    telegram_plot_config = {
        'main_plot': {
            'short_ma': {'color': 'blue'},
            'long_ma': {'color': 'red'}
        }
    }


    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame

        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        :param dataframe: Dataframe with data from the exchange
        :param metadata: Additional information, like the currently traded pair
        :return: a Dataframe with all mandatory indicators for the strategies
        """

        dataframe['short_ma'] = ta.EMA(dataframe, timeperiod=self.short_ma_len)
        dataframe['long_ma'] = ta.EMA(dataframe, timeperiod=self.long_ma_len)

        dataframe['long_trades'] = np.nan
        dataframe['short_trades'] = np.nan

        dataframe.loc[
            (
                qtpylib.crossed_above(dataframe['short_ma'], dataframe['long_ma'])

            ),
            'long_trades'] = 1

        dataframe.loc[
            (
                qtpylib.crossed_below(dataframe['short_ma'], dataframe['long_ma'])
            ),
            'short_trades'] = 1

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with entry columns populated
        """

        dataframe.loc[
            (
                (dataframe['long_trades'] == 1)
            ),
            'enter_long'] = 1

        if dataframe['enter_long'].iloc[-1] == 1:
            data = dataframe.tail(self.plot_candle_count)
            entry_markers = {
                "data": [round(value, 7) for value in
                         data['close'].where(data['enter_long'] == 1, other=np.nan).tolist()],
                "color": 'green'}

            self.custom_notif.send_custom_message(self.dp, data, metadata,
                                                  plot_config=self.telegram_plot_config,
                                                  markers={"entry": entry_markers})

        dataframe.loc[
            (
                (dataframe['short_trades'] == 1)
            ),
            'enter_short'] = 1

        if dataframe['enter_short'].iloc[-1] == 1:
            data = dataframe.tail(self.plot_candle_count)
            entry_markers = {
                "data": [round(value, 7) for value in
                         data['close'].where(data['enter_short'] == 1, other=np.nan).tolist()],
                "color": 'red'}

            self.custom_notif.send_custom_message(self.dp, data, metadata,
                                                  plot_config=self.telegram_plot_config,
                                                  markers={"entry": entry_markers})


        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the exit signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with exit columns populated
        """

        return dataframe
