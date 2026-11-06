import json
import random
import time
from datetime import datetime
from pathlib import Path

import boto3

BUCKET_NAME = "jsp-radio-recordings-bucket-2026-demo"

stations = [
    "station-001",
    "station-002",
    "station-003"
]

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

s3 = boto3.client("s3")


def upload_file(filepath, station):
    """
    Upload file to S3 using a structured key path.
    """

    current_time = datetime.utcnow()

    object_key = (
        f"{station}/"
        f"{current_time.strftime('%Y/%m/%d/%H')}/"
        f"{filepath.name}"
    )

    s3.upload_file(
        str(filepath),
        BUCKET_NAME,
        object_key
    )

    print(f"Uploaded: {object_key}")


while True:

    for station in stations:

        payload = {
            "station_id": station,
            "timestamp": datetime.utcnow().isoformat(),
            "signal_strength": random.randint(80, 100),
            "status": "SUCCESS"
        }

        station_dir = OUTPUT_DIR / station
        station_dir.mkdir(parents=True, exist_ok=True)

        filename = station_dir / f"{int(time.time())}.json"

        with open(filename, "w") as file:
            json.dump(payload, file)

        print(f"Created: {filename}")

        try:

            upload_file(filename, station)

            filename.unlink()

            print(f"Deleted local file: {filename}")

        except Exception as error:

            print(f"Upload failed: {error}")

    time.sleep(10)