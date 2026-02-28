# Flipkart Product Review Analyzer 🔍

AI-powered web application that scrapes and analyzes product reviews from **Flipkart**, providing deep insights through sentiment analysis, aspect extraction, topic modeling, and fake review detection.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

- 🔗 **URL Scraping** – Paste any Flipkart product URL
- 🎭 **Sentiment Analysis** – AI-powered positive/negative/neutral classification
- 📊 **Aspect-Based Insights** – Analyze quality, price, delivery, battery, design, and more
- 🏷️ **Topic Discovery** – Automatic theme clustering using LDA
- 🚨 **Fake Review Detection** – ML classifier (TF-IDF + Logistic Regression, 97.5% accuracy) + heuristic scoring
- 📈 **Product Comparison** – Compare 2 products side-by-side
- 📄 **Export Reports** – Download PDF and CSV reports
- 🤖 **AI Summaries** – Groq-powered structured insights (pros, cons, recommendation)
- 🔒 **API Rate Limiting** – slowapi-based request throttling
- 🧪 **Tested** – 71 backend tests (pytest) + 16 frontend tests (Vitest)
- 🌙 **Modern UI** – Dark mode, glassmorphism, responsive design

## 🛠️ Tech Stack

### Backend
- **FastAPI** – High-performance async API framework
- **SQLAlchemy** – ORM with SQLite (configurable to PostgreSQL)
- **Playwright** – Headless browser for Flipkart scraping
- **BeautifulSoup** – HTML parsing
- **HuggingFace Transformers** – Pre-trained sentiment models
- **Gensim** – Topic modeling (LDA with auto-tuned alpha/eta)
- **scikit-learn** – Fake review classifier (TF-IDF + LogisticRegression)
- **slowapi** – API rate limiting (60 req/min default, 5/min for scraping)
- **Groq AI** – LLM-powered structured insights (llama-3.3-70b-versatile)

### Frontend
- **React 18** – Component-based UI
- **Vite** – Fast build tool
- **TailwindCSS** – Utility-first styling
- **Recharts** – Interactive charts
- **Framer Motion** – Smooth animations
- **Lucide React** – Beautiful icons
- **Vitest** – Frontend unit testing

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/flipkart-review-analyzer.git
cd flipkart-review-analyzer

# Start all services
docker-compose up -d

# Wait for services to be ready (first run downloads ML models + Chromium)
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

# Install Playwright browser
python -m playwright install chromium

# Copy environment file
copy .env.example .env
# Edit .env with your settings (Groq API key, etc.)

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
flipkart-review-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Settings management
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/              # Database models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API endpoints
│   │   └── services/
│   │       ├── scraper/         # Flipkart Playwright scraper
│   │       ├── analysis/        # ML/NLP services
│   │       ├── ai/              # Groq AI integration
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
├── .env.example
└── README.md
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scrape` | Start scraping a Flipkart product URL |
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
| POST | `/api/demo` | Create a demo product for testing |

Full API documentation available at `/docs` (Swagger UI).

## 📊 ML Models Used

- **Sentiment**: `distilbert-base-uncased-finetuned-sst-2-english`
- **Aspect Extraction**: Keyword-based NLP
- **Topic Modeling**: Gensim LDA
- **Fake Detection**: TF-IDF + Logistic Regression (97.5% accuracy, trained on labeled dataset) + heuristic ensemble (70% ML / 30% heuristic)
- **AI Insights**: Groq (llama-3.3-70b-versatile)

## 🔧 How Scraping Works

Flipkart blocks all direct HTTP requests with reCAPTCHA. This project uses **Playwright** (headless Chromium) with a specific navigation flow:

1. Visit `flipkart.com` to establish a browser session
2. Search for the product using the search bar
3. Click the product link (opens in a new tab with full content)
4. Navigate to the reviews page
5. Paginate through review pages to collect data

This approach reliably bypasses anti-bot protections while respecting rate limits.

## 📝 Environment Variables

```env
# Database (defaults to SQLite)
DATABASE_URL=sqlite:///./reviews.db

# API
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Groq AI (get key from https://console.groq.com)
GROQ_API_KEY=your_groq_api_key_here

# ML Models
SENTIMENT_MODEL=distilbert-base-uncased-finetuned-sst-2-english
MODEL_CACHE_DIR=./models_cache

# Scraping
SCRAPE_DELAY_MIN=2
SCRAPE_DELAY_MAX=4
```

## ⚠️ Disclaimer

This project is for **educational purposes only**. Web scraping may violate the Terms of Service of e-commerce platforms. Use responsibly and consider using official APIs for production applications.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built with ❤️ using FastAPI, React, Playwright, and AI
