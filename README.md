# LifeFix AI - Your Daily Life Problem Solver

<p align="center">
  <img src="https://img.shields.io/badge/LifeFix-AI-blue?style=for-the-badge&logo=ai&logoColor=white" alt="LifeFix AI">
  <img src="https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js" alt="Next.js">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL">
</p>

## Overview

LifeFix AI is an AI-powered daily life problem-solving assistant. Unlike simple chatbots, it provides structured diagnostic output including:

- **Problem Summary** - Clear description of the issue
- **Problem Risk Level (0-100)** - Quantitative risk assessment
- **Solution Risk Level (0-100)** - Risk assessment for proposed solution
- **Confidence Score (%)** - Reliability indicator
- **Step-by-step solution** - Detailed action plan
- **Required tools** - Materials needed
- **Safety warnings** - Important precautions
- **Decision recommendation** - Call professional or DIY

## Tech Stack

### Frontend

- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **Zustand** (State Management)
- **Framer Motion** (Animations)
- **Radix UI** (UI Components)

### Backend

- **FastAPI** (Python)
- **PostgreSQL** with pgvector
- **SQLAlchemy** (Async)
- **LangChain** + HuggingFace
- **JWT Authentication**

## Project Structure

```
lifeFix-ai/
├── frontend/                 # Next.js frontend
│   ├── app/                 # App router pages
│   │   ├── (auth)/         # Authentication pages
│   │   ├── (chat)/         # Chat pages
│   │   ├── profile/        # Profile page
│   │   └── settings/       # Settings page
│   ├── components/         # React components
│   │   ├── chat/          # Chat components
│   │   ├── layout/        # Layout components
│   │   └── ui/            # UI components
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # Utilities and API client
│   └── context/            # React contexts
│
└── backend/                 # FastAPI backend
    ├── routers/            # API routes
    ├── services/           # Business logic
    ├── models/             # SQLAlchemy models
    ├── schemas/            # Pydantic schemas
    └── database/           # Database configuration
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- PostgreSQL 14+

### Frontend Setup

```
bash
cd frontend
npm install
npm run dev
```

The frontend will run on `http://localhost:3000`

### Backend Setup

```
bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The backend will run on `http://localhost:8000`

### Database Setup

1. Create a PostgreSQL database named `lifefix_ai`
2. Update the `DATABASE_URL` in `backend/.env`

## Environment Variables

### Frontend (.env.local)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (.env)

```
DEBUG=true
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost:5432/lifefix_ai
HUGGINGFACE_API_KEY=your-api-key
```

## Features

### GPT-Style Chat Interface

- Left sidebar with chat history
- Risk indicator dots
- Real-time typing indicator
- Mobile-responsive design

### Structured AI Responses

- Visual RiskMeter component
- ConfidenceBadge display
- SolutionCard with detailed steps
- Tool and warning lists

### Authentication

- JWT-based auth
- Login/Register pages
- Protected routes
- User profile management

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Chat

- `GET /api/chat/` - List user's chats
- `POST /api/chat/` - Create new chat
- `GET /api/chat/{chat_id}` - Get chat details
- `POST /api/chat/{chat_id}/messages` - Send message

### Reports

- `GET /api/reports/` - List reports
- `GET /api/reports/{report_id}` - Get report

## Risk Engine

The Risk Engine analyzes problems and calculates risk levels based on:

- **Keyword matching** - Identifies high-risk terms
- **Category multipliers** - Electrical, plumbing, structural, etc.
- **Urgency indicators** - Emergency vs routine problems

## Confidence Engine

The Confidence Engine calculates reliability scores based on:

- **Risk consistency** - Problem vs solution risk alignment
- **Step quality** - Detailed action plans
- **Tool adequacy** - Proper equipment specification
- **Warning thoroughness** - Safety considerations

## Deployment

### Frontend (Vercel)

1. Connect repository to Vercel
2. Add environment variables
3. Deploy

### Backend (Render)

1. Connect repository to Render
2. Add environment variables
3. Deploy as Python web service

## License

MIT License - See LICENSE file for details

---

Built with ❤️ using Next.js and FastAPI
