import os
import sys
from dotenv import load_dotenv
load_dotenv()
# Ensure the root project directory is in the path so visionfacts_api can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import pytz

from mcp.server.fastmcp import FastMCP
from visionfacts_api.auth_manager import auth
from visionfacts_api import api_functions
import dateparser
from datetime import datetime

def normalize_to_utc(date_str: str) -> str:
    """
    Parses a flexible date string (like 'today 9am' or ISO), 
    assumes IST (+5:30) if no timezone is present,
    and returns a UTC ISO 8601 string.
    """
    try:
        # dateparser logic:
        # - TIMEZONE: The default timezone to assume if none is in the string.
        # - TO_TIMEZONE: The timezone to convert the result to.
        dt = dateparser.parse(
            date_str,
            settings={
                'TIMEZONE': 'Asia/Kolkata', # Default to IST
                'TO_TIMEZONE': 'UTC',       # Convert to UTC
                'RETURN_AS_TIMEZONE_AWARE': True
            }
        )
        if dt:
            return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        return date_str
    except Exception as e:
        print(f"Date parsing error for '{date_str}': {e}")
        return date_str

# Create the MCP server instance
port = int(os.getenv("MCP_PORT", "8000"))
mcp = FastMCP("Analytical Tools",port=port)

# Initialize the shared session automatically with default credentials
try:
    print("Initializing API session...")
    auth.login("admin@gmail.com", "Abc@12345")
except Exception as e:
    print(f"Initial login warning: {e}")


@mcp.tool()
def get_event_counts(range_type: str = "today") -> dict:
    """
    Retrieves counts for 'Summary of All Events' across various categories.
    Supported ranges: 'today', 'week', 'month', 'year'.
    
    This tool provides data for event types including: 
    Human/Intrusion detection, Crowd/Dispersal detection, Line/Vehicle crossing, 
    Geo-fencing, Occupancy/Queue/Wait-time monitoring, Distress gestures, 
    PPE violations, Fall detection, Suspicious motion, Tailgating, and SOS signals.
    """
    return api_functions.get_event_counts(range_type)

@mcp.tool()
def get_vehicle_counts(range_type: str = "today") -> dict:
    """
    Retrieves counts for 'Summary of All Vehicle' broken down by type.
    Supported ranges: 'today', 'week', 'month', 'year'.
    
    This tool provides counts for specific vehicle categories:
    Bicycle, Bike, Auto, Car, Van, Bus, and Truck.
    """
    return api_functions.get_vehicle_counts(range_type)

@mcp.tool()
def get_crowd_counts(range_type: str = "today") -> dict:
    """
    Retrieves counts for 'Crowd Summary' broken down by density levels.
    Supported ranges: 'today', 'week', 'month', 'year'.
    
    This tool provides counts for different crowd density scenarios, 
    specifically: Crowd III, Crowd IV, and Crowd V events.
    """
    return api_functions.get_crowd_counts(range_type)

@mcp.tool()
def get_line_crossing_counts(range_type: str = "today") -> dict:
    """
    Retrieves counts for 'People line crossing' by device.
    Supported ranges: 'today', 'week', 'month', 'year'.
    
    This tool provides detailed metrics for people movement including: 
    Walk In, Walk Out, Cross In, and Cross Out across different camera devices.
    """
    return api_functions.get_line_crossing_counts(range_type)

@mcp.tool()
def get_vehicle_line_crossing_counts(range_type: str = "today") -> dict:
    """
    Retrieves counts for 'Vehicle line crossing' identifying Entrances and Exits.
    Supported ranges: 'today', 'week', 'month', 'year'.
    
    This tool provides specific data for vehicle movement through designated 
    points like HO-CAM-02 Entrance, HO-CAM-03 Entrance, and PARKING OUT HO Exit.
    Use this when the user asks for 'entrance' or 'exit' counts.
    """
    return api_functions.get_vehicle_line_crossing_counts(range_type)

# @mcp.tool()
# def generate_heatmap(start_date: str, end_date: str) -> dict:
#     """
#     Generates a heatmap image (base64) for a specific date-time range.
    
#     IMPORTANT: If you are unsure of the current date, ALWAYS call 'get_current_time' first.
#     You can use natural language like 'today 9am' or ISO strings.
#     Times are assumed to be in IST (+5:30) unless specified otherwise.
#     """,
#     # Normalize inputs to UTC ISO strings before calling the API
#     print(start_date,end_date)
#     utc_start = normalize_to_utc(start_date)
#     utc_end = normalize_to_utc(end_date)
    
#     print(f"Generating heatmap: {start_date} -> {utc_start} to {end_date} -> {utc_end}")
#     return api_functions.generate_heatmap(utc_start, utc_end)

@mcp.tool()
def get_current_time() -> dict:
    """
    Returns the current local (Asia/Kolkata) and UTC date and time.
    Call this tool whenever you need to resolve 'today', 'yesterday', or 'this hour'.
    """
    from datetime import datetime
    import pytz
    
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    now_utc = datetime.now(pytz.UTC)
    
    return {
        "local_time": now_ist.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
        "utc_time": now_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "timezone": "Asia/Kolkata"
    }

@mcp.tool()
def get_event_types(limit: int = 20, offset: int = 0) -> dict:
    """
    Retrieves the list of supported event types and active detection status.
    Use this to see what categories of events the system can monitor.
    """
    return api_functions.get_event_types(limit, offset)


def convert_utc_to_ist_readable(utc_str: str) -> str:
    """
    Converts UTC ISO string to IST human-readable format.
    Example: 2026-04-05T07:13:02.826Z → 05 Apr 2026, 12:43 PM
    """
    if not utc_str:
        return None

    try:
        utc_time = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        utc_time = utc_time.replace(tzinfo=pytz.UTC)

        ist = pytz.timezone("Asia/Kolkata")
        ist_time = utc_time.astimezone(ist)

        return ist_time.strftime("%d %b %Y, %I:%M %p")
    except Exception as e:
        print(f"Time conversion error: {e}")
        return utc_str

@mcp.tool()
def get_attendances_advanced(
    limit: int = 10,
    offset: int = 0,
    search: str = "",
    staff_id: str = "",
    branch_id: int = None,
    start_date: str = "",
    end_date: str = "",
    staff_type: str = ""
) -> dict:
    """
    Retrieves attendance records with flexible filters.

    ⚠️ IMPORTANT FOR AI AGENTS:

    1. Dates MUST be in format: YYYY-MM-DD
    - Example: "2026-04-05"
    - Do NOT use "today", "yesterday", or natural language.

    2. If you do NOT know the current date:
    → FIRST call `get_current_time` tool and extract the date.

    3. If you do NOT know the staff_id:
    → FIRST call `get_staffs(search="name")` to find the correct staff_id.

    ───────────────────────────────

    You can use this tool to:
    - Get all attendance records
    - Search by staff name
    - Filter by staff_id, branch, or staff_type
    - Filter by date range

    Examples:
    - get_attendances_advanced()
    - get_attendances_advanced(search="Ahmed")
    - get_attendances_advanced(staff_id="232")
    - get_attendances_advanced(start_date="2026-04-05", end_date="2026-04-05")

    Args:
        limit (int): Number of records
        offset (int): Pagination offset
        search (str): Search keyword
        staff_id (str): Staff ID (use get_staffs tool if unknown)
        branch_id (int): Branch ID
        start_date (str): Date in YYYY-MM-DD format ONLY
        end_date (str): Date in YYYY-MM-DD format ONLY
        staff_type (str): Staff type (e.g., 'shell_staff')
    """

    # ✅ Do not normalize dates; the API expects raw YYYY-MM-DD strings.
    # The agent provides them properly as instructed.

    return api_functions.get_attendances_advanced(
        limit=limit,
        offset=offset,
        search=search or None,
        staff_id=staff_id or None,
        branch_id=branch_id,
        start_date=start_date or None,
        end_date=end_date or None,
        staff_type=staff_type or None
    )

@mcp.tool()
def get_attendance_logs(attendance_record_id: int) -> dict:
    """
    Retrieves detailed logs for a specific attendance record.

    IMPORTANT:
    Use the 'attendance_record_id' from 'get_attendances'.

    Returns:
    - Cleaned attendance data
    - IST formatted timestamps
    - Safe user data
    - Full image URLs
    """
    data = api_functions.get_attendance_logs(attendance_record_id)

    # 🔴 Remove unwanted top-level fields
    data.pop("event_id", None)
    data.pop("unique_event_id", None)
    data.pop("is_present", None)

    # Convert main timestamps
    data["check_in"] = convert_utc_to_ist_readable(data.get("check_in"))
    data["check_out"] = convert_utc_to_ist_readable(data.get("check_out"))
    data["created_at"] = convert_utc_to_ist_readable(data.get("created_at"))

    # Process logs
    for log in data.get("attendancelogs", []):
        # 🔴 Remove unwanted fields
        log.pop("device_id", None)
        log.pop("attendance_id", None)
        log.pop('staff_id',None)
        log.pop('userData',None)
        log.pop('device_name',None)

        # ✅ Add full image URL
        if log.get("image"):
            log["image"] = f"{auth.base_url}{log['image']}"

        # ✅ Keep only required user data
        if "userData" in log:
            log["userData"] = {
                "first_name": log["userData"].get("first_name"),
                "last_name": log["userData"].get("last_name"),
            }

    # 🔒 Clean top-level userData also (IMPORTANT — you missed this earlier)
    if "userData" in data:
        data["userData"] = {
            "first_name": data["userData"].get("first_name"),
            "last_name": data["userData"].get("last_name"),
        }

    return data


@mcp.tool()
def get_staffs(limit: int = 10, offset: int = 0, search: str = "") -> dict:
    """
    Retrieves staff list with optional search.

    Use this tool to:
    - Get all staff (no search)
    - Search staff by name (e.g., "Ahmed")

    Examples:
    - get_staffs()
    - get_staffs(search="Ahmed")

    Args:
        limit (int): Number of records
        offset (int): Pagination offset
        search (str, optional): Search keyword (name)
    """
    return api_functions.get_staffs(limit, offset, search if search else None)


if __name__ == "__main__":
    import os
    # Get configuration from environment variables
    # Use transport="sse" to run as an HTTP server
    transport = os.getenv("MCP_TRANSPORT", "stdio")
   
    
    if transport == "sse":
        print(f"Starting MCP SSE server on port {port}...")
        mcp.run(transport="sse")
    else:
        # Default to stdio for local agent execution
        mcp.run(transport="stdio")
