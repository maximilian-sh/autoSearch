import os
import asyncio
import logging
import sys
from src.database.storage import Database

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

logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler]
)
logger = logging.getLogger(__name__)

async def clear_database():
    """Clear all listings from the database."""
    db_path = "data/listings.db"
    
    if not os.path.exists(db_path):
        logger.info(f"Database file {db_path} does not exist. Nothing to clear.")
        return
    
    try:
        # Initialize database
        logger.info("Connecting to database...")
        db = Database(db_path)
        await db.initialize()
        
        # Clear all listings
        logger.info("Clearing all listings from database...")
        count = await db.clear_all_listings()
        
        logger.info(f"✅ Successfully cleared {count} listings from the database.")
    except Exception as e:
        logger.error(f"❌ Error clearing database: {e}")
        raise

if __name__ == "__main__":
    print("🗑️  Database Cleanup Utility")
    print("----------------------------")
    asyncio.run(clear_database())
    print("Done!") 