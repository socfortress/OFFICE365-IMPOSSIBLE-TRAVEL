# Office 365 Impossible Travel Detection API

A FastAPI application that detects impossible travel patterns based on user login locations and timestamps. This system analyzes login attempts from Office 365 (or any system) to identify when a user logs in from different geographic locations within a short time window that would be impossible to physically travel between.

## Features

-   🌍 **IP Geolocation**: Automatically geolocates IP addresses to determine login locations
-   ⚡ **Impossible Travel Detection**: Identifies when users login from different countries or distant locations within a configured time window
-   💾 **SQLite Database**: Stores login history for pattern analysis
-   ⚙️ **Configurable**: Customizable time windows, distance thresholds, and record retention
-   🔄 **Auto-cleanup**: Automatically maintains a rolling window of login records per user
-   📊 **Statistics**: View database stats and analytics

## How It Works

1. **Receive Login Data**: API receives GET requests from Graylog (or any system) with user, IP, and timestamp
2. **Geolocate IP**: Looks up the geographic location of the IP address
3. **Check History**: Retrieves previous login records for the user from SQLite database
4. **Compare Locations**: Checks if the user logged in from a different country or distant location
5. **Check Time Window**: Verifies if the logins occurred within the configured time window
6. **Detect Anomaly**: Flags as impossible travel if user is in different locations within the time window
7. **Store Record**: Saves the login attempt and maintains the configured number of historical records

**Example**: If a user logs in from the United States, then 5 minutes later logs in from Canada, this is flagged as impossible travel.

## Quick Start with Docker Compose (Recommended)

### Prerequisites

-   Docker and Docker Compose installed
-   That's it!

### Setup

1. Create a new directory for the deployment:

```bash
mkdir impossible-travel-detection
cd impossible-travel-detection
```

2. Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  impossible-travel-api:
    image: ghcr.io/socfortress/office365-impossible-travel:latest
    container_name: impossible-travel-detection
    restart: unless-stopped
    ports:
      - "80:80"  # Change left side to 8000:80 if port 80 is in use
    environment:
      # Time window in minutes for impossible travel detection
      - IMPOSSIBLE_TRAVEL_TIME_WINDOW=${IMPOSSIBLE_TRAVEL_TIME_WINDOW:-5}

      # Maximum number of login records to keep per user
      - MAX_RECORDS_PER_USER=${MAX_RECORDS_PER_USER:-10}

      # Minimum distance in km to consider as different location (within same country)
      - MIN_DISTANCE_KM=${MIN_DISTANCE_KM:-100}

      # Database path (inside container)
      - DATABASE_PATH=/opt/copilot/app/data/impossible_travel.db

      # API Configuration
      - API_HOST=0.0.0.0
      - API_PORT=80

      # Log Level
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      # Persist SQLite database
      - ./data:/opt/copilot/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - impossible-travel-net

networks:
  impossible-travel-net:
    driver: bridge

volumes:
  data:
    driver: local
```

3. Create a `.env` file (optional - for custom settings):

```bash
# Time window for impossible travel detection (in minutes)
IMPOSSIBLE_TRAVEL_TIME_WINDOW=5

# Maximum number of login records to keep per user
MAX_RECORDS_PER_USER=10

# Minimum distance in km to consider as different location (within same country)
MIN_DISTANCE_KM=100

# Log Level
LOG_LEVEL=INFO
```

4. Start the service:

```bash
docker-compose up -d
```

5. Access the API:
   - **Swagger UI**: http://localhost/docs
   - **API Health**: http://localhost/health
   - **Statistics**: http://localhost/stats

**That's it!** The database will be created automatically in the `./data` directory.

### Managing the Service

**View logs:**
```bash
docker-compose logs -f
```

**Stop the service:**
```bash
docker-compose down
```

**Update to latest version:**
```bash
docker-compose pull
docker-compose up -d
```

**Reset the database:**
```bash
docker-compose down
rm -rf data/
docker-compose up -d
```

## Configuration

Edit the `.env` file to customize behavior:

```env
# Time window for impossible travel detection (in minutes)
IMPOSSIBLE_TRAVEL_TIME_WINDOW=5

# Maximum number of login records to keep per user
MAX_RECORDS_PER_USER=10

# Minimum distance in km to consider as different location (within same country)
MIN_DISTANCE_KM=100

# Database path
DATABASE_PATH=./data/impossible_travel.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=80

# Log Level
LOG_LEVEL=INFO
```

### Configuration Parameters

-   **IMPOSSIBLE_TRAVEL_TIME_WINDOW**: Time window in minutes. If a user logs in from different locations within this window, it's flagged as impossible travel
-   **MAX_RECORDS_PER_USER**: Number of historical logins to keep per user. Older records are automatically deleted
-   **MIN_DISTANCE_KM**: Minimum distance in km between locations (within same country) to consider as different locations. Different countries always trigger detection.
-   **DATABASE_PATH**: Path to SQLite database file
-   **API_HOST/PORT**: Server binding configuration
-   **LOG_LEVEL**: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Alternative: Running from Source

If you want to develop or modify the code:

1. Clone the repository:
```bash
git clone https://github.com/socfortress/office365-impossible-travel.git
cd office365-impossible-travel
```

2. Install dependencies:
```bash
cd app
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp ../.env.example ../.env
# Edit .env with your settings
```

4. Run the application:
```bash
python module.py
```

## API Endpoints

### 1. Analyze Login (GET /analyze)

Analyze a login attempt for impossible travel.

**Query Format:**

```
/analyze?query=user=email@domain.com|ip=1.2.3.4|ts=2025-12-10T10:17:54
```

**Example Request:**

```bash
curl "http://localhost/analyze?query=user%3Dtest%40socfortress.com%7Cip%3D102.78.106.220%7Cts%3D2025-12-10T10%3A17%3A54"
```

**Example Response (No Impossible Travel):**

```json
{
    "user": "test@socfortress.com",
    "current_ip": "102.78.106.220",
    "current_location": {
        "country": "Morocco",
        "city": "Casablanca",
        "latitude": 33.5731,
        "longitude": -7.5898
    },
    "current_timestamp": "2025-12-10T10:17:54",
    "impossible_travel_detected": false,
    "message": "First login for this user"
}
```

**Example Response (Impossible Travel Detected):**

```json
{
    "user": "test@socfortress.com",
    "current_ip": "8.8.8.8",
    "current_location": {
        "country": "United States",
        "city": "Mountain View",
        "latitude": 37.386,
        "longitude": -122.0838
    },
    "current_timestamp": "2025-12-10T10:22:54",
    "impossible_travel_detected": true,
    "previous_login": {
        "user": "test@socfortress.com",
        "ip": "102.78.106.220",
        "country": "Morocco",
        "city": "Casablanca",
        "latitude": 33.5731,
        "longitude": -7.5898,
        "timestamp": "2025-12-10T10:17:54"
    },
    "distance_km": 5896.42,
    "time_difference_minutes": 5.0,
    "message": "IMPOSSIBLE TRAVEL DETECTED: User logged in from Morocco and then from United States within 5.0 minutes (5896.42 km apart)"
}
```

### 2. Purge Database (POST /purge)

Delete all login history records from the database.

**Request:**

```bash
curl -X POST "http://localhost/purge"
```

**Response:**

```json
{
    "success": true,
    "message": "Successfully purged 42 records from database",
    "records_deleted": 42
}
```

### 3. Get Statistics (GET /stats)

Get database statistics.

**Request:**

```bash
curl "http://localhost/stats"
```

**Response:**

```json
{
    "total_records": 150,
    "unique_users": 25
}
```

### 4. Health Check (GET /health)

Check if the API is running.

**Request:**

```bash
curl "http://localhost/health"
```

**Response:**

```json
{
    "status": "healthy",
    "service": "impossible-travel-detection"
}
```

### 5. API Documentation (GET /docs)

Interactive API documentation (Swagger UI):

```
http://localhost/docs
```

## Graylog Integration

To integrate with Graylog, configure an HTTP Notification with the following settings:

1. **URL**: `http://your-api-server/analyze?query=${key}`
2. **Single value JSONPath**: `$.success`
3. **Multi value JSONPath**: `$.result`
3. **Headers**: None required

Graylog will automatically URL-encode the parameters.

### Graylog Pipeline Rule

```
rule "impossible_travel_office365_api_lookup"
when
  has_field("data_office365_UserId") &&
  has_field("data_office365_ActorIpAddress") &&
  has_field("data_office365_CreationTime")
then
  // Extract required values
  let user_id = to_string($message.data_office365_UserId);
  let ip     = to_string($message.data_office365_ActorIpAddress);
  let ts      = to_string($message.data_office365_CreationTime);

  /*
    Build a single lookup key.
    Your FastAPI service will parse this.
    Example received by API:
      user=user@example.com|ip=1.1.1.1|ts=2025-12-10T10:17:54
  */
  let query = concat("user=", user_id);
  let query = concat(query, "|ip=");
  let query = concat(query, ip);
  let query = concat(query, "|ts=");
  let query = concat(query, ts);

  // Call the lookup table backed by the HTTP data adapter
  let result = lookup("impossible_travel_api", query);

  // Store the raw response for inspection / debugging
  set_field("impossible_travel_result", result);

end
```

## Use Cases

### Security Monitoring

-   Detect compromised accounts accessing from multiple geographic locations
-   Identify credential sharing across different regions
-   Flag potential account takeovers

### Compliance

-   Audit user access patterns
-   Monitor for policy violations (e.g., accessing from restricted countries)
-   Generate reports on login anomalies

### Fraud Detection

-   Identify suspicious login patterns
-   Detect automated attacks from distributed sources
-   Flag high-risk authentication attempts

## Database Schema

The SQLite database stores login history with the following schema:

```sql
CREATE TABLE login_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    ip TEXT NOT NULL,
    country TEXT NOT NULL,
    city TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    timestamp TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_timestamp ON login_history(user, timestamp DESC);
```

## Architecture

```
┌─────────────┐
│   Graylog   │
│  (or other) │
└──────┬──────┘
       │ GET /analyze?query=...
       ▼
┌─────────────────────────────────┐
│      FastAPI Application        │
│                                 │
│  ┌──────────────────────────┐  │
│  │   Analyze Endpoint       │  │
│  └────────┬─────────────────┘  │
│           │                     │
│           ▼                     │
│  ┌──────────────────────────┐  │
│  │ Impossible Travel        │  │
│  │ Detection Service        │  │
│  └────┬─────────────┬───────┘  │
│       │             │           │
│       ▼             ▼           │
│  ┌─────────┐  ┌──────────┐    │
│  │Geolocation│ │ Database │    │
│  │ Service  │  │ Service  │    │
│  │(ip-api)  │  │(SQLite)  │    │
│  └─────────┘  └──────────┘    │
└─────────────────────────────────┘
```

## Development

### Project Structure

```
OFFICE365-IMPOSSIBLE-TRAVEL/
├── .env                                 # Configuration
├── .env.example                         # Example configuration
├── README.md                            # This file
└── app/
    ├── Dockerfile                       # Docker configuration
    ├── module.py                        # Main FastAPI application
    ├── requirements.in                  # Python dependencies (source)
    ├── requirements.txt                 # Pinned dependencies
    ├── routes/
    │   └── analyze.py                   # API endpoints
    ├── schema/
    │   └── impossible_travel.py         # Pydantic models
    └── services/
        ├── database.py                  # Database operations
        ├── geolocation.py               # IP geolocation
        └── impossible_travel.py         # Detection logic
```

### Testing

You can test the API with sample requests:

```bash
# First login (will be stored)
curl "http://localhost/analyze?query=user%3Dtest%40example.com%7Cip%3D8.8.8.8%7Cts%3D2025-12-10T10%3A00%3A00"

# Second login from different location 5 minutes later (should detect impossible travel)
curl "http://localhost/analyze?query=user%3Dtest%40example.com%7Cip%3D102.78.106.220%7Cts%3D2025-12-10T10%3A05%3A00"
```

## Troubleshooting

### Database Issues

-   Check that the `DATABASE_PATH` directory exists and is writable
-   Verify SQLite database file permissions

### Geolocation Failures

-   The API uses ip-api.com (free tier: 45 requests/minute)
-   Check your internet connection
-   Consider implementing a paid geolocation service for production

### False Positives

-   Increase `IMPOSSIBLE_TRAVEL_TIME_WINDOW` for less sensitive detection (e.g., 30 minutes, 1 hour, 24 hours)
-   Adjust `MIN_DISTANCE_KM` to only flag locations further apart
-   Consider VPN usage patterns in your environment (VPNs can make users appear in different countries)

### False Negatives

-   Decrease `IMPOSSIBLE_TRAVEL_TIME_WINDOW` to catch faster location changes
-   Reduce `MIN_DISTANCE_KM` to detect smaller distance changes within same country

## License

This project is provided as-is for security monitoring purposes.

## Contributing

Feel free to submit issues and enhancement requests!
