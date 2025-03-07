import os
import logging
from telegram.ext import Application
from ..models.car import CarListing
from dotenv import load_dotenv
from datetime import datetime
import re

load_dotenv()

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if not self.token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env file")
        
        logger.info(f"Initializing Telegram notifier with chat ID: {self.chat_id}")
        self.app = Application.builder().token(self.token).build()

    async def notify_new_listing(self, listing: CarListing):
        logger.info(f"Preparing to send notification for listing: {listing.id}")
        
        # Log all listing details for debugging
        logger.info(f"Listing details: ID={listing.id}, Make={listing.make}, Model={listing.model}, "
                   f"Title={listing.title}, Price={listing.price}, Year={listing.year}, "
                   f"Kilometers={listing.kilometers}, Location={listing.location}, URL={listing.url}")
        
        message = self._format_listing_message(listing)
        logger.info(f"Formatted message: {message}")
        
        try:
            # Send text-only message
            async with self.app:
                await self.app.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='HTML',
                    disable_web_page_preview=False
                )
            logger.info(f"Successfully sent notification for listing: {listing.id}")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            # Try a simpler fallback message
            try:
                async with self.app:
                    await self.app.bot.send_message(
                        chat_id=self.chat_id,
                        text=f"New listing: {listing.make} {listing.model}\n\nView at: {listing.url}",
                        disable_web_page_preview=False
                    )
                logger.info(f"Sent simplified fallback notification for listing: {listing.id}")
            except Exception as e2:
                logger.error(f"Failed to send fallback notification: {e2}")

    def _format_listing_message(self, listing: CarListing) -> str:
        # Format price
        if listing.price > 0:
            price_str = f"€{listing.price:,}"
        else:
            price_str = "Price not available"
        
        # Format year
        if listing.year > 0:
            year_str = str(listing.year)
        else:
            year_str = "Year not available"
        
        # Format kilometers
        if listing.kilometers > 0:
            km_str = f"{listing.kilometers:,} km"
        else:
            km_str = "Mileage not available"
        
        # Format location - only include if it's more than just a postal code
        location_str = ""
        if listing.location and listing.location.strip():
            # Check if location is more than just a postal code
            if not listing.location.strip().isdigit() and len(listing.location.strip()) > 5:
                location_str = f"\nLocation: {listing.location}"
        
        # Format title - clean up any extra spaces or special characters
        if listing.title and listing.title.strip():
            # Clean up title by removing excessive spaces and asterisks
            clean_title = ' '.join(listing.title.split())
            clean_title = clean_title.replace('****', '').replace('***', '').replace('**', '').replace('*', '')
            
            # Remove redundant make/model from the beginning of the title
            # Try different patterns to catch variations like "VolkswagenT5" or "Volkswagen T5"
            patterns = [
                f"^{listing.make}\\s*{listing.model}\\s*",  # Volkswagen T5
                f"^{listing.make}{listing.model}\\s*",      # VolkswagenT5
                f"^{listing.make}\\s*",                     # Volkswagen
            ]
            
            for pattern in patterns:
                clean_title = re.sub(pattern, "", clean_title, flags=re.IGNORECASE)
                if clean_title != listing.title:
                    break
            
            # If title is now empty or just whitespace, use a default
            clean_title = clean_title.strip()
            if not clean_title:
                clean_title = f"{listing.make} {listing.model}"
            
            title_str = clean_title
        else:
            title_str = f"{listing.make} {listing.model}"
        
        # Format the message with clean, minimalistic structure
        return f"""{listing.make} {listing.model}
{title_str}

{year_str}
{km_str}
{price_str}{location_str}

<a href="{listing.url}">View Details</a>"""

    async def notify_error(self, error: str):
        logger.info(f"Sending error notification: {error}")
        
        # Format the error message with clean, minimalistic structure
        error_message = f"""<b>Error Alert</b>

An error occurred during the search process:

{error}

{datetime.now().strftime('%Y-%m-%d %H:%M')}"""
        
        try:
            async with self.app:
                await self.app.bot.send_message(
                    chat_id=self.chat_id,
                    text=error_message,
                    parse_mode='HTML'
                )
            logger.info("Successfully sent error notification")
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}") 