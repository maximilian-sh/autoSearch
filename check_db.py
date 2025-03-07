import os
import asyncio
import logging
import sys
from datetime import datetime
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
log_format = '%(levelname)-8s - %(message)s'
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColoredFormatter(log_format))

logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler]
)
logger = logging.getLogger(__name__)

async def check_database():
    """Check the current status of the database."""
    db_path = "data/listings.db"
    
    if not os.path.exists(db_path):
        logger.error(f"Database file {db_path} does not exist.")
        return
    
    try:
        # Initialize database
        logger.info("Connecting to database...")
        db = Database(db_path)
        await db.initialize()
        
        # Get current listings
        logger.info("Fetching listings...")
        listings = await db.get_all_listings()
        count = len(listings)
        
        print("\n" + "="*50)
        print(f"📊 Database Status Report")
        print("="*50)
        
        if count == 0:
            print("\n🔍 No listings found in the database.")
            return
            
        print(f"\n📦 Total listings: {count}")
        
        # Group by make and model
        makes = {}
        for listing in listings:
            make_model = f"{listing.make} {listing.model}"
            if make_model not in makes:
                makes[make_model] = 0
            makes[make_model] += 1
        
        print("\n📋 Listings by make and model:")
        for make_model, count in makes.items():
            print(f"  • {make_model}: {count} listings")
        
        # Show the newest listings
        newest = sorted(listings, key=lambda x: x.first_seen, reverse=True)[:5]
        if newest:
            print("\n🆕 Most recent listings:")
            for i, listing in enumerate(newest, 1):
                first_seen = datetime.fromisoformat(str(listing.first_seen))
                first_seen_str = first_seen.strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {i}. {listing.make} {listing.model} ({listing.year}) - €{listing.price:,}")
                print(f"     Location: {listing.location} | First seen: {first_seen_str}")
                print(f"     Title: {listing.title}")
                print(f"     URL: {listing.url}")
                if i < len(newest):
                    print("     ---")
        
        # Show oldest listings
        oldest = sorted(listings, key=lambda x: x.first_seen)[:3]
        if oldest:
            print("\n⏳ Oldest listings:")
            for i, listing in enumerate(oldest, 1):
                first_seen = datetime.fromisoformat(str(listing.first_seen))
                first_seen_str = first_seen.strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {i}. {listing.make} {listing.model} ({listing.year}) - €{listing.price:,}")
                print(f"     First seen: {first_seen_str}")
        
        print("\n" + "="*50)
    
    except Exception as e:
        logger.error(f"❌ Error checking database: {e}")
        raise

if __name__ == "__main__":
    print("🔍 Database Status Checker")
    print("-------------------------")
    asyncio.run(check_database())
    print("\nDone!") 