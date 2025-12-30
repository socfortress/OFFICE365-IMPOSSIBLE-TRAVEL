# Quick Start Guide

## Overview

This FastAPI application detects impossible travel by analyzing login patterns. When a user logs in from different countries or distant locations within a short time window (e.g., USA then Canada 5 minutes later), the system flags it as impossible travel.

## Installation & Setup

1. **Install Dependencies**

    ```bash
    cd app
    pip install -r requirements.txt
    ```

2. **Configure Settings**

    ```bash
    # Copy the example environment file
    cp .env.example .env

    # Edit .env to customize settings
    # - IMPOSSIBLE_TRAVEL_TIME_WINDOW: Time window in minutes (default: 5)
    # - MAX_RECORDS_PER_USER: Number of records to keep per user (default: 10)
    # - MIN_DISTANCE_KM: Minimum distance in km for same country (default: 100)
    ```

3. **Start the Server**

    ```bash
    cd app
    python module.py
    ```

    The API will start on http://localhost:80

## Usage

### Analyze a Login

Send a GET request with user, IP, and timestamp:

```bash
curl "http://localhost/analyze?query=user%3Dtest%40socfortress.com%7Cip%3D102.78.106.220%7Cts%3D2025-12-10T10%3A17%3A54"
```

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

### Test with the Test Script

Run the included test script:

```bash
# Run a complete test scenario
python test_api.py scenario

# Check database statistics
python test_api.py stats

# Test a single login
python test_api.py test user@example.com 8.8.8.8 2025-12-10T10:00:00
```

### View API Documentation

Open http://localhost/docs in your browser for interactive API documentation.

## How It Works

1. **Receive Request**: API receives login data (user, IP, timestamp)
2. **Geolocate IP**: Looks up the geographic location of the IP address
3. **Check History**: Retrieves previous logins for the user from SQLite database
4. **Compare Locations**: Checks if user is in a different country or distant location
5. **Check Time Window**: Verifies if logins occurred within configured time window
6. **Detect**: Flags as impossible travel if different locations within time window
7. **Store**: Saves login and maintains rolling history

**Example**: User logs in from USA → 5 minutes later → logs in from Canada = Impossible Travel

-   ✅ Automatic IP geolocation
-   ✅ Detects logins from different countries within time window
-   ✅ Configurable time windows and distance thresholds
-   ✅ SQLite database for login history
-   ✅ Auto-cleanup of old records
-   ✅ REST API with full documentation
-   ✅ Easy Graylog integration

## Configuration Parameters

| Parameter                     | Default                     | Description                                                                                            |
| ----------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------ |
| IMPOSSIBLE_TRAVEL_TIME_WINDOW | 5                           | Time window in minutes - logins from different locations within this window are flagged                |
| MAX_RECORDS_PER_USER          | 10                          | Number of login records to keep per user                                                               |
| MIN_DISTANCE_KM               | 100                         | Minimum distance in km between locations (same country). Different countries always trigger detection. |
| DATABASE_PATH                 | ./data/impossible_travel.db | Path to SQLite database                                                                                |
| API_HOST                      | 0.0.0.0                     | Server host binding                                                                                    |
| API_PORT                      | 80                          | Server port                                                                                            |
| LOG_LEVEL                     | INFO                        | Logging level                                                                                          |

## API Endpoints

| Endpoint | Method | Description                           |
| -------- | ------ | ------------------------------------- |
| /analyze | GET    | Analyze a login for impossible travel |
| /purge   | POST   | Purge all records from database       |
| /stats   | GET    | Get database statistics               |
| /health  | GET    | Health check                          |
| /docs    | GET    | Interactive API documentation         |

## Example Response

When impossible travel is detected:

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

## Graylog Integration

Configure an HTTP Notification in Graylog:

-   URL: `http://your-server/analyze?query=user=${user.username}|ip=${source}|ts=${timestamp}`
-   Method: GET

## Troubleshooting

**Q: Geolocation not working?**

-   Check internet connection
-   ip-api.com has a free tier limit of 45 requests/minute

**Q: Too many false positives?**

-   Increase `IMPOSSIBLE_TRAVEL_TIME_WINDOW` (e.g., 30 minutes, 1 hour)
-   Increase `MIN_DISTANCE_KM` to only flag locations further apart
-   Consider VPN usage in your environment

**Q: Database issues?**

-   Ensure `data/` directory exists and is writable
-   Check file permissions on the database

## Support

For issues or questions, refer to the full README.md file.
