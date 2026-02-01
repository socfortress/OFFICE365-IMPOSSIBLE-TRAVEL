# Office 365 Impossible Travel Detection API

A FastAPI application that detects impossible travel patterns based on user login locations and timestamps. This system analyzes login attempts from Office 365 (or any system) to identify when a user logs in from different geographic locations within a short time window that would be impossible to physically travel between.

## Features

-   🌍 **IP Geolocation**: Automatically geolocates IP addresses to determine login locations
-   ⚡ **Impossible Travel Detection**: Identifies when users login from different countries or distant locations within a configured time window
-   💾 **SQLite Database**: Stores login history for pattern analysis
-   ⚙️ **Configurable**: Customizable time windows, distance thresholds, and record retention
-   🔄 **Auto-cleanup**: Automatically maintains a rolling window of login records per user
-   📊 **Statistics**: View database stats and analytics

## Video Tutorial

📺 **Watch the complete tutorial walkthrough**: [Office 365 Impossible Travel Detection - Setup Guide](https://youtu.be/is1ic1Fma1I)

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

## Wazuh Manager Integration

Use Wazuh Manager to call the `/analyze` endpoint directly from Office 365 alerts. See the installation and configuration guide in `wazuh/README.md`.

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

### Pipeline Rule Test Data
```json
{
  "data_office365_Version": "1",
  "source_reserved_ip": true,
  "data_office365_ClientIP_geolocation": "33.5922,-7.6184",
  "agent_id": "000",
  "agent_name": "mgr-node-01",
  "gl2_remote_ip": "10.10.20.30",
  "data_office365_ResultStatus": "Success",
  "gl2_remote_port": 48556,
  "data_office365_ClientIP_city_name": "Casablanca",
  "data_office365_UserKey": "0f3b6e7a-1c2d-4b5a-9e1f-1a2b3c4d5e6f",
  "source": "10.10.20.30",
  "data_office365_InterSystemsId": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "gl2_source_input": "aaaaaaaaaaaaaaaaaaaaaaaa",
  "rule_level": 3,
  "data_office365_ActorContextId": "b1c2d3e4-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
  "data_office365_ClientIP_country_code": "MA",
  "gl2_processing_timestamp": "2025-12-10 10:22:32.140",
  "data_office365_ClientIP": "102.78.106.220",
  "syslog_type": "office365",
  "rule_description": "Office 365: Secure Token Service (STS) logon events in Azure Active Directory.",
  "gl2_source_node": "cccccccc-cccc-cccc-cccc-cccccccccccc",
  "data_office365_OrganizationId": "d7e8f9a0-1b2c-3d4e-5f6a-7b8c9d0e1f2a",
  "id": "1765362148.159908",
  "data_office365_ActorIpAddress_geolocation": "33.5922,-7.6184",
  "data_office365_CreationTime": "2025-12-10T10:17:54",
  "gl2_processing_duration_ms": 2,
  "gl2_accounted_message_size": 4876,
  "data_integration": "office365",
  "streams": [
    "bbbbbbbbbbbbbbbbbbbbbbbb"
  ],
  "data_office365_ExtendedProperties": "{Name=ResultStatusDetail, Value=Redirect}, {Name=UserAgent, Value=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36}, {Name=RequestType, Value=OAuth2:Authorize}",
  "gl2_message_id": "01KC3WHCPB1TJWWG8DFA4R2HS3",
  "data_office365_Id": "e9836c09-aad3-482b-8ecc-2c67d8e93a00",
  "data_office365_AzureActiveDirectoryEventType": "1",
  "data_office365_ActorIpAddress_city_name": "Casablanca",
  "data_office365_Operation": "UserLoggedIn",
  "data_office365_ActorIpAddress": "102.78.106.220",
  "true": 1765362148.975397,
  "data_office365_ApplicationId": "9199bf20-a13f-4107-85dc-02114787ef48",
  "data_office365_Subscription": "Audit.AzureActiveDirectory",
  "rule_hipaa": "164.312.a.2.I, 164.312.b, 164.312.d, 164.312.e.2.II",
  "_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
  "rule_groups": "office365, AzureActiveDirectoryStsLogon",
  "data_office365_UserType": "0",
  "data_office365_UserId": "user@example.com",
  "data_office365_DeviceProperties": "{Name=OS, Value=Linux}, {Name=BrowserType, Value=Chrome}, {Name=IsCompliant, Value=False}, {Name=IsCompliantAndManaged, Value=False}, {Name=SessionId, Value=eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee}",
  "data_office365_Actor": "{ID=0f3b6e7a-1c2d-4b5a-9e1f-1a2b3c4d5e6f, Type=0}, {ID=user@example.com, Type=5}",
  "data_office365_Target": "{ID=00000002-0000-0ff1-ce00-000000000000, Type=0}",
  "gl2_receive_timestamp": "2025-12-10 10:22:32.138",
  "rule_firedtimes": 1,
  "rule_mail": false,
  "rule_pci_dss": "8.3, 10.6.1",
  "decoder_name": "json",
  "data_office365_TargetContextId": "d7e8f9a0-1b2c-3d4e-5f6a-7b8c9d0e1f2a",
  "syslog_level": "INFO",
  "data_office365_ObjectId": "00000002-0000-0ff1-ce00-000000000000",
  "data_office365_IntraSystemId": "e9836c09-aad3-482b-8ecc-2c67d8e93a00",
  "timestamp": "2025-12-10T10:22:32.139Z",
  "cluster_name": "cluster-01",
  "data_office365_RecordType": "15",
  "gl2_processing_error": "Replaced invalid timestamp value in message <dddddddd-dddd-dddd-dddd-dddddddddddd> with current time - Value <2025-12-10T10:22:28.026+0000> caused exception: Invalid format: \"2025-12-10T10:22:28.026+0000\" is malformed at \"T10:22:28.026+0000\".",
  "data_office365_ErrorNumber": "0",
  "data_office365_Workload": "AzureActiveDirectory",
  "message": "{\"true\":1765362148.975397,\"timestamp\":\"2025-12-10T10:22:28.026+0000\",\"rule\":{\"level\":3,\"description\":\"Office 365: Secure Token Service (STS) logon events in Azure Active Directory.\",\"id\":\"91545\",\"firedtimes\":1,\"mail\":false,\"groups\":[\"office365\",\"AzureActiveDirectoryStsLogon\"],\"hipaa\":[\"164.312.a.2.I\",\"164.312.b\",\"164.312.d\",\"164.312.e.2.II\"],\"pci_dss\":[\"8.3\",\"10.6.1\"]},\"agent\":{\"id\":\"000\",\"name\":\"mgr-node-01\"},\"manager\":{\"name\":\"mgr-node-01\"},\"id\":\"1765362148.159908\",\"cluster\":{\"name\":\"cluster-01\",\"node\":\"mgr-node-01.example.local\"},\"decoder\":{\"name\":\"json\"},\"data\":{\"integration\":\"office365\",\"office365\":{\"CreationTime\":\"2025-12-10T10:17:54\",\"Id\":\"e9836c09-aad3-482b-8ecc-2c67d8e93a00\",\"Operation\":\"UserLoggedIn\",\"OrganizationId\":\"d7e8f9a0-1b2c-3d4e-5f6a-7b8c9d0e1f2a\",\"RecordType\":\"15\",\"ResultStatus\":\"Success\",\"UserKey\":\"0f3b6e7a-1c2d-4b5a-9e1f-1a2b3c4d5e6f\",\"UserType\":\"0\",\"Version\":\"1\",\"Workload\":\"AzureActiveDirectory\",\"ClientIP\":\"102.78.106.220\",\"ObjectId\":\"00000002-0000-0ff1-ce00-000000000000\",\"UserId\":\"user@example.com\",\"AzureActiveDirectoryEventType\":\"1\",\"ExtendedProperties\":[{\"Name\":\"ResultStatusDetail\",\"Value\":\"Redirect\"},{\"Name\":\"UserAgent\",\"Value\":\"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36\"},{\"Name\":\"RequestType\",\"Value\":\"OAuth2:Authorize\"}],\"ModifiedProperties\":[],\"Actor\":[{\"ID\":\"0f3b6e7a-1c2d-4b5a-9e1f-1a2b3c4d5e6f\",\"Type\":0},{\"ID\":\"user@example.com\",\"Type\":5}],\"ActorContextId\":\"b1c2d3e4-5f6a-7b8c-9d0e-1f2a3b4c5d6e\",\"ActorIpAddress\":\"102.78.106.220\",\"InterSystemsId\":\"1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d\",\"IntraSystemId\":\"e9836c09-aad3-482b-8ecc-2c67d8e93a00\",\"Target\":[{\"ID\":\"00000002-0000-0ff1-ce00-000000000000\",\"Type\":0}],\"TargetContextId\":\"d7e8f9a0-1b2c-3d4e-5f6a-7b8c9d0e1f2a\",\"ApplicationId\":\"9199bf20-a13f-4107-85dc-02114787ef48\",\"DeviceProperties\":[{\"Name\":\"OS\",\"Value\":\"Linux\"},{\"Name\":\"BrowserType\",\"Value\":\"Chrome\"},{\"Name\":\"IsCompliant\",\"Value\":\"False\"},{\"Name\":\"IsCompliantAndManaged\",\"Value\":\"False\"},{\"Name\":\"SessionId\",\"Value\":\"eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee\"}],\"ErrorNumber\":\"0\",\"Subscription\":\"Audit.AzureActiveDirectory\"}},\"location\":\"office365\"}",
  "rule_id": "91545",
  "manager_name": "mgr-node-01",
  "cluster_node": "mgr-node-01.example.local",
  "data_office365_ActorIpAddress_country_code": "MA",
  "location": "office365",
  "msg_timestamp": "2025-12-10T10:22:28.026Z",
  "rule_group2": "AzureActiveDirectoryStsLogon",
  "rule_group1": "office365"
}
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
