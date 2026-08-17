"""
Data Analyst Agent with multi-step reasoning.
Combines SQL, schema exploration, and visualization.
"""
import json
import time
from datetime import datetime
from typing import Callable, Optional
from dataclasses import dataclass, field
from openai import OpenAI
import structlog

from app.config import Config

logger = structlog.get_logger()

_VISUAL_HINTS = (
    "graph", "chart", "plot", "visuali", "show me",
)
_PLAN_NUDGE = (
    "Do not describe a plan. Call a tool now. "
    "If the schema is unknown, call list_tables immediately."
)
_CHART_NUDGE = (
    "The user asked for a graph. Call create_chart now. "
    "For increase/decrease or % change, use chart_type='change' with percent "
    "values (12.5 means +12.5%, -8.2 means -8.2%) and is_currency=false."
)


def _wants_visualization(query: str) -> bool:
    q = query.lower()
    return any(hint in q for hint in _VISUAL_HINTS)


@dataclass
class ToolCall:
    """Single tool execution record."""
    tool_name: str
    arguments: dict
    result: any
    duration_ms: float
    iteration: int
    timestamp: str


@dataclass
class ReasoningTrace:
    """Complete reasoning trace for one query."""
    user_query: str
    started_at: str
    completed_at: str = ""
    total_duration_ms: float = 0
    tool_calls: list = field(default_factory=list)
    iterations: int = 0
    final_response: str = ""
    total_tokens: int = 0
    
    def summary(self) -> dict:
        return {
            "query": self.user_query,
            "duration_ms": self.total_duration_ms,
            "iterations": self.iterations,
            "tool_count": len(self.tool_calls),
            "tools_used": [tc.tool_name for tc in self.tool_calls],
            "charts_generated": [
                tc.result.get("url") for tc in self.tool_calls
                if tc.tool_name == "create_chart" 
                and isinstance(tc.result, dict) 
                and tc.result.get("success")
            ],
        }


SYSTEM_PROMPT = """You are a senior data analyst working with a PostgreSQL database.

**SAFETY: You have READ-ONLY access. Only SELECT queries allowed.**

**Available tools:**
- list_tables: See what tables exist
- describe_table: Get column details
- get_relationships: Understand foreign keys
- safe_run_sql: Execute SELECT queries
- create_chart: Create visualizations (bar, horizontal_bar, line, pie, change)

**CRITICAL RULES**

1. Always use tools via real function calls. Never write fake markers.
2. Never stop after planning. If you need data, call the tool in THIS turn.
3. Prefer calling tools with little or no preamble. Do not narrate next steps.
4. For unknown databases, call list_tables in the first turn.
5. After getting data, create a chart when the user asked for a graph or it helps.

**When to create charts:**

Create a chart when:
- User asks to "see", "show", "visualize", "chart", "graph", "plot"
- Data has 3+ items suitable for comparison
- Trends over time would benefit from visualization
- Distribution/share would be clearer as pie chart
- User asks for increase, decrease, reduction, growth, or % change

**Chart type selection:**
- **bar**: Comparing categories
- **horizontal_bar**: When labels are long
- **line**: Time-series of actual values (sales, revenue)
- **pie**: Showing distribution/share (3-6 categories ideal)
- **change**: +/- percent increase or decrease (green up, red down)

**Percentage change graphs:**

When the user wants +/-, % reduction, increase, or decrease in sales:
1. Aggregate sales by month from orders (completed orders, total_amount)
2. Compute percent change vs the previous period with LAG, e.g.
   (this_period - prev_period) / NULLIF(prev_period, 0) * 100
3. Call create_chart with chart_type="change", is_currency=false
   Values are percent numbers: 12.5 means +12.5%, -8.2 means -8.2%
4. Then write short business insights

**Workflow for chart queries:**

Step 1: Query the data with safe_run_sql
Step 2: Transform SQL results into chart data format:
        [{"label": "X", "value": 100}, {"label": "Y", "value": 200}]
Step 3: Call create_chart with appropriate type
Step 4: Write business insights based on the data

**Formatting (final answer only):**
- Currency: Indian Rupees (₹) with format ₹1,00,000 or ₹1L or ₹1Cr
- Business language, not technical
- Highlight key insights
- Reference charts when created

Current date: 2026-08-18"""


class DataAnalystAgent:
    """
    Data Analyst Agent with full reasoning trace capture.
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_iterations: Optional[int] = None,
    ):
        self.model = model or Config.LLM_MODEL
        self.max_iterations = max_iterations or Config.MAX_ITERATIONS
        
        api_key = Config.get_api_key()
        if not api_key:
            raise ValueError("API key not configured. Set OPENROUTER_API_KEY or OPENAI_API_KEY")
        
        self.client = OpenAI(
            base_url=Config.LLM_BASE_URL,
            api_key=api_key,
            timeout=Config.LLM_TIMEOUT,
        )
        
        self.tools_registry: dict[str, dict] = {}
        self.conversation: list[dict] = []
        
        prompt = system_prompt or SYSTEM_PROMPT
        self.conversation.append({"role": "system", "content": prompt})
    
    def register_tool(self, schema: dict, function: Callable):
        tool_name = schema["function"]["name"]
        self.tools_registry[tool_name] = {"schema": schema, "function": function}
    
    def get_tool_schemas(self) -> list[dict]:
        return [tool["schema"] for tool in self.tools_registry.values()]
    
    def get_tool_names(self) -> list[str]:
        return list(self.tools_registry.keys())
    
    def execute_tool(self, tool_name: str, arguments: dict):
        if tool_name not in self.tools_registry:
            return {"error": f"Unknown tool: {tool_name}"}
        
        function = self.tools_registry[tool_name]["function"]
        try:
            return function(**arguments)
        except Exception as e:
            return {"error": f"{type(e).__name__}: {str(e)}"}
    
    def run(self, user_message: str) -> ReasoningTrace:
        """Run the agent and return complete reasoning trace."""
        trace = ReasoningTrace(
            user_query=user_message,
            started_at=datetime.now().isoformat(),
        )
        
        start_time = time.time()
        self.conversation.append({"role": "user", "content": user_message})
        wants_chart = _wants_visualization(user_message)
        planning_nudges = 0
        chart_nudges = 0
        
        for iteration in range(self.max_iterations):
            trace.iterations = iteration + 1
            
            force_tools = bool(self.tools_registry) and not trace.tool_calls
            tool_choice = None
            if self.tools_registry:
                tool_choice = "required" if force_tools else "auto"
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation,
                    tools=self.get_tool_schemas() if self.tools_registry else None,
                    tool_choice=tool_choice,
                    max_tokens=2000,
                )
            except Exception:
                if tool_choice != "required":
                    raise
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation,
                    tools=self.get_tool_schemas(),
                    tool_choice="auto",
                    max_tokens=2000,
                )
            
            message = response.choices[0].message
            
            if response.usage:
                trace.total_tokens += response.usage.total_tokens
            
            assistant_msg = {"role": "assistant", "content": message.content}
            
            if message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in message.tool_calls
                ]
            
            self.conversation.append(assistant_msg)
            
            if not message.tool_calls:
                has_chart = any(tc.tool_name == "create_chart" for tc in trace.tool_calls)
                remaining = iteration < self.max_iterations - 1
                
                if not trace.tool_calls and planning_nudges < 1 and remaining:
                    planning_nudges += 1
                    self.conversation.append({"role": "user", "content": _PLAN_NUDGE})
                    continue
                
                if wants_chart and not has_chart and chart_nudges < 1 and remaining:
                    chart_nudges += 1
                    self.conversation.append({"role": "user", "content": _CHART_NUDGE})
                    continue
                
                trace.final_response = message.content or ""
                break
            
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_start = time.time()
                
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}
                
                result = self.execute_tool(tool_name, arguments)
                tool_duration_ms = (time.time() - tool_start) * 1000
                
                trace.tool_calls.append(ToolCall(
                    tool_name=tool_name,
                    arguments=arguments,
                    result=result,
                    duration_ms=tool_duration_ms,
                    iteration=iteration + 1,
                    timestamp=datetime.now().isoformat(),
                ))
                
                self.conversation.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str),
                })
        
        trace.completed_at = datetime.now().isoformat()
        trace.total_duration_ms = (time.time() - start_time) * 1000
        
        if not trace.final_response:
            trace.final_response = (
                "I started the analysis but ran out of steps before finishing. "
                "Please ask the question again."
            )
        
        return trace
    
    def reset_conversation(self, keep_system_prompt: bool = True):
        if keep_system_prompt and self.conversation and self.conversation[0]["role"] == "system":
            self.conversation = [self.conversation[0]]
        else:
            self.conversation = []
