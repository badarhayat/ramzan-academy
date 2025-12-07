from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, flash
import sqlite3
from pathlib import Path
import io
from datetime import datetime
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# -----------------------------------
# DB Path
# -----------------------------------
import os
DB_PATH = Path(os.environ.get("DB_PATH", "database.db"))


app = Flask(__name__)
app.config["SECRET_KEY"] = "ramzan_academy_secret_123"


# -----------------------------------
# SUBJECTS BY CLASS
# -----------------------------------
SUBJECTS_BY_CLASS = {
    "9th": ["English", "Math", "TJQ", "Urdu", "Physics", "Chemistry", "Biology",
            "Computer", "General Science", "Islamiyat (Elective)", "Education"],

    "10th": ["English", "Math", "TJQ", "Urdu", "Physics", "Chemistry", "Biology",
             "Computer", "General Science", "Islamiyat (Elective)", "Education", "Pak Studies"],

    "11th": ["English", "Math", "TJQ", "Urdu", "Physics", "Chemistry", "Biology",
             "Computer", "Education", "Islamiyat (Compulsory)"],

    "12th": ["English", "Math", "TJQ", "Urdu", "Physics", "Chemistry", "Biology",
             "Computer", "Education", "Pak Studies"]
}


# -----------------------------------
# DB Setup
# -----------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        father_name TEXT,
        class TEXT,
        contact TEXT,
        career_goal TEXT,
        registered_at TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        date TEXT,
        test_name TEXT,
        subject TEXT NOT NULL,
        total_marks REAL NOT NULL,
        obtained_marks REAL NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )""")

    conn.commit()
    conn.close()


def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return (rows[0] if rows else None) if one else rows


init_db()


# -----------------------------------
# HOME - Student List
# -----------------------------------
@app.route("/")
def index():
    students = query_db("SELECT * FROM students ORDER BY id DESC")
    return render_template("students.html", students=students)


# -----------------------------------
# REGISTER STUDENT
# -----------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        father = request.form.get("father_name")
        cls = request.form.get("class")
        contact = request.form.get("contact")
        career = request.form.get("career_goal")

        query_db("""
        INSERT INTO students (name, father_name, class, contact, career_goal, registered_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (name, father, cls, contact, career, datetime.utcnow().isoformat()))

        flash("Student registered successfully.", "success")
        return redirect(url_for("index"))

    classes = SUBJECTS_BY_CLASS.keys()
    return render_template("register.html", classes=classes)


# -----------------------------------
# EDIT STUDENT
# -----------------------------------
@app.route("/student/<int:student_id>/edit", methods=["GET", "POST"])
def edit_student(student_id):
    student = query_db("SELECT * FROM students WHERE id=?", (student_id,), one=True)

    if request.method == "POST":
        name = request.form.get("name")
        father = request.form.get("father_name")
        cls = request.form.get("class")
        contact = request.form.get("contact")
        career = request.form.get("career_goal")

        query_db("""
            UPDATE students
            SET name=?, father_name=?, class=?, contact=?, career_goal=?
            WHERE id=?
        """, (name, father, cls, contact, career, student_id))

        flash("Student updated.", "success")
        return redirect(url_for("student_profile", student_id=student_id))

    return render_template("edit_student.html", student=student, classes=SUBJECTS_BY_CLASS.keys())


# -----------------------------------
# DELETE STUDENT
# -----------------------------------
@app.route("/student/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    query_db("DELETE FROM marks WHERE student_id=?", (student_id,))
    query_db("DELETE FROM students WHERE id=?", (student_id,))
    flash("Student deleted.", "danger")
    return redirect(url_for("index"))


# -----------------------------------
# ADD MARKS
# -----------------------------------
@app.route("/add_marks", methods=["GET", "POST"])
def add_marks():
    if request.method == "POST":
        sid = request.form.get("student_id")
        subject = request.form.get("subject")
        total = float(request.form.get("total_marks"))
        obtained = float(request.form.get("obtained_marks"))
        test_name = request.form.get("test_name")
        date = request.form.get("date") or datetime.utcnow().date().isoformat()

        query_db("""
        INSERT INTO marks (student_id, date, test_name, subject, total_marks, obtained_marks)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (sid, date, test_name, subject, total, obtained))

        flash("Marks added successfully.", "success")
        return redirect(url_for("student_profile", student_id=sid))

    students = query_db("SELECT id, name, class FROM students ORDER BY name")
    return render_template("add_marks.html", students=students, subjects_by_class=SUBJECTS_BY_CLASS)


# -----------------------------------
# EDIT MARKS
# -----------------------------------
@app.route("/marks/<int:mark_id>/edit", methods=["GET", "POST"])
def edit_marks(mark_id):
    mark = query_db("SELECT * FROM marks WHERE id=?", (mark_id,), one=True)
    student = query_db("SELECT * FROM students WHERE id=?", (mark["student_id"],), one=True)
    
    if request.method == "POST":
        subject = request.form.get("subject")
        total = float(request.form.get("total_marks"))
        obtained = float(request.form.get("obtained_marks"))
        test_name = request.form.get("test_name")
        date = request.form.get("date")

        query_db("""
        UPDATE marks
        SET subject=?, total_marks=?, obtained_marks=?, test_name=?, date=?
        WHERE id=?
        """, (subject, total, obtained, test_name, date, mark_id))

        flash("Marks updated successfully.", "success")
        return redirect(url_for("student_profile", student_id=mark["student_id"]))

    subjects = SUBJECTS_BY_CLASS[student["class"]]
    return render_template("edit_marks.html", mark=mark, subjects=subjects)


# -----------------------------------
# DELETE MARK
# -----------------------------------
@app.route("/marks/<int:mark_id>/delete", methods=["POST"])
def delete_mark(mark_id):
    mark = query_db("SELECT * FROM marks WHERE id=?", (mark_id,), one=True)
    query_db("DELETE FROM marks WHERE id=?", (mark_id,))
    flash("Mark deleted.", "danger")
    return redirect(url_for("student_profile", student_id=mark["student_id"]))


# -----------------------------------
# STUDENT PROFILE + API
# -----------------------------------
@app.route("/student/<int:student_id>")
def student_profile(student_id):
    student = query_db("SELECT * FROM students WHERE id=?", (student_id,), one=True)
    return render_template("profile.html", student=student)


@app.route("/api/student/<int:student_id>/marks")
def api_marks(student_id):
    rows = query_db("SELECT * FROM marks WHERE student_id=? ORDER BY date ASC", (student_id,))

    result = []
    for r in rows:
        pct = (r["obtained_marks"] / r["total_marks"]) * 100
        result.append({
            "id": r["id"],
            "date": r["date"],
            "test_name": r["test_name"],
            "subject": r["subject"],
            "total": r["total_marks"],
            "obtained": r["obtained_marks"],
            "percentage": round(pct, 2)
        })
    return jsonify(result)


# -----------------------------------
# PDF GENERATION
# -----------------------------------
def plot_chart(dates, values, title):
    plt.figure(figsize=(6, 3))
    plt.plot(dates, values, marker="o")
    plt.ylim(0, 100)
    plt.title(title)
    plt.grid(True)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=150)
    plt.close()
    buf.seek(0)
    return buf


@app.route("/report/<int:student_id>/pdf")
def pdf_report(student_id):
    student = query_db("SELECT * FROM students WHERE id=?", (student_id,), one=True)
    marks = query_db("SELECT * FROM marks WHERE student_id=?", (student_id,))

    # MAIN AVERAGE PROGRESS
    date_map = {}
    for m in marks:
        if m["date"] not in date_map:
            date_map[m["date"]] = []
        pct = (m["obtained_marks"] / m["total_marks"]) * 100
        date_map[m["date"]].append(pct)

    dates = sorted(date_map.keys())
    avg_values = [sum(date_map[d])/len(date_map[d]) for d in dates]

    main_chart = plot_chart(dates, avg_values, "Average Progress Over Time")

    # SUBJECT-WISE CHARTS
    subject_charts = []
    subjects = {}
    for m in marks:
        if m["subject"] not in subjects:
            subjects[m["subject"]] = {"dates": [], "pct": []}
        pct = (m["obtained_marks"] / m["total_marks"]) * 100
        subjects[m["subject"]]["dates"].append(m["date"])
        subjects[m["subject"]]["pct"].append(pct)

    for sub, data in subjects.items():
        buf = plot_chart(data["dates"], data["pct"], f"{sub} Progress")
        subject_charts.append((sub, buf))

    # BUILD PDF
    pdf = io.BytesIO()
    c = canvas.Canvas(pdf, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 40, "Ramzan Academy Student Progress Report")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Name: {student['name']}")
    c.drawString(50, height - 100, f"Father: {student['father_name']}")
    c.drawString(50, height - 120, f"Class: {student['class']}")
    c.drawString(50, height - 140, f"Contact: {student['contact']}")
    c.drawString(50, height - 160, f"Career Goal: {student['career_goal']}")

    # Insert main chart
    c.drawImage(ImageReader(main_chart), 50, height - 360, width=500, height=180)

    c.showPage()

    # Subject charts
    for sub, img in subject_charts:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 60, sub)
        c.drawImage(ImageReader(img), 50, height - 340, width=500, height=220)
        c.showPage()

    c.save()
    pdf.seek(0)

    return send_file(pdf, as_attachment=True,
                     download_name=f"{student['name']}_Report.pdf",
                     mimetype="application/pdf")


# -----------------------------------
# RUN SERVER
# -----------------------------------
if __name__ == "__main__":
    app.run(debug=True)
