import csv
import io
import json
import math
from datetime import datetime, timedelta

from flask import Flask, flash, redirect, render_template, request, send_file, url_for

from algorithm.coloring import greedy_graph_coloring
from algorithm.graph import build_conflict_graph, get_conflict_pairs
from database.db import (
    add_enrollment,
    add_student,
    add_subject,
    delete_enrollment,
    delete_student,
    delete_subject,
    ensure_default_settings,
    fetch_conflicts,
    fetch_enrollments,
    fetch_students,
    fetch_subjects,
    get_connection,
    get_settings,
    init_db,
    seed_sample_data,
    set_setting,
    update_student,
    update_subject,
)

app = Flask(__name__, static_folder="public/static", static_url_path="/static")
app.secret_key = "smart-exam-timetable-generator-secret-key"


def get_slot_names():
    settings = get_settings()
    slot_count = int(settings.get("slot_count", "6"))
    slot_prefix = settings.get("slot_prefix", "Exam Slot")
    start_time = settings.get("slot_start_time", "09:00")
    duration_minutes = int(settings.get("slot_duration_minutes", "120"))

    try:
        start_dt = datetime.strptime(start_time, "%H:%M")
    except ValueError:
        start_dt = datetime.strptime("09:00", "%H:%M")

    slots = []
    for index in range(slot_count):
        slot_start = start_dt + timedelta(minutes=index * duration_minutes)
        slot_end = slot_start + timedelta(minutes=duration_minutes)
        slots.append({
            "index": index,
            "name": f"{slot_prefix} {index + 1}",
            "time": f"{slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}",
        })
    return slots


def build_subject_lookup():
    return {subject["id"]: subject for subject in fetch_subjects()}


def build_conflict_map(subjects):
    subject_ids = [subject["id"] for subject in subjects]
    enrollments = []
    conn = get_connection()
    rows = conn.execute("SELECT student_id, subject_id FROM enrollments").fetchall()
    conn.close()
    for row in rows:
        enrollments.append({"student_id": row["student_id"], "subject_id": row["subject_id"]})
    adjacency = build_conflict_graph(subjects, enrollments)
    ordered = sorted(subject_ids, key=lambda subject_id: (-len(adjacency.get(subject_id, [])), subject_id))
    return adjacency, ordered


def get_subject_assignment(subjects):
    adjacency, ordered = build_conflict_map(subjects)
    coloring = greedy_graph_coloring(adjacency, ordered)
    return coloring


def generate_timetable_data():
    subjects = fetch_subjects()
    if not subjects:
        return []
    assignment = get_subject_assignment(subjects)
    slots = get_slot_names()
    timetable_by_slot = {}
    for subject in subjects:
        subject_slot = assignment.get(subject["id"], 0)
        timetable_by_slot.setdefault(subject_slot, []).append(subject)

    final_data = []
    for slot_index, slot in enumerate(slots):
        if slot_index not in timetable_by_slot:
            continue
        for subject in sorted(timetable_by_slot.get(slot_index, []), key=lambda item: item["code"]):
            final_data.append({
                "subject_id": subject["id"],
                "subject_code": subject["code"],
                "subject_name": subject["name"],
                "department": subject["department"],
                "slot_index": slot_index,
                "slot_name": slot["name"],
                "slot_time": slot["time"],
            })
    return final_data


def save_generated_timetable():
    conn = get_connection()
    conn.execute("DELETE FROM generated_timetable")
    schedule = generate_timetable_data()
    for item in schedule:
        conn.execute(
            "INSERT INTO generated_timetable (subject_id, slot_index, slot_name) VALUES (?, ?, ?)",
            (item["subject_id"], item["slot_index"], item["slot_name"]),
        )
    conn.commit()
    conn.close()


def get_generated_timetable():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT gt.subject_id, gt.slot_index, gt.slot_name,
               s.code AS subject_code, s.name AS subject_name, s.department, s.semester
        FROM generated_timetable gt
        JOIN subjects s ON s.id = gt.subject_id
        ORDER BY gt.slot_index, s.code
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def build_graph_svg(subjects):
    adjacency, ordered = build_conflict_map(subjects)
    assignment = greedy_graph_coloring(adjacency, ordered)
    center_x, center_y = 360, 260
    radius = 180
    nodes = []
    for index, subject in enumerate(subjects):
        angle = (2 * math.pi * index) / max(len(subjects), 1)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        nodes.append({
            "id": subject["id"],
            "label": subject["code"],
            "name": subject["name"],
            "color": assignment[subject["id"]],
            "x": round(x, 2),
            "y": round(y, 2),
        })

    node_map = {node["id"]: node for node in nodes}
    edges = []
    for subject in subjects:
        for neighbor in sorted(adjacency.get(subject["id"], [])):
            if subject["id"] < neighbor:
                edges.append({
                    "source": subject["id"],
                    "target": neighbor,
                    "source_x": node_map[subject["id"]]["x"],
                    "source_y": node_map[subject["id"]]["y"],
                    "target_x": node_map[neighbor]["x"],
                    "target_y": node_map[neighbor]["y"],
                })

    return {"nodes": nodes, "edges": edges, "assignments": assignment}


@app.route("/")
def dashboard():
    subjects = fetch_subjects()
    students = fetch_students()
    enrollments = fetch_enrollments()
    settings = get_settings()
    conflict_pairs = get_conflict_pairs(subjects, [{"student_id": item["student_id"], "subject_id": item["subject_id"]} for item in enrollments])
    timetable = get_generated_timetable()
    used_slots = len({item["slot_index"] for item in timetable}) if timetable else 0
    return render_template(
        "index.html",
        subjects=subjects,
        students=students,
        enrollments=enrollments,
        settings=settings,
        conflict_count=len(conflict_pairs),
        timetable=timetable,
        used_slots=used_slots,
    )


@app.route("/subjects", methods=["GET", "POST"])
def subjects_page():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            code = request.form.get("code", "").strip()
            name = request.form.get("name", "").strip()
            department = request.form.get("department", "").strip()
            semester = request.form.get("semester", "").strip()
            if not code or not name or not department or not semester:
                flash("Please complete all subject fields.", "error")
            else:
                add_subject(code, name, department, semester)
                flash("Subject added successfully.", "success")
        elif action == "edit":
            subject_id = request.form.get("subject_id")
            code = request.form.get("code", "").strip()
            name = request.form.get("name", "").strip()
            department = request.form.get("department", "").strip()
            semester = request.form.get("semester", "").strip()
            if not subject_id or not code or not name or not department or not semester:
                flash("Invalid subject update data.", "error")
            else:
                update_subject(subject_id, code, name, department, semester)
                flash("Subject updated successfully.", "success")
        elif action == "delete":
            subject_id = request.form.get("subject_id")
            if subject_id:
                delete_subject(subject_id)
                flash("Subject deleted successfully.", "success")
        return redirect(url_for("subjects_page"))

    subjects = fetch_subjects()
    return render_template("subjects.html", subjects=subjects)


@app.route("/students", methods=["GET", "POST"])
def students_page():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            student_code = request.form.get("student_code", "").strip()
            name = request.form.get("name", "").strip()
            program = request.form.get("program", "").strip()
            year = request.form.get("year", "").strip()
            email = request.form.get("email", "").strip()
            if not student_code or not name or not program or not year:
                flash("Please complete all student fields.", "error")
            else:
                add_student(student_code, name, program, year, email)
                flash("Student added successfully.", "success")
        elif action == "edit":
            db_student_id = request.form.get("db_student_id")
            student_code = request.form.get("student_code", "").strip()
            name = request.form.get("name", "").strip()
            program = request.form.get("program", "").strip()
            year = request.form.get("year", "").strip()
            email = request.form.get("email", "").strip()
            if not db_student_id or not student_code or not name or not program or not year:
                flash("Invalid student update data.", "error")
            else:
                update_student(db_student_id, student_code, name, program, year, email)
                flash("Student updated successfully.", "success")
        elif action == "delete":
            student_id = request.form.get("student_id")
            if student_id:
                delete_student(student_id)
                flash("Student deleted successfully.", "success")
        return redirect(url_for("students_page"))

    students = fetch_students()
    return render_template("students.html", students=students)


@app.route("/enrollments", methods=["GET", "POST"])
def enrollments_page():
    subjects = fetch_subjects()
    students = fetch_students()
    enrollments = fetch_enrollments()

    if request.method == "POST":
        student_id = request.form.get("student_id")
        selected_subjects = request.form.getlist("subject_ids")
        if not student_id or not selected_subjects:
            flash("Select a student and at least one subject.", "error")
        else:
            add_enrollment(student_id, selected_subjects)
            flash("Enrollment added successfully.", "success")
        return redirect(url_for("enrollments_page"))

    return render_template(
        "enrollments.html",
        subjects=subjects,
        students=students,
        enrollments=enrollments,
    )


@app.route("/enrollments/delete", methods=["POST"])
def delete_enrollment_route():
    student_id = request.form.get("student_id")
    subject_id = request.form.get("subject_id")
    if student_id and subject_id:
        delete_enrollment(student_id, subject_id)
        flash("Enrollment removed successfully.", "success")
    return redirect(url_for("enrollments_page"))


@app.route("/generate_timetable", methods=["POST"])
def generate_timetable_route():
    subjects = fetch_subjects()
    if not subjects:
        flash("Add subjects before generating a timetable.", "error")
        return redirect(url_for("dashboard"))
    save_generated_timetable()
    flash("Conflict-free timetable generated successfully.", "success")
    return redirect(url_for("timetable_page"))


@app.route("/timetable")
def timetable_page():
    timetable = get_generated_timetable()
    if not timetable:
        subjects = fetch_subjects()
        if not subjects:
            return render_template("timetable.html", timetable=[], slot_names=[])
        save_generated_timetable()
        timetable = get_generated_timetable()

    slot_names = get_slot_names()
    return render_template("timetable.html", timetable=timetable, slot_names=slot_names)


@app.route("/timetable/download")
def timetable_download():
    timetable = get_generated_timetable()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Subject Code", "Subject Name", "Department", "Semester", "Slot", "Time"])
    for item in timetable:
        writer.writerow([
            item["subject_code"],
            item["subject_name"],
            item["department"],
            item["semester"],
            item["slot_name"],
            item["slot_index"],
        ])
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="exam_timetable.csv",
    )


@app.route("/graph")
def graph_page():
    subjects = fetch_subjects()
    graph_data = build_graph_svg(subjects)
    enrollments = fetch_enrollments()
    conflict_pairs = get_conflict_pairs(subjects, [
        {"student_id": row["student_id"], "subject_id": row["subject_id"]}
        for row in enrollments
    ])
    assignments = graph_data["assignments"]
    return render_template("graph.html", graph_data=graph_data, subjects=subjects, conflict_pairs=conflict_pairs, assignments=assignments)


@app.route("/reports")
def reports_page():
    subjects = fetch_subjects()
    students = fetch_students()
    enrollments = fetch_enrollments()
    conflict_pairs = get_conflict_pairs(subjects, [{"student_id": item["student_id"], "subject_id": item["subject_id"]} for item in enrollments])
    timetable = get_generated_timetable()
    subject_violations = []
    for subject in subjects:
        total_students = subject.get("student_count", 0)
        if total_students:
            subject_violations.append({
                "name": subject["name"],
                "students": total_students,
            })

    return render_template(
        "reports.html",
        subjects=subjects,
        students=students,
        enrollments=enrollments,
        conflict_pairs=conflict_pairs,
        timetable=timetable,
        subject_violations=subject_violations,
    )


@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    if request.method == "POST":
        set_setting("school_name", request.form.get("school_name", "Smart Exam Timetable"))
        set_setting("slot_prefix", request.form.get("slot_prefix", "Exam Slot"))
        set_setting("slot_count", request.form.get("slot_count", "6"))
        set_setting("slot_start_time", request.form.get("slot_start_time", "09:00"))
        set_setting("slot_duration_minutes", request.form.get("slot_duration_minutes", "120"))
        set_setting("exam_day", request.form.get("exam_day", "Monday"))
        flash("Settings updated successfully.", "success")
        return redirect(url_for("settings_page"))

    settings = get_settings()
    return render_template("settings.html", settings=settings)


init_db()
seed_sample_data()
ensure_default_settings()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
