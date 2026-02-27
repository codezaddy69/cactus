# MONITORING & DASHBOARD MODULE - RESEARCH PLAN
## Real-Time Visualization, Control Interface & Alerting System

**Document Version:** 1.0  
**Last Updated:** 2026-02-10  
**Priority:** HIGH - Phase 3  
**Estimated Development:** 2 Weeks

---

## Executive Summary

The Monitoring & Dashboard Module provides real-time visibility into the trading bot's performance, positions, and health. It serves as the control center for operators to monitor P&L, manage strategies, receive alerts, and intervene when necessary. This plan integrates FastAPI for the backend API, WebSockets for real-time updates, and Dash/Plotly for interactive visualizations.

**Key Sources:**
1. FastAPI Documentation - https://fastapi.tiangolo.com/
2. WebSocket Best Practices - https://fastapi.tiangolo.com/advanced/websockets/
3. Dash/Plotly Documentation - https://dash.plotly.com/
4. Trading Dashboard Examples - https://github.com/JOravetz/stock-market-dashboard

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                      MONITORING & DASHBOARD ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  FRONTEND (React/Dash)                                                               │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │ Components:                                                                    │  │
│  │ • P&L Chart (Real-time equity curve)                                          │  │
│  │ • Position Table (Open positions)                                             │  │
│  │ • Trade History (Recent trades)                                               │  │
│  │ • Strategy Controls (Start/Stop/Config)                                       │  │
│  │ • Performance Metrics (Sharpe, Drawdown)                                      │  │
│  │ • Alert Panel (Active alerts)                                                 │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ HTTP / WebSocket
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  BACKEND API (FastAPI - MIT License)                                                 │
│  ┌───────────────────┬───────────────────┬───────────────────┐                     │
│  │ REST Endpoints    │ WebSocket         │ Background        │                     │
│  │ • /api/positions  │ • /ws/realtime    │ • Data Collector  │                     │
│  │ • /api/trades     │   (P&L updates)   │ • Alert Checker   │                     │
│  │ • /api/strategies │ • /ws/alerts      │ • Metric Computer │                     │
│  │ • /api/metrics    │   (Alerts)        │                   │                     │
│  └───────────────────┴───────────────────┴───────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            │                          │                          │
            ▼                          ▼                          ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│  DATABASES          │  │  STRATEGY MODULE    │  │  RISK MODULE        │
│                     │  │                     │  │                     │
│  • InfluxDB (P&L)   │  │  • Signal updates   │  │  • Risk alerts      │
│  • PostgreSQL       │  │  • Strategy status  │  │  • Circuit breaker  │
│    (trades)         │  │  • Performance      │  │  • Limits breached  │
│  • Redis (Cache)    │  │                     │  │                     │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

---

## Phase 1: Backend API Development

### 1.1 FastAPI Application Structure

**Source:** FastAPI Documentation (https://fastapi.tiangolo.com/)

```python
# dashboard/api/main.py
"""
FastAPI application for dashboard backend.

Source: https://fastapi.tiangolo.com/tutorial/first-steps/
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
import logging

from .routes import positions, trades, strategies, metrics, alerts
from .websocket import ConnectionManager
from .background_tasks import start_background_tasks, stop_background_tasks

logger = logging.getLogger(__name__)

# Connection manager for WebSockets
manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Starts background tasks on startup, stops on shutdown.
    
    Source: https://fastapi.tiangolo.com/advanced/events/
    """
    # Startup
    logger.info("Starting dashboard background tasks...")
    await start_background_tasks()
    yield
    # Shutdown
    logger.info("Stopping dashboard background tasks...")
    await stop_background_tasks()

app = FastAPI(
    title="Trading Bot Dashboard API",
    description="Real-time API for trading bot monitoring and control",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(positions.router, prefix="/api/positions", tags=["positions"])
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Trading Bot Dashboard API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# WebSocket endpoint for real-time updates
@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time data streaming.
    
    Source: https://fastapi.tiangolo.com/advanced/websockets/
    """
    await manager.connect(websocket)
    try:
        while True:
            # Receive message (optional - for client commands)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client commands
            if message.get('action') == 'subscribe':
                channel = message.get('channel')
                await manager.subscribe(websocket, channel)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    """WebSocket endpoint for alert streaming"""
    await manager.connect(websocket, channel="alerts")
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### 1.2 REST API Routes

```python
# dashboard/api/routes/positions.py
"""
Position management API routes.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class PositionResponse(BaseModel):
    position_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    opened_at: datetime

class PositionUpdate(BaseModel):
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

# Mock data - replace with database queries
MOCK_POSITIONS = []

@router.get("/", response_model=List[PositionResponse])
async def get_positions(symbol: Optional[str] = None):
    """
    Get all open positions.
    
    Args:
        symbol: Optional filter by symbol
        
    Returns:
        List of open positions
    """
    positions = MOCK_POSITIONS
    
    if symbol:
        positions = [p for p in positions if p['symbol'] == symbol]
    
    return positions

@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(position_id: str):
    """Get specific position details"""
    position = next(
        (p for p in MOCK_POSITIONS if p['position_id'] == position_id),
        None
    )
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    return position

@router.post("/{position_id}/close")
async def close_position(position_id: str):
    """
    Close a position manually.
    
    This will trigger an immediate market order to close the position.
    """
    position = next(
        (p for p in MOCK_POSITIONS if p['position_id'] == position_id),
        None
    )
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    # TODO: Trigger position close through exchange module
    
    return {"message": f"Position {position_id} close requested"}

@router.patch("/{position_id}")
async def update_position(position_id: str, update: PositionUpdate):
    """
    Update position parameters (stop loss, take profit).
    """
    position = next(
        (p for p in MOCK_POSITIONS if p['position_id'] == position_id),
        None
    )
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    if update.stop_loss is not None:
        position['stop_loss'] = update.stop_loss
    
    if update.take_profit is not None:
        position['take_profit'] = update.take_profit
    
    return position
```

```python
# dashboard/api/routes/strategies.py
"""
Strategy control API routes.
"""

from fastapi import APIRouter
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter()

class StrategyResponse(BaseModel):
    strategy_id: str
    name: str
    enabled: bool
    weight: float
    symbols: List[str]
    total_trades: int
    win_rate: float
    total_pnl: float

class StrategyToggle(BaseModel):
    enabled: bool

MOCK_STRATEGIES = []

@router.get("/", response_model=List[StrategyResponse])
async def get_strategies():
    """Get all strategies and their status"""
    return MOCK_STRATEGIES

@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: str):
    """Get specific strategy details"""
    strategy = next(
        (s for s in MOCK_STRATEGIES if s['strategy_id'] == strategy_id),
        None
    )
    return strategy

@router.post("/{strategy_id}/toggle")
async def toggle_strategy(strategy_id: str, toggle: StrategyToggle):
    """
    Enable or disable a strategy.
    
    This immediately stops the strategy from generating new signals.
    Existing positions are not affected.
    """
    strategy = next(
        (s for s in MOCK_STRATEGIES if s['strategy_id'] == strategy_id),
        None
    )
    
    if not strategy:
        return {"error": "Strategy not found"}
    
    strategy['enabled'] = toggle.enabled
    
    action = "enabled" if toggle.enabled else "disabled"
    return {"message": f"Strategy {strategy_id} {action}"}

@router.post("/{strategy_id}/emergency-stop")
async def emergency_stop(strategy_id: str):
    """
    Emergency stop: disable strategy AND close all positions.
    
    Use this when a strategy is behaving unexpectedly.
    """
    # TODO: Implement emergency stop logic
    return {"message": f"Emergency stop triggered for {strategy_id}"}
```

### 1.3 Metrics API

```python
# dashboard/api/routes/metrics.py
"""
Performance metrics API routes.
"""

from fastapi import APIRouter
from typing import Dict
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/overview")
async def get_metrics_overview():
    """
    Get high-level performance metrics.
    
    Returns:
        Dictionary of key metrics
    """
    # TODO: Calculate from actual data
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "account": {
            "balance": 12500.00,
            "equity": 12750.00,
            "unrealized_pnl": 250.00,
            "realized_pnl_today": 125.00,
            "realized_pnl_week": 450.00,
            "realized_pnl_month": 1250.00
        },
        "performance": {
            "total_return_pct": 27.5,
            "sharpe_ratio": 1.42,
            "max_drawdown_pct": -12.3,
            "win_rate": 54.2,
            "profit_factor": 1.85,
            "total_trades": 156
        },
        "positions": {
            "open_count": 3,
            "total_exposure": 6250.00,
            "exposure_pct": 50.0
        }
    }

@router.get("/equity-curve")
async def get_equity_curve(days: int = 30):
    """
    Get equity curve data for charting.
    
    Args:
        days: Number of days of history
        
    Returns:
        List of {timestamp, equity} data points
    """
    # TODO: Query from InfluxDB
    return {
        "data": [
            {"timestamp": "2026-01-01T00:00:00Z", "equity": 10000},
            {"timestamp": "2026-01-15T00:00:00Z", "equity": 10500},
            {"timestamp": "2026-02-01T00:00:00Z", "equity": 11200},
        ]
    }

@router.get("/drawdown")
async def get_drawdown_history(days: int = 30):
    """
    Get drawdown history for charting.
    """
    return {
        "data": [
            {"timestamp": "2026-01-01T00:00:00Z", "drawdown": 0},
            {"timestamp": "2026-01-10T00:00:00Z", "drawdown": -0.05},
            {"timestamp": "2026-01-20T00:00:00Z", "drawdown": -0.08},
        ]
    }
```

---

## Phase 2: WebSocket Real-Time Updates

### 2.1 Connection Manager

**Source:** FastAPI WebSocket Guide (https://fastapi.tiangolo.com/advanced/websockets/)

```python
# dashboard/api/websocket.py
"""
WebSocket connection manager for real-time updates.
"""

from fastapi import WebSocket
from typing import List, Dict
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.
    
    Source: https://fastapi.tiangolo.com/advanced/websockets/
    """
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.channel_subscriptions: Dict[str, List[WebSocket]] = {
            'pnl_updates': [],
            'trade_alerts': [],
            'system_alerts': []
        }
    
    async def connect(self, websocket: WebSocket, channel: str = None):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if channel and channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].append(websocket)
        
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove disconnected WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from all channels
        for channel, connections in self.channel_subscriptions.items():
            if websocket in connections:
                connections.remove(websocket)
        
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def subscribe(self, websocket: WebSocket, channel: str):
        """Subscribe WebSocket to specific channel"""
        if channel in self.channel_subscriptions:
            if websocket not in self.channel_subscriptions[channel]:
                self.channel_subscriptions[channel].append(websocket)
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "channel": channel
                })
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """Broadcast message to specific channel"""
        if channel not in self.channel_subscriptions:
            return
        
        disconnected = []
        
        for connection in self.channel_subscriptions[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to channel {channel}: {e}")
                disconnected.append(connection)
        
        # Clean up
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
```

### 2.2 Real-Time Data Broadcasting

```python
# dashboard/api/background_tasks.py
"""
Background tasks for real-time data collection and broadcasting.
"""

import asyncio
import logging
from datetime import datetime

from .websocket import ConnectionManager

logger = logging.getLogger(__name__)
manager = ConnectionManager()

background_tasks = []

async def pnl_updater():
    """
    Background task to collect P&L updates and broadcast.
    Runs every 5 seconds.
    """
    while True:
        try:
            # TODO: Get actual P&L data from position manager
            pnl_data = {
                "type": "pnl_update",
                "timestamp": datetime.utcnow().isoformat(),
                "equity": 12750.00,
                "unrealized_pnl": 250.00,
                "unrealized_pnl_pct": 2.0,
                "open_positions": 3
            }
            
            await manager.broadcast_to_channel('pnl_updates', pnl_data)
            
        except Exception as e:
            logger.error(f"Error in P&L updater: {e}")
        
        await asyncio.sleep(5)

async def trade_monitor():
    """
    Monitor for new trades and broadcast alerts.
    """
    while True:
        try:
            # TODO: Check for new trades
            # If new trade detected, broadcast
            pass
            
        except Exception as e:
            logger.error(f"Error in trade monitor: {e}")
        
        await asyncio.sleep(1)

async def alert_checker():
    """
    Check for system alerts and broadcast.
    """
    while True:
        try:
            # TODO: Check risk limits, circuit breakers, etc.
            alerts = check_system_alerts()
            
            for alert in alerts:
                await manager.broadcast_to_channel('system_alerts', {
                    "type": "alert",
                    "severity": alert['severity'],
                    "message": alert['message'],
                    "timestamp": datetime.utcnow().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Error in alert checker: {e}")
        
        await asyncio.sleep(10)

def check_system_alerts():
    """Check for system alerts"""
    # TODO: Implement actual alert checking
    return []

async def start_background_tasks():
    """Start all background tasks"""
    global background_tasks
    
    background_tasks = [
        asyncio.create_task(pnl_updater()),
        asyncio.create_task(trade_monitor()),
        asyncio.create_task(alert_checker())
    ]
    
    logger.info("Background tasks started")

async def stop_background_tasks():
    """Stop all background tasks"""
    global background_tasks
    
    for task in background_tasks:
        task.cancel()
    
    background_tasks = []
    logger.info("Background tasks stopped")
```

---

## Phase 3: Dashboard Frontend

### 3.1 Dash Application Structure

**Source:** Dash Documentation (https://dash.plotly.com/)

```python
# dashboard/frontend/app.py
"""
Dash application for trading bot dashboard.

Source: https://dash.plotly.com/layout
"""

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.express as px
import requests
import json

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Trading Bot Dashboard"

# Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Trading Bot Dashboard", className="dashboard-title"),
        html.Div(id="connection-status", children="Disconnected")
    ], className="header"),
    
    # Key Metrics Row
    html.Div([
        html.Div([
            html.H3("Account Balance"),
            html.H2(id="balance-value", children="$12,500.00")
        ], className="metric-card"),
        
        html.Div([
            html.H3("Unrealized P&L"),
            html.H2(id="unrealized-pnl", children="+$250.00", 
                   style={'color': 'green'})
        ], className="metric-card"),
        
        html.Div([
            html.H3("Today's P&L"),
            html.H2(id="daily-pnl", children="+$125.00",
                   style={'color': 'green'})
        ], className="metric-card"),
        
        html.Div([
            html.H3("Open Positions"),
            html.H2(id="open-positions", children="3")
        ], className="metric-card"),
    ], className="metrics-row"),
    
    # Main Content
    html.Div([
        # Left Column - Charts
        html.Div([
            # Equity Curve Chart
            html.Div([
                html.H3("Equity Curve"),
                dcc.Graph(id="equity-chart")
            ], className="chart-container"),
            
            # Drawdown Chart
            html.Div([
                html.H3("Drawdown"),
                dcc.Graph(id="drawdown-chart")
            ], className="chart-container"),
            
        ], className="left-column"),
        
        # Right Column - Tables and Controls
        html.Div([
            # Positions Table
            html.Div([
                html.H3("Open Positions"),
                html.Div(id="positions-table")
            ], className="table-container"),
            
            # Strategy Controls
            html.Div([
                html.H3("Strategy Controls"),
                html.Div(id="strategy-controls")
            ], className="controls-container"),
            
            # Alerts Panel
            html.Div([
                html.H3("Recent Alerts"),
                html.Div(id="alerts-panel")
            ], className="alerts-container"),
            
        ], className="right-column"),
        
    ], className="main-content"),
    
    # Update interval
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # 5 seconds
        n_intervals=0
    ),
    
    # WebSocket connection (using dcc.Store for now)
    dcc.Store(id='websocket-data')
    
], className="dashboard-container")

# Callbacks
@app.callback(
    Output('equity-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_equity_chart(n):
    """Update equity curve chart"""
    # TODO: Fetch from API
    data = {
        'dates': ['2026-01-01', '2026-01-15', '2026-02-01'],
        'equity': [10000, 10500, 11200]
    }
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['dates'],
        y=data['equity'],
        mode='lines',
        name='Equity',
        line=dict(color='blue')
    ))
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

@app.callback(
    Output('positions-table', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_positions_table(n):
    """Update positions table"""
    # TODO: Fetch from API
    positions = [
        {
            'symbol': 'BTC/USDT',
            'side': 'Long',
            'quantity': 0.5,
            'entry': 45000,
            'current': 46000,
            'pnl': 500,
            'pnl_pct': 2.2
        }
    ]
    
    # Create table
    header = html.Tr([
        html.Th("Symbol"),
        html.Th("Side"),
        html.Th("Qty"),
        html.Th("Entry"),
        html.Th("Current"),
        html.Th("P&L"),
        html.Th("Actions")
    ])
    
    rows = []
    for pos in positions:
        pnl_color = 'green' if pos['pnl'] > 0 else 'red'
        rows.append(html.Tr([
            html.Td(pos['symbol']),
            html.Td(pos['side']),
            html.Td(pos['quantity']),
            html.Td(f"${pos['entry']:,.2f}"),
            html.Td(f"${pos['current']:,.2f}"),
            html.Td(f"${pos['pnl']:,.2f} ({pos['pnl_pct']:.1f}%)", 
                   style={'color': pnl_color}),
            html.Td(html.Button("Close", className="close-btn"))
        ]))
    
    return html.Table([header] + rows, className="positions-table")

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
```

---

## Phase 4: Alerting System

### 4.1 Alert Configuration

```python
# dashboard/alerts/alert_manager.py
"""
Alert management and notification system.
"""

from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class Alert:
    alert_id: str
    severity: AlertSeverity
    category: str
    message: str
    timestamp: datetime
    acknowledged: bool = False
    auto_resolve: bool = False

class AlertManager:
    """
    Manages system alerts and notifications.
    """
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.subscribers: List[callable] = []
        
        # Alert thresholds
        self.thresholds = {
            'daily_loss_pct': 0.05,      # 5% daily loss
            'drawdown_pct': 0.20,         # 20% drawdown
            'position_heat_pct': 0.50,    # 50% portfolio heat
            'latency_ms': 1000,           # 1 second latency
        }
    
    def create_alert(
        self,
        severity: AlertSeverity,
        category: str,
        message: str,
        auto_resolve: bool = False
    ) -> Alert:
        """Create new alert"""
        
        alert = Alert(
            alert_id=f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            severity=severity,
            category=category,
            message=message,
            timestamp=datetime.now(),
            auto_resolve=auto_resolve
        )
        
        self.alerts.append(alert)
        
        # Notify subscribers
        self._notify_subscribers(alert)
        
        logger.warning(f"Alert created: {message}")
        
        return alert
    
    def check_risk_alerts(
        self,
        daily_pnl: float,
        account_balance: float,
        drawdown: float,
        portfolio_heat: float
    ):
        """Check for risk-related alerts"""
        
        # Check daily loss
        daily_loss_pct = abs(daily_pnl) / account_balance
        if daily_loss_pct >= self.thresholds['daily_loss_pct']:
            self.create_alert(
                AlertSeverity.CRITICAL,
                "risk",
                f"Daily loss {daily_loss_pct:.1%} exceeded threshold "
                f"{self.thresholds['daily_loss_pct']:.1%}"
            )
        
        # Check drawdown
        if drawdown >= self.thresholds['drawdown_pct']:
            self.create_alert(
                AlertSeverity.CRITICAL,
                "risk",
                f"Drawdown {drawdown:.1%} exceeded threshold "
                f"{self.thresholds['drawdown_pct']:.1%}"
            )
        
        # Check portfolio heat
        if portfolio_heat >= self.thresholds['position_heat_pct']:
            self.create_alert(
                AlertSeverity.WARNING,
                "risk",
                f"Portfolio heat {portfolio_heat:.1%} exceeded threshold "
                f"{self.thresholds['position_heat_pct']:.1%}"
            )
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                break
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active (unacknowledged) alerts"""
        alerts = [a for a in self.alerts if not a.acknowledged]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts
    
    def subscribe(self, callback: callable):
        """Subscribe to alert notifications"""
        self.subscribers.append(callback)
    
    def _notify_subscribers(self, alert: Alert):
        """Notify all subscribers of new alert"""
        for callback in self.subscribers:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Failed to notify subscriber: {e}")
```

---

## Phase 5: Implementation Timeline

### Week 1: Backend API
- Day 1-2: FastAPI setup and structure
- Day 3-4: REST endpoints (positions, trades, strategies)
- Day 5-7: WebSocket implementation

### Week 2: Frontend & Integration
- Day 1-2: Dash frontend layout
- Day 3-4: Charts and data binding
- Day 5: Alert system
- Day 6-7: Testing and refinement

---

## Success Criteria

- [ ] Dashboard loads in < 3 seconds
- [ ] P&L updates every 5 seconds via WebSocket
- [ ] Can view all open positions
- [ ] Can start/stop strategies from UI
- [ ] Alerts display in real-time
- [ ] Mobile-responsive layout
- [ ] Historical charts load properly
- [ ] API latency < 100ms

---

*Monitoring & Dashboard Research Plan Complete*
*Ready for Real-Time Visualization Implementation*
