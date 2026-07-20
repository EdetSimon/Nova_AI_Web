def build_dataset_prompt(df, rows, columns, missing, duplicates):
    """
    Build a concise, dataset-aware prompt without sending raw sample rows
    to the AI model.
    """

    column_list = ", ".join(df.columns.astype(str).tolist()[:25])

    numeric_columns = df.select_dtypes(include="number").columns.tolist()[:8]
    categorical_columns = df.select_dtypes(
        include=["object", "category", "string"]
    ).columns.tolist()[:6]

    numeric_summary_lines = []

    for column in numeric_columns:
        series = df[column].dropna()

        if series.empty:
            continue

        numeric_summary_lines.append(
            (
                f"- {column}: minimum={series.min():,.2f}, "
                f"maximum={series.max():,.2f}, "
                f"average={series.mean():,.2f}, "
                f"total={series.sum():,.2f}"
            )
        )

    categorical_summary_lines = []

    for column in categorical_columns:
        top_values = df[column].dropna().astype(str).value_counts().head(5)

        if top_values.empty:
            continue

        formatted_values = ", ".join(
            f"{value} ({count})"
            for value, count in top_values.items()
        )

        categorical_summary_lines.append(
            f"- {column}: {formatted_values}"
        )

    numeric_summary = (
        "\n".join(numeric_summary_lines)
        if numeric_summary_lines
        else "- No numeric columns were detected."
    )

    categorical_summary = (
        "\n".join(categorical_summary_lines)
        if categorical_summary_lines
        else "- No categorical columns were detected."
    )

    prompt = f"""
You are Nova AI Analyst, an expert Business Intelligence consultant and Senior Data Analyst.

Analyze the uploaded dataset and produce a concise, professional Executive Business Intelligence Report.

Use clear Markdown formatting.

# Executive Summary

Provide a short overview of what the dataset appears to represent and the most important business takeaway.

---

# Dataset Overview

- Total Rows: {rows}
- Total Columns: {columns}
- Missing Values: {missing}
- Duplicate Rows: {duplicates}

Briefly assess the overall data quality.

---

# Available Columns

{column_list}

---

# Numeric Summary

{numeric_summary}

---

# Leading Categories

{categorical_summary}

---

# Key Business Insights

Provide 4–6 important insights supported by the summaries above.

Use bullet points.

---

# Data Quality Assessment

Discuss:

- Missing values
- Duplicate records
- Possible inconsistencies
- Dataset limitations

---

# Business Opportunities

Suggest realistic opportunities management could explore based on the available evidence.

Use bullet points.

---

# Recommendations

Provide 5 practical and actionable recommendations for decision-makers.

Use numbered points.

---

# Executive Conclusion

Finish with a concise conclusion of 2–4 sentences suitable for a CEO or senior executive.

Important Instructions:

- Use professional business language.
- Keep explanations concise.
- Never invent facts that are not supported by the supplied summaries.
- If revenue, sales, profit, customers, products, locations, or regions are present, prioritize them.
- Treat identifiers such as Order ID as identifiers, not business performance measures.
- Clearly state when the dataset is too limited to support a conclusion.
- Do not reproduce raw dataset rows.
- Format the response using Markdown headings, bullet lists, and numbered lists.
"""

    return prompt
