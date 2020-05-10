import pytz

CHAT_IDS_WHITELIST = [
    -467632056,         # Test
    -1001205725373,     # Helli84
]
MESSAGE_LIMIT_COUNT = 5
TIMEZONE = pytz.timezone("Asia/Tehran")
DATA_FILE_PATH = './bot.db'

with open('api.token') as token_file:
    API_TOKEN = token_file.read().strip()
