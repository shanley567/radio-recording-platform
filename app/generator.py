import json
import logging
import random
import time
from datetime import UTC, datetime
from pathlib import Path
from threading import Thread

import boto3
from flask import Flask, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest
)

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

# ------------------------------------------------------------------
# AWS CLIENTS
# ------------------------------------------------------------------

s3 = boto3.client("s3")

# ------------------------------------------------------------------
# PROMETHEUS METRICS
# ------------------------------------------------------------------

recordings_generated_total = Counter(
    "recordings_generated_total",
    "Total recordings generated",
    ["station"]
)

s3_upload_success_total = Counter(
    "s3_upload_success_total",
    "Total successful S3 uploads",
    ["station"]
)

s3_upload_failure_total = Counter(
    "s3_upload_failure_total",
    "Total failed S3 uploads",
    ["station"]
)

upload_duration_seconds = Histogram(
    "upload_duration_seconds",
    "Time spent uploading files to S3",
    ["station"]
)

generation_cycle_duration_seconds = Histogram(
    "generation_cycle_duration_seconds",
    "Time taken to complete a generation cycle"
)

# ------------------------------------------------------------------
# FLASK APP
# ------------------------------------------------------------------

app = Flask(__name__)


@app.route("/health/live")
def live():
    """
    Liveness probe.
    Confirms the application process is alive.
    """
    return Response("OK", status=200)


@app.route("/health/ready")
def ready():
    """
    Readiness probe.
    Confirms application can communicate with S3.
    """

    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        return Response("READY", status=200)

    except Exception:
        logger.exception("Readiness check failed")

        return Response(
            "NOT READY",
            status=503
        )


@app.route("/metrics")
def metrics():
    """
    Prometheus metrics endpoint.
    """

    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST
    )


def start_web_server():
    """
    Starts Flask web server.
    """

    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False,
        use_reloader=False
    )


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------

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

    upload_start = time.time()

    s3.upload_file(
        str(filepath),
        BUCKET_NAME,
        object_key
    )

    upload_duration = time.time() - upload_start

    upload_duration_seconds.labels(
        station=station
    ).observe(upload_duration)

    logger.info(
        "Upload successful | station=%s key=%s duration_seconds=%.3f",
        station,
        object_key,
        upload_duration
    )


# ------------------------------------------------------------------
# STARTUP
# ------------------------------------------------------------------

Thread(
    target=start_web_server,
    daemon=True
).start()

logger.info("===================================================")
logger.info("Synthetic Generator Starting")
logger.info("Bucket: %s", BUCKET_NAME)
logger.info("Stations Configured: %s", len(STATIONS))
logger.info("Station List: %s", ", ".join(STATIONS))
logger.info("Output Directory: %s", OUTPUT_DIR.absolute())
logger.info("Metrics Endpoint: http://0.0.0.0:8000/metrics")
logger.info("Liveness Endpoint: http://0.0.0.0:8000/health/live")
logger.info("Readiness Endpoint: http://0.0.0.0:8000/health/ready")
logger.info("Generation Interval: 60 seconds")
logger.info("===================================================")

# ------------------------------------------------------------------
# MAIN PROCESSING LOOP
# ------------------------------------------------------------------

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
        station_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        filename = station_dir / f"{int(time.time())}.json"

        with open(filename, "w") as file:

            json.dump(
                payload,
                file
            )

        recordings_generated_total.labels(
            station=station
        ).inc()

        logger.info(
            "Recording generated | station=%s file=%s signal_strength=%s",
            station,
            filename,
            payload["signal_strength"]
        )

        try:

            upload_file(
                filename,
                station
            )

            s3_upload_success_total.labels(
                station=station
            ).inc()

            filename.unlink()

            logger.info(
                "Local file deleted | station=%s file=%s",
                station,
                filename
            )

        except Exception as error:

            s3_upload_failure_total.labels(
                station=station
            ).inc()

            logger.exception(
                "Upload failed | station=%s file=%s error=%s",
                station,
                filename,
                str(error)
            )

    cycle_duration = round(
        time.time() - cycle_start,
        2
    )

    generation_cycle_duration_seconds.observe(
        cycle_duration
    )

    logger.info(
        "Generation cycle completed | stations_processed=%s duration_seconds=%s",
        len(STATIONS),
        cycle_duration
    )

    logger.info(
        "Sleeping before next cycle | sleep_seconds=60"
    )

    time.sleep(60)