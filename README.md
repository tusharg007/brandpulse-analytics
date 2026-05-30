# 🚀 BrandPulse — D2C Brand Analytics Platform

A full-stack web application that ingests e-commerce sales data, processes it through an ETL pipeline, stores it in a database, exposes it via a REST API, and displays it on an interactive React dashboard.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ARCHITECTURE                                │
│                                                                     │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │   React      │────▶│   Flask      │────▶│  PostgreSQL  │        │
│  │   Frontend   │     │   REST API   │     │  Database    │        │
│  │   :3000      │     │   :5000      │     │  :5432       │        │
│  └──────────────┘     └──────┬───────┘     └──────────────┘        │
│                              │                                      │
│                              ▼                                      │
│                       ┌──────────────┐                              │
│                       │    Redis     │                              │
│                       │    Cache     │                              │
│                       │    :6379     │                              │
│                       └──────────────┘                              │
│                                                                     │
│  ┌──────────────┐     ┌──────────────┐                              │
│  │  CSV / Blob  │────▶│  ETL Pipeline│────▶ PostgreSQL              │
│  │  Storage     │     │  (Pandas)    │                              │
│  └──────────────┘     └──────────────┘                              │
│                                                                     │
│           All services orchestrated via Docker Compose               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Tech Stack

| Layer           | Technology                            |
|-----------------|---------------------------------------|
| Frontend        | React 18, Recharts, Tailwind CSS 3    |
| Backend API     | Python 3.11, Flask 3, SQLAlchemy      |
| Database        | PostgreSQL 15                         |
| Cache           | Redis 7                               |
| ETL Pipeline    | Python, Pandas                        |
| Containerization| Docker, Docker Compose                |
| Testing         | pytest, Flask test client             |
| CI/CD           | GitHub Actions                        |
| Cloud-ready     | Azure Blob Storage SDK (commented)    |

---

## 🏗️ Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Git

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/your-username/brandpulse.git
cd brandpulse

# 2. (Optional) Copy and configure environment
cp .env.example .env

# 3. Build and start all services
docker-compose up --build
```

**That's it!** 🎉 The app will:
1. Start PostgreSQL and Redis
2. Run Alembic migrations to create tables
3. Seed the database with 10 brands and 2,000 sales records
4. Start the Flask API on **http://localhost:5000**
5. Build and serve the React dashboard on **http://localhost:3000**

---

## 📡 API Documentation

| Endpoint | Method | Description | Sample Response |
|----------|--------|-------------|-----------------|
| `/api/health` | GET | Health check (DB + Redis) | `{"status": "healthy", "database": "ok", "redis": "ok"}` |
| `/api/brands` | GET | List brands (paginated) | `{"brands": [...], "total": 10, "page": 1}` |
| `/api/brands/<id>` | GET | Brand detail with revenue | `{"id": 1, "name": "...", "total_revenue": 50000}` |
| `/api/brands` | POST | Create a new brand | `{"id": 11, "name": "NewBrand", ...}` |
| `/api/sales` | GET | Filtered sales records | `{"sales": [...], "total": 2000}` |
| `/api/analytics/summary` | GET | KPI summary (cached) | `{"total_revenue": 1500000, "top_brand": "..."}` |
| `/api/analytics/trends` | GET | Revenue trends over time | `[{"period": "2024-01", "revenue": 50000}]` |
| `/api/analytics/top-brands` | GET | Top N brands by revenue | `[{"name": "...", "total_revenue": 200000}]` |
| `/api/analytics/platform-split` | GET | Revenue by platform | `[{"platform": "Amazon", "revenue": 500000}]` |
| `/api/analytics/export` | GET | Download CSV of sales data | CSV file download |
| `/api/etl/trigger` | POST | Run ETL pipeline | `{"message": "ETL complete", "records_processed": 50}` |
| `/api/etl/logs` | GET | ETL run history | `[{"status": "success", "records_processed": 50}]` |

### Query Parameters

- **`/api/brands`**: `page`, `per_page`
- **`/api/sales`**: `brand_id`, `start_date`, `end_date`, `platform`, `page`, `per_page`
- **`/api/analytics/trends`**: `brand_id`, `period` (monthly/weekly)
- **`/api/analytics/top-brands`**: `limit`

---

## ⚙️ Running the ETL Pipeline Manually

```bash
# From inside the running backend container
docker-compose exec backend python -c "
from app import create_app
from app.services.etl_service import run_etl_pipeline
app = create_app()
with app.app_context():
    result = run_etl_pipeline()
    print(result)
"
```

Or trigger via the API:
```bash
curl -X POST http://localhost:5000/api/etl/trigger
```

Or use the **"Run ETL Pipeline"** button on the Dashboard UI.

---

## ☁️ Production Cloud Deployment

### Azure Blob Storage Integration

The ETL pipeline is designed with Azure Blob Storage in mind. In `backend/app/services/etl_service.py`, the Extract step includes a comment block showing how to replace local CSV reading with Azure Blob Storage SDK:

```python
from azure.storage.blob import BlobServiceClient

blob_service = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service.get_container_client('sales-data')
for blob in container_client.list_blobs(name_starts_with='raw/'):
    stream = blob_client.download_blob()
    df = pd.read_csv(io.BytesIO(stream.readall()))
```

### Azure Data Factory Mapping

| BrandPulse ETL Step | Azure Data Factory Equivalent |
|---------------------|-------------------------------|
| Extract (CSV read)  | ADF Copy Activity from Blob Storage |
| Transform (Pandas)  | ADF Data Flow / Databricks notebook |
| Load (DB upsert)    | ADF Sink to Azure SQL / PostgreSQL |
| Log (ETLLog)        | ADF Pipeline monitoring + Log Analytics |

### Deployment Architecture

- **Frontend**: Azure Static Web Apps or Azure CDN
- **Backend**: Azure App Service or AKS (Kubernetes)
- **Database**: Azure Database for PostgreSQL
- **Cache**: Azure Cache for Redis
- **ETL**: Azure Data Factory with scheduled triggers

---

## 🧪 Running Tests

```bash
# Inside the backend directory
cd backend
pip install -r requirements.txt
pytest tests/ -v

# Or via Docker
docker-compose exec backend python -m pytest tests/ -v
```

---

## 📁 Project Structure

```
brandpulse/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── .github/workflows/test.yml
│
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   ├── run.py
│   ├── seed.py
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/001_initial.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── extensions.py
│   │   ├── models.py
│   │   ├── routes/
│   │   │   ├── analytics.py
│   │   │   ├── brands.py
│   │   │   ├── etl.py
│   │   │   ├── health.py
│   │   │   └── sales.py
│   │   └── services/
│   │       ├── cache_service.py
│   │       └── etl_service.py
│   ├── data/raw/
│   └── tests/
│       ├── conftest.py
│       ├── test_analytics.py
│       ├── test_brands.py
│       └── test_etl.py
│
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── index.css
        ├── App.jsx
        ├── services/api.js
        ├── components/
        │   ├── BrandCard.jsx
        │   ├── ETLPanel.jsx
        │   ├── FilterBar.jsx
        │   ├── KPICard.jsx
        │   ├── LoadingSpinner.jsx
        │   ├── Navbar.jsx
        │   ├── PlatformPieChart.jsx
        │   ├── SalesChart.jsx
        │   └── TopBrandsChart.jsx
        └── pages/
            ├── Brands.jsx
            └── Dashboard.jsx
```

---

## 🔮 Future Improvements

- **Apache Airflow** for scheduled ETL pipeline orchestration
- **Azure deployment** with Terraform IaC scripts
- **User authentication** (JWT / OAuth2) with role-based access
- **Real-time updates** via WebSockets for live dashboard refresh
- **Advanced analytics**: cohort analysis, predictive revenue forecasting
- **Monitoring**: Prometheus + Grafana dashboards for API health metrics
- **Mobile-responsive** progressive web app (PWA)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
