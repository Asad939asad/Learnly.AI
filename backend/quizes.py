# backend/quizes.py

import os
import requests
import json
import datetime
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor # NEW: For concurrent grading

# Ensure this is set in your environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def generate_quiz(
    prompt: str,
    num_questions: int,
    difficulty: str,
    mcq_percent: int,
    rag_context: Optional[str] = None # Added for future RAG integration
) -> Dict[str, Any]:
    """
    Calls the Groq LLM to generate a quiz based on user-defined parameters.
    (This function remains the same as the previous version)
    """
    if not GROQ_API_KEY:
        raise ValueError("Missing GROQ_API_KEY environment variable")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Calculate question mix
    num_mcq = round(num_questions * (mcq_percent / 100))
    num_short_answer = num_questions - num_mcq
    
    # === Future RAG Integration Placeholder ===
    rag_instruction = ""
    if rag_context:
        rag_instruction = f"Base the quiz strictly on the following context. Do not use external knowledge: {rag_context}\n\n"
    # ========================================

    # Construct the dynamic system prompt
    system_prompt = f"""
    You are a professional quiz generator. Your task is to create a quiz based on the user's request.
    
    # Quiz Generation Requirements
    1. The quiz must have exactly {num_questions} questions.
    2. The difficulty level must be **{difficulty}**.
    3. The question mix must be: 
        - Approximately {num_mcq} Multiple Choice Questions (MCQ)
        - Approximately {num_short_answer} Short Answer Questions
    4. Ensure the Short Answer questions require a concise, single correct answer for future automated grading.
    5. {rag_instruction}

    # Output Format
    Always return the output as a JSON object in this exact schema. The 'correct_answer' and 'explanation' fields are critical for the grading system.
    {{
      "quiz": {{
        "title": string,
        "topic": string,
        "metadata": {{
          "difficulty": "{difficulty}",
          "num_questions": {num_questions},
          "generated_at": string (ISO8601 datetime)
        }},
        "questions": [
          {{
            "id": string (unique ID for the question),
            "type": "mcq" | "short_answer",
            "question": string,
            "options": [string] (only if type='mcq' and must have 4 options),
            "correct_answer": string (the exact correct option text for mcq, or the exact expected answer for short_answer),
            "explanation": string (A detailed explanation of the correct answer, which will be used for feedback/improvement areas.)
          }}
        ]
      }}
    }}
    Do not include any text before or after the JSON. Return only valid JSON.
    """

    payload = {
        "model": "llama-3.1-8b-instant",  # Use your preferred Groq model
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a quiz for the topic: {prompt}"}
        ],
        "temperature": 0.5,
        "max_tokens": 8000
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()

    # Extract quiz JSON text
    quiz_text = data["choices"][0]["message"]["content"]

    try:
        quiz_json = json.loads(quiz_text)
        # Ensure 'generated_at' is present for completeness
        if 'metadata' in quiz_json['quiz']:
            quiz_json['quiz']['metadata']['generated_at'] = datetime.datetime.now().isoformat()
    except json.JSONDecodeError:
        raise ValueError(f"Model returned invalid JSON: {quiz_text}")

    return quiz_json

# ----------------------------------------------------------------------
# NEW GRADING IMPLEMENTATION
# ----------------------------------------------------------------------

def semantically_grade_short_answer(
    question: str, 
    user_answer: str, 
    correct_answer: str, 
    explanation: str
) -> Dict[str, Any]:
    """
    Calls the Groq LLM to semantically grade a short answer.
    This is a synchronous, blocking function designed to be run in a thread.
    """
    if not GROQ_API_KEY:
        # In a real app, you might fall back to simple string matching here
        # or raise an error depending on your design.
        return {'is_correct': False, 'llm_explanation': "Grading failed: Missing API Key."}

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = f"""
    You are an impartial academic grader. Your task is to evaluate a student's answer based on the provided correct answer and question.

    # Grading Rules
    1. **Strictness:** Be lenient. If the student captures the core concept, structure, or main keywords of the correct answer, mark it as **True**. Spelling or minor grammatical errors should be ignored.
    2. **Output:** You MUST respond with ONLY a single JSON object.
    
    # Context
    Question: {question}
    Correct/Expected Answer: {correct_answer}
    Original Explanation: {explanation}
    
    # Output Schema
    {{
      "is_correct": boolean,
      "llm_explanation": string (A 1-2 sentence tailored feedback on why the student was correct/incorrect, referencing the core concept.)
    }}
    """
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Student's Answer to Grade: {user_answer}"}
        ],
        "temperature": 0.3, # Use a low temp for reliable, deterministic grading
        "max_tokens": 500
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Extract and parse the LLM's JSON response
        llm_text = data["choices"][0]["message"]["content"].strip()
        
        # Groq often wraps the JSON in markdown blocks, so we clean it up
        if llm_text.startswith("```json"):
            llm_text = llm_text[7:-3].strip()
            
        llm_result = json.loads(llm_text)
        
        # Return the parsed result, ensuring the keys are present
        return {
            'is_correct': llm_result.get('is_correct', False),
            'llm_explanation': llm_result.get('llm_explanation', "LLM failed to provide specific feedback.")
        }
        
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError, ValueError) as e:
        # Catch any errors (API down, timeout, invalid JSON) and fail safely
        print(f"Error during LLM grading: {e}")
        return {
            'is_correct': False,
            'llm_explanation': f"An error occurred during automated grading ({type(e).__name__}). The expected answer was: {correct_answer}."
        }

def grade_quiz(quiz_data: Dict[str, Any], user_answers: Dict[str, str]) -> Dict[str, Any]:
    """
    Compares user answers against the correct answers and generates feedback.
    Uses concurrent threads for LLM-based semantic grading of short answers.
    """
    
    def grade_single_question_task(q: Dict[str, Any], user_answer: str) -> Dict[str, Any]:
        """Handles the grading logic for a single question."""
        q_id = q['id']
        correct_answer = q['correct_answer'].strip()
        explanation = q['explanation']
        is_correct = False
        final_explanation = explanation
        
        user_answer = user_answer.strip() # Already done in the loop, but safe to repeat

        if q['type'] == 'mcq':
            # Case-insensitive string comparison for MCQs
            is_correct = (user_answer.lower() == correct_answer.lower())
            
        elif q['type'] == 'short_answer':
            # Call the synchronous LLM grading function for subjective answers
            llm_result = semantically_grade_short_answer(
                q['question'], user_answer, correct_answer, explanation
            )
            is_correct = llm_result.get('is_correct', False)
            # Overwrite the simple explanation with the richer LLM feedback
            final_explanation = llm_result['llm_explanation'] 

        return {
            'id': q_id,
            'is_correct': is_correct,
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'explanation': final_explanation
        }

    # 1. Prepare data for concurrent execution
    grading_tasks = []
    for q in quiz_data['quiz']['questions']:
        q_id = q['id']
        user_answer = user_answers.get(f"answer-{q_id}", "")
        # Add the function call arguments to a list for the executor
        grading_tasks.append((q, user_answer))

    # 2. Run grading tasks concurrently using a ThreadPoolExecutor
    # A max_workers of 5-10 is usually a good starting point for API calls
    with ThreadPoolExecutor(max_workers=8) as executor:
        # `executor.map` applies `grade_single_question_task` to each set of arguments
        graded_results: List[Dict[str, Any]] = list(executor.map(
            lambda args: grade_single_question_task(*args), grading_tasks
        ))
    
    # 3. Calculate final score
    total_questions = len(graded_results)
    correct_count = sum(1 for result in graded_results if result['is_correct'])

    # 4. Compile the final score and results
    return {
        'status': 'graded',
        'score': f"{correct_count}/{total_questions}",
        'percent': round((correct_count / total_questions) * 100) if total_questions > 0 else 0,
        'results': graded_results
    }