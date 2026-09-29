"""Generate a fictional text-based PDF; requires the dev extra."""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

path = Path(__file__).resolve().parents[1] / "examples" / "resume.pdf"
path.parent.mkdir(exist_ok=True)
pdf = canvas.Canvas(str(path), pagesize=A4)
pdf.setTitle("Fictional resume - Alex Chen")
pdf.setFont("Helvetica-Bold", 22)
pdf.drawString(56, 780, "Alex Chen")
pdf.setFont("Helvetica", 11)
lines = [
    "Name: Alex Chen", "City: Beijing", "Email: alex@example.com",
    "Fictional sample for software demonstration. No real personal data.", "",
    "EDUCATION", "Example University | Computer Science | Bachelor | 2022-06", "",
    "SKILLS", "Python, React, FastAPI, Docker, PostgreSQL, Git, OpenAI", "",
    "EXPERIENCE", "2022-2025: Full-stack engineer at Example Lab (fictional).",
    "Built a React dashboard and FastAPI service for scientific job workflows.",
    "Designed PostgreSQL data models and packaged services using Docker.",
    "Integrated OpenAI APIs with timeout handling and JSON validation.",
    "Added automated tests and reviewed changes with Git.", "",
    "PROJECT", "Research workflow assistant: track jobs, results and API failures.",
]
for index, line in enumerate(lines):
    pdf.drawString(56, 742 - index * 23, line)
pdf.save()
print(path)
