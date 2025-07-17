import requests
import time
import json
import os

# Konfiguration
NAUTILUS_API_URL = "https://nautilus.delta-dao.com/api/v1/nautilus/jobs"
YOUR_DATASET_DID = "did:op:..."  # Durch deine Dataset-DID ersetzen
YOUR_DOCKER_IMAGE = "ghcr.io/dein-repo/llm-chatbot:latest"
YOUR_OCEAN_TOKEN = os.getenv("OCEAN_TOKEN")  # Für Authentifizierung

class NautilusComputeService:
    def __init__(self, api_url, dataset_did, docker_image):
        self.api_url = api_url
        self.dataset_did = dataset_did
        self.docker_image = docker_image
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {YOUR_OCEAN_TOKEN}"
        }
    
    def start_compute_job(self, user_question: str) -> str:
        """Startet einen Compute-to-Data Job mit Nutzerfrage"""
        job_payload = {
            "dataset": {
                "did": self.dataset_did,
                "serviceId": "compute"
            },
            "algorithm": {
                "container": {
                    "image": self.docker_image,
                    "tag": "latest",
                    "entrypoint": "python",
                    "args": [
                        "/app/llm_chatbot.py",
                        "--input", "/data/input.txt",
                        "--output", "/outputs/response.txt"
                    ]
                }
            },
            "additionalInputs": {
                "input": user_question
            },
            "environment": {
                "variables": {
                    "LLM_MODEL": "gpt-4"
                }
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=job_payload
            )
            response.raise_for_status()
            return response.json()["jobId"]
        
        except Exception as e:
            raise RuntimeError(f"Job start failed: {str(e)}")

    def get_job_status(self, job_id: str) -> dict:
        """Ruft aktuellen Job-Status ab"""
        try:
            response = requests.get(
                f"{self.api_url}/{job_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            raise RuntimeError(f"Status check failed: {str(e)}")

    def download_job_result(self, job_id: str) -> str:
        """Lädt Ergebnis nach erfolgreicher Ausführung"""
        try:
            response = requests.get(
                f"{self.api_url}/{job_id}/results",
                headers=self.headers
            )
            response.raise_for_status()
            return response.text
        
        except Exception as e:
            raise RuntimeError(f"Result download failed: {str(e)}")

    def get_job_logs(self, job_id: str) -> str:
        """Ruft Job-Logs zur Fehlerdiagnose ab"""
        try:
            response = requests.get(
                f"{self.api_url}/{job_id}/logs",
                headers=self.headers
            )
            response.raise_for_status()
            return response.text
        
        except Exception as e:
            raise RuntimeError(f"Log retrieval failed: {str(e)}")

    def run_chatbot_query(self, question: str, timeout=600, poll_interval=5) -> str:
        """Vollständiger Workflow: Starte Job → Überwache → Hole Ergebnis"""
        job_id = self.start_compute_job(question)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status_data = self.get_job_status(job_id)
            status = status_data["status"]
            
            if status == "succeeded":
                return self.download_job_result(job_id)
            
            elif status == "failed":
                logs = self.get_job_logs(job_id)
                raise RuntimeError(f"Job failed. Logs:\n{logs}")
            
            time.sleep(poll_interval)
        
        raise TimeoutError("Job execution timed out")
# Beispielverwendung
if __name__ == "__main__":
    nautilus = NautilusComputeService(
        api_url=NAUTILUS_API_URL,
        dataset_did=YOUR_DATASET_DID,
        docker_image=YOUR_DOCKER_IMAGE
    )
    
    try:
        user_question = "Was ist der Sinn des Lebens?"
        response = nautilus.run_chatbot_query(user_question)
        print(f"Chatbot-Antwort:\n{response}")
    
    except Exception as e:
        print(f"Fehler: {str(e)}")