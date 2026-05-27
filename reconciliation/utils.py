"""
Python module used by the reconciliation application.

Professional note:
    This project follows a simple separation of concerns:
    models store data, forms validate input, views control request/response flow,
    and services contain business rules such as import, reconciliation, dashboard
    summaries, dispute creation, and Excel generation.
"""

from datetime import datetime, date
import pandas as pd



def normalize_datetime(value):
    """
    Converts multiple source date formats into Python datetime object.

    Supported:
    260402
    02-04-2026
    02-04-2026 05:23:46
    April 2, 2026
    April 2, 2026 05:23:46
    2026-04-02
    """

    if value is None or value == "":
        return None

    if pd.isna(value):
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(
            value,
            datetime.min.time()
        )

    value = str(value).strip()

    possible_formats = [
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",

        "%B %d, %Y %H:%M:%S",   # April 2, 2026 05:23:46
        "%b %d, %Y %H:%M:%S",   # Apr 2, 2026 05:23:46

        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",

        "%B %d, %Y",            # April 2, 2026
        "%b %d, %Y",            # Apr 2, 2026

        "%y%m%d",
    ]

    for fmt in possible_formats:
        try:
            return datetime.strptime(
                value,
                fmt
            )

        except ValueError:
            continue

    raise ValueError(
        f"Invalid datetime format: {value}"
    )


def normalize_date(value):
    dt = normalize_datetime(value)

    return dt.date() if dt else None