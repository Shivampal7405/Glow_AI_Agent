"""
AI-Powered Tools - Code fixing, analysis, writing assistance
Uses Gemini/Groq for intelligent automation
"""

import os
import pyautogui
import time
import json
import base64
from io import BytesIO
from typing import Optional
from pathlib import Path


# ===== AI MODEL HELPERS =====

def _load_config():
    """Load configuration from config.json"""
    try:
        config_path = Path(__file__).parent.parent / "config.json"
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def _call_groq(prompt: str, max_tokens: int = 1000) -> str:
    """
    Call Groq API to generate response

    Args:
        prompt: The prompt to send
        max_tokens: Maximum tokens in response

    Returns:
        AI-generated response
    """
    try:
        from groq import Groq

        config = _load_config()
        api_key = config.get("groq_api_key")
        model = config.get("groq_model", "meta-llama/llama-4-maverick-17b-128e-instruct")

        if not api_key:
            return "Error: Groq API key not configured in config.json"

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling Groq: {str(e)}"


def _call_gemini_vision(prompt: str, screenshot_b64: Optional[str] = None) -> str:
    """
    Call Gemini Vision API with screenshot

    Args:
        prompt: The prompt to send
        screenshot_b64: Base64 encoded screenshot (if None, takes new screenshot)

    Returns:
        AI-generated response
    """
    try:
        import google.generativeai as genai

        config = _load_config()
        api_key = config.get("gemini_api_key")
        model_name = config.get("gemini_model", "gemini-3-flash-preview")

        if not api_key:
            return "Error: Gemini API key not configured in config.json"

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        # Take screenshot if not provided
        if not screenshot_b64:
            screenshot = pyautogui.screenshot()
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            screenshot_b64 = base64.b64encode(buffered.getvalue()).decode()

        # Call vision model
        response = model.generate_content([
            prompt,
            {'mime_type': 'image/png', 'data': screenshot_b64}
        ])

        return response.text.strip()
    except Exception as e:
        return f"Error calling Gemini Vision: {str(e)}"


# ===== CODE ANALYSIS & FIXING =====

def analyze_code_on_screen() -> str:
    """
    Take screenshot of code on screen and analyze it
    Returns analysis of what the code does
    """
    try:
        # Take screenshot
        screenshot_path = Path.home() / "glow_screenshot.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)

        return f"Screenshot saved: {screenshot_path}. Use with vision model to analyze code."
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"


def fix_code_errors(code: str, error_message: str) -> str:
    """
    Suggest fixes for code errors

    Args:
        code: The code with errors
        error_message: The error message

    Returns:
        Suggested fix prompt for AI
    """
    prompt = f"""
Fix this code error:

CODE:
{code}

ERROR:
{error_message}

Provide the corrected code with explanation.
"""
    return f"Use AI to fix code with this prompt: {prompt}"


def explain_code(code: str) -> str:
    """
    Generate explanation prompt for code

    Args:
        code: Code to explain

    Returns:
        Explanation prompt for AI
    """
    prompt = f"""
Explain this code step by step:

{code}

Provide:
1. What it does
2. How it works
3. Key concepts used
"""
    return f"Use AI to explain code with this prompt: {prompt}"


def optimize_code(code: str = "", optimization_goal: str = "performance", **kwargs) -> str:
    """
    Optimize code using AI

    Args:
        code: Code to optimize
        optimization_goal: What to optimize for (performance/readability/memory)

    Returns:
        Optimized code from AI
    """
    # handle aliases
    target_code = code or kwargs.get('content') or kwargs.get('source_code') or "Code from previous step"

    prompt = f"""Optimize this code for {optimization_goal}:

{target_code}

Provide the optimized code with brief comments explaining the improvements. Focus on making it more efficient while keeping it readable.

Return ONLY the optimized code, no explanations before or after."""

    # Call AI to generate optimized code
    optimized = _call_groq(prompt, max_tokens=2000)

    return optimized


# ===== WRITING ASSISTANCE =====

def improve_writing(text: str, style: str = "professional") -> str:
    """
    Generate prompt to improve writing

    Args:
        text: Text to improve
        style: Writing style (professional/casual/academic/creative)

    Returns:
        Writing improvement prompt
    """
    prompt = f"""
Improve this text to be more {style}:

{text}

Make it clear, concise, and {style}. Fix grammar and enhance readability.
"""
    return f"Use AI to improve writing with this prompt: {prompt}"


def generate_email_reply(original_email: str, tone: str = "professional") -> str:
    """
    Generate email reply prompt

    Args:
        original_email: The email to reply to
        tone: Reply tone (professional/friendly/formal)

    Returns:
        Email reply prompt
    """
    prompt = f"""
Generate a {tone} reply to this email:

{original_email}

Write a {tone} response that addresses all points.
"""
    return f"Use AI to draft email reply with this prompt: {prompt}"


def summarize_text(text: str, max_sentences: int = 3) -> str:
    """
    Summarize text using AI

    Args:
        text: Text to summarize
        max_sentences: Maximum sentences in summary

    Returns:
        AI-generated summary
    """
    prompt = f"""Summarize this text in {max_sentences} concise sentences. Capture only the key points:

{text}

Provide ONLY the summary text, no explanations or preamble."""

    # Call AI to generate actual summary
    summary = _call_groq(prompt, max_tokens=500)

    return summary


# ===== SCREEN READING & OCR =====

def analyze_screen_with_ai(task: str = "Describe what you see on screen") -> str:
    """
    Analyze current screen using AI vision (Gemini Vision)
    More powerful than OCR - understands charts, images, UI, etc.

    Args:
        task: What to analyze (e.g., "Analyze this chart", "Describe this code")

    Returns:
        AI analysis of screen content
    """
    prompt = f"""Look at this screenshot and {task}.

Provide a clear, detailed analysis focusing on the most important information visible."""

    # Use Gemini Vision to analyze screen
    analysis = _call_gemini_vision(prompt)

    return analysis


def _configure_tesseract() -> bool:
    """
    Configure Tesseract OCR path for Windows
    
    Returns:
        True if Tesseract is found and configured, False otherwise
    """
    import pytesseract
    
    # Common Tesseract installation paths on Windows
    tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
    ]
    
    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    
    # Check if tesseract is in PATH
    import shutil
    if shutil.which("tesseract"):
        return True
    
    return False


def read_screen_text() -> str:
    """
    Extract all text from current screen using OCR (Tesseract)

    Returns:
        Extracted text or error message
    """
    try:
        import pytesseract
        from PIL import Image
        
        # Configure Tesseract path
        if not _configure_tesseract():
            return (
                "Error: Tesseract OCR is not installed.\n"
                "Please install from: https://github.com/UB-Mannheim/tesseract/wiki\n"
                "After installation, make sure tesseract.exe is in your PATH or installed in Program Files."
            )
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        
        # Extract text
        text = pytesseract.image_to_string(screenshot)
        
        if not text.strip():
            return "No text found on screen"
        
        return f"Screen text:\n{text.strip()}"
        
    except ImportError:
        return "Error: pytesseract not installed. Run: pip install pytesseract"
    except Exception as e:
        return f"Error reading screen: {str(e)}"


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from image file using OCR (Tesseract)

    Args:
        image_path: Path to image file

    Returns:
        Extracted text
    """
    try:
        import pytesseract
        from PIL import Image
        
        # Configure Tesseract path
        if not _configure_tesseract():
            return (
                "Error: Tesseract OCR is not installed.\n"
                "Please install from: https://github.com/UB-Mannheim/tesseract/wiki\n"
                "After installation, make sure tesseract.exe is in your PATH or installed in Program Files."
            )
        
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        
        if not text.strip():
            return f"No text found in {image_path}"
        
        return f"Extracted text from {image_path}:\n{text.strip()}"
        
    except ImportError:
        return "Error: pytesseract not installed. Run: pip install pytesseract"
    except Exception as e:
        return f"Error extracting text: {str(e)}"


# ===== QUICK AI TASKS =====

def translate_text(text: str, target_language: str) -> str:
    """
    Generate translation prompt

    Args:
        text: Text to translate
        target_language: Target language

    Returns:
        Translation prompt
    """
    prompt = f"""
Translate this text to {target_language}:

{text}

Provide accurate translation maintaining the original meaning.
"""
    return f"Use AI to translate with this prompt: {prompt}"


def generate_code(description: str, language: str = "python") -> str:
    """
    Generate code generation prompt

    Args:
        description: What the code should do
        language: Programming language

    Returns:
        Code generation prompt
    """
    prompt = f"""
Write {language} code to: {description}

Requirements:
1. Clean, readable code
2. Include comments
3. Handle errors
4. Follow best practices
"""
    return f"Use AI to generate code with this prompt: {prompt}"


def answer_question(question: str, context: Optional[str] = None) -> str:
    """
    Generate question answering prompt

    Args:
        question: Question to answer
        context: Additional context (optional)

    Returns:
        Question answering prompt
    """
    if context:
        prompt = f"""
Answer this question using the provided context:

QUESTION: {question}

CONTEXT:
{context}

Provide a clear, accurate answer.
"""
    else:
        prompt = f"""
Answer this question:

{question}

Provide a clear, accurate, and helpful answer.
"""
    return f"Use AI to answer with this prompt: {prompt}"


def brainstorm_ideas(topic: str, count: int = 5) -> str:
    """
    Generate brainstorming prompt

    Args:
        topic: Topic to brainstorm about
        count: Number of ideas to generate

    Returns:
        Brainstorming prompt
    """
    prompt = f"""
Generate {count} creative ideas for: {topic}

Provide diverse, innovative, and practical ideas.
"""
    return f"Use AI to brainstorm with this prompt: {prompt}"


# ===== DOCUMENT ANALYSIS =====

def analyze_document_structure() -> str:
    """
    Take screenshot and analyze document structure
    Useful for understanding document layout
    """
    try:
        screenshot_path = Path.home() / "glow_doc_screenshot.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)

        return f"Document screenshot saved: {screenshot_path}. Use vision model to analyze structure."
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"


def extract_key_points() -> str:
    """
    Extract key points from visible content on screen
    """
    try:
        # Read screen text
        text_result = read_screen_text()

        if "Error" in text_result or "No text" in text_result:
            return text_result

        prompt = f"""
Extract the key points from this text:

{text_result}

Provide a bulleted list of main points.
"""
        return f"Use AI to extract key points with this prompt: {prompt}"
    except Exception as e:
        return f"Error extracting key points: {str(e)}"
