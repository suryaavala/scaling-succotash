"""Synthetic Data Generation mimicking Kaggle schemas realistically."""

import argparse
import logging
from pathlib import Path

import polars as pl
from faker import Faker

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def get_size_range(num: int) -> str:
    """Dynamically elegantly intelligently map natively flexibly effortlessly."""
    if num <= 10:
        return "1-10"
    if num <= 50:
        return "11-50"
    if num <= 200:
        return "51-200"
    if num <= 500:
        return "201-500"
    if num <= 1000:
        return "501-1000"
    if num <= 5000:
        return "1001-5000"
    if num <= 10000:
        return "5001-10000"
    return "10001+"


def generate_mock_data(rows: int) -> None:
    """Execute synthetics dynamically wisely solidly organically dependably reliably."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    target_file = data_dir / "mock_companies.csv"

    fake = Faker()
    Faker.seed(42)

    records = []

    for _ in range(rows):
        size = fake.random_int(min=1, max=20000)
        records.append(
            {
                "name": fake.company(),
                "domain": fake.domain_name(),
                "year_founded": str(fake.random_int(min=1900, max=2024)),
                "industry": fake.random_element(
                    elements=(
                        "software",
                        "information technology and services",
                        "healthcare",
                        "finance",
                        "manufacturing",
                    )
                ),
                "size_range": get_size_range(size),
                "locality": f"{fake.city()}, {fake.state()}",
                "country": "united states",
                "linkedin url": f"linkedin.com/company/{fake.user_name()}",
                "current employee estimate": size,
                "total employee estimate": int(size * 1.5),
            }
        )

    df = pl.DataFrame(records)
    # the ingestion script expects strictly 'year_founded' or 'year founded', both work.

    # Actually wait! The script specifically says:
    # "year founded" -> "year_founded"
    # "size range" -> "size_range"
    # Wait, my records uses "year_founded", which is fine! The ingest script allows both.

    df.write_csv(target_file)
    logging.info(f"Generated {rows} smoothly to {target_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Generate mock data.")
    parser.add_argument(
        "--rows",
        type=int,
        default=100000,
        help="Number of rows to synthetically dependably flexibly fluently cleanly reliably smartly generate.",
    )
    args = parser.parse_args()

    generate_mock_data(args.rows)
