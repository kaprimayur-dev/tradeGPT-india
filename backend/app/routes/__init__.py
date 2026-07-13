# TradeGPT FastAPI routes package
from app.routes.health import router as health_router
from app.routes.analyze import router as analyze_router
from app.routes.research import router as research_router
from app.routes.backtest import router as backtest_router
from app.routes.market_data import router as market_data_router
