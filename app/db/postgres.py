"""PostgreSQL client for metadata storage."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON

from app.core.exceptions import DatabaseError
from app.core.logging_config import logger
from config.settings import settings

# SQLAlchemy Base
Base = declarative_base()


class Trade(Base):
    """Trade model for PostgreSQL."""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    exchange = Column(String, nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    side = Column(String, nullable=False)
    order_type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    price = Column(Float)
    filled = Column(Float, default=0.0)
    status = Column(String, nullable=False)
    order_id = Column(String, unique=True, index=True)
    strategy_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Strategy(Base):
    """Strategy configuration model."""
    __tablename__ = "strategies"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    config = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PostgreSQLClient:
    """PostgreSQL client for metadata storage."""

    def __init__(self, url: Optional[str] = None):
        """
        Initialize PostgreSQL client.

        Args:
            url: PostgreSQL connection URL
        """
        self.url = url or settings.postgres_url
        self._engine = None
        self._async_session = None

    async def connect(self) -> None:
        """Establish connection to PostgreSQL."""
        try:
            self._engine = create_async_engine(
                self.url,
                echo=False,
                pool_pre_ping=True
            )
            self._async_session = sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # Test connection
            async with self._engine.begin() as conn:
                await conn.run_sync(lambda conn: None)

            logger.info(f"Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise DatabaseError(f"PostgreSQL connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """Close PostgreSQL connection."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            logger.info("Disconnected from PostgreSQL")

    async def create_tables(self) -> None:
        """Create all tables."""
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Created PostgreSQL tables")
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise DatabaseError(f"Table creation failed: {str(e)}")

    async def save_trade(self, trade_data: Dict[str, Any]) -> int:
        """
        Save trade to database.

        Args:
            trade_data: Trade information

        Returns:
            Trade ID
        """
        if not self._async_session:
            raise DatabaseError("Not connected to PostgreSQL")

        try:
            async with self._async_session() as session:
                trade = Trade(**trade_data)
                session.add(trade)
                await session.commit()
                await session.refresh(trade)
                logger.info(f"Saved trade {trade.id}")
                return trade.id
        except Exception as e:
            logger.error(f"Failed to save trade: {str(e)}")
            raise DatabaseError(f"Trade save failed: {str(e)}")

    async def get_trades(
        self,
        exchange: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query trades from database.

        Args:
            exchange: Filter by exchange
            symbol: Filter by symbol
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of trades
        """
        if not self._async_session:
            raise DatabaseError("Not connected to PostgreSQL")

        try:
            async with self._async_session() as session:
                query = session.query(Trade)

                if exchange:
                    query = query.filter(Trade.exchange == exchange)
                if symbol:
                    query = query.filter(Trade.symbol == symbol)

                query = query.order_by(Trade.created_at.desc())
                query = query.limit(limit).offset(offset)

                result = await query.all()

                trades = []
                for trade in result:
                    trades.append({
                        'id': trade.id,
                        'exchange': trade.exchange,
                        'symbol': trade.symbol,
                        'side': trade.side,
                        'order_type': trade.order_type,
                        'amount': trade.amount,
                        'price': trade.price,
                        'filled': trade.filled,
                        'status': trade.status,
                        'order_id': trade.order_id,
                        'strategy_id': trade.strategy_id,
                        'created_at': trade.created_at,
                        'updated_at': trade.updated_at
                    })

                logger.debug(f"Retrieved {len(trades)} trades")
                return trades
        except Exception as e:
            logger.error(f"Failed to get trades: {str(e)}")
            raise DatabaseError(f"Trade query failed: {str(e)}")

    async def save_strategy(self, strategy_data: Dict[str, Any]) -> None:
        """
        Save strategy configuration.

        Args:
            strategy_data: Strategy information
        """
        if not self._async_session:
            raise DatabaseError("Not connected to PostgreSQL")

        try:
            async with self._async_session() as session:
                strategy = Strategy(**strategy_data)
                session.add(strategy)
                await session.commit()
                logger.info(f"Saved strategy {strategy.id}")
        except Exception as e:
            logger.error(f"Failed to save strategy: {str(e)}")
            raise DatabaseError(f"Strategy save failed: {str(e)}")

    async def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        Get strategy by ID.

        Args:
            strategy_id: Strategy ID

        Returns:
            Strategy data or None
        """
        if not self._async_session:
            raise DatabaseError("Not connected to PostgreSQL")

        try:
            async with self._async_session() as session:
                result = await session.query(Strategy).filter(
                    Strategy.id == strategy_id
                ).first()

                if result:
                    return {
                        'id': result.id,
                        'name': result.name,
                        'description': result.description,
                        'config': result.config,
                        'is_active': result.is_active,
                        'created_at': result.created_at,
                        'updated_at': result.updated_at
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get strategy: {str(e)}")
            raise DatabaseError(f"Strategy query failed: {str(e)}")

    async def list_strategies(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        List all strategies.

        Args:
            active_only: Only return active strategies

        Returns:
            List of strategies
        """
        if not self._async_session:
            raise DatabaseError("Not connected to PostgreSQL")

        try:
            async with self._async_session() as session:
                query = session.query(Strategy)

                if active_only:
                    query = query.filter(Strategy.is_active == True)

                result = await query.all()

                strategies = []
                for strategy in result:
                    strategies.append({
                        'id': strategy.id,
                        'name': strategy.name,
                        'description': strategy.description,
                        'config': strategy.config,
                        'is_active': strategy.is_active,
                        'created_at': strategy.created_at,
                        'updated_at': strategy.updated_at
                    })

                logger.debug(f"Retrieved {len(strategies)} strategies")
                return strategies
        except Exception as e:
            logger.error(f"Failed to list strategies: {str(e)}")
            raise DatabaseError(f"Strategy list failed: {str(e)}")
