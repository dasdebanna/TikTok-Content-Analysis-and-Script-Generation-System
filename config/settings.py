import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# API Keys
APIFY_API_KEY = os.getenv('APIFY_API_KEY')
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# LLM Settings
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
APP_NAME = os.getenv('APP_NAME', 'TikTok Content Analyzer')
APP_URL = os.getenv('APP_URL', 'http://localhost:3000')

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

# Create directories if they don't exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)