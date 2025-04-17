import pandas as pd
import json
import os
import logging
from typing import Dict, List, Any, Optional
import whisper
from apify_client import ApifyClient
from config.settings import APIFY_API_KEY, RAW_DATA_DIR, PROCESSED_DATA_DIR

# Configure logging
logger = logging.getLogger(__name__)

class TikTokDataProcessor:
    def __init__(self):
        self.apify_client = ApifyClient(APIFY_API_KEY)
        self.whisper_model = None  # We'll load it only when needed
        
    def load_whisper_model(self, model_size: str = "base"):
        """Load Whisper model for transcription"""
        logger.info(f"Loading Whisper model: {model_size}")
        self.whisper_model = whisper.load_model(model_size)
        return self.whisper_model
    
    def fetch_tiktok_data(self, actor_id: str = "clockworks/tiktok-scraper", 
                         hashtags: List[str] = None, 
                         usernames: List[str] = None,
                         max_items: int = 10) -> List[Dict[str, Any]]:
        """Fetch TikTok data from Apify"""
        if not hashtags and not usernames:
            raise ValueError("At least one hashtag or username must be provided")
            
        logger.info(f"Fetching TikTok data for hashtags: {hashtags}, usernames: {usernames}")
        
        # Prepare the run input
        run_input = {
            "maxItems": max_items,
        }
        
        if hashtags:
            run_input["hashtags"] = hashtags
            
        if usernames:
            run_input["usernames"] = usernames
        
        # Run the Actor and wait for it to finish
        run = self.apify_client.actor(actor_id).call(run_input=run_input)
        
        # Fetch and return the Actor's output items
        items = self.apify_client.dataset(run["defaultDatasetId"]).list_items().items
        
        # Save raw data
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(RAW_DATA_DIR, f"tiktok_raw_{timestamp}.json")
        with open(save_path, 'w') as f:
            json.dump(items, f)
        
        logger.info(f"Fetched {len(items)} items. Raw data saved to {save_path}")
        return items
    
    def process_tiktok_data(self, data: List[Dict[str, Any]], 
                           transcribe: bool = False,
                           save: bool = True) -> pd.DataFrame:
        """Process TikTok data into a structured DataFrame"""
        logger.info(f"Processing {len(data)} TikTok videos")
        processed_data = []
        
        for item in data:
            try:
                # Extract the basic metadata
                video_data = {
                    "video_id": item.get("id", ""),
                    "creator_name": item.get("authorMeta", {}).get("name", ""),
                    "creator_username": item.get("authorMeta", {}).get("name", ""),
                    "caption": item.get("text", ""),
                    "likes": item.get("diggCount", 0),
                    "shares": item.get("shareCount", 0),
                    "comments": item.get("commentCount", 0),
                    "duration": item.get("videoMeta", {}).get("duration", 0),
                    "hashtags": [tag["name"] for tag in item.get("hashtags", [])],
                    "video_url": item.get("webVideoUrl", ""),
                    "download_url": item.get("videoUrl", ""),
                    "created_at": item.get("createTime", 0),
                    "transcript": "",
                }
                
                # Transcribe if requested and URL is available
                if transcribe and video_data["download_url"] and not self.whisper_model:
                    self.load_whisper_model()
                
                if transcribe and video_data["download_url"] and self.whisper_model:
                    try:
                        # This is a placeholder - in a real implementation, 
                        # you would download the video and transcribe it
                        # video_data["transcript"] = self._transcribe_video(video_data["download_url"])
                        # For now, we'll just log that we would transcribe it
                        logger.info(f"Would transcribe video {video_data['video_id']}")
                    except Exception as e:
                        logger.error(f"Error transcribing video {video_data['video_id']}: {e}")
                
                processed_data.append(video_data)
            except Exception as e:
                logger.error(f"Error processing video item: {e}")
        
        df = pd.DataFrame(processed_data)
        
        if save and not df.empty:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(PROCESSED_DATA_DIR, f"tiktok_processed_{timestamp}.csv")
            df.to_csv(save_path, index=False)
            logger.info(f"Processed data saved to {save_path}")
            
            # Also save as JSON for easier processing
            json_path = os.path.join(PROCESSED_DATA_DIR, f"tiktok_processed_{timestamp}.json")
            df.to_json(json_path, orient="records")
            logger.info(f"Processed data also saved to {json_path}")
        
        return df
    
    def _transcribe_video(self, video_url: str) -> str:
        """
        Transcribe a video using Whisper
        NOTE: This is a placeholder. In a real implementation, you would:
        1. Download the video
        2. Extract audio
        3. Transcribe with Whisper
        4. Clean up temporary files
        """
        # This is just a placeholder - in a real implementation you would download
        # the video and transcribe it using the Whisper model
        return f"Placeholder transcript for {video_url}"