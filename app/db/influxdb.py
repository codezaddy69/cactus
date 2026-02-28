"""InfluxDB 3 client for time-series data storage."""

from typing import List, Optional
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions
from influxdb_client.client.query_api import QueryApi

from app.core.types import OHLCV, Ticker
from app.core.exceptions import DatabaseError
from app.core.logging_config import logger
from config.settings import settings


class InfluxDBClient:
    """InfluxDB 3 client for time-series data."""

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        org: Optional[str] = None,
        bucket: Optional[str] = None
    ):
        """
        Initialize InfluxDB client.

        Args:
            url: InfluxDB server URL
            token: Authentication token
            org: Organization name
            bucket: Bucket name
        """
        self.url = url or settings.influxdb_url
        self.token = token or settings.influxdb_token
        self.org = org or settings.influxdb_org
        self.bucket = bucket or settings.influxdb_bucket

        self._client: Optional[InfluxDBClient] = None
        self._write_api = None
        self._query_api = None

    async def connect(self) -> None:
        """Establish connection to InfluxDB."""
        try:
            self._client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org
            )
            self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
            self._query_api = self._client.query_api()

            logger.info(f"Connected to InfluxDB at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {str(e)}")
            raise DatabaseError(f"InfluxDB connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """Close InfluxDB connection."""
        if self._write_api:
            self._write_api.close()

        if self._client:
            self._client.close()
            self._client = None
            logger.info("Disconnected from InfluxDB")

    def write_ohlcv(self, exchange: str, symbol: str, ohlcv: OHLCV) -> None:
        """
        Write OHLCV candle data to InfluxDB.

        Args:
            exchange: Exchange name (e.g., 'binance')
            symbol: Trading pair symbol
            ohlcv: OHLCV data point
        """
        if not self._write_api:
            raise DatabaseError("Not connected to InfluxDB")

        try:
            point = (
                Point("ohlcv")
                .tag("exchange", exchange)
                .tag("symbol", symbol)
                .field("open", ohlcv['open'])
                .field("high", ohlcv['high'])
                .field("low", ohlcv['low'])
                .field("close", ohlcv['close'])
                .field("volume", ohlcv['volume'])
                .time(ohlcv['timestamp'])
            )

            self._write_api.write(bucket=self.bucket, record=point)
            logger.debug(f"Wrote OHLCV for {symbol} at {ohlcv['timestamp']}")
        except Exception as e:
            logger.error(f"Failed to write OHLCV: {str(e)}")
            raise DatabaseError(f"OHLCV write failed: {str(e)}")

    def write_ohlcv_batch(
        self,
        exchange: str,
        symbol: str,
        ohlcv_list: List[OHLCV]
    ) -> None:
        """
        Write multiple OHLCV candles in batch.

        Args:
            exchange: Exchange name
            symbol: Trading pair symbol
            ohlcv_list: List of OHLCV data points
        """
        if not self._write_api:
            raise DatabaseError("Not connected to InfluxDB")

        try:
            points = []
            for ohlcv in ohlcv_list:
                point = (
                    Point("ohlcv")
                    .tag("exchange", exchange)
                    .tag("symbol", symbol)
                    .field("open", ohlcv['open'])
                    .field("high", ohlcv['high'])
                    .field("low", ohlcv['low'])
                    .field("close", ohlcv['close'])
                    .field("volume", ohlcv['volume'])
                    .time(ohlcv['timestamp'])
                )
                points.append(point)

            self._write_api.write(bucket=self.bucket, record=points)
            logger.debug(f"Wrote batch of {len(points)} OHLCV for {symbol}")
        except Exception as e:
            logger.error(f"Failed to write OHLCV batch: {str(e)}")
            raise DatabaseError(f"OHLCV batch write failed: {str(e)}")

    def write_ticker(self, exchange: str, ticker: Ticker) -> None:
        """
        Write ticker data to InfluxDB.

        Args:
            exchange: Exchange name
            ticker: Ticker data
        """
        if not self._write_api:
            raise DatabaseError("Not connected to InfluxDB")

        try:
            point = (
                Point("ticker")
                .tag("exchange", exchange)
                .tag("symbol", ticker['symbol'])
                .field("last_price", ticker['last_price'])
                .field("bid", ticker['bid'])
                .field("ask", ticker['ask'])
                .field("volume", ticker['volume'])
                .time(ticker['timestamp'])
            )

            self._write_api.write(bucket=self.bucket, record=point)
            logger.debug(f"Wrote ticker for {ticker['symbol']}")
        except Exception as e:
            logger.error(f"Failed to write ticker: {str(e)}")
            raise DatabaseError(f"Ticker write failed: {str(e)}")

    def query_ohlcv(
        self,
        exchange: str,
        symbol: str,
        start: datetime,
        stop: Optional[datetime] = None
    ) -> List[OHLCV]:
        """
        Query OHLCV data from InfluxDB.

        Args:
            exchange: Exchange name
            symbol: Trading pair symbol
            start: Start time
            stop: End time (optional, defaults to now)

        Returns:
            List of OHLCV candles
        """
        if not self._query_api:
            raise DatabaseError("Not connected to InfluxDB")

        try:
            stop_time = stop or datetime.utcnow()

            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: {start.isoformat()}Z, stop: {stop_time.isoformat()}Z)
              |> filter(fn: (r) => r._measurement == "ohlcv")
              |> filter(fn: (r) => r.exchange == "{exchange}")
              |> filter(fn: (r) => r.symbol == "{symbol}")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
              |> sort(columns: ["_time"])
            '''

            result = self._query_api.query(query)

            ohlcv_list = []
            for table in result:
                for record in table.records:
                    ohlcv_list.append(OHLCV(
                        timestamp=record.get_time(),
                        open=record.get_value("open"),
                        high=record.get_value("high"),
                        low=record.get_value("low"),
                        close=record.get_value("close"),
                        volume=record.get_value("volume")
                    ))

            logger.debug(f"Queried {len(ohlcv_list)} OHLCV for {symbol}")
            return ohlcv_list
        except Exception as e:
            logger.error(f"Failed to query OHLCV: {str(e)}")
            raise DatabaseError(f"OHLCV query failed: {str(e)}")
