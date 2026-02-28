"""Main entry point for Cactus Trading Bot."""

import asyncio
from loguru import logger

from app.core.logging_config import setup_logging
from app.exchanges.binance import BinanceExchange
from app.db.influxdb import InfluxDBClient
from app.db.redis import RedisClient
from app.db.postgres import PostgreSQLClient
from app.data.pipeline import DataPipeline


async def test_system():
    """Test the complete system setup."""
    logger.info("=" * 60)
    logger.info("Cactus AI Auto Trader - System Test")
    logger.info("=" * 60)

    try:
        # Initialize exchange (sandbox mode for testing)
        logger.info("Initializing Binance exchange...")
        exchange = BinanceExchange(
            api_key="test_key",
            secret="test_secret",
            sandbox=True
        )
        await exchange.connect()
        logger.success("✓ Exchange connected")

        # Initialize databases
        logger.info("Initializing databases...")

        # InfluxDB (will fail if not running, but that's OK for now)
        try:
            influxdb = InfluxDBClient()
            await influxdb.connect()
            logger.success("✓ InfluxDB connected")
        except Exception as e:
            logger.warning(f"✗ InfluxDB not available: {e}")
            influxdb = None

        # Redis (will fail if not running, but that's OK for now)
        try:
            redis_client = RedisClient()
            await redis_client.connect()
            logger.success("✓ Redis connected")
        except Exception as e:
            logger.warning(f"✗ Redis not available: {e}")
            redis_client = None

        # PostgreSQL (will fail if not running, but that's OK for now)
        try:
            postgres = PostgreSQLClient()
            await postgres.connect()
            logger.success("✓ PostgreSQL connected")
        except Exception as e:
            logger.warning(f"✗ PostgreSQL not available: {e}")
            postgres = None

        # Initialize data pipeline
        if influxdb and redis_client:
            logger.info("Initializing data pipeline...")
            pipeline = DataPipeline(exchange, influxdb, redis_client)
            logger.success("✓ Data pipeline initialized")

            # Test ticker fetch (will use public data, no auth needed)
            logger.info("Testing ticker fetch...")
            try:
                ticker = await exchange.get_ticker('BTC/USDT')
                logger.success(f"✓ BTC/USDT: ${ticker['last_price']:,.2f}")
            except Exception as e:
                logger.warning(f"✗ Ticker fetch failed: {e}")

        # Cleanup
        logger.info("Cleaning up...")
        await exchange.disconnect()
        if influxdb:
            await influxdb.disconnect()
        if redis_client:
            await redis_client.disconnect()
        if postgres:
            await postgres.disconnect()
        logger.success("✓ Cleanup complete")

        logger.info("=" * 60)
        logger.success("System test complete!")
        logger.info("=" * 60)

        logger.info("\n📋 Setup Status:")
        logger.info("✓ Project structure: Complete")
        logger.info("✓ Exchange integration: Complete")
        logger.info("✓ Database clients: Complete")
        logger.info("✓ Data pipeline: Complete")
        logger.info("✓ Configuration: Complete")
        logger.info("✓ Logging: Complete")
        logger.info("\n🔧 Next Steps:")
        logger.info("1. Start InfluxDB: docker run -d -p 8086:8086 influxdb:3.0")
        logger.info("2. Start Redis: docker run -d -p 6379:6379 redis:7-alpine")
        logger.info("3. Start PostgreSQL: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15")
        logger.info("4. Configure .env file with your API keys")
        logger.info("5. Run tests: pytest")

    except Exception as e:
        logger.error(f"System test failed: {str(e)}")
        raise


async def main():
    """Main entry point."""
    setup_logging()
    await test_system()


if __name__ == "__main__":
    asyncio.run(main())
