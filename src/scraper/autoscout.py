import logging
import re
import requests
import time
import random
import json
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Any, Optional

from ..models.car import CarListing

logger = logging.getLogger(__name__)

class AutoScoutScraper:
    def __init__(self):
        self.base_url = "https://www.autoscout24.de"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        })
        
    async def initialize(self):
        logger.info("Initializing HTTP session...")
        # Set cookies by visiting the main page
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            logger.info("Session initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize session: {e}")
            raise

    async def close(self):
        logger.info("Closing HTTP session...")
        self.session.close()

    def build_search_url(self, params: Dict[str, Any]) -> str:
        """Build the search URL based on the provided parameters."""
        make = params.get('make', '').lower()
        models = params.get('models', [])
        
        # Format the model part of the URL
        if models and len(models) == 1:
            model = models[0].lower()
            # Special case for T6 and similar models that need the (alle) suffix
            if model in ["t6", "t5", "t4", "t3"]:
                model_part = f"{model}-(alle)"
            else:
                model_part = model
        elif models and len(models) > 1:
            # If multiple models, use the first one with (alle) suffix
            model_part = f"{models[0].lower()}-(alle)"
        else:
            model_part = ""
        
        # Base URL
        if model_part:
            base_url = f"{self.base_url}/lst/{make}/{model_part}"
        else:
            base_url = f"{self.base_url}/lst/{make}"
        
        # Query parameters
        query_params = []
        
        # Vehicle type (Car)
        query_params.append("atype=C")
        
        # Country codes (Austria, Germany)
        countries = params.get('countries', ["AT", "DE"])
        country_codes = []
        for country in countries:
            if country == 'AT':
                country_codes.append('A')
            elif country == 'DE':
                country_codes.append('D')
            elif country == 'BE':
                country_codes.append('B')
            elif country == 'ES':
                country_codes.append('E')
            elif country == 'FR':
                country_codes.append('F')
            elif country == 'IT':
                country_codes.append('I')
            elif country == 'LU':
                country_codes.append('L')
            elif country == 'NL':
                country_codes.append('NL')
        
        # If no countries specified, use all available
        if not country_codes:
            country_codes = ['D', 'A', 'B', 'E', 'F', 'I', 'L', 'NL']
            
        query_params.append(f"cy={('%2C').join(country_codes)}")
        
        # Exclude damaged listings
        query_params.append("damaged_listing=exclude")
        
        # Sorting (default: standard, no descending)
        query_params.append("desc=0")
        
        # First registration from
        if params.get('year_range', {}).get('min'):
            query_params.append(f"fregfrom={params['year_range']['min']}")
        
        # First registration to
        if params.get('year_range', {}).get('max'):
            query_params.append(f"fregto={params['year_range']['max']}")
        
        # Maximum kilometers
        if params.get('max_kilometers'):
            query_params.append(f"kmto={params['max_kilometers']}")
        
        # Include original classified listings
        query_params.append("ocs_listing=include")
        
        # Power type (kW)
        query_params.append("powertype=kw")
        
        # Minimum price
        if params.get('price_range', {}).get('min'):
            query_params.append(f"pricefrom={params['price_range']['min']}")
        
        # Maximum price
        if params.get('price_range', {}).get('max'):
            query_params.append(f"priceto={params['price_range']['max']}")
        
        # Add search_id if provided
        if params.get('search_id'):
            query_params.append(f"search_id={params['search_id']}")
        
        # Sorting (standard, age, price)
        query_params.append("sort=standard")
        
        # Source
        query_params.append("source=homepage_search-mask")
        
        # Vehicle state (New, Used)
        query_params.append("ustate=N%2CU")
        
        # Body type
        if params.get('body_type'):
            query_params.append(f"body={params['body_type']}")
        
        # Minimum seats
        if params.get('seats', {}).get('min'):
            query_params.append(f"seatsfrom={params['seats']['min']}")
        
        # Maximum seats
        if params.get('seats', {}).get('max'):
            query_params.append(f"seatsto={params['seats']['max']}")
        
        # Fuel type
        if params.get('fuel_type'):
            query_params.append(f"fuel={params['fuel_type']}")
        
        # Transmission
        if params.get('transmission'):
            query_params.append(f"gear={params['transmission']}")
        
        # Minimum doors
        if params.get('doors', {}).get('min'):
            query_params.append(f"doorfrom={params['doors']['min']}")
        
        # Maximum doors
        if params.get('doors', {}).get('max'):
            query_params.append(f"doorto={params['doors']['max']}")
        
        # Equipment
        if params.get('equipment'):
            for eq in params['equipment']:
                query_params.append(f"eq={eq}")
        
        # Color
        if params.get('color'):
            query_params.append(f"color={params['color']}")
        
        # ZIP code
        if params.get('zip'):
            query_params.append(f"zip={params['zip']}")
        
        # ZIP radius
        if params.get('zipr'):
            query_params.append(f"zipr={params['zipr']}")
        
        # Combine URL
        url = f"{base_url}?{'&'.join(query_params)}"
        logger.info(f"Built search URL: {url}")
        return url

    async def search(self, make: str, model: str, params: Dict) -> List[CarListing]:
        """Search for car listings based on the provided parameters."""
        # Prepare search parameters
        search_params = params.copy()
        search_params['make'] = make
        search_params['models'] = [model]
        
        url = self.build_search_url(search_params)
        print(f"Built search URL: {url}")
        logger.info(f"Built search URL: {url}")
        logger.info(f"Searching URL: {url}")
        
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Add a small delay to avoid rate limiting
                time.sleep(random.uniform(1.0, 2.0))
                
                print(f"Making request to {url}")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                print(f"Got response with status code {response.status_code}")
                
                # Extract total number of results from the JSON data
                total_results = 0
                try:
                    # Look for the listHeaderTitle field in the JSON data
                    match = re.search(r'"listHeaderTitle":"([^"]*)"', response.text)
                    if match:
                        header_title = match.group(1)
                        print(f"Found listHeaderTitle: {header_title}")
                        logger.info(f"Found listHeaderTitle: {header_title}")
                        # Extract the number from strings like "5.808 Angebote für Volkswagen"
                        number_match = re.search(r'(\d+(?:\.\d+)?)', header_title)
                        if number_match:
                            # Convert to integer, handling thousands separator
                            total_results_str = number_match.group(1).replace('.', '')
                            total_results = int(total_results_str)
                            print(f"Total results found: {total_results}")
                            logger.info(f"Total results found: {total_results}")
                            
                            # If there are 0 results, return an empty list
                            if total_results == 0:
                                print(f"No results found for {make} {model} according to listHeaderTitle")
                                logger.info(f"No results found for {make} {model} according to listHeaderTitle")
                                return []
                    else:
                        print("No listHeaderTitle found in the response")
                except Exception as e:
                    print(f"Error extracting total results: {e}")
                    logger.error(f"Error extracting total results: {e}")
                
                # Parse the HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all article elements that might contain car listings
                listing_elements = soup.find_all('article')
                print(f"Found {len(listing_elements)} article elements")
                logger.info(f"Found {len(listing_elements)} article elements")
                
                if not listing_elements:
                    print(f"No article elements found for {make} {model}")
                    logger.info(f"No article elements found for {make} {model}")
                    
                    # Try alternative selectors if no articles found
                    listing_elements = soup.select('[data-testid="listing-item"]')
                    if listing_elements:
                        print(f"Found {len(listing_elements)} listing items using alternative selector")
                        logger.info(f"Found {len(listing_elements)} listing items using alternative selector")
                    else:
                        # Try another alternative selector
                        listing_elements = soup.select('.ListItem_article')
                        if listing_elements:
                            print(f"Found {len(listing_elements)} listing items using .ListItem_article selector")
                            logger.info(f"Found {len(listing_elements)} listing items using .ListItem_article selector")
                    
                    if not listing_elements:
                        if total_results > 0:
                            print(f"Found {total_results} total results in header, but no listings were extracted")
                            logger.warning(f"Found {total_results} total results in header, but no listings were extracted")
                        return []
                
                # Try to identify and exclude recommendation articles
                # Look for a parent div that might contain recommendations
                main_listings = []
                recommendation_listings = []
                
                # First, try to find the main content section
                main_content = soup.find('div', class_=lambda c: c and 'ListPage_main' in c)
                recommendations_section = soup.find('div', class_=lambda c: c and 'Recommendations_recommendations' in c)
                
                if main_content:
                    # If we found the main content section, get articles only from there
                    main_listings = main_content.find_all('article')
                    print(f"Found {len(main_listings)} articles in main content section")
                    logger.info(f"Found {len(main_listings)} articles in main content section")
                
                if recommendations_section:
                    # If we found the recommendations section, identify those articles
                    recommendation_listings = recommendations_section.find_all('article')
                    print(f"Found {len(recommendation_listings)} articles in recommendations section")
                    logger.info(f"Found {len(recommendation_listings)} articles in recommendations section")
                
                # If we couldn't find the sections by class, fall back to the old method
                if not main_content:
                    print("Could not find main content section by class, using fallback method")
                    logger.warning("Could not find main content section by class, using fallback method")
                    
                    # Try to identify recommendations by looking for parent divs with 'recommendation' in class
                    for article in listing_elements:
                        is_recommendation = False
                        parent_divs = article.find_parents('div')
                        for div in parent_divs:
                            if div.get('class') and any('recommendation' in cls.lower() for cls in div.get('class')):
                                recommendation_listings.append(article)
                                is_recommendation = True
                                break
                        
                        if not is_recommendation:
                            main_listings.append(article)
                
                # If we still don't have main listings but have total_results > 0, use all listings
                if not main_listings and total_results > 0:
                    print("No main listings found, but total_results > 0. Using all listings.")
                    logger.warning("No main listings found, but total_results > 0. Using all listings.")
                    main_listings = listing_elements
                
                # Ensure we don't return more listings than reported in the header
                if total_results > 0 and len(main_listings) > total_results:
                    print(f"Limiting results to {total_results} as reported in header (found {len(main_listings)})")
                    logger.info(f"Limiting results to {total_results} as reported in header (found {len(main_listings)})")
                    main_listings = main_listings[:total_results]
                
                if not main_listings:
                    print(f"No matching listings found for {make} {model} after filtering")
                    logger.info(f"No matching listings found for {make} {model} after filtering")
                    return []
                
                print(f"Found {len(main_listings)} matching listings out of {total_results} total results")
                logger.info(f"Found {len(main_listings)} matching listings out of {total_results} total results")
                
                # Extract details from each listing
                listings = []
                for i, element in enumerate(main_listings):
                    try:
                        print(f"Processing listing {i+1}/{len(main_listings)}")
                        logger.info(f"Processing listing {i+1}/{len(main_listings)}")
                        
                        # Log the HTML structure of the element for debugging
                        element_html = str(element)
                        logger.info(f"Element HTML (first 500 chars): {element_html[:500]}...")
                        
                        listing = self.extract_listing_details(element, make, model)
                        if listing:
                            print(f"Successfully extracted listing: {listing.id}")
                            logger.info(f"Successfully extracted listing: {listing.id}")
                            listings.append(listing)
                        else:
                            print(f"Failed to extract listing {i+1}")
                            logger.warning(f"Failed to extract listing {i+1}")
                    except Exception as e:
                        print(f"Error extracting listing details: {e}")
                        logger.error(f"Error extracting listing details: {e}")
                
                print(f"Successfully extracted {len(listings)} listings")
                logger.info(f"Successfully extracted {len(listings)} listings")
                return listings
            
            except requests.RequestException as e:
                retry_count += 1
                print(f"Request failed (attempt {retry_count}/{max_retries}): {e}")
                logger.warning(f"Request failed (attempt {retry_count}/{max_retries}): {e}")
                if retry_count >= max_retries:
                    print(f"Max retries reached. Failed to fetch search results: {e}")
                    logger.error(f"Max retries reached. Failed to fetch search results: {e}")
                    return []
                time.sleep(random.uniform(2.0, 5.0))  # Longer delay between retries
        
        print("All search attempts failed")
        logger.error("All search attempts failed")
        return []

    def extract_listing_details(self, element, make: str, model: str) -> Optional[CarListing]:
        """Extract details from a listing element."""
        try:
            # Extract listing ID from the article element
            listing_id = element.get('id', '')
            logger.info(f"Extracting details for listing ID: {listing_id}")
            
            # If ID not found in article, try to extract from URL
            if not listing_id:
                url_element = element.select_one('a')
                if url_element and 'href' in url_element.attrs:
                    url = url_element['href']
                    # Extract ID from the end of the URL
                    listing_id = url.split('/')[-1]
                    logger.info(f"Extracted ID from URL: {listing_id}")
            
            # Extract URL
            url_element = element.select_one('a')
            url = url_element['href'] if url_element and 'href' in url_element.attrs else ''
            full_url = f"{self.base_url}{url}" if url.startswith('/') else url
            logger.info(f"Extracted URL: {full_url}")
            
            # Extract title
            title = ''
            title_element = element.select_one('h2')
            if title_element:
                title = title_element.get_text(strip=True)
                logger.info(f"Extracted title: {title}")
            
            # Initialize variables
            price = 0
            year = 0
            kilometers = 0
            location = ''
            
            # NEW APPROACH: First try to extract data directly from data attributes
            # This is the most reliable source for all the data
            logger.info("Trying to extract data from data attributes")
            
            # Extract data from data attributes
            data_attrs = {k: v for k, v in element.attrs.items() if k.startswith('data-')}
            logger.info(f"Found {len(data_attrs)} data attributes")
            
            # Extract mileage from data-mileage attribute
            if 'data-mileage' in data_attrs:
                try:
                    kilometers = int(data_attrs['data-mileage'])
                    logger.info(f"Extracted kilometers {kilometers} from data-mileage attribute")
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert data-mileage '{data_attrs['data-mileage']}' to integer")
            
            # Extract year from data-first-registration attribute
            if 'data-first-registration' in data_attrs:
                reg_str = data_attrs['data-first-registration']
                logger.info(f"Found first registration: {reg_str}")
                
                # Try different patterns for registration date
                year_match = re.search(r'(\d{2})-(\d{4})', reg_str)
                if year_match:
                    year = int(year_match.group(2))
                    logger.info(f"Extracted year {year} from data-first-registration attribute")
                else:
                    year_match = re.search(r'(\d{4})', reg_str)
                    if year_match:
                        year = int(year_match.group(1))
                        logger.info(f"Extracted year {year} from data-first-registration attribute")
            
            # Extract price from data-price attribute
            if 'data-price' in data_attrs:
                try:
                    price = int(data_attrs['data-price'])
                    logger.info(f"Extracted price {price} from data-price attribute")
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert data-price '{data_attrs['data-price']}' to integer")
            
            # Extract location from data-listing-zip-code and data-listing-city attributes
            city = data_attrs.get('data-listing-city', '')
            zip_code = data_attrs.get('data-listing-zip-code', '')
            if city or zip_code:
                location = f"{city} {zip_code}".strip()
                logger.info(f"Extracted location {location} from data attributes")
            
            # If we couldn't extract from data attributes, fall back to the previous methods
            
            # FALLBACK 1: Try to extract from vehicleDetails JSON array
            if kilometers == 0 or year == 0 or price == 0:
                element_str = str(element)
                vehicle_details_match = re.search(r'"vehicleDetails":\s*(\[.*?\])(?=,)', element_str, re.DOTALL)
                
                if vehicle_details_match:
                    try:
                        vehicle_details = json.loads(vehicle_details_match.group(1))
                        logger.info(f"Successfully parsed vehicleDetails JSON array with {len(vehicle_details)} items")
                        
                        for detail in vehicle_details:
                            if 'data' in detail and 'iconName' in detail:
                                logger.info(f"Processing detail: {detail}")
                                # Check for kilometers
                                if 'mileage' in detail['iconName'] and kilometers == 0:
                                    km_text = re.sub(r'[^\d]', '', detail['data'])
                                    if km_text:
                                        try:
                                            kilometers = int(km_text)
                                            logger.info(f"Extracted kilometers {kilometers} from vehicleDetails JSON")
                                        except ValueError:
                                            logger.warning(f"Could not convert kilometers text '{detail['data']}' to integer")
                                
                                # Check for year/registration date
                                elif 'calendar' in detail['iconName'] and year == 0:
                                    year_match = re.search(r'(\d{2})/(\d{4})', detail['data'])
                                    if year_match:
                                        year = int(year_match.group(2))
                                        logger.info(f"Extracted year {year} from vehicleDetails JSON")
                                    else:
                                        year_match = re.search(r'(\d{4})', detail['data'])
                                        if year_match:
                                            year = int(year_match.group(1))
                                            logger.info(f"Extracted year {year} from vehicleDetails JSON")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Error parsing vehicleDetails JSON: {e}")
                else:
                    logger.warning("No vehicleDetails JSON array found in the element")
            
            # FALLBACK 2: Try to extract from tracking data
            if kilometers == 0 or year == 0 or price == 0:
                element_str = str(element)
                tracking_match = re.search(r'"tracking":\s*({.*?})(?=,)', element_str, re.DOTALL)
                
                if tracking_match:
                    try:
                        tracking_data = json.loads(tracking_match.group(1))
                        logger.info(f"Tracking data: {tracking_data}")
                        
                        # Extract year if not already found
                        if 'firstRegistration' in tracking_data and year == 0:
                            logger.info(f"First registration from tracking: {tracking_data['firstRegistration']}")
                            reg_match = re.search(r'(\d{2})-(\d{4})', tracking_data['firstRegistration'])
                            if reg_match:
                                year = int(reg_match.group(2))
                                logger.info(f"Extracted year {year} from tracking data")
                        
                        # Extract kilometers if not already found
                        if 'mileage' in tracking_data and kilometers == 0:
                            logger.info(f"Mileage from tracking: {tracking_data['mileage']}")
                            try:
                                kilometers = int(tracking_data['mileage'])
                                logger.info(f"Extracted kilometers {kilometers} from tracking data")
                            except (ValueError, TypeError):
                                logger.warning(f"Could not convert mileage '{tracking_data['mileage']}' to integer")
                        
                        # Extract price if not already found
                        if 'price' in tracking_data and price == 0:
                            logger.info(f"Price from tracking: {tracking_data['price']}")
                            try:
                                price = int(tracking_data['price'])
                                logger.info(f"Extracted price {price} from tracking data")
                            except (ValueError, TypeError):
                                logger.warning(f"Could not convert price '{tracking_data['price']}' to integer")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Error parsing tracking JSON: {e}")
                else:
                    logger.warning("No tracking data found in the element")
            
            # FALLBACK 3: Try to extract price from price object
            if price == 0:
                element_str = str(element)
                price_match = re.search(r'"price":({[^}]+})', element_str)
                if price_match:
                    try:
                        price_data_str = '{' + price_match.group(1).strip('{').strip('}') + '}'
                        price_data = json.loads(price_data_str)
                        logger.info(f"Price data: {price_data}")
                        
                        if 'priceFormatted' in price_data:
                            price_formatted = price_data['priceFormatted']
                            logger.info(f"Formatted price: {price_formatted}")
                            # Extract digits only from formatted price (e.g., "€ 15.990,-")
                            price_digits = re.sub(r'[^\d]', '', price_formatted)
                            if price_digits:
                                try:
                                    price = int(price_digits)
                                    logger.info(f"Extracted price {price} from price object")
                                except ValueError:
                                    logger.warning(f"Could not convert price '{price_formatted}' to integer")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Error parsing price JSON: {e}")
            
            # FALLBACK 4: Try to extract location from location element
            if not location:
                location_element = element.select_one('.location')
                if location_element:
                    location = location_element.get_text(strip=True)
                    logger.info(f"Extracted location {location} from location element")
            
            # Ensure we have valid data before creating the CarListing
            if not listing_id:
                logger.warning("No listing ID found, cannot create CarListing")
                return None
            
            # Create CarListing object
            car_listing = CarListing(
                id=listing_id,
                make=make,
                model=model,
                title=title,
                price=price,
                year=year,
                kilometers=kilometers,
                location=location,
                url=full_url,
                first_seen=datetime.now(),
                last_seen=datetime.now()
            )
            
            logger.info(f"Created CarListing: {car_listing}")
            return car_listing
            
        except Exception as e:
            logger.error(f"Error extracting listing details: {e}")
            return None 