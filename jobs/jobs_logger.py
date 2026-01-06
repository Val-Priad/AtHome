import logging

jobs_logger = logging.getLogger(__name__)

jobs_logger.setLevel(logging.INFO)

jobs_file_handler = logging.FileHandler("jobs.log", mode="w")
jobs_stream_handler = logging.StreamHandler()

jobs_formatter = logging.Formatter(
    "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

jobs_file_handler.setFormatter(jobs_formatter)
jobs_stream_handler.setFormatter(jobs_formatter)

if not jobs_logger.handlers:
    jobs_logger.addHandler(jobs_file_handler)
    jobs_logger.addHandler(jobs_stream_handler)
