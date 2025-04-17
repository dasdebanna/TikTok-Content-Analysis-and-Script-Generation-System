import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

import pandas as pd

from src.utils import generate_llm_response, get_timestamp_str, save_json
from config.settings import PROCESSED_DATA_DIR

logger = logging.getLogger(__name__)

class TikTokScriptGenerator:
    """Generates TikTok scripts based on content analysis"""
    
    def __init__(self):
        """Initialize the script generator"""
        pass
    
    def generate_scripts(
        self, 
        analysis_path: str,
        products: str,
        brand_voice: str,
        target_audience: str,
        style: str = 'educational',
        variants: int = 1
    ) -> str:
        """
        Generate TikTok scripts based on content analysis
        
        Args:
            analysis_path: Path to analysis results file
            products: Products to promote
            brand_voice: Brand voice description
            target_audience: Target audience description
            style: Script style (educational, entertaining, etc.)
            variants: Number of script variants to generate
            
        Returns:
            Path to generated scripts file
        """
        try:
            # Load analysis results
            analysis_data = json.loads(Path(analysis_path).read_text())
            
            # Validate analysis data
            if 'results' not in analysis_data:
                logger.error(f"Invalid analysis data format in {analysis_path}")
                raise ValueError("Invalid analysis data format")
                
            logger.info(f"Generating scripts for {len(analysis_data['results'])} analyzed videos")
            
            # Generate scripts for each analyzed video
            scripts_data = {"scripts": []}
            
            for video_analysis in analysis_data['results']:
                video_id = video_analysis.get('video_id', 'unknown')
                
                try:
                    # Generate scripts for this video
                    video_scripts = self._generate_video_scripts(
                        video_analysis,
                        products,
                        brand_voice,
                        target_audience,
                        style,
                        variants
                    )
                    
                    # Add to results
                    scripts_data["scripts"].append({
                        "video_id": video_id,
                        "variants": video_scripts
                    })
                    
                except Exception as e:
                    logger.error(f"Error generating scripts for video {video_id}: {e}")
                    scripts_data["scripts"].append({
                        "video_id": video_id,
                        "error": str(e),
                        "variants": []
                    })
            
            # Save results
            output_path = PROCESSED_DATA_DIR / f"scripts_{get_timestamp_str()}.json"
            save_json(scripts_data, str(output_path))
            logger.info(f"Generated scripts saved to {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error generating scripts: {e}")
            raise
    
    def _generate_video_scripts(
        self,
        video_analysis: Dict[str, Any],
        products: str,
        brand_voice: str,
        target_audience: str,
        style: str,
        variants: int
    ) -> List[Dict[str, Any]]:
        """
        Generate script variants for a single video
        
        Args:
            video_analysis: Analysis data for a single video
            products: Products to promote
            brand_voice: Brand voice description
            target_audience: Target audience description
            style: Script style
            variants: Number of variants
            
        Returns:
            List of script variants
        """
        # Extract key insights
        content_type = video_analysis.get('classification', {}).get('content_type', 'unknown')
        content_approach = video_analysis.get('classification', {}).get('content_approach', 'unknown')
        hook_pattern = video_analysis.get('hook_analysis', {}).get('hook_pattern', 'unknown')
        psych_triggers = video_analysis.get('hook_analysis', {}).get('psych_triggers', [])
        
        # Format psych_triggers for the prompt
        psych_triggers_text = ", ".join(psych_triggers) if psych_triggers else "none identified"
        
        # Create system prompt
        system_prompt = f"""
        You are an expert TikTok script writer for {brand_voice} content targeted at {target_audience}.
        Create {variants} script variants for a {style} TikTok video.
        
        Use the following insights from content analysis:
        - Content type: {content_type}
        - Content approach: {content_approach}
        - Hook pattern: {hook_pattern}
        - Psychological triggers: {psych_triggers_text}
        
        Each script should:
        1. Follow a specific structure: Hook, Value, CTA
        2. Be concise and follow TikTok best practices
        3. Naturally incorporate {products} in a way that doesn't feel forced
        4. Match the identified content type and approach
        5. Use the hook pattern and psychological triggers effectively
        6. Be formatted for a 30-60 second video
        
        For each script variant, include:
        - hook: The attention-grabbing opening
        - value: Main content/value delivery
        - cta: Call to action
        - visuals: Brief description of suggested visuals
        - audio: Suggestions for audio/music
        """
        
        # Create user prompt
        user_prompt = f"""
        Create exactly {variants} script variants for a {style} TikTok video promoting {products}.
        Target audience: {target_audience}
        Brand voice: {brand_voice}
        
        Format your response as a JSON array with {variants} objects, each containing hook, value, cta, visuals, and audio fields.
        """
        
        script_variants = []
        
        try:
            # Generate scripts using LLM
            response = generate_llm_response(user_prompt, system_prompt, json_output=True)
            
            # Parse response
            try:
                # First try to parse as an array
                scripts = json.loads(response)
                
                # Check if we already have an array structure
                if isinstance(scripts, list):
                    script_variants = scripts[:variants]  # Limit to requested variants
                # If we have a single object with nested scripts array
                elif 'scripts' in scripts and isinstance(scripts['scripts'], list):
                    script_variants = scripts['scripts'][:variants]
                # If we have some other structure, try to extract what we need
                else:
                    script_variants = [scripts]  # Use as single script
                    
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse response as JSON: {response[:100]}...")
                # Create a placeholder script with error
                script_variants = [{
                    "hook": "Error parsing script response",
                    "value": "Error parsing script response",
                    "cta": "Error parsing script response",
                    "visuals": "Error parsing script response",
                    "audio": "Error parsing script response"
                }]
            
            # Ensure we have exactly the requested number of variants
            while len(script_variants) < variants:
                script_variants.append({
                    "hook": f"Additional script variant {len(script_variants) + 1}",
                    "value": f"Generated value for variant {len(script_variants) + 1}",
                    "cta": f"Generated CTA for variant {len(script_variants) + 1}",
                    "visuals": f"Generated visuals for variant {len(script_variants) + 1}",
                    "audio": f"Generated audio for variant {len(script_variants) + 1}"
                })
            
            # Truncate if we received too many variants
            script_variants = script_variants[:variants]
            
            # Ensure each script has all required fields
            for script in script_variants:
                for field in ["hook", "value", "cta", "visuals", "audio"]:
                    if field not in script:
                        script[field] = f"Missing {field}"
            
            return script_variants
            
        except Exception as e:
            logger.error(f"Error generating scripts: {e}")
            return [{
                "hook": f"Error generating script: {str(e)}",
                "value": "Error generating script",
                "cta": "Error generating script",
                "visuals": "Error generating script",
                "audio": "Error generating script"
            } for _ in range(variants)]