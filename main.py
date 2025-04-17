#!/usr/bin/env python3
import argparse
import logging
import os
import json
import pandas as pd  # Ensure pandas is imported
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from src.data_processor import TikTokDataProcessor
from src.content_analyzer import TikTokContentAnalyzer
from src.script_generator import TikTokScriptGenerator
from src.output_manager import OutputManager
from src.utils import load_json, get_timestamp_str
from config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def get_full_path(filename: str, default_dir: Path) -> str:
    """
    Get full path for a file, using default directory if no path provided
    
    Args:
        filename: File name or path
        default_dir: Default directory to use if no path provided
        
    Returns:
        Full path to file
    """
    if not filename:
        return None
        
    # If filename already has a directory, use it as is
    if os.path.dirname(filename):
        return filename
        
    # Otherwise, combine with default directory
    return str(default_dir / filename)

def main():
    """Main entry point for the CLI application"""
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='TikTok Content System')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch TikTok data')
    fetch_parser.add_argument('--username', required=True, help='TikTok username')
    fetch_parser.add_argument('--limit', type=int, default=10, help='Maximum number of videos to fetch')
    fetch_parser.add_argument('--output-file', help='Output file name (optional)')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process raw TikTok data')
    process_parser.add_argument('--input-file', required=True, help='Input file name or path')
    process_parser.add_argument('--output-file', help='Output file name (optional)')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze processed TikTok data')
    analyze_parser.add_argument('--input-file', required=True, help='Input file name or path')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate scripts based on analysis')
    generate_parser.add_argument('--input-file', required=True, help='Input file name or path')
    generate_parser.add_argument('--products', required=True, help='Products to promote')
    generate_parser.add_argument('--brand-voice', required=True, help='Brand voice description')
    generate_parser.add_argument('--target-audience', required=True, help='Target audience description')
    generate_parser.add_argument('--style', default='educational', choices=['educational', 'entertaining', 'testimonial', 'demonstration'], help='Script style')
    generate_parser.add_argument('--variants', type=int, default=1, help='Number of script variants to generate')
    
    # Publish command
    publish_parser = subparsers.add_parser('publish', help='Publish scripts to Notion database')
    publish_parser.add_argument('--input-file', required=True, help='Input file name or path')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize output manager (for Notion publishing)
    output_manager = OutputManager()
    
    # Process command
    if args.command == "fetch":
        username = args.username
        limit = args.limit
        output_file = args.output_file or f"tiktok_raw_{username}_{get_timestamp_str()}.json"
        output_path = get_full_path(output_file, RAW_DATA_DIR)
        
        logger.info(f"Fetching TikTok data for @{username} (limit: {limit})")
        
        # Initialize data processor
        data_processor = TikTokDataProcessor()
        
        # Fetch data
        result = data_processor.fetch_tiktok_data(username, limit, output_path)
        
        logger.info(f"Fetched {len(result['items'])} TikTok videos")
        
    elif args.command == "process":
        input_path = get_full_path(args.input_file, RAW_DATA_DIR)
        output_file = args.output_file or f"tiktok_processed_{get_timestamp_str()}.json"
        output_path = get_full_path(output_file, PROCESSED_DATA_DIR)
        
        logger.info(f"Processing TikTok data from {input_path}")
        
        # Initialize data processor
        data_processor = TikTokDataProcessor()
        
        # Process data
        processed_data = data_processor.process_raw_data(input_path, output_path)
        
        logger.info(f"Processed {len(processed_data)} TikTok videos")
        
    elif args.command == "analyze":
        input_path = get_full_path(args.input_file, PROCESSED_DATA_DIR)
        logger.info(f"Analyzing TikTok content from {input_path}")
        
        # Initialize content analyzer
        content_analyzer = TikTokContentAnalyzer()
        
        # Analyze content - UPDATED METHOD NAME
        results_path = content_analyzer.analyze_content(input_path)
        
        # UPDATED LOGGING LINE
        logger.info(f"Analysis completed and saved to {results_path}")
        
    elif args.command == "generate":
        # Load parameters
        input_path = get_full_path(args.input_file, PROCESSED_DATA_DIR)
        logger.info(f"Generating scripts from analysis in {input_path}")
        
        products = args.products
        brand_voice = args.brand_voice
        target_audience = args.target_audience
        style = args.style
        variants = args.variants
        
        # Initialize script generator
        script_generator = TikTokScriptGenerator()
        
        # Generate scripts - UPDATED METHOD NAME AND PARAMETERS
        scripts_path = script_generator.generate_scripts(
            input_path,
            products,
            brand_voice,
            target_audience,
            style,
            variants
        )
        
        # UPDATED LOGGING LINE
        logger.info(f"Script generation completed and saved to {scripts_path}")
        
    elif args.command == "publish":
        input_path = get_full_path(args.input_file, PROCESSED_DATA_DIR)
        logger.info(f"Publishing scripts from {input_path}")
        
        # Load scripts
        scripts_data = load_json(input_path)

        # Properly formatted database ID with hyphens
        database_id = "YOUR_DATABASE_ID"  # Replace with your actual database ID
        
        # Publish to Notion
        results = output_manager.push_to_notion(scripts_data, database_id)
        
        # Handle potential boolean return value
        if isinstance(results, bool):
            if results:
                logger.info("Successfully published scripts to Notion")
            else:
                logger.error("Failed to publish scripts to Notion")
        else:
            logger.info(f"Published {len(results)} script sets to Notion")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()