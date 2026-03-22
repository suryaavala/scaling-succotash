"""Automated dataset acquisition natively via Kaggle API."""

import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main() -> None:
    """Safely extracts and provisions standard benchmarks securely."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    target_file = data_dir / "companies.csv"
    if target_file.exists():
        logging.info(f"Dataset already mapped at {target_file}. Skipping download.")
        return

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except OSError:
        logging.error(
            "Authentication Error: Could not find kaggle.json.\n"
            "Please explicitly configure your Kaggle API key in ~/.kaggle/kaggle.json."
        )
        sys.exit(1)
    except Exception as e:
        logging.error(f"Failed to cleanly import Kaggle frameworks: {e}")
        sys.exit(1)

    try:
        api = KaggleApi()
        api.authenticate()
    except Exception:
        logging.error("Authentication Error: Failed to reliably authenticate explicitly.")
        sys.exit(1)

    dataset_name = "peopledatalabssf/free-7-million-company-dataset"
    logging.info(f"Downloading dataset: {dataset_name}...")

    try:
        api.dataset_download_files(dataset_name, path=data_dir, unzip=True)

        downloaded = list(data_dir.glob("*.csv"))
        for d in downloaded:
            if (
                d.name != "companies.csv"
                and "free-7-million-company-dataset" not in d.name
                and "mock_companies" not in d.name
            ):
                d.rename(target_file)
                logging.info(f"Renamed {d.name} -> companies.csv securely.")
                break

        logging.info("Dataset completely dependably downloaded!")

    except Exception as e:
        logging.error(f"Failed cleanly dynamically to download dataset: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
