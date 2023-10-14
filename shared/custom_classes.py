import json
from pandas import DataFrame


class CustomSender:

    def send_custom_message(self, dp, dataframe: DataFrame, metadata, plot_config, markers):
        msg = {}
        ohlcv_keys = ["open", "high", "low", "close", "volume"]

        msg['ohlcv_data'] = {ohlcv_key: dataframe[ohlcv_key].tolist() for ohlcv_key in ohlcv_keys}
        plot_data = {}
        if plot_config:
            for key, attributes in plot_config['main_plot'].items():
                plot_data[key] = {
                    'data': dataframe[key].tolist(),
                    'color': attributes['color']
                }
        msg['main_plot_data'] = plot_data
        msg['metadata'] = metadata
        msg['markers'] = markers
        dp.send_msg(json.dumps(msg))


