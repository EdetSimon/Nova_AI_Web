import pandas as pd
import plotly.express as px


# Preferred business columns, ordered by importance
PREFERRED_NUMERIC_COLUMNS = [
    "total revenue",
    "revenue",
    "sales",
    "total sales",
    "profit",
    "total profit",
    "amount",
    "income",
    "units sold",
    "quantity",
    "unit price",
    "unit cost",
    "cost"
]

PREFERRED_CATEGORY_COLUMNS = [
    "region",
    "country",
    "category",
    "item type",
    "product",
    "product name",
    "sales channel",
    "department",
    "segment",
    "state",
    "city"
]


def find_preferred_column(columns, preferred_names):
    """
    Find the most meaningful column from a list of preferred names.
    Matching is case-insensitive.
    """

    normalized_columns = {
        str(column).strip().lower(): column
        for column in columns
    }

    for preferred_name in preferred_names:
        if preferred_name in normalized_columns:
            return normalized_columns[preferred_name]

    return None


def select_numeric_column(df):
    """
    Select a useful business metric.

    ID-style columns are avoided because summing or plotting identifiers
    normally produces meaningless business visualizations.
    """

    numeric_columns = df.select_dtypes(include="number").columns.tolist()

    preferred_column = find_preferred_column(
        numeric_columns,
        PREFERRED_NUMERIC_COLUMNS
    )

    if preferred_column:
        return preferred_column

    usable_columns = [
        column
        for column in numeric_columns
        if not any(
            excluded_word in str(column).strip().lower()
            for excluded_word in ["id", "code", "number"]
        )
    ]

    if usable_columns:
        return usable_columns[0]

    return numeric_columns[0] if numeric_columns else None


def select_category_column(df):
    """
    Select a useful categorical column for grouping charts.
    """

    categorical_columns = df.select_dtypes(
        include=["object", "category", "string"]
    ).columns.tolist()

    preferred_column = find_preferred_column(
        categorical_columns,
        PREFERRED_CATEGORY_COLUMNS
    )

    if preferred_column:
        return preferred_column

    return categorical_columns[0] if categorical_columns else None


def configure_figure(fig):
    """
    Apply consistent responsive styling to every Plotly figure.
    """

    fig.update_layout(
        autosize=True,
        height=460,
        margin=dict(
            left=55,
            right=35,
            top=75,
            bottom=65
        ),
        paper_bgcolor="#172033",
        plot_bgcolor="#172033",
        font=dict(
            color="#E2E8F0"
        ),
        title=dict(
            x=0.02,
            xanchor="left"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def figure_to_html(fig, include_plotlyjs=False):
    """
    Convert a Plotly figure into responsive HTML for Flask.
    """

    return fig.to_html(
        full_html=False,
        include_plotlyjs=include_plotlyjs,
        config={
            "responsive": True,
            "displaylogo": False,
            "scrollZoom": False
        },
        default_width="100%",
        default_height="460px"
    )


def generate_charts(df):
    """
    Automatically generate three interactive Plotly charts
    based on the uploaded dataset.

    Returns:
        dict: Chart names mapped to Plotly HTML.
    """

    charts = {}

    if df is None or df.empty:
        return charts

    numeric_column = select_numeric_column(df)
    category_column = select_category_column(df)

    # -----------------------------
    # BAR CHART
    # -----------------------------

    if numeric_column and category_column:

        grouped = (
            df[[category_column, numeric_column]]
            .dropna()
            .groupby(category_column, as_index=False)[numeric_column]
            .sum()
            .sort_values(numeric_column, ascending=False)
            .head(10)
        )

        if not grouped.empty:

            bar_figure = px.bar(
                grouped,
                x=category_column,
                y=numeric_column,
                title=f"{numeric_column} by {category_column}",
                template="plotly_dark"
            )

            bar_figure.update_traces(
                hovertemplate=(
                    f"<b>%{{x}}</b><br>"
                    f"{numeric_column}: %{{y:,.2f}}"
                    "<extra></extra>"
                )
            )

            bar_figure = configure_figure(bar_figure)

            charts["bar"] = figure_to_html(
                bar_figure,
                include_plotlyjs="cdn"
            )

    # -----------------------------
    # PIE CHART
    # -----------------------------

    if numeric_column and category_column:

        grouped = (
            df[[category_column, numeric_column]]
            .dropna()
            .groupby(category_column, as_index=False)[numeric_column]
            .sum()
            .sort_values(numeric_column, ascending=False)
            .head(8)
        )

        if not grouped.empty:

            pie_figure = px.pie(
                grouped,
                names=category_column,
                values=numeric_column,
                title=f"{numeric_column} Distribution by {category_column}",
                template="plotly_dark",
                hole=0.35
            )

            pie_figure.update_traces(
                textposition="inside",
                textinfo="percent+label",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Value: %{value:,.2f}<br>"
                    "Share: %{percent}"
                    "<extra></extra>"
                )
            )

            pie_figure = configure_figure(pie_figure)

            charts["pie"] = figure_to_html(pie_figure)

    # -----------------------------
    # HISTOGRAM
    # -----------------------------

    if numeric_column:

        histogram_data = df[[numeric_column]].dropna()

        if not histogram_data.empty:

            histogram_figure = px.histogram(
                histogram_data,
                x=numeric_column,
                nbins=25,
                title=f"{numeric_column} Distribution",
                template="plotly_dark"
            )

            histogram_figure.update_traces(
                hovertemplate=(
                    f"{numeric_column}: %{{x}}<br>"
                    "Count: %{y}"
                    "<extra></extra>"
                )
            )

            histogram_figure = configure_figure(histogram_figure)

            charts["histogram"] = figure_to_html(
                histogram_figure
            )

    return charts