# HireMind AI 🎙️🤖

> AI-Powered Real-Time Interview Platform for Technical, Behavioral, and Resume-Based Mock Interviews

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)
![AI Powered](https://img.shields.io/badge/AI-Gemini-orange)

---

## 🚀 Overview

HireMind AI is an intelligent interview preparation platform that conducts realistic AI-powered interviews based on a candidate's resume.

The platform uses voice interaction, resume analysis, webcam integration, and AI-generated follow-up questions to simulate a real interview experience.

Unlike traditional mock interview tools, HireMind AI dynamically adapts questions according to the candidate's profile, skills, projects, and responses.

---

## ✨ Features

### 📄 Resume Analysis

- PDF Resume Upload
- Resume Parsing using PyMuPDF
- Skills Extraction
- Project Extraction
- Education Detection
- Experience Detection

---

### 🎤 Real-Time Voice Interview

- Speech-to-Text
- Continuous Listening
- Real-Time Transcript
- AI Voice Responses
- Natural Conversation Flow

---

### 🤖 AI Interviewer

- Technical Interview Questions
- Behavioral Questions
- Project-Based Discussions
- Dynamic Follow-Up Questions
- Context-Aware Conversation

---

### 📷 Webcam Integration

- Live Webcam Feed
- Candidate Monitoring
- Future Eye Contact Analysis
- Future Attention Tracking

---

### 📊 Interview Dashboard

- Question Feed
- Live Transcript
- Voice Status
- Interview Progress
- Session Tracking

---

### 📈 AI Evaluation Engine (In Progress)

- Technical Score
- Communication Score
- Confidence Score
- Project Discussion Score
- Personalized Feedback

---

## 🏗️ System Architecture

```text
                     Candidate
                          │
                          ▼

                  Next.js Frontend
                          │
         ┌────────────────┼────────────────┐
         │                │                │

         ▼                ▼                ▼

     Webcam          Voice Input      Resume Upload

         │                │                │

         ▼                ▼                ▼

     Media APIs     Speech-To-Text    Resume Parser

                          │
                          ▼

                   FastAPI Backend

                          │

         ┌────────────────┼────────────────┐
         │                │                │

         ▼                ▼                ▼

      Gemini AI        PostgreSQL       Qdrant

         │
         ▼

   Dynamic Interview Engine

         │
         ▼

      AI Feedback
```

---

## 🛠️ Tech Stack

### Frontend

- Next.js 15
- TypeScript
- Tailwind CSS
- Zustand
- Framer Motion
- React Webcam
- React Speech Recognition

### Backend

- FastAPI
- Python
- SQLAlchemy
- Pydantic

### AI & ML

- Gemini AI
- Sentence Transformers
- RAG Pipeline

### Database

- PostgreSQL
- Qdrant Vector Database

### Resume Processing

- PyMuPDF

### Deployment

- Docker
- Vercel
- Render / Railway

---

## 📂 Project Structure

```bash
HireMind-AI/

├── frontend/
│
├── src/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── services/
│   ├── store/
│   └── types/
│
├── backend/
│
├── app/
│   ├── routes/
│   ├── services/
│   ├── models/
│   ├── rag/
│   ├── prompts/
│   └── utils/
│
├── docs/
│
└── docker/
```

---

## ⚡ Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/hiremind-ai.git

cd hiremind-ai
```

---

### Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```bash
http://localhost:3000
```

---

### Backend Setup

```bash
cd backend

python -m venv venv

venv\Scripts\activate
```

Install Dependencies

```bash
pip install -r requirements.txt
```

Run Server

```bash
uvicorn app.main:app --reload
```

Backend:

```bash
http://localhost:8000
```

---

## 🔐 Environment Variables

Create `.env`

```env
GEMINI_API_KEY=your_api_key

DATABASE_URL=postgresql://user:password@localhost/hiremind

QDRANT_URL=http://localhost:6333

QDRANT_API_KEY=your_key
```

---

## 🎯 Future Roadmap

### Phase 1

- [x] Resume Upload
- [x] Resume Parsing
- [x] Voice Input
- [x] Voice Output
- [x] Webcam Feed
- [x] Interview Dashboard

### Phase 2

- [ ] Resume RAG
- [ ] Qdrant Integration
- [ ] Dynamic Resume-Based Questions

### Phase 3

- [ ] AI Evaluation Engine
- [ ] Feedback Reports
- [ ] Interview Analytics

### Phase 4

- [ ] Coding Interview Round
- [ ] Monaco Editor
- [ ] Judge0 Integration

### Phase 5

- [ ] Multi-Agent Interviewers
- [ ] HR Agent
- [ ] Technical Agent
- [ ] System Design Agent

### Phase 6

- [ ] AI Avatar Interviewer
- [ ] Emotion Analysis
- [ ] Eye Contact Tracking

---

## 💡 Use Cases

- Placement Preparation
- Software Engineering Interviews
- Technical Assessments
- Behavioral Interview Practice
- Resume-Based Mock Interviews
- AI-Powered Candidate Screening

---

## 📸 Screenshots

### Landing Page

_Add screenshot here_

### Interview Dashboard

_Add screenshot here_

### Resume Upload

_Add screenshot here_

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome.

Feel free to fork the repository and submit a pull request.

---

## 📧 Contact

**Prince**

LinkedIn: _Add Your LinkedIn_

GitHub: _Add Your GitHub_

Email: _Add Your Email_

---

## ⭐ Support

If you found this project useful, consider giving it a star ⭐ on GitHub.

It helps the project reach more developers and recruiters.

---

### Built with ❤️ using Next.js, FastAPI, Gemini AI, and modern AI engineering practices.
