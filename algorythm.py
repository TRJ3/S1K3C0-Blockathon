import os
import requests
import pandas as pd
import json
from logging import getLogger
from pathlib import Path
from typing import Any, Optional
import re

logger = getLogger(__name__)

class Algorithm:
    def __init__(self, job_details):
        self._job_details = job_details
        self.results: Optional[Any] = None

    def _validate_input(self) -> None:
        if not self._job_details.files:
            logger.warning("No files found")
            raise ValueError("No files found")

    def _remove_privacy(self, data):
        """
        개인정보(이름, 이메일, 전화번호, 주소 등)를 제거한 데이터를 반환합니다.
        - data: dict, list, str 등 다양한 형태 지원
        """
        # 개인정보 패턴 정의
        privacy_keys = [
            '이름', 'name', 'Name', '성명',
            '이메일', 'email', 'Email',
            '전화', '전화번호', '연락처', 'phone', 'Phone',
            '주소', 'address', 'Address',
            '주민등록번호', 'id', 'ID', 'ssn', 'SSN'
        ]
        email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+')
        phone_pattern = re.compile(r'(\d{2,4}-\d{3,4}-\d{4}|\d{10,11})')
        id_pattern = re.compile(r'\d{6}-\d{7}')

        def clean_dict(d):
            return {
                k: v for k, v in d.items()
                if k not in privacy_keys and not email_pattern.match(str(v))
                and not phone_pattern.match(str(v))
                and not id_pattern.match(str(v))
            }

        if isinstance(data, dict):
            return clean_dict(data)
        elif isinstance(data, list):
            return [clean_dict(item) if isinstance(item, dict) else item for item in data]
        elif isinstance(data, str):
            # 문자열에서 이메일, 전화번호, 주민번호 패턴 제거
            s = email_pattern.sub('[이메일 제거]', data)
            s = phone_pattern.sub('[전화번호 제거]', s)
            s = id_pattern.sub('[주민번호 제거]', s)
            return s
        else:
            return data

    def _read_input_file(self, filepath: str) -> str:
        """
        다양한 파일 형식을 지원하여 입력 데이터를 읽고,
        개인정보를 제거한 후 남은 정보를 요약/정리하여 반환합니다.
        """
        try:
            file_extension = Path(filepath).suffix.lower()
            summary = ""
            if file_extension == '.csv':
                df = pd.read_csv(filepath)
                # 개인정보 컬럼 제거
                df_clean = df.drop(columns=[col for col in df.columns if any(key in col for key in ['이름','email','Email','name','Name','전화','연락처','주소','id','ID','주민등록번호','ssn','SSN','address','Address'])], errors='ignore')
                summary = df_clean.to_string(index=False)
                logger.info(f"Read CSV file: {filepath}, shape: {df.shape}")
            elif file_extension == '.json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data_clean = self._remove_privacy(data)
                summary = json.dumps(data_clean, ensure_ascii=False, indent=2)
                logger.info(f"Read JSON file: {filepath}")
            elif file_extension == '.txt':
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                # 문자열에서 개인정보 패턴 제거
                summary = self._remove_privacy(content)
                logger.info(f"Read TXT file: {filepath}")
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                summary = self._remove_privacy(content)
                logger.info(f"Read {file_extension} file: {filepath}")
            return summary if summary else "No data after privacy removal."
        except Exception as e:
            logger.error(f"Error reading input file {filepath}: {e}")
            return "Error or no data."

    def run(self) -> "Algorithm":
        self._validate_input()
        try:
            filepath = self._job_details.files.files[0].input_files[0]
            logger.info(f"Getting input data from file: {filepath}")
            summary = self._read_input_file(filepath)
        except Exception as e:
            logger.error(f"Error reading input file: {e}")
            summary = "Error or no data."
        # LLM API 호출 대신 개인정보 제거 후 요약 결과를 바로 output에 저장
        self.results = {
            "output": summary
        }
        return self

    def save_result(self, path: Path) -> None:
        # 결과를 텍스트 파일로 저장
        result_path = path / "llm_result.txt"
        try:
            with open(result_path, "w", encoding="utf-8") as f:
                f.write(f"Output (privacy removed):\n{self.results['output']}\n")
            logger.info(f"Saved output to {result_path}")
        except Exception as e:
            logger.error(f"Error saving output: {e}")