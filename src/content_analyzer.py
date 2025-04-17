import json
import logging
from typing import Dict, List, Any, Optional

import pandas as pd

from src.utils import generate_llm_response, save_json, get_timestamp_str
from config.settings import PROCESSED_DATA_DIR

logger = logging.getLogger(__name__)

class TikTokContentAnalyzer:
    """Analyzes TikTok content using GPT-3.5-turbo"""
    
    def __init__(self):
        """Initialize the content analyzer"""
        pass
    
    def analyze_content(self, data_path: str) -> str:
        """
        Analyze TikTok content from processed data
        
        Args:
            data_path: Path to processed data file
            
        Returns:
            Path to analysis results file
        """
        # Load data
        if data_path.endswith('.csv'):
            df = pd.read_csv(data_path)
        else:
            df = pd.read_json(data_path)
            
        logger.info(f"Batch analyzing {len(df)} videos")
        
        # Prepare results container
        analysis_results = {"results": []}
        
        # Process each video
        for _, row in df.iterrows():
            video_id = row['video_id']
            
            try:
                # Extract basic data
                video_data = {
                    "video_id": video_id,
                    "classification": self._classify_content(row),
                    "hook_analysis": self._extract_hook(row)
                }
                
                # Add to results
                analysis_results["results"].append(video_data)
                
            except Exception as e:
                logger.error(f"Error analyzing video {video_id}: {e}")
                # Add error entry
                analysis_results["results"].append({
                    "video_id": video_id,
                    "error": str(e)
                })
        
        # Save results
        output_path = PROCESSED_DATA_DIR / f"analysis_results_{get_timestamp_str()}.json"
        save_json(analysis_results, str(output_path))
        logger.info(f"Analysis results saved to {output_path}")
        
        return str(output_path)
    
    def _classify_content(self, video_data: pd.Series) -> Dict[str, Any]:
        """
        Classify content type and approach using GPT-3.5-turbo
        
        Args:
            video_data: Video data as pandas Series
            
        Returns:
            Classification results
        """
        video_id = video_data['video_id']
        logger.info(f"Classifying content for video ID: {video_id}")
        
        # Create prompt
        system_prompt = """
        You are a TikTok content analysis expert. Analyze the provided TikTok video data and classify:
        1. Content Type (e.g., Tutorial, Storytime, Educational, Entertainment, etc.)
        2. Content Approach (e.g., Direct-to-camera, Voice-over, Text-heavy, etc.)
        
        Provide a brief reasoning for your classification.
        
        Return ONLY a JSON object with the following structure:
        {
          "content_type": "string",
          "content_approach": "string",
          "reasoning": "string"
        }
        """
        
        user_prompt = f"""
        Video Caption: {video_data['caption']}
        Likes: {video_data.get('likes', 'unknown')}
        Comments: {video_data.get('comments', 'unknown')}
        Shares: {video_data.get('shares', 'unknown')}
        """
        
        try:
            # Get response from GPT
            response = generate_llm_response(user_prompt, system_prompt, json_output=True)
            
            # Parse response
            classification = json.loads(response)
            return classification
        except Exception as e:
            logger.error(f"Error classifying content: {e}")
            return {
                "content_type": "unknown",
                "content_approach": "unknown",
                "reasoning": f"Error analyzing: {str(e)}"
            }
    
    def _extract_hook(self, video_data: pd.Series) -> Dict[str, Any]:
        """
        Extract hook pattern and psychological triggers using GPT-3.5-turbo
        
        Args:
            video_data: Video data as pandas Series
            
        Returns:
            Hook analysis results
        """
        video_id = video_data['video_id']
        logger.info(f"Extracting hook for video ID: {video_id}")
        
        # Create prompt
        system_prompt = """
        You are a TikTok content analysis expert. Analyze the provided TikTok video caption for:
        1. Hook Pattern (e.g., Question, Controversial statement, Promise, etc.)
        2. Psychological Triggers (e.g., curiosity, fear of missing out, exclusivity, etc.)
        3. Effectiveness Score (1-10)
        
        Return ONLY a JSON object with the following structure:
        {
          "hook_pattern": "string",
          "psych_triggers": ["string", "string"],
          "hook_effectiveness_score": number
        }
        """
        
        user_prompt = f"""
        Video Caption: {video_data['caption']}
        """
        
        try:
            # Get response from GPT
            response = generate_llm_response(user_prompt, system_prompt, json_output=True)
            
            # Parse response
            hook_analysis = json.loads(response)
            return hook_analysis
        except Exception as e:
            logger.error(f"Error extracting hook: {e}")
            return {
                "hook_pattern": "unknown",
                "psych_triggers": ["unknown"],
                "hook_effectiveness_score": 0,
                "error": str(e)
            }