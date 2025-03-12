import pytest
import httpx
# from fastapi.testclient import TestClient
# from serve.wsgi import app

# client = TestClient(app)
BASE_URL = "http://llm_backend:5000"

# Define test cases
@pytest.mark.parametrize("prompt,generation_model,expected_status", [
    ("What is the capital of France?", "allenai/OLMo-2-1124-7B-Instruct", 200),
    ("Explain quantum computing in simple terms.", "allenai/OLMo-2-1124-7B-Instruct", 200),
])

def test_generate_endpoint(prompt, generation_model, expected_status):
    """
    Test the text generation API endpoint.
    """
    payload = {
        "prompt": prompt,
        "generation_model": generation_model
    }

    with httpx.Client(timeout=30.0) as client:  # Increased timeout for model loading
        response = client.post(f"{BASE_URL}/generate/", json=payload)
    
        assert response.status_code == expected_status
        assert "answer" in response.json()
        assert isinstance(response.json()["answer"], str)
        assert len(response.json()["answer"]) > 0  # Ensure the model generates text

        print(f"✅ Test passed for prompt: {prompt}")

if __name__ == "__main__":
    pytest.main()