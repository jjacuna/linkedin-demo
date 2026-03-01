"""
LinkedIn Post Generator — Flask Backend
Generates LinkedIn posts using OpenRouter (Gemini 2.5 Flash)
and professional images using Kie.ai Nano Banana.
"""

import json
import logging
import os
import time

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
KIE_API_KEY = os.getenv("KIE_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "google/gemini-2.5-flash"

KIE_CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
KIE_RECORD_INFO_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"

KIE_POLL_INTERVAL_SECONDS = 2
KIE_POLL_TIMEOUT_SECONDS = 120

VEO_GENERATE_URL = "https://api.kie.ai/api/v1/veo/generate"
VEO_POLL_URL = "https://api.kie.ai/api/v1/veo/get-1080p-video"
VEO_MODEL = "veo-3-1"
VEO_POLL_INTERVAL_SECONDS = 20
VEO_POLL_TIMEOUT_SECONDS = 300

VEO_SYSTEM_PROMPT = """You are a video prompt engineer specializing in Google Veo 3.1.

Given a topic or idea, write a single detailed video generation prompt optimized for Veo 3.1.

Your prompt must:
- Be 2-4 sentences describing the visual scene in rich detail
- Include camera movement (e.g., slow dolly in, aerial drone shot, cinematic tracking shot)
- Specify lighting and mood (e.g., golden hour, soft diffused light, dramatic shadows)
- Describe the subject, environment, and atmosphere clearly
- Specify a visual style (e.g., photorealistic, documentary, commercial, cinematic)
- Be suitable for a 16:9 professional video

Return ONLY the video prompt text. No quotes, no explanation, no extra text."""

SYSTEM_PROMPT = """You are a LinkedIn ghostwriter and visual content strategist.

You will receive two inputs:
1. A business persona — who the person is, what they do, and their call-to-action.
2. A content idea — the topic or angle for the post.

Your job:
1. Write an engaging LinkedIn post in the persona's authentic voice. Structure it with:
   - A strong hook line (first 1-2 lines that make people stop scrolling)
   - A compelling body with short paragraphs, line breaks for readability, and storytelling or insight
   - A clear call-to-action at the end
   - Relevant hashtags (3-5)
2. Generate an image prompt for Nano Banana image generation. The image should be:
   - 1:1 square aspect ratio
   - Professional and visually engaging
   - Relevant to the post topic
   - Clean, modern style suitable for LinkedIn

Return ONLY valid JSON with no markdown formatting, no code fences, no extra text:
{"post": "the full linkedin post text here", "imagePrompt": "the image generation prompt here"}"""


def _validate_api_keys():
    """Check that required API keys are configured."""
    missing = []
    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if not KIE_API_KEY:
        missing.append("KIE_API_KEY")
    return missing


def _call_openrouter(persona: str, content_idea: str) -> dict:
    """Call OpenRouter with persona and content idea, return parsed JSON with post and imagePrompt."""
    user_message = (
        f"Business Persona:\n{persona}\n\n"
        f"Content Idea:\n{content_idea}"
    )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7,
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=60)
    response.raise_for_status()

    data = response.json()
    raw_content = data["choices"][0]["message"]["content"]

    # Strip markdown code fences if the model wraps its output
    cleaned = raw_content.strip()
    if cleaned.startswith("```"):
        first_newline = cleaned.index("\n")
        cleaned = cleaned[first_newline + 1:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    result = json.loads(cleaned)

    if "post" not in result or "imagePrompt" not in result:
        raise ValueError("OpenRouter response missing required fields 'post' or 'imagePrompt'")

    return result


def _create_kie_task(image_prompt: str) -> str:
    """Create a Kie.ai Nano Banana image generation task. Returns the taskId."""
    payload = {
        "model": "nano-banana-pro",
        "input": {
            "prompt": image_prompt,
            "aspect_ratio": "1:1",
            "resolution": "1K",
            "output_format": "png",
        },
    }

    headers = {
        "Authorization": f"Bearer {KIE_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(KIE_CREATE_TASK_URL, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    logger.info("Kie.ai createTask response: %s", json.dumps(data, indent=2))

    if data.get("code") != 200:
        error_msg = data.get("message") or data.get("msg") or json.dumps(data)
        raise RuntimeError(f"Kie.ai createTask failed: {error_msg}")

    task_id = data["data"]["taskId"]
    return task_id


def _poll_kie_task(task_id: str) -> str:
    """Poll Kie.ai until the task succeeds or times out. Returns the first image URL."""
    headers = {
        "Authorization": f"Bearer {KIE_API_KEY}",
    }

    elapsed = 0
    while elapsed < KIE_POLL_TIMEOUT_SECONDS:
        time.sleep(KIE_POLL_INTERVAL_SECONDS)
        elapsed += KIE_POLL_INTERVAL_SECONDS

        response = requests.get(
            KIE_RECORD_INFO_URL,
            params={"taskId": task_id},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        task_data = data.get("data", {})
        state = task_data.get("state", "unknown")

        logger.info("Kie.ai task %s state: %s (elapsed %ds)", task_id, state, elapsed)

        if state == "success":
            result_json_str = task_data.get("resultJson", "")
            result_json = json.loads(result_json_str)
            urls = result_json.get("resultUrls", [])
            if not urls:
                raise RuntimeError("Kie.ai task succeeded but returned no image URLs")
            return urls[0]

        if state == "fail":
            raise RuntimeError(f"Kie.ai task {task_id} failed during image generation")

    raise TimeoutError(f"Kie.ai task {task_id} timed out after {KIE_POLL_TIMEOUT_SECONDS}s")


def _generate_image(image_prompt: str) -> str | None:
    """Create a Kie.ai task and poll until completion. Returns the image URL or None on failure."""
    try:
        task_id = _create_kie_task(image_prompt)
        logger.info("Kie.ai task created: %s", task_id)
        image_url = _poll_kie_task(task_id)
        logger.info("Kie.ai image generated: %s", image_url)
        return image_url
    except Exception:
        logger.exception("Image generation failed")
        return None


# ---------------------------------------------------------------------------
# Veo 3.1 Video Generation
# ---------------------------------------------------------------------------

def _generate_veo_prompt(topic: str) -> str:
    """Use OpenRouter to craft an optimized Veo 3.1 video prompt from a topic."""
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": VEO_SYSTEM_PROMPT},
            {"role": "user", "content": topic},
        ],
        "temperature": 0.8,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def _create_veo_task(video_prompt: str) -> str:
    """Submit a Veo 3.1 generation task. Returns the taskId."""
    payload = {
        "prompt": video_prompt,
        "model": VEO_MODEL,
        "aspect_ratio": "16:9",
    }
    headers = {
        "Authorization": f"Bearer {KIE_API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.post(VEO_GENERATE_URL, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    logger.info("Veo createTask response: %s", json.dumps(data, indent=2))
    if data.get("code") != 200:
        error_msg = data.get("message") or data.get("msg") or json.dumps(data)
        raise RuntimeError(f"Veo generate failed: {error_msg}")
    return data["data"]["taskId"]


def _poll_veo_task(task_id: str) -> str:
    """Poll Veo 1080p endpoint until the video is ready. Returns the video URL."""
    headers = {"Authorization": f"Bearer {KIE_API_KEY}"}
    elapsed = 0
    while elapsed < VEO_POLL_TIMEOUT_SECONDS:
        time.sleep(VEO_POLL_INTERVAL_SECONDS)
        elapsed += VEO_POLL_INTERVAL_SECONDS
        response = requests.get(
            VEO_POLL_URL,
            params={"taskId": task_id},
            headers=headers,
            timeout=30,
        )
        logger.info("Veo poll task %s — HTTP %s (elapsed %ds)", task_id, response.status_code, elapsed)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                result_url = (data.get("data") or {}).get("resultUrl")
                if result_url:
                    return result_url
        # Non-200 or not ready yet — keep polling
    raise TimeoutError(f"Veo task {task_id} timed out after {VEO_POLL_TIMEOUT_SECONDS}s")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the main application page."""
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """Generate a LinkedIn post and accompanying image from persona + content idea."""
    missing_keys = _validate_api_keys()
    if missing_keys:
        logger.error("Missing API keys: %s", ", ".join(missing_keys))
        return jsonify({"error": f"Server misconfiguration: missing {', '.join(missing_keys)}"}), 500

    data = request.get_json(silent=True) or {}

    # Persona can be an object {whoYouAre, whatYouDo, callToAction} or a plain string
    raw_persona = data.get("persona", "")
    if isinstance(raw_persona, dict):
        parts = []
        if raw_persona.get("whoYouAre"):
            parts.append(f"Who I am: {raw_persona['whoYouAre']}")
        if raw_persona.get("whatYouDo"):
            parts.append(f"What I do: {raw_persona['whatYouDo']}")
        if raw_persona.get("callToAction"):
            parts.append(f"Call to action: {raw_persona['callToAction']}")
        persona = "\n".join(parts).strip()
    else:
        persona = (raw_persona or "").strip()

    content_idea = (data.get("contentIdea") or data.get("content") or "").strip()

    if not persona:
        return jsonify({"error": "Persona is required"}), 400
    if not content_idea:
        return jsonify({"error": "Content idea is required"}), 400

    # Step 1: Generate post text and image prompt via OpenRouter
    try:
        ai_result = _call_openrouter(persona, content_idea)
    except requests.exceptions.HTTPError as exc:
        logger.exception("OpenRouter HTTP error")
        status = exc.response.status_code if exc.response is not None else 502
        return jsonify({"error": "Text generation service returned an error. Please try again."}), status
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        logger.exception("Failed to parse OpenRouter response")
        return jsonify({"error": "Failed to parse AI response. Please try again."}), 502
    except requests.exceptions.RequestException:
        logger.exception("OpenRouter request failed")
        return jsonify({"error": "Could not reach text generation service. Please try again."}), 502

    post_text = ai_result["post"]
    image_prompt = ai_result["imagePrompt"]

    # Step 2: Generate image via Kie.ai (non-blocking failure)
    image_url = _generate_image(image_prompt)

    return jsonify({
        "post": post_text,
        "imagePrompt": image_prompt,
        "imageUrl": image_url,
    })


@app.route("/regenerate-image", methods=["POST"])
def regenerate_image():
    """Regenerate an image from an existing image prompt."""
    missing_keys = _validate_api_keys()
    if "KIE_API_KEY" in missing_keys:
        logger.error("Missing KIE_API_KEY")
        return jsonify({"error": "Server misconfiguration: missing KIE_API_KEY"}), 500

    data = request.get_json(silent=True) or {}
    image_prompt = (data.get("imagePrompt") or "").strip()

    if not image_prompt:
        return jsonify({"error": "Image prompt is required"}), 400

    image_url = _generate_image(image_prompt)

    if image_url is None:
        return jsonify({"error": "Image generation failed. Please try again."}), 502

    return jsonify({
        "imageUrl": image_url,
        "imagePrompt": image_prompt,
    })


@app.route("/generate-video", methods=["POST"])
def generate_video():
    """Generate a Veo 3.1 video from a topic: craft prompt via AI, submit to Kie.ai, poll for result."""
    missing_keys = _validate_api_keys()
    if missing_keys:
        return jsonify({"error": f"Server misconfiguration: missing {', '.join(missing_keys)}"}), 500

    data = request.get_json(silent=True) or {}
    topic = (data.get("topic") or "").strip()
    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    # Step 1: Generate an optimized Veo 3.1 prompt
    try:
        video_prompt = _generate_veo_prompt(topic)
        logger.info("Veo prompt generated: %s", video_prompt)
    except requests.exceptions.RequestException:
        logger.exception("OpenRouter request failed for Veo prompt")
        return jsonify({"error": "Could not generate video prompt. Please try again."}), 502

    # Step 2: Submit to Veo 3.1
    try:
        task_id = _create_veo_task(video_prompt)
        logger.info("Veo task created: %s", task_id)
    except (requests.exceptions.RequestException, RuntimeError):
        logger.exception("Veo task creation failed")
        return jsonify({"error": "Video generation service failed. Please try again."}), 502

    # Step 3: Poll until ready
    try:
        video_url = _poll_veo_task(task_id)
        logger.info("Veo video ready: %s", video_url)
    except TimeoutError:
        logger.error("Veo task %s timed out", task_id)
        return jsonify({"error": "Video generation timed out. Please try again."}), 504
    except Exception:
        logger.exception("Veo polling failed")
        return jsonify({"error": "Video generation failed during processing."}), 502

    return jsonify({"videoUrl": video_url, "videoPrompt": video_prompt})


@app.route("/health")
def health():
    """Health check endpoint."""
    missing_keys = _validate_api_keys()
    return jsonify({
        "status": "healthy" if not missing_keys else "degraded",
        "missingKeys": missing_keys,
    })


if __name__ == "__main__":
    logger.info("Starting LinkedIn Post Generator on port 5001")
    app.run(host="0.0.0.0", port=5001, debug=True)
