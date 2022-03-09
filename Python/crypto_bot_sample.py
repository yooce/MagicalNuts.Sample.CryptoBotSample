import asyncio
import pybotters
import time
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import json
import requests

async def main():
    apis= {"bybit": ["___KEY___", "___SECRET___"]}

    async with pybotters.Client(base_url="https://api.bybit.com", apis=apis) as client:
        store = pybotters.BybitUSDTDataStore()

        # initialize
        ts = int(time.time()) - 60 * 60
        await store.initialize(
            client.get("/private/linear/order/search?symbol=BTCUSDT"),
            client.get("/private/linear/stop-order/search?symbol=BTCUSDT"),
            client.get("/private/linear/position/list?symbol=BTCUSDT"),
            client.get(f"/public/linear/kline?symbol=BTCUSDT&interval=1&from={ ts }"),
            client.get("/v2/private/wallet/balance"),
        )
        pybotters.print("order")
        pybotters.print(store.order.find({"symbol": "BTCUSDT"}))
        pybotters.print("stoporder")
        pybotters.print(store.stoporder.find({"symbol": "BTCUSDT"}))
        pybotters.print("position")
        pybotters.print(store.position.both("BTCUSDT"))
        pybotters.print("kline")
        pybotters.print(store.kline.find({"symbol": "BTCUSDT"}))
        pybotters.print("wallet")
        pybotters.print(store.wallet.find({"coin": "USDT"}))
        pybotters.print("Initialized")

        # connect ws
        await asyncio.gather(
            client.ws_connect(
                "wss://stream.bybit.com/realtime_public",
                send_json={
                    "op": "subscribe",
                    "args": [
                        "orderBookL2_25.BTCUSDT",
                        "trade.BTCUSDT",
                        "instrument_info.100ms.BTCUSDT",
                        "candle.1.BTCUSDT",
                        "liquidation.BTCUSDT",
                    ],
                },
                hdlr_json=store.onmessage,
            ),
            client.ws_connect(
                "wss://stream.bybit.com/realtime_private",
                send_json={
                    "op": "subscribe",
                    "args": [
                        "position",
                        "execution",
                        "order",
                        "stop_order",
                        "wallet",
                    ],
                },
                hdlr_json=store.onmessage,
            ),
        )
        pybotters.print("Connected")

        # event-driven bot main loop (Ctrl+C to break)
        prev_timestamp = store.kline.find()[-2]['start']
        while True:
            # wait for next loop
            await store.kline.wait()

            if store.kline.find()[-2]['start'] == prev_timestamp:
                continue

            prev_timestamp = store.kline.find()[-2]['start']

            pybotters.print("Start main loop")
            orderbook = store.orderbook.sorted({"symbol": "BTCUSDT"})
            position = store.position.both("BTCUSDT")

            # prepare candles
            df = pd.DataFrame(store.kline.find())
            df = df[len(df.index) - (21 + 1) :-1]
            df.sort_values('start', inplace=True, ascending=False)
            df['DateTime'] = np.nan
            for idx in df.index:
                df.loc[idx, 'DateTime'] = datetime.fromtimestamp(df.loc[idx, 'start'], tz=pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%dT%H:%M:%S+09:00')
            df.drop(['confirm', 'cross_seq', 'end', 'id', 'interval', 'period', 'start', 'start_at', 'symbol', 'timestamp', 'turnover'], axis=1, inplace=True)
            df.rename(columns={'open': 'op', 'high': 'hi', 'low': 'lo', 'close': 'cl', 'volume': 'vo'}, inplace=True)
            df.rename(columns={'op': 'Open', 'hi': 'High', 'lo': 'Low', 'cl': 'Close', 'vo': 'Volume'}, inplace=True)

            # prepare post data
            data = {
                'StockCandles':  [{
                    'Candles': df.to_dict(orient='records'),
                    'Additional': { 'Code': 'BTCUSDT', 'Unit': 0.001 },
                    'PeriodInfo': { 'Unit': 'Minute', 'Period': 1 }
                }],
                'MarketAssets': store.wallet.find()[-1]['wallet_balance'],
                'NetBalance': store.wallet.find()[-1]['available_balance'],
                'Orders': [],
                'ActivePositions': [],
                'CurrencyDigits': 3,
                'Leverage': 10,
            }
            pybotters.print('data')
            pybotters.print(data)

            # post data to local ASP.NET Core server
            response = None
            try:
                response = requests.post('http://localhost:5101/strategy', json=json.dumps(data), verify=False)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                pybotters.print('Failed to POST to API server.')
                continue

            # get orders
            orders = response.json()
            pybotters.print('orders')
            pybotters.print(orders)

            # trading condition
            spread = float(orderbook["Sell"][0]["price"]) - float(orderbook["Buy"][0]["price"])
            pybotters.print(
                f"Ask: {orderbook['Sell'][0]['price']}({sum(x['size'] for x in orderbook['Sell']):.4f}) "
                f"Bid: {orderbook['Buy'][0]['price']}({sum(x['size'] for x in orderbook['Buy']):.4f}) "
                f"Spread: {spread:.2f}"
            )
            cond = all(
                [
                    spread > 999.0,
                    position["Buy"]["size"] < 0.0,
                    False,
                ]
            )
            price = orderbook["Buy"][0]["price"]

            if cond:
                wswait = asyncio.create_task(store.order.wait())
                # create limit order into best bid
                r = await client.post(
                    "/private/linear/order/create",
                    data=dict(
                        side="Buy",
                        symbol="BTCUSDT",
                        order_type="Limit",
                        qty=0.001,
                        price=price,
                        time_in_force="PostOnly",
                        close_on_trigger=False,
                        reduce_only=False,
                    )
                )
                data = await r.json()
                pybotters.print(data)
                if data["ret_code"] == 0:
                    await wswait
                else:
                    wswait.cancel()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass