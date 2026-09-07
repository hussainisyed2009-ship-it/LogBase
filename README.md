# 📚 LogBase — Gamified AI-Powered Reading Tracker

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20SQLite-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![AI](https://img.shields.io/badge/AI-OpenRouter%20LLM-purple.svg)](https://openrouter.ai/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Submitted to the Congressional App Challenge**  
> *LogBase is an intelligent, gamified reading platform engineered to foster digital literacy and build sustainable reading habits through behavioral gamification and personalized generative AI.*

---

## 📖 Table of Contents
- [Inspiration & Mission](#-inspiration--mission)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Database Schema](#-database-schema)
- [Getting Started Locally](#-getting-started-locally)
- [Environment Variables](#-environment-variables)
- [Deployment](#-deployment)
- [Future Roadmap](#-future-roadmap)

---

## 🎯 Inspiration & Mission

In an era of endless digital distractions, daily reading habits are declining among students and young adults. Traditional reading logs often feel like passive homework assignments with no immediate engagement or incentive.

**LogBase** transforms reading into an active, rewarding journey. By combining **Duolingo-inspired gamification** (daily streaks, in-app currency, and streak freezes) with **Generative AI book curation**, LogBase empowers readers to take ownership of their reading goals, discover titles tailored to their tastes, and celebrate their milestones.

---

## ✨ Key Features

### 📷 1. Instant ISBN & Barcode Scanner
- Scan physical books in real-time using device cameras powered by `html5-qrcode`.
- Integrates with the **Open Library Books API** to automatically retrieve book titles, authors, genres, and high-resolution cover art without manual typing.

### 🔥 2. Gamified Habit Tracking & Virtual Economy
- **Daily Streaks**: Encourages daily reading habit retention by tracking consecutive active days.
- **Wallet & Coin Rewards**: Readers earn in-app coins for logging sessions and exploring new books.
- **Streak Freezes**: Coins can be redeemed in the store for streak freezes to protect streaks from breaking during busy days.
- **Global Leaderboard**: Compete with other readers based on streak length and total minutes read.

### 🤖 3. Personalized AI Recommendations
- Powered by a multi-model LLM pipeline via OpenRouter.
- Analyzes the reader's **onboarding survey**, **most-read genres**, and **top authors** to generate custom 5-book recommendations.
- Implements resilient multi-model failovers (`openrouter/free`, `Llama 3.3 70B`, `Gemma 2`, `Mistral`) and smart database caching to eliminate redundant API latency.

### 🎯 4. Milestone & Goal Engine
- Readers can set custom, time-sensitive goals (e.g., target minutes, specific reading challenges, or suggested AI recommendations).
- Real-time progress updates automatically mark goals complete upon logging matching reading sessions.

### 📰 5. Automated NYT Best Sellers Integration
- Features a weekly background cron service that automatically syncs and parses the official **New York Times Hardcover Fiction Best Sellers**.

### 🔐 6. Secure Authentication & Verification
- User authentication with hashed passwords (`Werkzeug`).
- Email verification with time-limited cryptographic tokens delivered via transactional email (`Flask-Mailman` / SMTP).

---

## 🏗 System Architecture

```mermaid
graph TD
    User([User / Browser]) <-->|HTTPS / UI| FlaskApp[Flask WSGI Application]
    
    subgraph Frontend
        FlaskApp <--> Templates[Jinja2 HTML5 / Modern CSS UI]
        Templates <--> Scanner[HTML5 QR / Barcode Scanner JS]
    end

    subgraph Backend Core
        FlaskApp <--> Auth[Auth & Verification Module]
        FlaskApp <--> Stats[Analytics & Streak Engine]
        FlaskApp <--> Goals[Goal Matching Service]
    end

    subgraph External APIs & Services
        FlaskApp <-->|Book & Cover Metadata| OpenLib[Open Library REST API]
        FlaskApp <-->|Personalized Curation| OpenRouter[OpenRouter LLM Engine]
        FlaskApp <-->|Weekly Best Sellers Sync| NYT[NY Times Books API]
        FlaskApp <-->|Verification Emails| SMTP[Gmail / AWS SES SMTP]
    end

    subgraph Data Persistence
        FlaskApp <--> DB[(PostgreSQL / SQLite Database)]
    end



🛠 Tech Stack
Layer	Technologies
Backend	Python 3, Flask, SQLAlchemy, Gunicorn, Werkzeug
Frontend	HTML5, CSS3 (Modern Responsive UI), Vanilla JavaScript, html5-qrcode
Database	PostgreSQL (Production) / SQLite (Local Development)
AI / Machine Learning	OpenRouter API (Auto-Router, Gemma, LLaMA 3.3, Mistral)
External APIs	Open Library API, NY Times Books API
DevOps & Cloud	AWS Elastic Beanstalk (Amazon Linux 2023), AWS RDS, AWS Route 53, ACM
🗄 Database Schema
The relational database is structured with SQLAlchemy:

User: Account credentials, email verification status, current streaks, last active date, streak freezes count, and activity timestamps.
Log_reading: Reading records containing user ID, book title, author, genre, minutes read, and timestamps.
goals: Active and completed goals tied to users with target parameters and deadlines.
currency_logs: Ledger tracking all coin rewards and streak freeze transactions.
background_info: Survey metadata (age group, favorite genres, reading background).
Recommend: Cached AI recommendations mapped to users to optimize LLM query costs.
ny_times_best_sellers: Periodic snapshots of the top best-selling books.
🚀 Getting Started Locally
Prerequisites
Python 3.10+
Git
Virtual Environment tool (venv)
Installation & Setup
Clone the repository:

bash


git clone https://github.com/your-username/LogBase.git
cd LogBase
Create and activate a virtual environment:

bash


# macOS / Linux
python3 -m venv venv
source venv/bin/activate
# Windows
python -m venv venv
venv\Scripts\activate
Install project dependencies:

bash


pip install -r requirements.txt
Configure Environment Variables: Create a .env.production file in the root directory (see 
Environment Variables
 below).

Initialize the Database:

bash


python -m website.init_db
Run the Development Server:

bash


python -m website.main
Open your browser and navigate to: http://localhost:8000 (or http://127.0.0.1:8000).

🔑 Environment Variables
Create a file named .env.production in the project root:

ini


# Flask Security
SECRET_KEY=your_super_secret_session_key
FLASK_DEBUG=True
# OpenRouter AI API Key
OPENROUTER_API_KEY=your_openrouter_api_key_here
# Email Verification (SMTP)
MAIL_PASSWORD=your_gmail_app_password_or_smtp_key
# Database Connection (Optional: defaults to SQLite if omitted)
# DATABASE_URL=postgresql://username:password@localhost:5432/logbase_db
☁️ Deployment
LogBase is optimized for deployment on AWS Elastic Beanstalk:

Platform: Python 3.11+ running on Amazon Linux 2023.
WSGI Entrypoint: 
app.py
 (WSGIPath: app:app).
Database: Managed AWS RDS PostgreSQL or external managed Postgres via DATABASE_URL.
Automated Cron Hooks: Includes 
.platform/cron/nytimes_bestsellers.cron
 to automate weekly bestseller updates.
🗺 Future Roadmap
 Classroom / Teacher Portals: Enable educators to create reading challenges for classrooms and monitor student literacy metrics.
 Social Reading Clubs: Community forums and shared reading lists with peer accountability.
 Native Mobile Application: Dedicated iOS/Android wrappers for push reminders and offline reading tracking.
👤 Author & Acknowledgments
Developer: Syed Taha Hussaini
Competition: Congressional App Challenge
API Credits: Open Library API, OpenRouter, The New York Times Developer Network.
12:59 PM




