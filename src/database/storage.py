import aiosqlite
import os
from datetime import datetime
from ..models.car import CarListing

class Database:
    def __init__(self, db_path: str = "data/listings.db"):
        self.db_path = db_path
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS listings (
                    id TEXT PRIMARY KEY,
                    make TEXT,
                    model TEXT,
                    price INTEGER,
                    year INTEGER,
                    kilometers INTEGER,
                    location TEXT,
                    url TEXT,
                    first_seen TIMESTAMP,
                    last_seen TIMESTAMP,
                    title TEXT,
                    description TEXT
                )
            ''')
            await db.commit()

    async def add_listing(self, listing: CarListing):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO listings 
                (id, make, model, price, year, kilometers, location, url, 
                first_seen, last_seen, title, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                listing.id, listing.make, listing.model, listing.price,
                listing.year, listing.kilometers, listing.location, listing.url,
                listing.first_seen, listing.last_seen, listing.title,
                listing.description
            ))
            await db.commit()

    async def get_listing(self, listing_id: str) -> CarListing:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT * FROM listings WHERE id = ?', (listing_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return CarListing(
                        id=row[0], make=row[1], model=row[2], price=row[3],
                        year=row[4], kilometers=row[5], location=row[6],
                        url=row[7], first_seen=row[8], last_seen=row[9],
                        title=row[10], description=row[11]
                    )
                return None

    async def remove_old_listings(self, current_ids: list[str]) -> int:
        """Remove listings that are no longer available.
        
        Args:
            current_ids: List of IDs that are currently available
            
        Returns:
            int: Number of listings removed
        """
        if not current_ids:
            return 0
            
        async with aiosqlite.connect(self.db_path) as db:
            # First, get the count of listings to be removed
            query_count = 'SELECT COUNT(*) FROM listings'
            if current_ids:
                placeholders = ','.join(['?' for _ in current_ids])
                query_count = f'SELECT COUNT(*) FROM listings WHERE id NOT IN ({placeholders})'
            
            async with db.execute(query_count, current_ids) as cursor:
                row = await cursor.fetchone()
                count_to_remove = row[0] if row else 0
            
            # Then delete the listings
            if current_ids:
                placeholders = ','.join(['?' for _ in current_ids])
                query = f'DELETE FROM listings WHERE id NOT IN ({placeholders})'
                await db.execute(query, current_ids)
            else:
                await db.execute('DELETE FROM listings')
            
            await db.commit()
            return count_to_remove

    async def get_all_listings(self) -> list[CarListing]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT * FROM listings') as cursor:
                rows = await cursor.fetchall()
                return [
                    CarListing(
                        id=row[0], make=row[1], model=row[2], price=row[3],
                        year=row[4], kilometers=row[5], location=row[6],
                        url=row[7], first_seen=row[8], last_seen=row[9],
                        title=row[10], description=row[11]
                    )
                    for row in rows
                ]
    
    async def clear_all_listings(self) -> int:
        """Delete all listings from the database.
        
        Returns:
            int: Number of listings removed
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Get count first
            async with db.execute('SELECT COUNT(*) FROM listings') as cursor:
                row = await cursor.fetchone()
                count = row[0] if row else 0
                
            # Then delete
            await db.execute('DELETE FROM listings')
            await db.commit()
            return count 