# Wazuh Manager Integration

This folder contains a Wazuh Manager integration script that calls the Office 365 Impossible Travel Detection API `/analyze` endpoint for incoming Office 365 alerts.

## Install on the Wazuh Manager

1) Copy the integration script to the Wazuh integrations directory and make it executable:

```bash
sudo cp /path/to/repo/wazuh/office365_impossible_travel_integration.py /var/ossec/integrations/
sudo chmod +x /var/ossec/integrations/office365_impossible_travel_integration.py
```

2) Configure the integration in `/var/ossec/etc/ossec.conf`:

```xml
<integration>
  <name>office365_impossible_travel_integration.py</name>
  <alert_format>json</alert_format>
  <!-- Optional scoping: use rule_id, group, or level to target Office 365 alerts -->
  <group>office365,</group>
</integration>
```

3) Set environment variables for the API URL, optional API key, and TLS verification. The cleanest way is a systemd drop-in:

```bash
sudo systemctl edit wazuh-manager
```

Add:

```ini
[Service]
Environment="IMPOSSIBLE_TRAVEL_API_BASE_URL=http://your-api-server"
Environment="IMPOSSIBLE_TRAVEL_API_KEY=change-me"
Environment="IMPOSSIBLE_TRAVEL_TLS_VERIFY=true"
```

Then reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart wazuh-manager
```

## Field Mapping Strategy

The script reads Wazuh alert JSON from stdin and extracts **user/email**, **source IP**, and **timestamp** using a list of possible JSON paths. It tries each path in order and uses the first non-empty match.

Defaults (examples):
- User: `data.user`, `data.office365.UserId`, `data.office365.UserPrincipalName`, `email`
- IP: `data.srcip`, `data.office365.ClientIP`, `data.source.ip`, `ip`
- Timestamp: `data.office365.CreationTime`, `data.timestamp`, `timestamp`, `@timestamp`

You can override these with comma-separated path lists via environment variables:
- `WAZUH_IT_USER_PATHS`
- `WAZUH_IT_IP_PATHS`
- `WAZUH_IT_TS_PATHS`

Example override:

```ini
Environment="WAZUH_IT_USER_PATHS=data.office365.UserPrincipalName,data.user"
Environment="WAZUH_IT_IP_PATHS=data.office365.ClientIP,srcip"
Environment="WAZUH_IT_TS_PATHS=data.office365.CreationTime,@timestamp"
```

## Test Invocation

```bash
cat alert.json | /var/ossec/integrations/office365_impossible_travel_integration.py
```

On detection, the script prints a JSON summary to stdout and exits `0`. On non-detection, it also exits `0`. Errors exit non-zero and print a clear message to stderr.

## What to Expect on an Impossible Travel Detection

When the API flags **impossible travel**, the integration prints a **single-line JSON object** to stdout.

Example output (fields may vary slightly depending on API response):

```json
{
  "distance_km": 5896.42,
  "impossible_travel_detected": true,
  "ip": "8.8.8.8",
  "message": "IMPOSSIBLE TRAVEL DETECTED: User logged in from Morocco and then from United States within 5.0 minutes (5896.42 km apart)",
  "time_difference_minutes": 5.0,
  "timestamp": "2025-12-10T10:22:54",
  "user": "user@example.com"
}
```

### Where you’ll see it

- **Manual test:** You’ll see the JSON printed directly in your terminal.
- **Wazuh Manager runtime:** Wazuh runs integrations via `wazuh-integratord` and logs execution/output. Depending on your distro/version, you’ll typically find related logs in:
  - `/var/ossec/logs/ossec.log`
  - `/var/ossec/logs/integrations.log` (if enabled/available)

When the API flags **impossible travel**, the integration also **injects a new event into Wazuh** via the manager queue socket. The resulting alert has `location` set to `impossible_travel` and includes `data.integration="impossible_travel"` so it is easy to target in custom rules.

Example alert shape (shortened):

```json
{
  "location": "impossible_travel",
  "rule": {
    "id": "100420",
    "description": "Impossible travel detected for user@example.com"
  },
  "data": {
    "integration": "impossible_travel",
    "impossible_travel": {
      "impossible_travel_detected": true,
      "user": "user@example.com",
      "current_ip": "8.8.8.8",
      "current_timestamp": "2025-12-10T10:22:54"
    },
    "original_alert": {
      "id": "1733854974.123456",
      "rule": {
        "id": "92103",
        "groups": ["office365", "authentication_failed"]
      }
    }
  }
}
```

## Environment Variables

- `IMPOSSIBLE_TRAVEL_API_BASE_URL` (default: `http://localhost`)
- `IMPOSSIBLE_TRAVEL_API_KEY` (optional, sent as `X-API-Key` header)
- `IMPOSSIBLE_TRAVEL_TLS_VERIFY` (`true`/`false`, default: `true`)
- `WAZUH_IT_USER_PATHS` (comma-separated JSON paths)
- `WAZUH_IT_IP_PATHS` (comma-separated JSON paths)
- `WAZUH_IT_TS_PATHS` (comma-separated JSON paths)
- `WAZUH_IT_LOG_LEVEL` (default: `INFO`)

## Example Wazuh Rules

See `wazuh/impossible_travel_rules.xml` for a minimal ruleset that matches the enrichment events and raises a higher-level alert when `impossible_travel_detected=true`.
