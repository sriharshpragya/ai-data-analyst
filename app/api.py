"""
FastAPI REST API for AI Data Analyst.
"""
import time
from datetime import datetime
from typing import Optional
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import structlog

from app.config import Config
from app.agent import DataAnalystAgent
from app.tools import register_all_tools, get_all_tools

# Setup structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()


# ============================================
# LIFESPAN
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info(
        "app_starting",
        model=Config.LLM_MODEL,
        database=Config.DATABASE_URL.split("@")[1] if "@" in Config.DATABASE_URL else "configured",
        environment=Config.ENVIRONMENT,
    )
    
    # Validate config
    errors = Config.validate()
    if errors:
        logger.error("config_validation_failed", errors=errors)
        raise RuntimeError(f"Configuration errors: {errors}")
    
    logger.info("app_ready")
    yield
    logger.info("app_shutting_down")


# ============================================
# APP INITIALIZATION
# ============================================

app = FastAPI(
    title="AI Data Analyst API",
    description="Natural language SQL agent with visualization. Talk to your database in plain English.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not Config.is_production() else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# STATIC FILES (Charts + Web UI)
# ============================================

# Serve generated charts
Config.CHARTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/charts", StaticFiles(directory=str(Config.CHARTS_DIR)), name="charts")

# Serve web UI static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class ChatRequest(BaseModel):
    """User's chat message."""
    message: str = Field(..., min_length=1, max_length=2000, description="Natural language question")
    reset_context: bool = Field(False, description="Reset conversation history")


class ToolCallInfo(BaseModel):
    """Information about a single tool call."""
    tool_name: str
    duration_ms: float
    iteration: int
    success: bool


class ChatResponse(BaseModel):
    """Response from the agent."""
    response: str
    iterations: int
    duration_ms: float
    tools_used: list[str]
    charts_generated: list[str] = []
    tool_calls: list[ToolCallInfo] = []
    warnings: list[str] = []


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str
    environment: str
    model: str
    tools_available: list[str]


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    message: str
    details: Optional[dict] = None


# ============================================
# AGENT INSTANCE (Global)
# ============================================
# In production, consider per-session agents

_agent: Optional[DataAnalystAgent] = None


def get_agent() -> DataAnalystAgent:
    """Get or create the agent instance."""
    global _agent
    if _agent is None:
        _agent = DataAnalystAgent()
        register_all_tools(_agent)
        logger.info("agent_initialized", tools=_agent.get_tool_names())
    return _agent


# ============================================
# ROUTES
# ============================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(), status_code=200)
    else:
        return HTMLResponse(content="""
        <html>
            <head><title>AI Data Analyst</title></head>
            <body>
                <h1>🤖 AI Data Analyst API</h1>
                <p>API is running!</p>
                <ul>
                    <li><a href="/docs">API Documentation</a></li>
                    <li><a href="/health">Health Check</a></li>
                </ul>
                <p>Web UI not yet built. Visit /docs for the API.</p>
            </body>
        </html>
        """)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    agent = get_agent()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        environment=Config.ENVIRONMENT,
        model=Config.LLM_MODEL,
        tools_available=agent.get_tool_names(),
    )


@app.get("/api/schema")
async def get_schema():
    """Get database schema information."""
    from app.tools.schema_tools import list_tables
    result = list_tables()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result)
    return result


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    Send a natural language question, get analysis + charts.
    """
    logger.info("chat_request", message=request.message[:100])
    
    agent = get_agent()
    
    if request.reset_context:
        agent.reset_conversation()
    
    try:
        trace = agent.run(request.message)
        
        # Extract tool call info
        tool_calls_info = [
            ToolCallInfo(
                tool_name=tc.tool_name,
                duration_ms=tc.duration_ms,
                iteration=tc.iteration,
                success=isinstance(tc.result, dict) and "error" not in tc.result,
            )
            for tc in trace.tool_calls
        ]
        
        # Extract chart URLs
        chart_urls = [
            tc.result.get("url", "")
            for tc in trace.tool_calls
            if tc.tool_name == "create_chart"
            and isinstance(tc.result, dict)
            and tc.result.get("success")
        ]
        
        # Extract warnings from SQL tool calls
        warnings = []
        for tc in trace.tool_calls:
            if tc.tool_name == "safe_run_sql" and isinstance(tc.result, dict):
                warnings.extend(tc.result.get("warnings", []))
        
        response = ChatResponse(
            response=trace.final_response,
            iterations=trace.iterations,
            duration_ms=trace.total_duration_ms,
            tools_used=list(set(tc.tool_name for tc in trace.tool_calls)),
            charts_generated=chart_urls,
            tool_calls=tool_calls_info,
            warnings=warnings,
        )
        
        logger.info(
            "chat_completed",
            iterations=trace.iterations,
            tools=len(trace.tool_calls),
            charts=len(chart_urls),
        )
        
        return response
    
    except Exception as e:
        logger.error("chat_error", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "agent_error",
                "message": str(e),
                "type": type(e).__name__,
            },
        )


@app.post("/api/reset")
async def reset_conversation():
    """Reset the conversation context."""
    agent = get_agent()
    agent.reset_conversation()
    return {"status": "reset", "message": "Conversation reset"}


@app.get("/api/examples")
async def get_examples():
    """Get example queries users can try."""
    return {
        "examples": [
            {
                "category": "Simple Analytics",
                "queries": [
                    "How many customers do we have?",
                    "What's our total revenue?",
                    "Show me all product categories",
                ],
            },
            {
                "category": "Charts",
                "queries": [
                    "Show me top 5 products by revenue as a bar chart",
                    "Monthly revenue trend for last 6 months as a line chart",
                    "Sales distribution by category as a pie chart",
                    "Graph monthly sales % increase or decrease",
                ],
            },
            {
                "category": "Business Insights",
                "queries": [
                    "Which customer segment brings the most revenue?",
                    "Compare this month's sales to last month",
                    "What are our best selling products in the last 30 days?",
                ],
            },
        ]
    }


# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if not Config.is_production() else None,
        },
    )


# ============================================
# RUN DIRECTLY
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api:app",
        host=Config.APP_HOST,
        port=Config.APP_PORT,
        reload=not Config.is_production(),
        log_level=Config.LOG_LEVEL.lower(),
    )
