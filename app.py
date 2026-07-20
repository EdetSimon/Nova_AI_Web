from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
import os

import markdown
import pandas as pd

from chart_generator import generate_charts
from nova_ai.llm import ask_nova
from nova_ai.prompts import build_dataset_prompt


app = Flask(__name__)


# ------------------------------------
# Configuration
# ------------------------------------

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = (".csv", ".xlsx", ".xls")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


# ------------------------------------
# Shared Dashboard Defaults
# ------------------------------------

def dashboard_defaults():
    return {
        "rows": 0,
        "columns": 0,
        "missing": 0,
        "duplicates": 0,
        "insights": (
            "Upload a dataset to begin your "
            "AI-powered business analysis."
        ),
        "charts": {},
        "preview_table": ""
    }


# ------------------------------------
# Home Page
# ------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# ------------------------------------
# Dashboard
# ------------------------------------

@app.route("/dashboard")
def dashboard():
    return render_template(
        "dashboard.html",
        **dashboard_defaults()
    )


# ------------------------------------
# Upload Dataset
# ------------------------------------

@app.route("/upload", methods=["POST"])
def upload():
    if "dataset" not in request.files:
        return redirect("/dashboard")

    file = request.files["dataset"]

    if not file or file.filename == "":
        return redirect("/dashboard")

    safe_name = secure_filename(file.filename)
    filename = safe_name.lower()

    if not filename.endswith(ALLOWED_EXTENSIONS):
        values = dashboard_defaults()
        values["insights"] = "❌ Please upload a CSV or Excel file."

        return render_template(
            "dashboard.html",
            **values
        )

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        safe_name
    )

    file.save(filepath)

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        if df.empty:
            values = dashboard_defaults()
            values["insights"] = (
                "⚠️ The uploaded file is valid, but it contains no data."
            )

            return render_template(
                "dashboard.html",
                **values
            )

    except Exception as error:
        values = dashboard_defaults()
        values["insights"] = (
            "⚠️ The uploaded file could not be read.<br><br>"
            f"Error: {str(error)}"
        )

        return render_template(
            "dashboard.html",
            **values
        )

    # Basic Statistics

    rows = len(df)
    columns = len(df.columns)
    missing = int(df.isnull().sum().sum())
    duplicates = int(df.duplicated().sum())

    # Dataset Preview

    preview_table = df.head(10).to_html(
        index=False,
        border=0,
        classes="preview-table",
        na_rep="—"
    )

    # Generate Charts

    try:
        charts = generate_charts(df)

    except Exception as error:
        print(f"Chart generation failed: {error}")
        charts = {}

    # Build AI Prompt

    prompt = build_dataset_prompt(
        df=df,
        rows=rows,
        columns=columns,
        missing=missing,
        duplicates=duplicates
    )

    # Ask Nova AI

    try:
        ai_response = ask_nova(prompt)

        insights = markdown.markdown(
            ai_response,
            extensions=[
                "extra",
                "tables",
                "fenced_code",
                "sane_lists"
            ]
        )

    except Exception as error:
        insights = (
            "⚠️ AI analysis could not be completed.<br><br>"
            f"Error: {str(error)}"
        )

    return render_template(
        "dashboard.html",
        rows=rows,
        columns=columns,
        missing=missing,
        duplicates=duplicates,
        insights=insights,
        charts=charts,
        preview_table=preview_table
    )


# ------------------------------------
# Upload Size Error
# ------------------------------------

@app.errorhandler(413)
def file_too_large(_error):
    values = dashboard_defaults()
    values["insights"] = (
        "⚠️ The uploaded file is too large. "
        "Please upload a file smaller than 16 MB."
    )

    return render_template(
        "dashboard.html",
        **values
    ), 413


# ------------------------------------
# Run App
# ------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
