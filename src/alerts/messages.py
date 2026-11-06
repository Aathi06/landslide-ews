"""Alert levels and the text of each alert in English, Tamil and Hindi."""
from config.settings import ALERT_THRESHOLD

WATCH = 0.50
WARNING = ALERT_THRESHOLD      # 0.70, the same threshold the dashboard uses for "on alert"
EMERGENCY = 0.85
LEVEL_RANK = {"watch": 1, "warning": 2, "emergency": 3}

TEMPLATES = {
    "en": {
        "watch": "WATCH: Landslide risk is rising near {village} ({risk}%). About {people} people live there. "
                 "Keep monitoring rainfall and be ready to move.",
        "warning": "WARNING: High landslide risk near {village} ({risk}%). About {people} people live there. "
                   "Stay away from steep slopes, streams and road cuts, and follow official instructions.",
        "emergency": "EMERGENCY: Very high landslide risk near {village} ({risk}%). About {people} people live there. "
                     "Move to a safe place now and call 112 for help.",
    },
    "ta": {
        "watch": "கவனிக்கவும்: {village} அருகே நிலச்சரிவு அபாயம் அதிகரித்து வருகிறது ({risk}%). "
                 "அங்கு சுமார் {people} பேர் வசிக்கின்றனர். மழை நிலவரத்தைக் கவனித்து, "
                 "பாதுகாப்பான இடத்திற்குச் செல்லத் தயாராக இருங்கள்.",
        "warning": "எச்சரிக்கை: {village} அருகே நிலச்சரிவு அபாயம் அதிகமாக உள்ளது ({risk}%). "
                   "அங்கு சுமார் {people} பேர் வசிக்கின்றனர். செங்குத்தான சரிவுகள், ஓடைகள் மற்றும் "
                   "சாலை வெட்டுப் பகுதிகளிலிருந்து விலகி இருங்கள்; அதிகாரிகளின் அறிவுறுத்தல்களைப் பின்பற்றுங்கள்.",
        "emergency": "அவசரம்: {village} அருகே நிலச்சரிவு அபாயம் மிக அதிகமாக உள்ளது ({risk}%). "
                     "அங்கு சுமார் {people} பேர் வசிக்கின்றனர். உடனடியாகப் பாதுகாப்பான இடத்திற்குச் செல்லுங்கள்; "
                     "உதவிக்கு 112 ஐ அழைக்கவும்.",
    },
    "hi": {
        "watch": "निगरानी: {village} के पास भूस्खलन का खतरा बढ़ रहा है ({risk}%)। वहाँ लगभग {people} लोग रहते हैं। "
                 "बारिश पर नज़र रखें और सुरक्षित स्थान पर जाने के लिए तैयार रहें।",
        "warning": "चेतावनी: {village} के पास भूस्खलन का खतरा अधिक है ({risk}%)। वहाँ लगभग {people} लोग रहते हैं। "
                   "ढलानों, नालों और सड़क कटान से दूर रहें और अधिकारियों के निर्देशों का पालन करें।",
        "emergency": "आपातकाल: {village} के पास भूस्खलन का खतरा बहुत अधिक है ({risk}%)। वहाँ लगभग {people} लोग रहते हैं। "
                     "तुरंत सुरक्षित स्थान पर जाएँ और सहायता के लिए 112 पर कॉल करें।",
    },
}
SUPPORTED_LANGS = tuple(TEMPLATES)


def alert_level(risk: float) -> str | None:
    """Map a risk probability (0..1) to 'watch' | 'warning' | 'emergency', or None if below watch."""
    if risk >= EMERGENCY:
        return "emergency"
    if risk >= WARNING:
        return "warning"
    if risk >= WATCH:
        return "watch"
    return None


def format_alert(village: str, risk: float, people: int, lang: str = "en") -> str | None:
    """Alert text for one settlement, or None when risk is below the watch level."""
    if lang not in TEMPLATES:
        raise ValueError(f"unsupported language '{lang}', choose from {SUPPORTED_LANGS}")
    level = alert_level(risk)
    if level is None:
        return None
    return TEMPLATES[lang][level].format(village=village, risk=round(risk * 100), people=f"{people:,}")
