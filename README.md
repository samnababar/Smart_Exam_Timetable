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
├── app.py
├── requirements.txt
├── README.md
├── algorithm/
│   ├── __init__.py
│   ├── graph.py
│   └── coloring.py
├── database/
│   ├── __init__.py
│   └── db.py
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── templates/
│   ├── base.html
│   ├── dashboard.html
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
