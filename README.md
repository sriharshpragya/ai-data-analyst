# 🤖 AI Data Analyst (Agent + UI + REST APIs)

<div align="center">

**The autonomous AI agent for your database. Ask questions in plain English — get SQL, charts, and business insights instantly.**

[Python](https://www.python.org/)
[FastAPI](https://fastapi.tiangolo.com/)
[PostgreSQL](https://www.postgresql.org/)
[Docker](https://www.docker.com/)
[License: MIT](https://opensource.org/licenses/MIT)

[Features](#-features) • [Quick Start](#-quick-start) • [Demo](#-demo) • [Architecture](#-architecture) • [Deployment](#-deployment)



---



## 🎯 What It Does

An **autonomous AI agent** that turns natural language questions into SQL queries, executes them safely, generates visualizations, and delivers business insights.

**Ask questions like:**

- 💬 "How many premium customers do we have?"
- 📊 "Show me top 5 products by revenue as a bar chart"
- 📈 "What's our monthly revenue trend over the last 6 months?"
- 🎯 "Compare this month's sales to last month"

**The agent autonomously:**

1. 🧠 Understands your question
2. 🔍 Explores your database schema
3. ⚡ Writes safe SQL queries
4. 📊 Generates visualizations
5. 💡 Delivers business insights

---



## 📸 Demo



### Split-View Interface

Main UI
*Chat interface with real-time chart generation*

### Multiple Charts

Multiple Charts
*Charts stack as you ask more questions*

### Complex Analysis

Complex Query
*Multi-step reasoning with tool trace*

### API Documentation

API Docs
*Full API documentation with try-it-out feature*

---



## ✨ Features



### 🤖 Autonomous Agent

- **Multi-step reasoning** — Breaks complex questions into steps
- **Schema discovery** — Works with ANY PostgreSQL database
- **Tool composition** — Chains SQL, exploration, and visualization
- **Reasoning traces** — See exactly how the agent thinks



### 🛡️ Production-Grade Safety

- **Read-only enforcement** — Cannot modify data
- **Multi-layer validation** — 7 defense layers
- **SQL injection prevention** — Blocks all attack patterns
- **Query cost estimation** — Rejects expensive queries via EXPLAIN
- **Timeout enforcement** — 10-second max per query
- **Automatic row limits** — Prevents memory issues
- **Zero known vulnerabilities** — Tested against 20+ attack scenarios



### 📊 Beautiful Visualizations

- **4 chart types** — Bar, horizontal bar, line, pie
- **Indian currency formatting** — ₹1L, ₹1.5Cr notation
- **Business color palette** — Professional, print-friendly
- **Automatic value labels** — Data points self-documenting
- **Smart label rotation** — Handles long text gracefully



### 🎨 Modern Web Interface

- **Split-view design** — Chat left, charts right
- **Real-time updates** — Streaming responses
- **Beautiful UI** — Modern, professional design
- **Mobile responsive** — Works on all devices
- **Example queries** — One-click to try



### 🚀 Multiple Interfaces

- **Web UI** — Beautiful chat interface
- **REST API** — Full FastAPI with docs
- **CLI** — Rich terminal experience
- **Docker** — One-command deployment

---



## 🚀 Quick Start



### Prerequisites

- Docker & Docker Compose
- OpenAI or OpenRouter API key



### Setup (3 Steps)

**1. Clone the repository**

```bash
git clone https://github.com/sriharshpragya/ai-data-analyst.git
cd ai-data-analyst
```

**2. Configure environment**

```bash
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

**3. Launch everything**

```bash
docker-compose up
```

That's it! Open [http://localhost:8000](http://localhost:8000) in your browser.

### What Just Happened?

Docker Compose started:

- 🐘 **PostgreSQL** — Database with sample e-commerce data
- 🌱 **Seeder** — Populated 30 customers, 20 products, 100 orders
- 🤖 **App** — AI agent + web UI at :8000
- 🔍 **Adminer** — Database GUI at :8080

Everything auto-configured, no manual setup needed.

---



## 💻 Usage



### Web UI

Open [http://localhost:8000](http://localhost:8000) and start chatting.

### CLI

```bash
# Interactive chat
docker-compose exec app python -m app.main chat

# Single query
docker-compose exec app python -m app.main query "How many customers?"

# System info
docker-compose exec app python -m app.main info
```



### REST API

```bash
# Health check
curl http://localhost:8000/health

# Ask a question
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me top 5 products by revenue"}'

# View interactive docs
open http://localhost:8000/docs
```

---

## 🏗️ Architecture

<div align="center">
  <img src="docs/architecture.svg" alt="System Architecture" width="800"/>
</div>

The system consists of four main layers:

1. **User Interface** — Web UI, CLI, or REST API
2. **FastAPI Application** — Coordinates request handling
3. **Data Analyst Agent** — LLM-powered reasoning with tool composition
4. **PostgreSQL Database** — Read-only access via safety layer

### Safety Architecture

<div align="center">
  <img src="docs/safety-flow.svg" alt="Safety Defense Layers" width="600"/>
</div>

Every query passes through 7 defense layers before execution. Any failure blocks the query with a clear explanation to the user. All configuration via environment variables (`.env` file):

---

### LLM Configuration

```env
OPENROUTER_API_KEY=your-key-here
LLM_MODEL=openai/gpt-4o-mini
```



### Database Configuration

```env
POSTGRES_USER=analyst
POSTGRES_PASSWORD=analyst_password
POSTGRES_DB=ecommerce
```



### Safety Configuration

```env
QUERY_TIMEOUT_SECONDS=10
MAX_QUERY_COST=10000
MAX_ROWS_PER_QUERY=1000
DEFAULT_ROWS_PER_QUERY=100
```



### Application Configuration

```env
APP_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development
```

See `.env.example` for full reference.

---



## 🎨 Example Queries



### Simple Analytics

- "How many customers do we have?"
- "What's our total revenue this year?"
- "Show me all product categories"



### With Visualizations

- "Show top 5 products by revenue as a bar chart"
- "Monthly revenue trend for last 6 months as line chart"
- "Sales distribution by category as pie chart"
- "Top 10 customers by spending as horizontal bar chart"



### Business Insights

- "Which customer segment brings the most revenue?"
- "Compare this month's sales to last month"
- "What are our best selling products in the last 30 days?"
- "Which cities generate the most orders?"



### Complex Multi-Step

- "Find our top-performing category, then show me the top 5 customers who buy from it most"
- "Analyze order statuses and show the distribution"
- "Which products have the highest profit margins?"

See [docs/examples.md](docs/examples.md) for 50+ examples.

---



## 🚀 Deployment



### Local Development

```bash
docker-compose up
```



### Production Deployment

The app is designed for zero-code-change deployment.

**Any Docker platform:**

- AWS ECS / Fargate
- Google Cloud Run
- Azure Container Instances
- Railway / Render / Fly.io
- DigitalOcean App Platform
- Kubernetes

**Steps:**

1. Set environment variables (including production database URL)
2. Deploy the Docker image
3. Point at your production PostgreSQL

**Production configuration:**

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@prod-host:5432/db
LOG_LEVEL=WARNING
```

See [docs/deployment.md](docs/deployment.md) for platform-specific guides.

---



## 🛠️ Development



### Run Locally (without Docker)

**Prerequisites:**

- Python 3.11+
- PostgreSQL 16
- Poetry or pip

**Setup:**

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database (assumes local PostgreSQL running)
psql -U postgres -f database/init.sql
python database/sample_data.py

# Configure
cp .env.example .env
# Edit .env with local settings

# Run
python -m app.main serve
```



### Project Structure

ai-data-analyst/
├── app/ # Application code
│ ├── config.py # Configuration
│ ├── agent.py # AI agent
│ ├── api.py # FastAPI endpoints
│ ├── main.py # CLI
│ ├── static/ # Web UI
│ └── tools/ # Agent tools
│ ├── sql_tools.py # Safe SQL execution
│ ├── schema_tools.py # Schema exploration
│ ├── chart_tools.py # Visualization
│ └── safety/ # Safety layers
├── database/ # DB init + seeder
├── docs/ # Documentation
├── charts/ # Generated charts
├── docker-compose.yml # Full stack
├── Dockerfile # App image
└── requirements.txt # Python deps

---



## 🧪 Testing

Manual testing:

```bash
# Test the API
docker-compose exec app python -c "
from app.agent import DataAnalystAgent
from app.tools import register_all_tools

agent = DataAnalystAgent()
register_all_tools(agent)
trace = agent.run('How many customers?')
print(trace.final_response)
"
```

Try attack scenarios (should all be blocked):

- "Delete all customers"
- "Drop the products table"
- "Show me pg_shadow"

---



## 📊 Performance

- **Simple query:** 1-2 seconds (1 tool call)
- **Complex query:** 2-4 seconds (2-3 tool calls)
- **With chart:** 2-3 seconds (query + chart generation)
- **Safety overhead:** ~30ms per query

**Optimizations:**

- Connection pooling
- Query caching (roadmap)
- Schema caching (roadmap)

---



## 🔐 Security

**By Design:**

- ✅ Read-only database access
- ✅ SQL injection prevention
- ✅ System table access blocked
- ✅ Multi-statement queries blocked
- ✅ Query cost limits
- ✅ Execution timeouts
- ✅ Non-root container user
- ✅ No hardcoded credentials

**Production Recommendations:**

- Use a dedicated READ-ONLY database user
- Deploy behind a reverse proxy (nginx/Cloudflare)
- Enable HTTPS with valid certificates
- Add authentication layer (API keys, OAuth)
- Enable row-level security in PostgreSQL
- Set up audit logging

---



## 💡 Use Cases



### Small Business Analytics

Give non-technical staff instant access to business insights.

### Freelance Development

White-label deploy for clients.

### SaaS Analytics

Embed as feature in your product.

### Internal Tools

Replace expensive BI tools with a chat interface.

### Data Exploration

Help data analysts explore unfamiliar databases quickly.

---



## 🗺️ Roadmap



### v1.1 (Coming Soon)

- [ ] Query history and saved queries
- [ ] User authentication
- [ ] Multiple database support
- [ ] Export to Excel/PDF
- [ ] Dashboard mode



### v2.0 (Future)

- [ ] Real-time streaming responses
- [ ] Multi-user support
- [ ] Team workspaces
- [ ] Custom LLM support (Ollama, Anthropic)
- [ ] Query performance analytics



### v3.0 (Vision)

- [ ] Predictive analytics
- [ ] Automated insights
- [ ] Anomaly detection
- [ ] Report scheduling

---



## 🤝 Contributing

Contributions welcome! Areas of interest:

- 🐛 Bug fixes
- ✨ New chart types (scatter, heatmap)
- 🌐 Multi-language support
- 📊 Additional database backends (MySQL, BigQuery)
- 🎨 UI/UX improvements
- 📖 Documentation

Please open an issue first to discuss significant changes.

---



## 📜 License

MIT License — See [LICENSE](LICENSE) for details.

---



## 👤 Author

**Pragya Sriharsh** — Senior Engineering Lead

Building AI agents that solve real business problems.

- **GitHub:** [@sriharshpragya](https://github.com/sriharshpragya)
- **Related project:** [ai-cli-chatbot](https://github.com/sriharshpragya/ai-cli-chatbot) — Personal AI Assistant with 14 tools

*Built with ❤️ during my Agentic AI learning journey.*

---


## 🙏 Acknowledgments

Built on the shoulders of:

- [OpenAI](https://openai.com/) / [OpenRouter](https://openrouter.ai/) — LLM providers
- [FastAPI](https://fastapi.tiangolo.com/) — Web framework
- [PostgreSQL](https://www.postgresql.org/) — Database
- [matplotlib](https://matplotlib.org/) — Visualizations
- [Docker](https://www.docker.com/) — Containerization

---



**⭐ Star this repo if you find it useful!**

*Because your database has stories to tell.*

