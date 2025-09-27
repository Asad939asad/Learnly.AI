# backend/quizes.py

import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def generate_quiz(prompt: str):
    """
    Calls the Groq LLM to generate a quiz in the structured JSON format.
    """
    if not GROQ_API_KEY:
        raise ValueError("Missing GROQ_API_KEY environment variable")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Instruct LLM to strictly follow your quiz JSON schema
    system_prompt = """
    You are a quiz generator. 
    Always return output as a JSON object in this exact schema:
    {
      "quiz": {
        "title": string,
        "topic": string,
        "metadata": {
          "difficulty": string,
          "num_questions": number,
          "generated_at": string (ISO8601 datetime)
        },
        "questions": [
          {
            "id": string,
            "type": "mcq" | "short_answer",
            "question": string,
            "options": [string] (only if type=mcq),
            "correct_answer": string,
            "explanation": string
          }
        ]
      }
    }
    Do not include any text before or after the JSON. Return only valid JSON.
    """

    payload = {
        "model": "llama-3.1-8b-instant",  # Change to any available Groq model
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 8000
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()

    # Extract quiz JSON text
    quiz_text = data["choices"][0]["message"]["content"]

    import json
    try:
        quiz_json = json.loads(quiz_text)
    except json.JSONDecodeError:
        raise ValueError(f"Model returned invalid JSON: {quiz_text}")

    return quiz_json
