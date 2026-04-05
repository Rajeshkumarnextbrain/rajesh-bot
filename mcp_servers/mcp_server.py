import os
import sys
from dotenv import load_dotenv
load_dotenv()
# Ensure the root project directory is in the path so visionfacts_api can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

@mcp.tool()
def generate_heatmap(start_date: str, end_date: str) -> dict:
    """
    Generates a heatmap image (base64) for a specific date-time range.
    
    You can use natural language like 'today 9am' or ISO strings.
    Times are assumed to be in IST (+5:30) unless specified otherwise,
    and will be automatically converted to UTC for the API.
    """
    # Normalize inputs to UTC ISO strings before calling the API
    print(start_date,end_date)
    utc_start = normalize_to_utc(start_date)
    utc_end = normalize_to_utc(end_date)
    
    print(f"Generating heatmap: {start_date} -> {utc_start} to {end_date} -> {utc_end}")
    return api_functions.generate_heatmap(utc_start, utc_end)

@mcp.tool()
def get_event_types(limit: int = 20, offset: int = 0) -> dict:
    """
    Retrieves the list of supported event types and active detection status.
    Use this to see what categories of events the system can monitor.
    """
    return api_functions.get_event_types(limit, offset)

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
