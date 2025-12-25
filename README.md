# NEXTRACION – Nextraction 2

## Overview
NEXTRACION is a web-based Retrieval-Augmented Generation (RAG) pipeline designed to extract insights from public web sources. This project leverages FastAPI for building the API and integrates various services for web scraping, data processing, and embedding generation.

## Features
- **Web Scraping**: Efficiently scrape data from specified web sources while enforcing domain allowlists and managing crawl depth.
- **Data Processing**: Clean, chunk, and index the scraped content for effective retrieval.
- **Retrieval-Augmented Generation**: Answer user queries based on indexed content using advanced embedding techniques.

## Project Structure
```
nextracion-nextraction-2
├── src
│   ├── main.py               # Entry point of the FastAPI application
│   ├── api                   # API related files
│   │   ├── routes.py         # API routes definition
│   │   └── schemas.py        # Pydantic models for request/response validation
│   ├── services              # Core services for RAG pipeline
│   │   ├── rag_pipeline.py    # Logic for RAG pipeline
│   │   ├── web_scraper.py     # Web scraping functions
│   │   └── embeddings.py       # Embedding generation and storage
│   ├── models                # Data models
│   │   └── document.py        # Document structure definition
│   └── utils                 # Utility functions and configuration
│       └── config.py         # Configuration management
├── tests                     # Unit tests
│   ├── test_api.py          # Tests for API endpoints
│   └── test_services.py      # Tests for service functions
├── requirements.txt          # Project dependencies
├── .env.example              # Example environment variables
└── README.md                 # Project documentation
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd nextracion-nextraction-2
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Copy `.env.example` to `.env` and fill in the necessary values.

## Running the Application
To start the FastAPI application, run:
```
uvicorn src.main:app --reload
```

## API Endpoints
- **Ingest Data**: `POST /ingest`
- **Check Status**: `GET /status/{job_id}`
- **Ask a Question**: `POST /ask`
- **Health Check**: `GET /health`

## Example Curl Commands
1. Ingest data:
   ```
   curl -X POST "http://localhost:8000/ingest" -H "Content-Type: application/json" -d '{"url": "http://example.com"}'
   ```

2. Ask a question:
   ```
   curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"question": "What is the insight?"}'
   ```

## License
This project is licensed under the MIT License. See the LICENSE file for more details.