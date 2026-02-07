# E-commerce Product Review Analyzer 🔍

AI-powered web application that scrapes and analyzes product reviews from Amazon and Flipkart, providing deep insights through sentiment analysis, aspect extraction, topic modeling, and fake review detection.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

- 🔗 **URL Scraping** - Paste any Amazon or Flipkart product URL
- 🎭 **Sentiment Analysis** - AI-powered positive/negative/neutral classification
- 📊 **Aspect-Based Insights** - Analyze quality, price, delivery, battery, design, and more
- 🏷️ **Topic Discovery** - Automatic theme clustering using LDA
- 🚨 **Fake Review Detection** - Flag suspicious reviews with confidence scores
- 📈 **Product Comparison** - Compare 2-3 products side-by-side
- 📄 **Export Reports** - Download PDF and CSV reports
- 🌙 **Modern UI** - Dark mode, glassmorphism, responsive design

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance async API framework
- **SQLAlchemy** - ORM for PostgreSQL
- **Celery + Redis** - Background task processing
- **HuggingFace Transformers** - Pre-trained sentiment models
- **Gensim** - Topic modeling (LDA)
- **BeautifulSoup + Selenium** - Web scraping

### Frontend
- **React 18** - Component-based UI
- **Vite** - Fast build tool
- **TailwindCSS** - Utility-first styling
- **Recharts** - Interactive charts
- **Lucide React** - Beautiful icons

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/e-commerce-review-analyzer.git
cd e-commerce-review-analyzer

# Start all services
docker-compose up -d

# Wait for services to be ready (first run downloads ML models)
# Backend: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

### Manual Setup

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Download NLP models
python -m spacy download en_core_web_sm

# Copy environment file
copy .env.example .env
# Edit .env with your PostgreSQL and Redis URLs

# Run the server
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📁 Project Structure

```
e-commerce-review-analysis/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Settings management
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/              # Database models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API endpoints
│   │   └── services/
│   │       ├── scraper/         # Amazon, Flipkart scrapers
│   │       ├── analysis/        # ML/NLP services
│   │       └── export/          # PDF/CSV generators
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/               # React pages
│   │   ├── components/          # Reusable components
│   │   └── services/            # API client
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scrape` | Start scraping a product URL |
| GET | `/api/scrape/{job_id}/status` | Check scraping progress |
| GET | `/api/products` | List all analyzed products |
| GET | `/api/products/{id}` | Get product details |
| GET | `/api/products/{id}/reviews` | Get paginated reviews |
| GET | `/api/products/{id}/sentiment` | Sentiment analysis |
| GET | `/api/products/{id}/aspects` | Aspect-based sentiment |
| GET | `/api/products/{id}/topics` | Topic modeling |
| GET | `/api/products/{id}/insights` | Key insights summary |
| POST | `/api/compare` | Compare multiple products |
| GET | `/api/products/{id}/export/pdf` | Download PDF report |
| GET | `/api/products/{id}/export/csv` | Download CSV data |

Full API documentation available at `/docs` (Swagger UI).

## 📊 ML Models Used

- **Sentiment**: `distilbert-base-uncased-finetuned-sst-2-english`
- **Aspect Extraction**: Keyword-based + spaCy NLP
- **Topic Modeling**: Gensim LDA
- **Fake Detection**: Custom scoring algorithm

## ⚠️ Disclaimer

This project is for **educational purposes only**. Web scraping may violate the Terms of Service of e-commerce platforms. Use responsibly and consider using official APIs for production applications.

## 📝 Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/reviewdb

# Redis
REDIS_URL=redis://localhost:6379/0

# API
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# ML Models
SENTIMENT_MODEL=distilbert-base-uncased-finetuned-sst-2-english
MODEL_CACHE_DIR=./models_cache

# Scraping
SCRAPE_DELAY_MIN=2
SCRAPE_DELAY_MAX=4
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built with ❤️ using FastAPI, React, and AI
