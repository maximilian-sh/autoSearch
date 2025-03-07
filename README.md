# AutoSearch

A car listing crawler for AutoScout24 that monitors listings based on your search criteria and sends notifications via Telegram when new matches are found.

## Features

-   Monitors AutoScout24 for cars matching your specific criteria
-   Supports a wide range of search parameters (make, model, price, year, seats, etc.)
-   Only extracts exact matching results, ignoring recommended vehicles
-   Sends Telegram notifications for new listings with properly formatted titles
-   Supports sending notifications to multiple Telegram users
-   Automatically removes listings that are no longer available
-   Runs continuously in the background
-   Supports multiple configuration files for different search criteria

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory with your Telegram credentials:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_IDS=id1,id2,id3
```

To get these values:

-   Create a new bot using [@BotFather](https://t.me/botfather) on Telegram to get the `TELEGRAM_BOT_TOKEN`
-   Send a message to your bot and visit `https://api.telegram.org/bot<YourBOTToken>/getUpdates` to get the chat IDs
-   For multiple users, add all chat IDs separated by commas (no spaces)
-   For backward compatibility, you can also use `TELEGRAM_CHAT_ID` for a single user

3. Configure your search parameters by creating one or more configuration files in the `config` directory. See the [Configuration](#configuration) section for details.

## Usage

Run the script:

```bash
python run.py
```

The script will:

1. Load all configuration files from the `config` directory
2. Monitor AutoScout24 for cars matching your criteria
3. Store listings in a local SQLite database
4. Send Telegram notifications when new matches are found
5. Remove listings that are no longer available
6. Run continuously until interrupted (Ctrl+C)

### Database Management

#### Checking Database Status

To check the current status of the database:

```bash
python check_db.py
```

This will show:

-   Total number of listings in the database
-   Breakdown by make and model
-   Details of the 5 most recent listings

#### Clearing the Database

If you want to clear all stored listings and start fresh:

```bash
python clear_db.py
```

This will remove all listings from the database but keep the database structure intact.

## Configuration

The application supports multiple configuration files in the `config` directory. Each file should be a YAML file with the following structure:

### Configuration Files

-   `default_config.yaml`: A template with all available options set to null/default values
-   Create your own configuration files (e.g., `volkswagen_vans.yaml`, `luxury_cars.yaml`) based on the template

You can have multiple configuration files for different types of searches. The application will load all `.yaml` files in the `config` directory (except for `default_config.yaml`).

### Basic Structure

Each configuration file should have the following structure:

```yaml
searches:
    - name: "My Search Name" # Give your search a descriptive name
      make: "Brand" # Brand name
      models:
          - "Model1" # You can add multiple models
          - "Model2"
      # Other search parameters...

general:
    # General settings
    check_interval_minutes: 15
    countries: ["DE", "AT"]
    notification_type: "telegram"
```

### Basic Parameters

```yaml
searches:
    - name: "Volkswagen T5/T6 Vans" # Descriptive name for this search
      make: "Volkswagen" # Brand name
      models:
          - "T5" # You can add multiple models
          - "T6"
      # Price range in EUR
      price_range:
          min: 0 # Minimum price
          max: 15000 # Maximum price
      # Registration year
      year_range:
          min: 2010 # From year
          max: null # To year (null = no limit)
```

### Vehicle Specifications

```yaml
# Mileage
max_kilometers: 200000 # Maximum kilometers

# Body type codes:
# 1 = Limousine, 2 = Van/Kleinbus, 3 = Kombi, 4 = Cabrio, 5 = SUV/Geländewagen
# 6 = Sportwagen/Coupé, 7 = Andere
body_type: 2 # Van/Kleinbus

# Number of seats
seats:
    min: 8 # Minimum seats
    max: 12 # Maximum seats

# Fuel type codes:
# D = Diesel, B = Gasoline/Petrol, E = Electric, L = LPG, C = CNG
# H = Hybrid (Petrol/Electric), M = Hybrid (Diesel/Electric), O = Other
fuel_type: "D" # Diesel

# Transmission type:
# A = Automatic, M = Manual, S = Semi-automatic
transmission: "A" # Automatic

# Number of doors
doors:
    min: 4 # Minimum doors
    max: 5 # Maximum doors
```

### Additional Features

```yaml
# Equipment/Features codes:
# 1 = Air conditioning, 2 = Alarm system, 3 = Alloy wheels, 4 = Bluetooth
# 5 = Central locking, 6 = Cruise control, 7 = Electric windows
# 8 = Heated seats, 9 = Navigation system, 10 = Parking sensors
# 11 = Power steering, 12 = Rain sensor, 13 = Start/stop system
# 14 = Sunroof, 15 = Tinted windows, 16 = Xenon headlights
# 17 = Leather seats, 18 = Roof rack, 19 = Sliding door
# 20 = Trailer hitch, 21 = Winter tires
equipment: [20, 8, 9] # Multiple features: Trailer hitch, Heated seats, Navigation

# Color codes:
# 0 = Not specified, 1 = Black, 2 = Blue, 3 = Brown, 4 = Beige
# 5 = Yellow, 6 = Grey, 7 = Green, 8 = Red, 9 = Silver, 10 = White
color: 9 # Silver

# Power range in kW
power_range:
    min: 75 # Minimum power in kW
    max: 150 # Maximum power in kW
```

### General Settings

```yaml
general:
    # How often to check for new listings (in minutes)
    check_interval_minutes: 15

    # Countries to search in
    # Available country codes:
    # AT = Austria, DE = Germany, BE = Belgium, ES = Spain
    # FR = France, IT = Italy, LU = Luxembourg, NL = Netherlands
    countries: ["AT", "DE"]

    # Notification type (currently only telegram is supported)
    notification_type: "telegram"
```

### Multiple Searches in One File

You can define multiple searches in a single configuration file:

```yaml
searches:
    - name: "BMW Luxury Sedans"
      make: "BMW"
      models:
          - "7er"
          - "5er"
      # Parameters for BMW search...

    - name: "Mercedes Luxury"
      make: "Mercedes-Benz"
      models:
          - "S-Klasse"
          - "E-Klasse"
      # Parameters for Mercedes search...

general:
    # General settings apply to all searches in this file
    check_interval_minutes: 30
    countries: ["DE"]
    notification_type: "telegram"
```

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). This means:

-   You are free to use, modify, and distribute this software
-   If you modify the software, you must distribute the source code of your modifications
-   If you run a modified version of this software as a service (e.g., on a website), you must make the complete source code available to users of that service
-   Any derivative work must also be licensed under AGPL-3.0

This license was chosen to ensure that improvements to the software remain available to the community, even when used in network services.

For the full license text, see the [LICENSE](LICENSE) file.

## Notes

-   The script uses requests and BeautifulSoup for web scraping
-   Listings are stored in a local SQLite database (`data/listings.db`)
-   The script respects website rate limits to avoid being blocked
-   Error notifications are sent via Telegram if something goes wrong
-   The scraper only extracts exact matching results, ignoring the "Diese Fahrzeuge könnten Dir gefallen" (recommended vehicles) section
-   Vehicle titles are properly formatted for better readability in notifications
