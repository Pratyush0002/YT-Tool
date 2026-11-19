import os
import sys
import json
import time
import uuid
import datetime
from pathlib import Path
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename

# YouTube Uploader Module
import youtube_uploader

# Optional OpenCV for video metadata in fallback mode
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
DATA_FOLDER = BASE_DIR / "data"
CONFIG_FILE = BASE_DIR / "config.json"
HISTORY_FILE = DATA_FOLDER / "history.json"

UPLOAD_FOLDER.mkdir(exist_ok=True)
DATA_FOLDER.mkdir(exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "shortsviral_secret_key_random_" + str(uuid.uuid4())
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 150 * 1024 * 1024

ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm", "m4v"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_saved_api_key():
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("gemini_api_key", "").strip()
        except Exception:
            pass
    return ""

def save_api_key(api_key):
    try:
        data = {}
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["gemini_api_key"] = api_key.strip()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_to_history(record):
    try:
        history = load_history()
        history.insert(0, record)
        history = history[:30]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")

def get_video_info(file_path):
    info = {"duration": 0, "width": 0, "height": 0, "fps": 0, "aspect_ratio": "9:16"}
    if not CV2_AVAILABLE:
        return info
    try:
        cap = cv2.VideoCapture(str(file_path))
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = round(frame_count / fps, 1) if fps > 0 else 0
            cap.release()
            info["duration"] = duration
            info["width"] = width
            info["height"] = height
            info["fps"] = round(fps, 1)
            if height > width:
                info["aspect_ratio"] = "Vertical (Shorts 9:16)"
            else:
                info["aspect_ratio"] = "Horizontal (Landscape)"
    except Exception as e:
        print(f"OpenCV metadata error: {e}")
    return info

def detect_fallback_category(text):
    text_lower = text.lower()
    if any(k in text_lower for k in ["game", "gaming", "bgmi", "freefire", "minecraft", "gta", "play"]):
        return "20", "Gaming (गेमिंग)"
    if any(k in text_lower for k in ["dog", "cat", "pet", "animal", "puppy", "kitten"]):
        return "15", "Pets & Animals (जानवर & पालतू)"
    if any(k in text_lower for k in ["song", "music", "singing", "dance", "beat", "rap"]):
        return "10", "Music (संगीत / म्यूज़िक)"
    if any(k in text_lower for k in ["car", "bike", "vehicle", "race", "motor"]):
        return "2", "Autos & Vehicles (गाड़ियाँ & वाहन)"
    if any(k in text_lower for k in ["cricket", "football", "gym", "workout", "match"]):
        return "17", "Sports (खेलकूद / स्पोर्ट्स)"
    if any(k in text_lower for k in ["tech", "phone", "mobile", "ai", "gadget", "laptop"]):
        return "28", "Science & Technology (साइंस & टेक)"
    if any(k in text_lower for k in ["news", "khabar", "politics"]):
        return "25", "News & Politics (समाचार)"
    if any(k in text_lower for k in ["vlog", "travel", "lifestyle", "daily"]):
        return "22", "People & Blogs (लोग & ब्लॉग्स)"
    if any(k in text_lower for k in ["learn", "fact", "education", "tips", "study", "gk"]):
        return "27", "Education (शिक्षा / ज्ञान)"
    # Default to Comedy for funny shorts, or Entertainment
    return "23", "Comedy (कॉमेडी / हास्य)"

def generate_fallback_content(filename, style="Desi Comedy", language="Hinglish", viral_strategy="max_retention", notes="", category_pref="auto"):
    name_clean = Path(filename).stem.replace("_", " ").replace("-", " ")
    topic = notes if notes else name_clean

    if category_pref and category_pref != "auto":
        cat_id = youtube_uploader.resolve_category_id(category_pref)
        cat_name = youtube_uploader.YOUTUBE_CATEGORIES.get(cat_id, "Entertainment")
    else:
        cat_id, cat_name = detect_fallback_category(topic + " " + style)

    return {
        "is_demo": True,
        "summary": f"वीडियो '{topic}' का सटीक विश्लेषण। AI ने वीडियो के कंटेंट के अनुसार सबसे उपयुक्त यूट्यूब कैटेगरी '{cat_name}' चुनी है।",
        "hook_analysis": "पहले 2 सेकंड में चौंकने वाला विजुअल + सस्पेंस हुक जो दर्शक को स्वाइप करने से रोकेगा।",
        "category_id": cat_id,
        "category_name": cat_name,
        "category_reason": f"वीडियो के टॉपिक और दृश्य के आधार पर '{cat_name}' कैटेगरी वीडियो को सही दर्शकों तक पहुँचाएगी।",
        "viral_score": 98,
        "metrics_breakdown": {
            "ctr_potential": "99% (High Curiosity Emojis)",
            "retention_power": "97% (Loop & Twist Hook)",
            "shareability": "98% (WhatsApp Viral Desi Relatable)",
            "algorithm_seo": "100% (500 Chars Tag Matrix)"
        },
        "loop_hack": "वीडियो के अंतिम सेकंड को पहले सेकंड से जोड़ें ताकि वीडियो लूप में 120%+ बार देखा जाए!",
        "best_title": f"Wait For The End! 💀🤣 ऐसा कभी नहीं देखा #{topic.replace(' ', '')[:10]} #shorts",
        "titles": [
            {
                "title": f"Wait For The End! 💀🤣 ऐसा कभी नहीं देखा #shorts",
                "type": "🔥 1. Wait For End (सस्पेंस & ट्विस्ट)",
                "ctr_score": 99,
                "hook_reason": "यूट्यूब शॉर्ट्स का नंबर-1 वायरल फॉर्मूला। व्यूअर आखिरी सेकंड तक रुकता है।"
            },
            {
                "title": f"आख़िरी 3 सेकंड भूलकर भी मत देखना! 🛑😭 #shorts",
                "type": "⚠️ 2. Reverse Psychology (चेतावनी हुक)",
                "ctr_score": 98,
                "hook_reason": "इंसानी दिमाग 'मत देखना' सुनकर तुरंत देखता है।"
            },
            {
                "title": f"हर किसी के साथ ऐसा होता है 🤦‍♂️😂 #{topic.replace(' ', '')[:10]} #viral",
                "type": "🤝 3. Desi Relatable (शेयर मैग्नेट)",
                "ctr_score": 96,
                "hook_reason": "लोग अपने दोस्तों और फैमिली ग्रुप्स में तुरंत शेयर करते हैं।"
            },
            {
                "title": f"ये क्या कर दिया भाई?! 😱💀 #funny #ytshorts",
                "type": "⚡ 4. Shock & Plot Twist (शॉकिंग रिएक्शन)",
                "ctr_score": 97,
                "hook_reason": "शॉकिंग इमोजी शॉर्ट्स फीड में स्क्रॉल करते हाथ को तुरंत रोकती है।"
            },
            {
                "title": f"ऐसी हरकत कभी नहीं देखी 🤣🔥 #shorts",
                "type": "🎯 5. Short & Punchy (क्लीन मोबाइल व्यू)",
                "ctr_score": 95,
                "hook_reason": "मोबाइल नोटिफिकेशन में बिना कटे पूरा दिखता है।"
            }
        ],
        "description": f"""लास्ट वाला रिएक्शन मिस मत करना! 💀🤣 अंत तक देखना और बताना आपके साथ भी ऐसा हुआ है क्या? 👇

😂👇 कमेंट में बताओ:
क्या आपके साथ भी कभी ऐसा हुआ है? सच-सच बताना! 🤣 

📲 अपने उस एक दोस्त को ज़रूर शेयर करो जो ऐसा ही है! 🤝😂

❤️ अगर मज़ा आया हो तो वीडियो को LIKE करें और CHANNEL को SUBSCRIBE करना न भूलें! 🔔🔥

#shorts #comedy #funny #viral #trendingshorts #ytshorts #desicomedy #viralvideo #lol #humor #explore #trending""",
        "tags": [
            "shorts", "comedy shorts", "funny shorts", "hindi comedy", "desi comedy",
            "funny video", "viral comedy", "relatable comedy", "youtube shorts",
            "trending shorts", "laugh", "meme shorts", "comedy video hindi",
            "desi jokes", "funny moments", "humor shorts", "viral yt shorts",
            "comedy reels", "hilarious video", "wait for end", "funny short video"
        ],
        "tags_string": "shorts, comedy shorts, funny shorts, hindi comedy, desi comedy, funny video, viral comedy, relatable comedy, youtube shorts, trending shorts, laugh, meme shorts, comedy video hindi, desi jokes, funny moments, humor shorts, viral yt shorts, comedy reels, hilarious video, wait for end, funny short video, funny reels, comedy club, desi funny video, top funny shorts",
        "hashtags": ["#shorts", "#comedy", "#funny", "#viral", "#trendingshorts", "#ytshorts", "#desicomedy", "#humor", "#viralvideo"],
        "pinned_comment": "आख़िरी 3 सेकंड में किस-किस की हंसी छूटी? 😂 झूठ मत बोलना, कमेंट में बताओ! 👇💀",
        "best_time_to_post": "शाम 6:00 PM से 8:30 PM (पीक ऑडियंस ट्रैफिक टाइम)",
        "thumbnail_frame_tip": "शॉर्ट्स अपलोड करते समय वही फ्रेम चुनें जहाँ मुख्य कैरेक्टर का सबसे अजीब या फनी चेहरा बना हो!"
    }

def get_viral_prompt(style_prompt, lang_prompt, viral_strategy_prompt, category_pref, notes_prompt):
    category_instruction = ""
    if category_pref and category_pref != "auto":
        category_instruction = f"User explicitly requested YouTube Category ID: {category_pref}. Use this category unless completely inaccurate."
    else:
        category_instruction = """DYNAMIC CATEGORY DETECTION:
Carefully inspect the video's actual subject matter and determine the EXACT best-fitting official YouTube Category ID and Name:
- '23': Comedy (Standup, pranks, jokes, comedy skits, laughing clips)
- '24': Entertainment (Movies, pop culture, drama, reactions, talent)
- '20': Gaming (Gameplays, BGMI, FreeFire, Minecraft, GTA, gaming memes)
- '22': People & Blogs (Personal vlogs, daily life, motivational, lifestyle)
- '15': Pets & Animals (Dogs, cats, wildlife, pet humor)
- '10': Music (Songs, dance, rapping, musical performances, beats)
- '28': Science & Technology (Gadgets, AI, coding, experiments)
- '27': Education (Facts, tips, tutorials, knowledge, science facts)
- '26': Howto & Style (Fashion, beauty, cooking, DIY)
- '17': Sports (Cricket, football, gym, fitness, sports moments)
- '1': Film & Animation (Short films, CGI, 3D/2D animation, anime clips)
- '2': Autos & Vehicles (Cars, bikes, racing, auto reviews)
- '25': News & Politics (News updates, current affairs)
Output the chosen category_id (e.g. '23', '24', '20', etc.) and category_name.
"""

    return f"""You are the world's #1 viral YouTube Shorts algorithm growth specialist and metadata director.
Analyze this video thoroughly and produce the #1 MOST VIRAL, algorithm-cracking metadata package.
The creator wants ZERO manual work. Everything must be automatic, elite, and ready for immediate publishing to YouTube.

Preferences:
- Vibe/Style: {style_prompt}
- Language: {lang_prompt}
- Strategy: {viral_strategy_prompt}
- Context: {notes_prompt}

{category_instruction}

MANDATORY RULES:
1. Dynamic Category: Select the exact official YouTube category ID and name that best fits this specific video so the YouTube algorithm reaches the exact target audience!
2. Best Title: Pick the single absolute #1 viral title with high-CTR emojis (💀🤣, 🛑😭, 😱🔥) and '#shorts'.
3. 5 Title Options: Provide 5 distinct viral archetypes (Wait for end, Warning reverse psychology, Desi relatable, Shock reaction, Short punchy).
4. Description: 5-part algorithmic formula (Hook with emojis, Story tease, Comment bait question, WhatsApp share CTA, Subscribe CTA, 12-15 trending hashtags).
5. Tag Matrix: 18-25 high-traffic tags formatted in a comma-separated string strictly under 490 characters.
6. Loop Hack: Instructions on how to make this video loop seamlessly.

Strictly output valid JSON matching this schema:
{{
  "summary": "1-2 sentences summarizing the video content and punchline.",
  "hook_analysis": "Explanation of the first 2-3 seconds hook.",
  "category_id": "23",
  "category_name": "Comedy (कॉमेडी)",
  "category_reason": "Brief 1-line reason why this YouTube category was selected based on the video content.",
  "viral_score": 98,
  "metrics_breakdown": {{
    "ctr_potential": "99% (High Curiosity Emojis)",
    "retention_power": "97% (Loop & Twist Hook)",
    "shareability": "98% (WhatsApp Viral Desi Relatable)",
    "algorithm_seo": "100% (500 Chars Tag Matrix)"
  }},
  "loop_hack": "Advice on how to loop this video seamlessly.",
  "best_title": "The absolute #1 best viral title with emojis and #shorts tag ready for direct YouTube publishing",
  "titles": [
    {{
      "title": "Title with high-converting emojis and #shorts tag (Wait For End style)",
      "type": "🔥 1. Wait For End (सस्पेंस & ट्विस्ट)",
      "ctr_score": 99,
      "hook_reason": "Forces viewer to watch till last second."
    }},
    {{
      "title": "Title with warning emojis and #shorts (Reverse psychology)",
      "type": "⚠️ 2. Reverse Psychology (चेतावनी हुक)",
      "ctr_score": 98,
      "hook_reason": "Triggers instant curiosity."
    }},
    {{
      "title": "Desi Relatable title with emojis and #comedy",
      "type": "🤝 3. Desi Relatable (व्हाट्सएप शेयर मैग्नेट)",
      "ctr_score": 96,
      "hook_reason": "Audience shares on WhatsApp."
    }},
    {{
      "title": "Shocking title with emojis (😱💀) and #shorts",
      "type": "⚡ 4. Shock & Plot Twist (शॉकिंग रिएक्शन)",
      "ctr_score": 97,
      "hook_reason": "Stops thumbs from scrolling."
    }},
    {{
      "title": "Short Punchy Title (Max 45 chars)",
      "type": "🎯 5. Short & Punchy (क्लीन मोबाइल व्यू)",
      "ctr_score": 95,
      "hook_reason": "Perfect for mobile notifications."
    }}
  ],
  "description": "Full formatted description with opening hook, punchline tease, comment prompt, share CTA, subscribe CTA, and 10-15 viral hashtags.",
  "tags": [
    "shorts", "funny shorts", "hindi comedy", "viral shorts", "trending shorts"
  ],
  "tags_string": "Comma-separated string of all tags strictly under 490 characters total length.",
  "hashtags": [
    "#shorts", "#comedy", "#funny", "#viral", "#trendingshorts", "#ytshorts"
  ],
  "pinned_comment": "Funny comment for creator to pin.",
  "best_time_to_post": "शाम 6:00 PM से 8:30 PM IST",
  "thumbnail_frame_tip": "Specific advice on thumbnail frame selection."
}}
"""

def analyze_video_with_gemini(video_path, api_key, style, language, viral_strategy, category_pref="auto", notes=""):
    if not GENAI_AVAILABLE:
        raise ValueError("google-genai SDK is not installed.")

    client = genai.Client(api_key=api_key)

    print(f"Uploading {video_path} to Gemini...")
    video_file = client.files.upload(file=str(video_path))

    print(f"Processing video {video_file.name}...")
    max_wait = 120
    waited = 0
    while video_file.state.name == "PROCESSING" and waited < max_wait:
        time.sleep(3)
        waited += 3
        video_file = client.files.get(name=video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError("Gemini could not process the video file.")

    style_prompt = style if style else "Desi Comedy / Funny Relatable"
    lang_prompt = language if language else "Hinglish (Hindi + English)"
    strat_prompt = viral_strategy if viral_strategy else "Maximum Retention & Loop"
    notes_prompt = f"Creator context: {notes}" if notes else "No additional notes provided."

    system_prompt = get_viral_prompt(style_prompt, lang_prompt, strat_prompt, category_pref, notes_prompt)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[video_file, system_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.75,
            )
        )
        raw_text = response.text.strip()
        result = json.loads(raw_text)
        result["is_demo"] = False
        if not result.get("best_title") and result.get("titles"):
            result["best_title"] = result["titles"][0]["title"]

        # Ensure valid category ID
        raw_cat = result.get("category_id", "23")
        resolved_cat = youtube_uploader.resolve_category_id(raw_cat)
        result["category_id"] = resolved_cat
        if not result.get("category_name"):
            result["category_name"] = youtube_uploader.YOUTUBE_CATEGORIES.get(resolved_cat, "Entertainment")

        return result
    finally:
        try:
            client.files.delete(name=video_file.name)
            print(f"Cleaned up remote file {video_file.name}")
        except Exception as e:
            print(f"Error cleaning remote file: {e}")

# ----------------- ROUTES ----------------- #

@app.route("/")
def index():
    return render_template("index.html")

# --- Gemini API Config ---
@app.route("/api/config", methods=["GET", "POST"])
def config_api():
    if request.method == "POST":
        data = request.get_json() or {}
        key = data.get("apiKey", "").strip()
        if not key:
            return jsonify({"success": False, "error": "API Key cannot be empty"}), 400
        save_api_key(key)
        masked = key[:4] + "..." + key[-4:] if len(key) > 8 else "***"
        return jsonify({"success": True, "maskedKey": masked})
    else:
        saved_key = get_saved_api_key()
        has_key = bool(saved_key)
        masked = (saved_key[:4] + "..." + saved_key[-4:]) if len(saved_key) > 8 else ""
        return jsonify({"hasKey": has_key, "maskedKey": masked})

# --- YouTube Channel Connection Endpoints ---
@app.route("/api/youtube/status", methods=["GET"])
def youtube_status():
    connected, channel_info = youtube_uploader.is_youtube_connected()
    config = youtube_uploader.get_oauth_config()
    has_oauth_config = bool(config.get("client_id") and config.get("client_secret"))
    return jsonify({
        "connected": connected,
        "channel": channel_info,
        "hasOAuthConfig": has_oauth_config,
        "availableCategories": youtube_uploader.YOUTUBE_CATEGORIES
    })

@app.route("/api/youtube/config", methods=["POST"])
def youtube_save_config():
    data = request.get_json() or {}
    client_id = data.get("clientId", "").strip()
    client_secret = data.get("clientSecret", "").strip()
    if not client_id or not client_secret:
        return jsonify({"success": False, "error": "Client ID और Secret आवश्यक हैं"}), 400
    youtube_uploader.save_oauth_config(client_id, client_secret)
    return jsonify({"success": True})

@app.route("/api/youtube/auth-url", methods=["GET"])
def youtube_auth_url():
    try:
        redirect_uri = url_for("oauth2callback", _external=True)
        flow = youtube_uploader.create_oauth_flow(redirect_uri)
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )
        session["oauth_state"] = state
        return jsonify({"success": True, "authUrl": auth_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/oauth2callback")
def oauth2callback():
    state = session.get("oauth_state")
    redirect_uri = url_for("oauth2callback", _external=True)
    try:
        flow = youtube_uploader.create_oauth_flow(redirect_uri)
        flow.fetch_token(authorization_response=request.url)
        creds = flow.credentials
        
        with open(youtube_uploader.TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

        channel_info = youtube_uploader.fetch_and_save_channel_info(creds)
        print(f"Successfully connected YouTube channel: {channel_info.get('title') if channel_info else 'Unknown'}")
        return redirect("/?youtube_connected=true")
    except Exception as e:
        print(f"OAuth Callback Error: {e}")
        return redirect(f"/?youtube_error={str(e)}")

@app.route("/api/youtube/disconnect", methods=["POST"])
def youtube_disconnect():
    youtube_uploader.disconnect_youtube()
    return jsonify({"success": True})

# --- Main Video Analysis & Auto-Upload Route ---
@app.route("/api/analyze-video", methods=["POST"])
def analyze_video_route():
    if "video" not in request.files:
        return jsonify({"success": False, "error": "कोई वीडियो फ़ाइल नहीं मिली (No video file uploaded)"}), 400

    file = request.files["video"]
    if file.filename == "":
        return jsonify({"success": False, "error": "फ़ाइल का नाम खाली है"}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "कृपया मान्य वीडियो फ़ाइल चुनें (.mp4, .mov, .webm, .avi, .mkv)"}), 400

    style = request.form.get("style", "Desi Comedy / Relatable")
    language = request.form.get("language", "Hinglish (Hindi + English)")
    viral_strategy = request.form.get("viralStrategy", "max_retention")
    category_pref = request.form.get("category", "auto")
    notes = request.form.get("notes", "")
    req_api_key = request.form.get("apiKey", "").strip()
    
    auto_upload = request.form.get("autoUpload", "false").lower() == "true"
    privacy_status = request.form.get("privacyStatus", "public")

    api_key = req_api_key if req_api_key else get_saved_api_key()

    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())[:8]
    saved_filename = f"{unique_id}_{filename}"
    file_path = UPLOAD_FOLDER / saved_filename

    try:
        file.save(str(file_path))
        video_info = get_video_info(file_path)

        # 1. AI Analysis & Dynamic Category Detection
        if api_key:
            try:
                analysis = analyze_video_with_gemini(file_path, api_key, style, language, viral_strategy, category_pref, notes)
            except Exception as e:
                print(f"Gemini error: {e}")
                analysis = generate_fallback_content(filename, style, language, viral_strategy, notes, category_pref)
                analysis["error_note"] = f"Gemini API Error: {str(e)}"
        else:
            analysis = generate_fallback_content(filename, style, language, viral_strategy, notes, category_pref)

        # Determine final category
        final_category_id = analysis.get("category_id", "23")
        if category_pref and category_pref != "auto":
            final_category_id = youtube_uploader.resolve_category_id(category_pref)
            analysis["category_id"] = final_category_id
            analysis["category_name"] = youtube_uploader.YOUTUBE_CATEGORIES.get(final_category_id, "Entertainment")

        best_title = analysis.get("best_title")
        if not best_title and analysis.get("titles"):
            best_title = analysis["titles"][0]["title"]
        analysis["best_title"] = best_title

        analysis["video_info"] = {
            "filename": filename,
            "duration": video_info.get("duration", 0),
            "dimensions": f"{video_info.get('width', 0)}x{video_info.get('height', 0)}",
            "aspect_ratio": video_info.get("aspect_ratio", "9:16"),
            "created_at": datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
        }

        # 2. Direct Auto-Upload to YouTube using Dynamic Video Category
        youtube_result = None
        is_connected, _ = youtube_uploader.is_youtube_connected()

        if auto_upload and is_connected:
            print(f"Auto-publishing video to YouTube Channel under category {final_category_id}...")
            try:
                youtube_result = youtube_uploader.upload_short_to_youtube(
                    video_path=file_path,
                    title=best_title,
                    description=analysis.get("description", ""),
                    tags=analysis.get("tags", []),
                    privacy_status=privacy_status,
                    category_id=final_category_id
                )
                analysis["youtube_published"] = youtube_result
            except Exception as yt_err:
                print(f"YouTube Upload Failed: {yt_err}")
                analysis["youtube_publish_error"] = str(yt_err)

        # 3. Save to history
        history_entry = {
            "id": unique_id,
            "filename": filename,
            "timestamp": datetime.datetime.now().isoformat(),
            "date_display": datetime.datetime.now().strftime("%d %b, %I:%M %p"),
            "category": analysis.get("category_name", "Comedy"),
            "is_demo": analysis.get("is_demo", False),
            "primary_title": best_title,
            "youtube_url": youtube_result.get("short_url") if youtube_result else None,
            "result": analysis
        }
        save_to_history(history_entry)

        return jsonify({
            "success": True,
            "data": analysis,
            "youtube": youtube_result
        })

    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass

@app.route("/api/history", methods=["GET"])
def history_api():
    return jsonify({"success": True, "history": load_history()})

@app.route("/api/history/<record_id>", methods=["DELETE"])
def delete_history_item(record_id):
    history = load_history()
    new_history = [h for h in history if h.get("id") != record_id]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(new_history, f, indent=2, ensure_ascii=False)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n==================================================")
    print(f" 🚀 ShortsViral AI Server running at http://127.0.0.1:{port}")
    print(f" Open your browser to upload and auto-publish your shorts!")
    print(f"==================================================\n")
    app.run(host="127.0.0.1", port=port, debug=False)
