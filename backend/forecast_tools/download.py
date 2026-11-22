"""Refresh the fixed Austin snapshot from the public Socrata API."""

import csv
import io
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

OUTPUT = Path(__file__).resolve().parents[1] / "forecast_assets" / "austin_weekly.csv"
API = "https://data.austintexas.gov/resource/mbnu-4wq9.csv"
QUERY = {
    "$select": "report_date,sum(load_weight) as pounds,count(*) as loads",
    "$where": (
        "load_type='RECYCLING - SINGLE STREAM' AND load_weight > 0 "
        "AND report_date >= '2016-01-04T00:00:00' AND report_date < '2021-07-05T00:00:00'"
    ),
    "$group": "report_date",
    "$order": "report_date",
    "$limit": "3000",
}


def aggregate(daily: str, path: Path) -> None:
    pounds: dict[date, Decimal] = defaultdict(Decimal)
    loads: dict[date, int] = defaultdict(int)
    for row in csv.DictReader(io.StringIO(daily)):
        day = date.fromisoformat(row["report_date"][:10])
        monday = day - timedelta(days=day.weekday())
        pounds[monday] += Decimal(row["pounds"])
        loads[monday] += int(row["loads"])
    if len(loads) < 250:
        raise ValueError("The Austin download contains too few observed weeks.")
    with path.open("w", encoding="utf-8", newline="") as result:
        writer = csv.writer(result, lineterminator="\n")
        writer.writerow(("week_start", "pounds", "loads"))
        writer.writerows((week, pounds[week], loads[week]) for week in sorted(loads))


def main() -> None:
    with urlopen(f"{API}?{urlencode(QUERY)}", timeout=45) as response:
        aggregate(response.read().decode("utf-8"), OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
