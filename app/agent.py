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
- create_chart: Create visualizations (bar, horizontal_bar, line, pie)

**CRITICAL RULES**

1. Always use tools via real function calls. Never write fake markers.
2. Do not stop after planning. If you need data, call the tool in THIS turn.
3. Prefer calling tools with little or no preamble.
4. For unknown databases, explore with list_tables/describe_table first.
5. After getting data, offer visualization when it helps understanding.

**When to create charts:**

Create a chart when:
- User asks to "see", "show", "visualize", "chart", "graph"
- Data has 3+ items suitable for comparison
- Trends over time would benefit from visualization
- Distribution/share would be clearer as pie chart

**Chart type selection:**
- **bar**: Comparing categories
- **horizontal_bar**: When labels are long
- **line**: Time-series data (include current period if partial)
- **pie**: Showing distribution/share (3-6 categories ideal)

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

Current date: 2026-08-17"""


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
        
        for iteration in range(self.max_iterations):
            trace.iterations = iteration + 1
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation,
                tools=self.get_tool_schemas() if self.tools_registry else None,
                tool_choice="auto" if self.tools_registry else None,
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
        
        return trace
    
    def reset_conversation(self, keep_system_prompt: bool = True):
        if keep_system_prompt and self.conversation and self.conversation[0]["role"] == "system":
            self.conversation = [self.conversation[0]]
        else:
            self.conversation = []
