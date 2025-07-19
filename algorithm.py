from logging import getLogger
from pathlib import Path
from typing import Any, Optional, TypeVar
from oceanprotocol_job_details.ocean import JobDetails

# =============================== IMPORT LIBRARY ====================
# TODO: import library here
import json
from llama_cpp import Llama
# =============================== END ===============================

T = TypeVar("T")
logger = getLogger(__name__)

class Algorithm:
    # TODO: [optional] add class variables here
    DEFAULT_MAX_TOKENS: int = 256
    DEFAULT_N_THREADS: int = 8

    def __init__(self, job_details: JobDetails):
        self._job_details = job_details
        self.results: Optional[Any] = None

    def _validate_input(self) -> None:
        if not (self._job_details.files and self._job_details.files.files):
            logger.warning("No input datasets provided.")
            raise ValueError("No input datasets provided.")

    def run(self) -> "Algorithm":
        # TODO: 1. Initialize results type
        self.results = {}

        # TODO: 2. validate input here
        self._validate_input()

        # TODO: 3. get input files here
        # Retrieve all mounted input files (model + question)
        input_paths = self._job_details.files.files[0].input_files
        # Identify GGUF model file
        question_file = next((f for f in input_paths if f.name.endswith(".txt") or f.name.endswith(".json")), None)
        if not question_file:
            raise FileNotFoundError("No question file found in inputs.")

        # TODO: 4. run algorithm here
        # Load GGUF model
        model_path = "algorithm/model/Q4_K_M.gguf"
        
        logger.info(f"Loading model: {Path(model_path).name}")  # Privacy: only filename
        model = Llama(
            model_path=model_path,
            n_threads=self.DEFAULT_N_THREADS,
            n_ctx=2048
        )

        # Load prompt: prefer explicit parameter, else question file
        prompt = getattr(self._job_details.input_parameters, "prompt", None)
        if not prompt and question_file:
            with open(str(question_file), "r", encoding="utf-8") as qf:
                prompt = qf.read().strip()
        if not prompt:
            raise ValueError("No prompt provided. Please supply via input_parameters or include a .txt/.json question file.")

        # Perform inference with privacy-aware logging
        output = model(prompt, max_tokens=self.DEFAULT_MAX_TOKENS, stop=["\n"])
        response_text = output.get("choices", [{}])[0].get("text", "").strip()
        logger.info(f"Generated response length: {len(response_text)} characters.")

        # TODO: 5. save results here
        self.results["response"] = response_text

        # TODO: 6. return self
        return self

    def save_result(self, path: Path) -> None:
        # TODO: 7. define/add result path here
        out_dir = path / "outputs"
        out_dir.mkdir(parents=True, exist_ok=True)
        result_path = out_dir / "result.json"

        with open(result_path, "w", encoding="utf-8") as f:
            try:
                # TODO: 8. save results here
                json.dump(self.results, f, ensure_ascii=False, indent=2)
                logger.info("Results saved successfully.")
            except Exception as e:
                logger.exception(f"Error saving data: {e}")
