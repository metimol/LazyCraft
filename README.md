# Keigen — AI-Powered Kleinanzeigen Telegram Bot & Monitor

<div align="center">

![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Aiogram Version](https://img.shields.io/badge/Aiogram-3.26%2B-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![LangChain & GenAI](https://img.shields.io/badge/AI-Google%20GenAI%20%2F%20LangChain-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Docker Supported](https://img.shields.io/badge/Docker-Compose%20Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Persistent%20Storage-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

*An intelligent, highly customizable Telegram bot for searching and monitoring **Kleinanzeigen** (Germany's largest classifieds platform) with AI-powered query optimization, semantic filtering, and real-time alerts.*

</div>

---

## 📖 Overview

Searching for deals on **Kleinanzeigen** often involves manually trying dozens of keyword variations, sifting through duplicate or irrelevant listings, and competing against other buyers.

**Keigen** solves this by integrating directly with Kleinanzeigen's mobile API and supercharging searches with **AI (Google GenAI / LangChain)**:
- **AI Query Expansion**: Automatically transforms a single prompt into distinct, highly optimized keyword variations and German synonyms to surface hidden listings.
- **AI Semantic Filtering**: Evaluates raw results against your actual buying intent, presenting only the best matches.
- **Automated Monitoring (Parsers)**: Runs background scheduled tasks at custom intervals and instantly notifies you on Telegram when new listings match your criteria.

---

## ✨ Key Features

- 🤖 **AI-Powered Fast Search**
  - Generates optimized search query variations using **Google GenAI** to discover items sellers listed under non-standard names.
  - Filters and ranks search results to match user intent accurately.
- ⏰ **Smart Scheduled Parsers**
  - Create recurring background monitoring jobs with configurable polling frequencies.
  - Optional custom AI prompt filtering for each parser to eliminate false positives automatically.
- 🛡️ **TLS Fingerprint Resistance**
  - Built with `curl-cffi` to mimic native Android app traffic and interact smoothly with Kleinanzeigen's endpoints.
- 📍 **Precise Geolocation & Distance Filtering**
  - Filter listings by German Postal Code (`PLZ`) and exact radius in kilometers.
- 💶 **Fine-Grained Category & Price Limits**
  - Navigate full Kleinanzeigen category trees and set minimum / maximum price boundaries.
- 🌐 **Multi-Language Support (i18n)**
  - Seamlessly switch between **English (`en`)**, **German (`de`)**, **Russian (`ru`)**, **Ukrainian (`ukr`)**, and **Turkish (`tur`)**.
- 🐳 **Production-Ready Docker Setup**
  - Fully containerized with `docker-compose.yml`, including a Redis service for state and scheduler persistence.

---

## 🏗️ Architecture & Tech Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Bot Framework** | [Aiogram 3.x](https://docs.aiogram.dev/) | Asynchronous Telegram bot framework with FSM & middleware support |
| **AI / LLM Engine** | [LangChain](https://python.langchain.com/) & Google GenAI | Powers query generation, semantic item filtering, and conversational assistance |
| **Kleinanzeigen API Client** | Asynchronous Python Client + `curl-cffi` | High-performance API wrapper interacting with mobile endpoints |
| **Background Scheduler** | [APScheduler 3.x](https://apscheduler.readthedocs.io/) | Manages concurrent monitoring jobs (`parsers`) across users |
| **State & Data Store** | [Redis](https://redis.io/) | Stores user settings, FSM states, active parsers, and rate limits |

---

## 📋 Prerequisites

Before setting up Keigen, ensure you have:
1. **Python 3.11+** (for local execution) or **Docker & Docker Compose** (recommended).
2. **Telegram Bot Token** — Obtain one from [@BotFather](https://t.me/BotFather).
3. **Google API Key** — Obtain a Gemini / Google GenAI API key from [Google AI Studio](https://aistudio.google.com/).
4. **Kleinanzeigen Mobile App Credentials** (`APP_USER`, `APP_PASSWORD`, `APP_VERSION`) — Mobile API credentials required to communicate with Kleinanzeigen API endpoints.

---

## 🚀 Getting Started

### Method 1: Using Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Keigen.git
   cd Keigen
   ```

2. **Configure environment variables:**
   Copy the example environment configuration:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your preferred editor and fill in your tokens and credentials (see the API Credentials section below for current defaults):
   ```ini
   # Telegram Bot Settings
   BOT_TOKEN=123456789:ABCdefGHIjklmNOPQrsTUVwxyz
   ADMIN_ID=123456789

   # AI Settings
   GOOGLE_API_KEY=AIzaSy...

   # Kleinanzeigen Mobile API Credentials
   APP_USER=android
   APP_PASSWORD=TaR60pEttY
   APP_VERSION=2026.23.1
   ```

3. **Start the containers:**
   ```bash
   docker compose up -d --build
   ```
   Check logs to verify the bot and Redis service started successfully:
   ```bash
   docker compose logs -f keigen-bot
   ```

---

### Method 2: Local Python Installation

1. **Clone the repository and enter the directory:**
   ```bash
   git clone https://github.com/yourusername/Keigen.git
   cd Keigen
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # On Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate

   # On Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install Python dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Ensure Redis is running locally:**
   ```bash
   # Example using Docker to run Redis locally on default port 6379
   docker run -d -p 6379:6379 --name keigen-redis redis:alpine
   ```

5. **Configure `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env and set REDIS_HOST=localhost and REDIS_PORT=6379
   ```

6. **Run the bot:**
   ```bash
   python bot.py
   ```

---

## ⚙️ Environment Variables Reference

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `BOT_TOKEN` | **Yes** | None | Your Telegram Bot API token from `@BotFather` |
| `GOOGLE_API_KEY` | **Yes** | None | API key for Google GenAI / Gemini models |
| `ADMIN_ID` | Optional | None | Telegram User ID of the bot administrator |
| `APP_USER` | **Yes** | `android` | Kleinanzeigen API mobile username |
| `APP_PASSWORD` | **Yes** | `TaR60pEttY` | Kleinanzeigen API mobile password |
| `APP_VERSION` | **Yes** | `2026.23.1` | Target Kleinanzeigen application version |
| `REDIS_HOST` | Optional | `localhost` | Hostname or IP address of the Redis server |
| `REDIS_PORT` | Optional | `6379` | Port of the Redis server |

---

### 🔐 API Credentials & Rotation (Important)

The `APP_USER`, `APP_PASSWORD`, and `APP_VERSION` values are app-distribution credentials baked directly into the official Kleinanzeigen Android client. They are *not* personal secrets, but rather the default basic-auth credentials the app uses to communicate with the backend.

Currently, the working defaults are:

```ini
APP_USER=android
APP_PASSWORD=TaR60pEttY
APP_VERSION=2026.23.1
```

#### What to do if the API stops working
Kleinanzeigen periodically rotates these credentials to combat unauthorized scraping. If the bot suddenly starts throwing `401 Unauthorized` or `403 Forbidden` errors, it means the keys have been rotated.

**Do not wait for a repository update.** You can fix this yourself immediately:
1. Decompile the latest version of the official Kleinanzeigen Android APK.
2. Extract the new basic-auth username, password, and version string.
3. Supply the fresh values in your `.env` file.

The application is designed to resolve credentials in this order: **`.env` variables → bundled defaults**. Supplying new keys in your `.env` file will override the source code automatically without requiring you to edit the Python packages manually.

---

## 💡 Usage Examples & Bot Workflow

### 1. Initial Setup (`/start`)
When you start a chat with the bot (`/start`), you will be greeted with the main interactive menu:
- **Language Selection**: Choose your preferred interface language (`EN`, `DE`, `RU`, `UKR`, `TR`).
- **Location Settings**: Configure your postal code (`PLZ`) and default search radius (e.g., `10 km`, `25 km`, `50 km`).

### 2. AI Fast Search
1. Tap **🔍 Fast Search** on the main keyboard.
2. Select a category or search across all categories.
3. Enter your search prompt in plain text (e.g., *"Looking for a used Fender Stratocaster electric guitar in good condition under 600€"*).
4. Keigen uses AI to generate multiple German keyword variations (`Fender Stratocaster`, `E-Gitarre Fender`, `Strat Gitarre`), queries Kleinanzeigen asynchronously, filters out noise, and delivers clean item cards with direct links and prices.

### 3. Creating a Scheduled Parser (Automated Monitor)
1. Tap **⏱ Manage Parsers** → **Add Parser**.
2. Name your monitor (e.g., `Sony A7IV Deals`).
3. Select the target category, price range, and polling frequency (e.g., every 15 minutes, 30 minutes, or 1 hour).
4. *(Optional)* Add an AI prompt to filter listings automatically before notification (e.g., *"Only alert me if the listing includes the original box and battery charger"*).
5. The bot will automatically check for new listings and message you as soon as matching items are posted.

---

## 📁 Project Structure

```text
Keigen/
├── ai/                      # AI integration layer (LangChain + Google GenAI)
│   ├── config.py            # AI model & agent configuration
│   ├── fast_search_ai.py    # Query optimization & semantic item filtering
│   └── process_text.py      # Conversational assistant handler
├── const/                   # Constants, environment loading & localization
│   ├── __init__.py          # Env variables & locale loader
│   └── locales/             # i18n JSON files (en, de, ru, tur, ukr)
├── database/                # Redis storage & management
│   ├── client.py            # Redis connection management
│   ├── limits.py            # Rate limits for Fast Search & Parsers
│   ├── parsers.py           # CRUD operations for scheduled parsers
│   └── users.py             # User preferences (location, radius, favorites)
├── handlers/                # Telegram bot message & callback handlers
│   ├── fast_search_handler.py # Interactive AI search workflow
│   ├── help_handler.py      # Help menu & documentation commands
│   ├── parser_handler.py    # Parser creation, editing & scheduling UI
│   └── settings_handler.py  # User preferences & language switcher
├── kleinanzeigen_api/       # Async Python client for Kleinanzeigen API
│   ├── categories.py        # Category catalog & tree navigation
│   └── client.py            # API request engine with TLS fingerprinting bypass
├── utils/                   # Keyboards, middlewares, formatting & schedulers
│   ├── keyboards.py         # Inline and reply keyboard builders
│   ├── middlewares.py       # Admin, Locale & prompt cleanup middlewares
│   └── scheduler_jobs.py    # APScheduler job execution & alert dispatching
├── bot.py                   # Main bot entrypoint & initialization
├── docker-compose.yml       # Docker Compose setup (Bot + Redis)
├── Dockerfile               # Docker container definition
└── requirements.txt         # Project dependencies
```

---

## 🛠️ Development & Code Quality

Keigen uses modern Python code quality tools including **Ruff** for linting and formatting.

To run linter checks locally:
```bash
# Install development/pre-commit dependencies
pip install pre-commit ruff

# Run ruff linter across the project
ruff check .

# Run pre-commit hooks
pre-commit run --all-files
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

## ⚠️ Disclaimer

This project is intended for educational and personal use. Users are responsible for adhering to the terms of service of any third-party platforms accessed via this software.
