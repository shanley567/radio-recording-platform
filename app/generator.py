import json
import logging
import random
import time
from datetime import UTC, datetime
from pathlib import Path

import boto3

BUCKET_NAME = "jsp-radio-recordings-bucket-2026-demo"

STATIONS = [
    "station-001",
    "station-002",
    "station-003"
]

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s"
)

logger = logging.getLogger(__name__)

s3 = boto3.client("s3")


def upload_file(filepath: Path, station: str) -> None:
    """
    Upload a generated recording file to S3 using a
    partitioned folder structure.
    """

    current_time = datetime.now(UTC)

    object_key = (
        f"{station}/"
        f"{current_time.strftime('%Y/%m/%d/%H')}/"
        f"{filepath.name}"
    )

    logger.info(
        "Uploading file | station=%s bucket=%s key=%s",
        station,
        BUCKET_NAME,
        object_key
    )

    s3.upload_file(
        str(filepath),
        BUCKET_NAME,
        object_key
    )

    logger.info(
        "Upload successful | station=%s key=%s",
        station,
        object_key
    )


logger.info("===================================================")
logger.info("Synthetic Generator Starting")
logger.info("Bucket: %s", BUCKET_NAME)
logger.info("Stations Configured: %s", len(STATIONS))
logger.info("Station List: %s", ", ".join(STATIONS))
logger.info("Output Directory: %s", OUTPUT_DIR.absolute())
logger.info("===================================================")

while True:

    cycle_start = time.time()

    logger.info(
        "Generation cycle started | stations=%s",
        len(STATIONS)
    )

    for station in STATIONS:

        payload = {
            "station_id": station,
            "timestamp": datetime.now(UTC).isoformat(),
            "signal_strength": random.randint(80, 100),
            "status": "SUCCESS"
        }

        station_dir = OUTPUT_DIR / station
        station_dir.mkdir(parents=True, exist_ok=True)

        filename = station_dir / f"{int(time.time())}.json"

        with open(filename, "w") as file:
            json.dump(payload, file)

        logger.info(
            "Recording generated | station=%s file=%s signal_strength=%s",
            station,
            filename,
            payload["signal_strength"]
        )

        try:

            upload_file(filename, station)

            filename.unlink()

            logger.info(
                "Local file deleted | station=%s file=%s",
                station,
                filename
            )

        except Exception as error:

            logger.exception(
                "Upload failed | station=%s file=%s error=%s",
                station,
                filename,
                str(error)
            )

    cycle_duration = round(time.time() - cycle_start, 2)

    logger.info(
        "Generation cycle completed | stations_processed=%s duration_seconds=%s",
        len(STATIONS),
        cycle_duration
    )

    logger.info(
        "Sleeping before next cycle | sleep_seconds=60"
    )

    time.sleep(60)