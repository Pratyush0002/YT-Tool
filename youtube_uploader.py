import os
import json
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FOLDER = BASE_DIR / "data"
DATA_FOLDER.mkdir(exist_ok=True)

OAUTH_CONFIG_FILE = DATA_FOLDER / "youtube_oauth_config.json"
TOKEN_FILE = DATA_FOLDER / "youtube_token.json"
CHANNEL_INFO_FILE = DATA_FOLDER / "channel_info.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

YOUTUBE_CATEGORIES = {
    "1": "Film & Animation (फ़िल्म & एनिमेशन)",
    "2": "Autos & Vehicles (गाड़ियाँ & वाहन)",
    "10": "Music (संगीत / म्यूज़िक)",
    "15": "Pets & Animals (जानवर & पालतू)",
    "17": "Sports (खेलकूद / स्पोर्ट्स)",
    "19": "Travel & Events (ट्रैवल & इवेंट्स)",
    "20": "Gaming (गेमिंग)",
    "22": "People & Blogs (लोग & ब्लॉग्स)",
    "23": "Comedy (कॉमेडी / हास्य)",
    "24": "Entertainment (मनोरंजन / एंटरटेनमेंट)",
    "25": "News & Politics (समाचार)",
    "26": "Howto & Style (टिप्स & लाइफस्टाइल)",
    "27": "Education (शिक्षा / ज्ञान)",
    "28": "Science & Technology (साइंस & टेक)"
}

def resolve_category_id(val):
    if not val or str(val).lower() == "auto":
        return "23"
    val_str = str(val).strip()
    if val_str in YOUTUBE_CATEGORIES:
        return val_str
    val_lower = val_str.lower()
    for cid, name in YOUTUBE_CATEGORIES.items():
        if val_lower in name.lower() or name.lower() in val_lower:
            return cid
    return "24" # Fallback to Entertainment

def get_oauth_config():
    if not OAUTH_CONFIG_FILE.exists():
        return {}
    try:
        with open(OAUTH_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_oauth_config(client_id, client_secret):
    data = {
        "client_id": client_id.strip(),
        "client_secret": client_secret.strip(),
        "updated_at": datetime.datetime.now().isoformat()
    }
    with open(OAUTH_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return True

def get_channel_info():
    if not CHANNEL_INFO_FILE.exists() or not TOKEN_FILE.exists():
        return None
    try:
        with open(CHANNEL_INFO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def is_youtube_connected():
    if not TOKEN_FILE.exists():
        return False, None
    info = get_channel_info()
    if info:
        return True, info
    return True, {"title": "Connected Channel", "customUrl": "", "thumbnail": ""}

def disconnect_youtube():
    try:
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
        if CHANNEL_INFO_FILE.exists():
            CHANNEL_INFO_FILE.unlink()
        return True
    except Exception as e:
        print(f"Error disconnecting YouTube: {e}")
        return False

def get_credentials():
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        return None

    if not TOKEN_FILE.exists():
        return None

    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            token_data = json.load(f)

        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
        return creds
    except Exception as e:
        print(f"Error loading YouTube credentials: {e}")
        return None

def fetch_and_save_channel_info(creds):
    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", credentials=creds)
        response = youtube.channels().list(mine=True, part="snippet,statistics").execute()
        items = response.get("items", [])
        if items:
            channel = items[0]
            snippet = channel.get("snippet", {})
            stats = channel.get("statistics", {})
            info = {
                "id": channel.get("id"),
                "title": snippet.get("title", "My YouTube Channel"),
                "description": snippet.get("description", ""),
                "customUrl": snippet.get("customUrl", ""),
                "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                "subscriberCount": stats.get("subscriberCount", "0"),
                "videoCount": stats.get("videoCount", "0"),
                "connected_at": datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
            }
            with open(CHANNEL_INFO_FILE, "w", encoding="utf-8") as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
            return info
    except Exception as e:
        print(f"Error fetching channel info: {e}")
    return None

def create_oauth_flow(redirect_uri):
    from google_auth_oauthlib.flow import Flow
    config = get_oauth_config()
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")

    if not client_id or not client_secret:
        raise ValueError("YouTube OAuth Client ID और Secret कॉन्फ़िगर नहीं हैं।")

    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    return flow

def upload_short_to_youtube(video_path, title, description, tags, privacy_status="public", category_id="23"):
    """
    Directly publishes a short video to the user's connected YouTube channel
    using dynamic category detection based on the video content!
    """
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        raise ValueError("google-api-python-client पैकेज इंस्टॉल नहीं है।")

    creds = get_credentials()
    if not creds:
        raise ValueError("YouTube चैनल कनेक्टेड नहीं है। कृपया पहले चैनल जोड़ें।")

    youtube = build("youtube", "v3", credentials=creds)

    safe_title = title.strip()[:100]
    if "#shorts" not in safe_title.lower():
        safe_title = f"{safe_title} #shorts"[:100]

    safe_description = description.strip()[:5000]

    clean_tags = []
    char_count = 0
    for t in tags:
        t_clean = t.strip()
        if t_clean and (char_count + len(t_clean) + 1) <= 490:
            clean_tags.append(t_clean)
            char_count += len(t_clean) + 1

    # Dynamically resolve Category ID
    final_cat_id = resolve_category_id(category_id)
    cat_name = YOUTUBE_CATEGORIES.get(final_cat_id, "Entertainment")

    body = {
        "snippet": {
            "title": safe_title,
            "description": safe_description,
            "tags": clean_tags,
            "categoryId": final_cat_id,
            "defaultLanguage": "hi",
            "defaultAudioLanguage": "hi"
        },
        "status": {
            "privacyStatus": privacy_status if privacy_status in ["public", "unlisted", "private"] else "public",
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        str(video_path),
        chunksize=1024 * 1024 * 4,
        resumable=True,
        mimetype="video/*"
    )

    print(f"Uploading short to YouTube: '{safe_title}' [Category: {final_cat_id} - {cat_name}] ({privacy_status})...")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"Upload progress: {pct}%")

    video_id = response.get("id")
    if not video_id:
        raise ValueError("YouTube ने वीडियो ID नहीं लौटाई।")

    short_url = f"https://youtube.com/shorts/{video_id}"
    watch_url = f"https://www.youtube.com/watch?v={video_id}"

    return {
        "success": True,
        "video_id": video_id,
        "short_url": short_url,
        "watch_url": watch_url,
        "title": safe_title,
        "category_id": final_cat_id,
        "category_name": cat_name,
        "privacy": privacy_status,
        "published_at": datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
    }
