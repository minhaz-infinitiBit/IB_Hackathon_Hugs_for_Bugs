# Hugs for Bugs - Hackathon Project

This project consists of a FastAPI backend and a frontend (TBD).

## Backend Setup

### 1. Prerequisites
- Python 3.8+ installed
- `pip` installed

### 2. Environment Setup

It is recommended to use a virtual environment.

```bash
# MacOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

navigate to the backend folder and install the requirements:

```bash
cd backend
pip install -r requirements.txt
```

### 4. Running the Application

**Important:** You must be inside the `backend` directory to run the application correctly with the current configuration.

```bash
# Make sure you are in the backend/ folder
cd backend

# Run the server
uvicorn app.main:app --reload
```

The server will start at `http://0.0.0.0:8000`.

## Frontend Setup

*(Coming soon)*