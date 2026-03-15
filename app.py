"""
Golden Crumb Bakery — Social Media Content Generator
Generates platform-specific social media posts using OpenRouter (Gemini 2.5 Flash)
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
VEO_MODEL = "veo3_fast"
VEO_POLL_INTERVAL_SECONDS = 20
VEO_POLL_TIMEOUT_SECONDS = 300

VEO_SYSTEM_PROMPT = """You are a video prompt engineer specializing in Google Veo 3.1, creating cinematic content for an artisan cookie store brand.

Given a topic or idea, write a single detailed video generation prompt optimized for Veo 3.1 that showcases the irresistible, handcrafted quality of premium cookies.

Your prompt must:
- Be 2-4 sentences describing the visual scene in rich, mouth-watering detail
- Feature cookies, baked goods, or bakery atmosphere as the hero of the shot
- Include camera movement that builds desire (e.g., slow macro dolly into a chocolate chip cookie, overhead pour shot of melted chocolate, close-up steam rising from fresh-baked cookies)
- Specify warm, inviting lighting (e.g., golden hour bakery window light, soft warm studio lighting with caramel tones, candlelit rustic ambiance)
- Convey warmth, indulgence, and artisan craftsmanship
- Specify a visual style (e.g., high-end food commercial, slow-motion cinematic, cozy lifestyle brand)
- Be suitable for a 16:9 professional video

Return ONLY the video prompt text. No quotes, no explanation, no extra text."""

BAKERY_PERSONA = """Golden Crumb Bakery — a premium artisan cookie shop in Austin, TX.
We handcraft small-batch cookies, brownies, and seasonal baked goods using locally sourced butter, real vanilla, and Belgian chocolate.
Our brand is warm, community-driven, and unapologetically indulgent.
We offer walk-in ordering, local delivery, custom cookie boxes for events, and corporate catering.
Website: goldencrumbbakery.com | Instagram: @goldencrumbbakery
Call to action: Order online or visit us in East Austin."""

PLATFORM_INSTRUCTIONS = {
    "linkedin": {
        "name": "LinkedIn",
        "char_limit": 3000,
        "instructions": """Write a professional yet warm LinkedIn post. Structure it with:
- A powerful hook (first 1-2 lines) that connects the bakery story to business insights, entrepreneurship, or community
- A compelling body using short paragraphs and line breaks — weave in storytelling, behind-the-scenes, lessons from running a food business
- A persuasive call-to-action
- Relevant hashtags (3-5, mix of #SmallBusiness #ArtisanBakery #FoodBusiness #Austin #Cookies)
Tone: Professional, authentic, story-driven. Show the human side of the business.""",
    },
    "instagram": {
        "name": "Instagram",
        "char_limit": 2200,
        "instructions": """Write a captivating Instagram caption. Structure it with:
- An attention-grabbing first line (this shows in the preview before "more")
- Engaging body with personality, emojis used naturally (not excessively), and line breaks
- A call-to-action (e.g., "Tag someone who needs cookies", "Link in bio to order", "Drop a cookie emoji if you agree")
- Relevant hashtags (15-20 mix of niche and broad: #CookiesOfInstagram #AustinFoodie #ArtisanCookies #BakeryLife #FoodPorn #SmallBatchBaking #ATXEats etc.)
Tone: Fun, visual, craving-inducing, community-oriented.""",
    },
    "twitter": {
        "name": "X / Twitter",
        "char_limit": 280,
        "instructions": """Write a punchy tweet (max 280 characters including hashtags). Make it:
- Concise and scroll-stopping
- Conversational, witty, or mouth-watering
- Include 1-3 relevant hashtags only if they fit naturally
- Can include a CTA like "RT if you agree" or "Link in bio"
Tone: Snappy, relatable, sometimes funny. Think short and shareable.""",
    },
    "facebook": {
        "name": "Facebook",
        "char_limit": 5000,
        "instructions": """Write an engaging Facebook post. Structure it with:
- A warm, conversational opening that feels like talking to a neighbor
- Storytelling body — behind-the-scenes, customer stories, seasonal specials, community involvement
- A clear call-to-action (order link, visit us, comment below)
- 3-5 relevant hashtags
Tone: Friendly, community-focused, inviting. Like chatting with your favorite local shop owner.""",
    },
}

SYSTEM_PROMPT_TEMPLATE = """You are a social media content creator and brand strategist for an artisan bakery.

Here is the business you are writing for:
{persona}

Platform: {platform_name}
Platform guidelines:
{platform_instructions}

Your job:
1. Write an engaging social media post optimized for {platform_name} that drives business growth, brand affinity, and cravings.
2. Generate an image prompt for Nano Banana image generation that makes viewers crave the product. The image should be:
   - 1:1 square aspect ratio
   - Feature beautifully styled cookies or bakery scenes — warm tones, rustic wood surfaces, artisan packaging, melted chocolate drizzles, stacked cookie towers
   - Evoke indulgence, warmth, and handcrafted quality
   - Shot in a clean, editorial food photography style with soft natural lighting
   - Professional and shareable on {platform_name}

Return ONLY valid JSON with no markdown formatting, no code fences, no extra text:
{{"post": "the full social media post text here", "imagePrompt": "the image generation prompt here"}}"""


def _validate_api_keys():
    """Check that required API keys are configured."""
    missing = []
    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if not KIE_API_KEY:
        missing.append("KIE_API_KEY")
    return missing


def _call_openrouter(content_idea: str, platform: str = "instagram") -> dict:
    """Call OpenRouter with content idea and platform, return parsed JSON with post and imagePrompt."""
    platform_config = PLATFORM_INSTRUCTIONS.get(platform, PLATFORM_INSTRUCTIONS["instagram"])

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        persona=BAKERY_PERSONA,
        platform_name=platform_config["name"],
        platform_instructions=platform_config["instructions"],
    )

    user_message = f"Content Idea:\n{content_idea}"

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
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

    # Detect model refusals before attempting JSON parse
    if not cleaned.startswith("{"):
        logger.error("OpenRouter returned a refusal or non-JSON response: %r", raw_content)
        raise ValueError(f"AI refused or returned unexpected content: {cleaned[:200]}")

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.error("OpenRouter returned non-JSON content: %r", raw_content)
        raise

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
        return jsonify({"error": f"Server misconfiguration: missing {', '.join(missing_keys)}"}), 503

    data = request.get_json(silent=True) or {}

    content_idea = (data.get("contentIdea") or data.get("content") or "").strip()
    platform = (data.get("platform") or "instagram").strip().lower()

    if platform not in PLATFORM_INSTRUCTIONS:
        return jsonify({"error": f"Unsupported platform: {platform}"}), 400
    if not content_idea:
        return jsonify({"error": "Content idea is required"}), 400

    # Step 1: Generate post text and image prompt via OpenRouter
    try:
        ai_result = _call_openrouter(content_idea, platform)
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

    platform_config = PLATFORM_INSTRUCTIONS[platform]
    return jsonify({
        "post": post_text,
        "imagePrompt": image_prompt,
        "imageUrl": image_url,
        "platform": platform,
        "platformName": platform_config["name"],
        "charLimit": platform_config["char_limit"],
    })


@app.route("/regenerate-image", methods=["POST"])
def regenerate_image():
    """Regenerate an image from an existing image prompt."""
    missing_keys = _validate_api_keys()
    if "KIE_API_KEY" in missing_keys:
        logger.error("Missing KIE_API_KEY")
        return jsonify({"error": "Server misconfiguration: missing KIE_API_KEY"}), 503

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
        return jsonify({"error": f"Server misconfiguration: missing {', '.join(missing_keys)}"}), 503

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
    port = int(os.getenv("PORT", 5001))
    logger.info("Starting Golden Crumb Social Media Generator on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=True)
