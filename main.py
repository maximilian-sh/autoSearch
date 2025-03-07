"""
AutoSearch - A car listing crawler for AutoScout24
Copyright (C) 2025

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import asyncio
import yaml
from datetime import datetime
import os
import logging
import sys
import glob
from typing import Dict, List, Any

from src.scraper.autoscout import AutoScoutScraper
from src.database.storage import Database
from src.notifier.notification import TelegramNotifier
from src.models.car import CarListing

# Custom log formatter with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels"""
    
    COLORS = {
        'DEBUG': '\033[94m',  # Blue
        'INFO': '\033[92m',   # Green
        'WARNING': '\033[93m', # Yellow
        'ERROR': '\033[91m',  # Red
        'CRITICAL': '\033[91m\033[1m', # Bold Red
        'RESET': '\033[0m'    # Reset
    }
    
    def format(self, record):
        log_message = super().format(record)
        if record.levelname in self.COLORS:
            return f"{self.COLORS[record.levelname]}{log_message}{self.COLORS['RESET']}"
        return log_message

# Set up logging
log_format = '%(asctime)s - %(levelname)-8s - %(message)s'
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColoredFormatter(log_format))

file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler]
)
logger = logging.getLogger(__name__)

async def load_all_configs() -> List[Dict[str, Any]]:
    """Load all configuration files from the config directory.
    
    Returns:
        List of configuration dictionaries, one for each config file.
    """
    logger.info("Loading configuration files...")
    config_dir = 'config'
    config_files = glob.glob(os.path.join(config_dir, '*.yaml'))
    
    # Skip the default config template
    config_files = [f for f in config_files if not os.path.basename(f).startswith('default_')]
    
    if not config_files:
        logger.error("No configuration files found in the config directory.")
        logger.info("Please create a configuration file based on default_config.yaml")
        raise FileNotFoundError("No configuration files found")
    
    configs = []
    for config_file in config_files:
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                file_name = os.path.basename(config_file)
                logger.info(f"Loaded configuration from {file_name}: {len(config['searches'])} search configurations")
                configs.append(config)
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file}: {e}")
    
    if not configs:
        logger.error("No valid configuration files found.")
        raise ValueError("No valid configuration files found")
    
    total_searches = sum(len(config['searches']) for config in configs)
    logger.info(f"Total configuration files: {len(configs)}, total searches: {total_searches}")
    
    return configs

async def main():
    try:
        # Initialize components
        logger.info("🚀 Starting AutoSearch...")
        configs = await load_all_configs()
        
        logger.info("Initializing database...")
        db = Database()
        await db.initialize()
        
        logger.info("Initializing scraper...")
        scraper = AutoScoutScraper()
        
        logger.info("Initializing Telegram notifier...")
        notifier = TelegramNotifier()
        
        logger.info("✅ All components initialized successfully")
        
        cycle_count = 0
        while True:
            cycle_count += 1
            logger.info(f"🔍 Starting search cycle #{cycle_count}...")
            all_current_ids = []
            cycle_stats = {
                "total_listings": 0,
                "new_listings": 0,
                "updated_listings": 0,
                "searches_completed": 0,
                "searches_failed": 0
            }
            
            # Process each configuration file
            for config in configs:
                # Process each search configuration
                for search in config['searches']:
                    search_name = search.get('name', f"{search['make']} {', '.join(search['models'])}")
                    
                    for model in search['models']:
                        try:
                            logger.info(f"Searching for {search['make']} {model} ({search_name})...")
                            
                            # Prepare search parameters with null checks
                            search_params = {
                                'countries': config['general'].get('countries', ['DE'])
                            }
                            
                            # Add optional parameters only if they exist and are not null
                            if 'price_range' in search and search['price_range']:
                                search_params['price_range'] = search['price_range']
                                
                            if 'year_range' in search and search['year_range']:
                                search_params['year_range'] = search['year_range']
                                
                            if 'max_kilometers' in search and search['max_kilometers'] is not None:
                                search_params['max_kilometers'] = search['max_kilometers']
                                
                            if 'kilometers_range' in search and search['kilometers_range']:
                                search_params['kilometers_range'] = search['kilometers_range']
                                
                            if 'body_type' in search and search['body_type'] is not None:
                                search_params['body_type'] = search['body_type']
                                
                            if 'seats' in search and search['seats']:
                                search_params['seats'] = search['seats']
                                
                            if 'fuel_type' in search and search['fuel_type']:
                                search_params['fuel_type'] = search['fuel_type']
                                
                            if 'transmission' in search and search['transmission']:
                                search_params['transmission'] = search['transmission']
                                
                            if 'doors' in search and search['doors']:
                                search_params['doors'] = search['doors']
                                
                            if 'equipment' in search and search['equipment']:
                                search_params['equipment'] = search['equipment']
                                
                            if 'color' in search and search['color'] is not None:
                                search_params['color'] = search['color']
                                
                            if 'power_range' in search and search['power_range']:
                                search_params['power_range'] = search['power_range']
                                
                            if 'zip' in search and search['zip']:
                                search_params['zip'] = search['zip']
                                
                            if 'zipr' in search and search['zipr'] is not None:
                                search_params['zipr'] = search['zipr']
                            
                            listings = await scraper.search(
                                make=search['make'],
                                model=model,
                                params=search_params
                            )
                            
                            num_listings = len(listings)
                            cycle_stats["total_listings"] += num_listings
                            logger.info(f"Found {num_listings} listings for {search['make']} {model}")
                            
                            # Process found listings
                            for listing in listings:
                                all_current_ids.append(listing.id)
                                existing_listing = await db.get_listing(listing.id)
                                
                                if not existing_listing:
                                    cycle_stats["new_listings"] += 1
                                    logger.info(f"📢 New listing: {listing.make} {listing.model} ({listing.year}) - €{listing.price:,}")
                                    await db.add_listing(listing)
                                    await notifier.notify_new_listing(listing)
                                else:
                                    cycle_stats["updated_listings"] += 1
                                    logger.debug(f"Updating existing listing: {listing.id}")
                                    existing_listing.last_seen = datetime.now()
                                    await db.add_listing(existing_listing)
                            
                            cycle_stats["searches_completed"] += 1
                        
                        except Exception as e:
                            cycle_stats["searches_failed"] += 1
                            error_msg = f"❌ Error processing {search['make']} {model}: {str(e)}"
                            logger.error(error_msg)
                            await notifier.notify_error(error_msg)
            
            # Remove listings that are no longer available
            logger.info("Cleaning up old listings...")
            removed_count = await db.remove_old_listings(all_current_ids)
            
            # Print cycle summary
            logger.info("📊 Search cycle summary:")
            logger.info(f"  - Total listings found: {cycle_stats['total_listings']}")
            logger.info(f"  - New listings: {cycle_stats['new_listings']}")
            logger.info(f"  - Updated listings: {cycle_stats['updated_listings']}")
            logger.info(f"  - Removed listings: {removed_count}")
            logger.info(f"  - Searches completed: {cycle_stats['searches_completed']}")
            logger.info(f"  - Searches failed: {cycle_stats['searches_failed']}")
            
            # Find the shortest check interval from all configs
            min_interval = min(config['general'].get('check_interval_minutes', 15) for config in configs)
            logger.info(f"⏱️ Search cycle completed. Next check in {min_interval} minutes...")
            await asyncio.sleep(min_interval * 60)
    
    except KeyboardInterrupt:
        logger.info("Received shutdown signal. Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
        raise
    finally:
        logger.info("Closing scraper...")
        await scraper.close()
        print("\nShutting down gracefully...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise 