# backend/slide_decks.py

import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def generate_slide_deck(prompt: str):
    """
    Calls the Groq LLM to generate a slide deck in the structured JSON format.
    """
    if not GROQ_API_KEY:
        raise ValueError("Missing GROQ_API_KEY environment variable")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = """
    You are a presentation slide generator.
    Always return output as a JSON object in this exact schema:
    {
      "slide_deck": {
        "title": string,
        "topic": string,
        "metadata": {
          "created_at": string (ISO8601 datetime),
          "created_by": string,
          "total_slides": number
        },
        "slides": [
          {
            "slide_id": string,
            "slide_type": "title_slide" | "paragraph" | "unordered_list" | "ordered_list",
            "slide_title": string,
            "slide_content": string | [string]
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
        "max_tokens": 800
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()

    # Extract slide deck JSON text
    slide_deck_text = data["choices"][0]["message"]["content"]

    import json
    try:
        slide_deck_json = json.loads(slide_deck_text)
    except json.JSONDecodeError:
        raise ValueError(f"Model returned invalid JSON: {slide_deck_text}")

    return slide_deck_json
