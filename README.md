# Vibe Mapping Agent

A conversational shopping assistant that translates vibe-based clothing queries into structured attributes and provides personalized product recommendations.

## Project Overview

This project implements a conversational agent that:

1. Takes in vibe-based shopper queries (e.g., "something cute for brunch")
2. Asks 1-2 targeted follow-up questions to clarify preferences
3. Maps vague terms to structured attributes
4. Recommends products from a catalog with justification

## Architecture

### Frontend
- Next.js application with a chat interface
- Built with shadcn UI components
- Simple, clean design focused on the conversation

### Backend
- FastAPI server with a single chat endpoint
- LangGraph for conversation flow management
- Gemini integration for natural language understanding

## Setup Instructions

### Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

### Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python run.py
```

## Project Structure

```
vibe-mapping-agent/
├── frontend/                  # Next.js app
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   └── styles/           # CSS styles
├── backend/                  # FastAPI app
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── routes.py        # API routes
│   │   └── services/        # Business logic
│   └── requirements.txt     # Python dependencies
```

## Features

- Natural language conversation with follow-up questions
- Vibe-to-attribute mapping
- Product recommendations based on user preferences
- Justification for recommendations# Force redeploy from working commit
