# Graph Coloring Based Smart Exam Timetable Generator

A Flask-based web application that generates a conflict-free university exam timetable using the Greedy Graph Coloring Algorithm.

## Features

- Subject management with add, edit, and delete actions
- Student management with validation
- Enrollment tracking across subjects
- Conflict detection using shared student enrollments
- Graph construction and visualization
- Greedy graph coloring for time-slot assignment
- Timetable generation, printing, and CSV download
- Dashboard with reports and settings
- SQLite database integration with sample data

## Project Structure

```text
Smart_Exam_Timetable/
├── .vercelignore
├── app.py
├── main.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── algorithm/
│   ├── __init__.py
│   ├── graph.py
│   └── coloring.py
├── database/
│   ├── __init__.py
│   ├── db.py
│   └── smart_exam.db
├── public/
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── app.js
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── subjects.html
│   ├── students.html
│   ├── enrollments.html
│   ├── graph.html
│   ├── timetable.html
│   ├── reports.html
│   └── settings.html
└── tests/
    └── test_app.py
```

## Setup

1. Open the project folder in VS Code.
2. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:

   ```bash
   python app.py
   ```

5. Open the browser at http://127.0.0.1:5000

## Notes

- The application stores data in SQLite.
- Sample subjects and students are added automatically on first run.
- Use the dashboard to generate the exam timetable after adding subjects and enrollments.

## Deploying to Vercel

- `pyproject.toml` explicitly points Vercel to the Flask instance in `app.py`.
- Static files are in `public/static/`, served from `/static/` both locally and on Vercel.
- Vercel's function filesystem is not durable. The app copies the bundled SQLite
  database to `/tmp/smart_exam.db` on a cold start and writes there; changes can
  disappear when the function instance is recycled and are not shared across
  instances. Use a managed database for durable, multi-instance production data.
- Set `SMART_EXAM_DB_PATH` to use a different writable SQLite path where the
  runtime provides persistent storage.

Deploy from the project root using Vercel's Python/Flask preset. No custom build
command is required.
