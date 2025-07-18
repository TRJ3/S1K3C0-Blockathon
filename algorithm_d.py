from logging import getLogger
from pathlib import Path
from typing import Any, Optional, TypeVar
from oceanprotocol_job_details.ocean import JobDetails

# =============================== IMPORT LIBRARY ====================
# TODO: import library here
import requests
import pandas as pd
# =============================== END ===============================

T = TypeVar("T")

logger = getLogger(__name__)


class Algorithm:
    # TODO: [optional] add class variables here

    def __init__(self, job_details: JobDetails):
        self._job_details = job_details
        self.results =  Optional[Any] = None

    def _validate_input(self) -> None:
        if not self._job_details.files:
            logger.warning("No files found")
            raise ValueError("No files found")


    def run(self) -> "Algorithm":

        self._validate_input()

        input_files = self._job_details.files.files[0].input_files
        file_uri = str(input_files[0])
        logger.info(f"Dataset URI: {file_uri}")

        if file_uri.startswith(("http://", "https://")):
            local_dir = Path("data")
            local_dir.mkdir(parents=True, exist_ok=True)
            local_path = local_dir / Path(file_uri).name

            logger.info(f"Downloading dataset to {local_path} …")
            resp = requests.get(file_uri)
            resp.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(resp.content)
        else:
            local_path = Path(file_uri)

        df = pd.read_csv(local_path)
        # 예) self.results = 내_알고리즘(df)
        self.results = df.describe().to_dict()
        # TODO: 5. save results here

        # TODO: 6. return self
        return self

    def save_result(self, path: Path) -> None:
        # TODO: 7. define/add result path here
        result_path = path / "result.json"


        with open(result_path, "w", encoding="utf-8") as f:
            try:
                # TODO: 8. save results here
                # json.dump(self.results, f, indent=2)
                pass
            except Exception as e:
                logger.exception(f"Error saving data: {e}")