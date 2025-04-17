import pandas as pd
import json
import logging
import os
from typing import Dict, List, Any, Optional
import datetime
from notion_client import Client
from config.settings import NOTION_API_KEY, PROCESSED_DATA_DIR

# Configure logging
logger = logging.getLogger(__name__)

class OutputManager:
    def __init__(self):
        # Initialize Notion client if API key is available
        self.notion_client = None
        if NOTION_API_KEY:
            try:
                self.notion_client = Client(auth=NOTION_API_KEY)
                logger.info("Notion client initialized")
            except Exception as e:
                logger.error(f"Error initializing Notion client: {e}")
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename_prefix: str = "output") -> str:
        """Save generated scripts to CSV for easy viewing"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"
        filepath = os.path.join(PROCESSED_DATA_DIR, filename)
        
        # Flatten the script data for CSV format
        flattened_data = []
        
        for script_set in data:
            video_id = script_set.get("video_id", "unknown")
            content_type = script_set.get("original_content_type", "unknown")
            hook_pattern = script_set.get("original_hook_pattern", "unknown")
            style = script_set.get("style_used", "standard")
            
            for variant in script_set.get("script_variants", []):
                flattened_data.append({
                    "video_id": video_id,
                    "content_type": content_type,
                    "hook_pattern": hook_pattern,
                    "style": style,
                    "variant_number": variant.get("variant_number", ""),
                    "title": variant.get("title", ""),
                    "hook": variant.get("hook", ""),
                    "build": variant.get("build", ""),
                    "cta": variant.get("cta", ""),
                    "visual_notes": variant.get("visual_notes", ""),
                    "timestamp": timestamp
                })
        
        # Create DataFrame and save to CSV
        if flattened_data:
            df = pd.DataFrame(flattened_data)
            df.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"Data saved to CSV: {filepath}")
        else:
            logger.warning("No data to save to CSV")
            
        return filepath
    
    def push_to_notion(self, data: List[Dict[str, Any]], database_id: str) -> bool:
        """Push generated scripts to a Notion database"""
        if not self.notion_client:
            logger.error("Notion client not initialized")
            return False
            
        logger.info(f"Pushing {len(data)} script sets to Notion database: {database_id}")
        
        success_count = 0
        error_count = 0
        
        try:
            # Check if database exists
            try:
                self.notion_client.databases.retrieve(database_id)
            except Exception as e:
                logger.error(f"Error accessing Notion database {database_id}: {e}")
                return False
            
            # Push each script variant as a separate page
            for script_set in data:
                video_id = script_set.get("video_id", "unknown")
                content_type = script_set.get("original_content_type", "unknown")
                hook_pattern = script_set.get("original_hook_pattern", "unknown")
                style = script_set.get("style_used", "standard")
                
                for variant in script_set.get("script_variants", []):
                    try:
                        # Create page in Notion database
                        self.notion_client.pages.create(
                            parent={"database_id": database_id},
                            properties={
                                "Name": {
                                    "title": [{"text": {"content": variant.get("title", "Untitled Script")}}]
                                },
                                "Video ID": {
                                    "rich_text": [{"text": {"content": video_id}}]
                                },
                                "Content Type": {
                                    "select": {"name": content_type}
                                },
                                "Hook Pattern": {
                                    "rich_text": [{"text": {"content": hook_pattern}}]
                                },
                                "Style": {
                                    "select": {"name": style}
                                },
                                "Variant": {
                                    "number": int(variant.get("variant_number", 0))
                                },
                                "Status": {
                                    "select": {"name": "For Review"}
                                }
                            },
                            children=[
                                {
                                    "object": "block",
                                    "heading_2": {
                                        "rich_text": [{"text": {"content": "Hook"}}]
                                    }
                                },
                                {
                                    "object": "block",
                                    "paragraph": {
                                        "rich_text": [{"text": {"content": variant.get("hook", "")}}]
                                    }
                                },
                                {
                                    "object": "block",
                                    "heading_2": {
                                        "rich_text": [{"text": {"content": "Build"}}]
                                    }
                                },
                                {
                                    "object": "block",
                                    "paragraph": {
                                        "rich_text": [{"text": {"content": variant.get("build", "")}}]
                                    }
                                },
                                {
                                    "object": "block",
                                    "heading_2": {
                                        "rich_text": [{"text": {"content": "CTA"}}]
                                    }
                                },
                                {
                                    "object": "block",
                                    "paragraph": {
                                        "rich_text": [{"text": {"content": variant.get("cta", "")}}]
                                    }
                                },
                                {
                                    "object": "block",
                                    "heading_2": {
                                        "rich_text": [{"text": {"content": "Visual Notes"}}]
                                    }
                                },
                                {
                                    "object": "block",
                                    "paragraph": {
                                        "rich_text": [{"text": {"content": variant.get("visual_notes", "")}}]
                                    }
                                }
                            ]
                        )
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Error creating Notion page for variant {variant.get('variant_number', 0)}: {e}")
                        error_count += 1
                        
            logger.info(f"Notion push complete. Success: {success_count}, Errors: {error_count}")
            return error_count == 0
            
        except Exception as e:
            logger.error(f"Error pushing to Notion: {e}")
            return False