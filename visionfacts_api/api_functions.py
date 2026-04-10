import json
import requests
import os
from dotenv import load_dotenv
from visionfacts_api.auth_manager import auth

load_dotenv()

def get_event_counts(range_type: str = "today") -> dict:
    """
    Retrieves event counts for a specific time range from 'multi-events-count' endpoint.
    """
    range_mapping = {"today": 1, "week": 2, "month": 3, "year": 4}
    if range_type.lower() not in range_mapping:
        return {"error": f"Invalid range_type '{range_type}'. Valid options: {list(range_mapping.keys())}"}
    type_id = range_mapping[range_type.lower()]
    
    url = f"{auth.base_url}/events/multi-events-count"
    headers = auth.get_auth_header()
    headers["accept"] = "application/json"
    
    response = requests.get(url, headers=headers, params={"type": type_id})
    
    # Check for token expiration (401 Unauthorized)
    if response.status_code == 401 and auth.email and auth.password:
        print("Token expired. Re-authenticating...")
        auth.login(auth.email, auth.password)
        headers = auth.get_auth_header()  # Get new token in header
        headers["accept"] = "application/json"
        response = requests.get(url, headers=headers, params={"type": type_id})
        
    response.raise_for_status()
    return response.json()

def get_vehicle_counts(range_type: str = "today") -> dict:
    """
    Retrieves vehicle counts for a specific time range from 'multi-vehicles-count' endpoint.
    """
    range_mapping = {"today": 1, "week": 2, "month": 3, "year": 4}
    if range_type.lower() not in range_mapping:
        return {"error": f"Invalid range_type '{range_type}'. Valid options: {list(range_mapping.keys())}"}
    type_id = range_mapping[range_type.lower()]
    
    url = f"{auth.base_url}/vehicles/multi-vehicles-count"
    headers = auth.get_auth_header()
    headers["accept"] = "application/json"
    
    response = requests.get(url, headers=headers, params={"type": type_id})
    
    # Check for token expiration (401 Unauthorized)
    if response.status_code == 401 and auth.email and auth.password:
        print("Token expired. Re-authenticating...")
        auth.login(auth.email, auth.password)
        headers = auth.get_auth_header()
        headers["accept"] = "application/json"
        response = requests.get(url, headers=headers, params={"type": type_id})
        
    response.raise_for_status()
    return response.json()

def get_crowd_counts(range_type: str = "today") -> dict:
    """
    Retrieves crowd counts for a specific time range from 'crowd-counts' endpoint.
    """
    range_mapping = {"today": 1, "week": 2, "month": 3, "year": 4}
    if range_type.lower() not in range_mapping:
        return {"error": f"Invalid range_type '{range_type}'. Valid options: {list(range_mapping.keys())}"}
    type_id = range_mapping[range_type.lower()]
    
    url = f"{auth.base_url}/events/crowd-counts"
    headers = auth.get_auth_header()
    headers["accept"] = "application/json"
    
    response = requests.get(url, headers=headers, params={"type": type_id})
    
    # Check for token expiration (401 Unauthorized)
    if response.status_code == 401 and auth.email and auth.password:
        print("Token expired. Re-authenticating...")
        auth.login(auth.email, auth.password)
        headers = auth.get_auth_header()
        headers["accept"] = "application/json"
        response = requests.get(url, headers=headers, params={"type": type_id})
        
    response.raise_for_status()
    return response.json()

def get_line_crossing_counts(range_type: str = "today") -> dict:
    """
    Retrieves line crossing counts for a specific time range from 'line-crossing' endpoint.
    """
    range_mapping = {"today": 1, "week": 2, "month": 3, "year": 4}
    if range_type.lower() not in range_mapping:
        return {"error": f"Invalid range_type '{range_type}'. Valid options: {list(range_mapping.keys())}"}
    type_id = range_mapping[range_type.lower()]
    
    url = f"{auth.base_url}/analytics/line-crossing"
    headers = auth.get_auth_header()
    headers["accept"] = "application/json"
    
    response = requests.get(url, headers=headers, params={"type": type_id})
    
    # Check for token expiration (401 Unauthorized)
    if response.status_code == 401 and auth.email and auth.password:
        print("Token expired. Re-authenticating...")
        auth.login(auth.email, auth.password)
        headers = auth.get_auth_header()
        headers["accept"] = "application/json"
        response = requests.get(url, headers=headers, params={"type": type_id})
        
    response.raise_for_status()
    return response.json()

def get_vehicle_line_crossing_counts(range_type: str = "today") -> dict:
    """
    Retrieves vehicle line crossing counts for a specific time range from 'vehicle-line-crossing' endpoint.
    """
    range_mapping = {"today": 1, "week": 2, "month": 3, "year": 4}
    if range_type.lower() not in range_mapping:
        return {"error": f"Invalid range_type '{range_type}'. Valid options: {list(range_mapping.keys())}"}
    type_id = range_mapping[range_type.lower()]
    
    url = f"{auth.base_url}/analytics/vehicle-line-crossing"
    headers = auth.get_auth_header()
    headers["accept"] = "application/json"
    
    response = requests.get(url, headers=headers, params={"type": type_id})
    
    # Check for token expiration (401 Unauthorized)
    if response.status_code == 401 and auth.email and auth.password:
        print("Token expired. Re-authenticating...")
        auth.login(auth.email, auth.password)
        headers = auth.get_auth_header()
        headers["accept"] = "application/json"
        response = requests.get(url, headers=headers, params={"type": type_id})
        
    response.raise_for_status()
    return response.json()

def generate_heatmap(start_date: str, end_date: str) -> dict:
    """
    Generates a heatmap image by calling the heatmap generator service.
    
    Args:
        start_date (str): Start date-time string (e.g., '2026-04-04T06:27:31Z').
        end_date (str): End date-time string (e.g., '2026-04-04T06:57:31Z').
        
    Returns:
        dict: JSON response containing the base64 image data.
    """
    print("Input to the generate heatmap api",start_date,end_date)
    heatmap_service_url = os.getenv("HEATMAP_SERVICE_URL", "http://10.254.10.251:7000/generate_heatmap")
    
    import urllib.parse
    # Ensure ISO format (replace spaces with T) and safely encode each parameter
    clean_start = start_date.replace(" ", "T")
    clean_end = end_date.replace(" ", "T")
    
    q_start = urllib.parse.quote(clean_start)
    q_end = urllib.parse.quote(clean_end)
    
    data_url = f"{auth.base_url}/heatmaps?start_date={q_start}&end_date={q_end}"
    
    payload = {
        "url": data_url
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Perform the POST request to the heatmap service
    response = requests.post(heatmap_service_url, json=payload, headers=headers)
    
    if not response.ok:
        print(f"Heatmap Service Error Detail (Status {response.status_code}): {response.text}")
        
    response.raise_for_status()
    return response.json()

def get_event_types(limit: int = 20, offset: int = 0) -> dict:
    """
    Retrieves the list of supported event types and active detection categories.
    
    Args:
        limit (int): Maximum number of records to return.
        offset (int): Number of records to skip.
    """
    import json
    filter_params = {
        "offset": offset,
        "limit": limit,
        "skip": offset,
        "order": "id DESC"
    }
    filter_json = json.dumps(filter_params)
    
    url = f"{auth.base_url}/event-types"
    headers = auth.get_auth_header()
    headers["accept"] = "application/json"
    
    response = requests.get(url, headers=headers, params={"filter": filter_json})
    
    # Check for token expiration (401 Unauthorized)
    if response.status_code == 401 and auth.email and auth.password:
        print("Token expired. Re-authenticating...")
        auth.login(auth.email, auth.password)
        headers = auth.get_auth_header()
        headers["accept"] = "application/json"
        response = requests.get(url, headers=headers, params={"filter": filter_json})
        
    response.raise_for_status()
    return response.json()

def convert_utc_to_ist_readable(utc_str: str) -> str:
    """
    Converts UTC ISO string to IST human-readable format.
    Example: 2026-04-05T07:13:02.826Z → 05 Apr 2026, 12:43 PM
    """
    import pytz
    from datetime import datetime
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

def get_attendances_advanced(
    limit: int = 10,
    offset: int = 0,
    search: str = None,
    staff_id: str = None,
    branch_id: int = None,
    start_date: str = None,
    end_date: str = None,
    staff_type: str = None
) -> dict:
    """
    Retrieves attendance records with advanced filtering.
    """

    import json

    filter_params = {
        "offset": offset,
        "limit": limit,
        "skip": offset,
        "order": "created_at DESC"
    }

    url = f"{auth.base_url}/attendances"
    headers = auth.get_auth_header()
    headers["accept"] = "application/json"

    params = {
        "filter": json.dumps(filter_params)
    }

    # ✅ Optional filters
    if search:
        params["search"] = search
    if staff_id:
        params["staff_id"] = staff_id
    if branch_id:
        params["branch_id"] = branch_id
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if staff_type:
        params["staff_type"] = staff_type

    response = requests.get(url, headers=headers, params=params)

    # 🔁 Token refresh
    if response.status_code == 401 and auth.email and auth.password:
        auth.login(auth.email, auth.password)
        headers = auth.get_auth_header()
        headers["accept"] = "application/json"
        response = requests.get(url, headers=headers, params=params)

    response.raise_for_status()
    data = response.json()

    # ✅ Clean response (same as your previous tool)
    for record in data.get("data", []):
        record["attendance_record_id"] = record.get("id")
        record["check_in"] = convert_utc_to_ist_readable(record.get("check_in"))
        record["check_out"] = convert_utc_to_ist_readable(record.get("check_out"))
        record["created_at"] = convert_utc_to_ist_readable(record.get("created_at"))

    return data

def get_attendance_logs(attendance_id: int) -> dict:
    """
    Retrieves detailed logs for a specific attendance record.

    Args:
        attendance_id (int): The attendance record ID.

    Returns:
        dict: JSON response containing logs, device info, and user details.
    """
    url = f"{auth.base_url}/attendances-logs/{attendance_id}"
    
    headers = auth.get_auth_header()
    headers["accept"] = "application/json"

    response = requests.get(url, headers=headers)

    # 🔁 Handle token expiration
    if response.status_code == 401 and auth.email and auth.password:
        print("Token expired. Re-authenticating...")
        auth.login(auth.email, auth.password)

        headers = auth.get_auth_header()
        headers["accept"] = "application/json"

        response = requests.get(url, headers=headers)

    response.raise_for_status()
    return response.json()

def get_staffs(limit: int = 10, offset: int = 0, search: str = None) -> dict:
    """
    Retrieves staff list with optional search.

    Args:
        limit (int): Number of records
        offset (int): Pagination offset
        search (str, optional): Search by name

    Returns:
        dict: Cleaned staff data
    """
    import json

    filter_params = {
        "offset": offset,
        "limit": limit,
        "skip": offset,
        "order": "id DESC"
    }

    filter_json = json.dumps(filter_params)

    url = f"{auth.base_url}/staff"
    headers = auth.get_auth_header()
    headers["accept"] = "application/json"

    params = {"filter": filter_json}
    if search:
        params["search"] = search

    response = requests.get(url, headers=headers, params=params)

    # 🔁 Token refresh
    if response.status_code == 401 and auth.email and auth.password:
        print("Token expired. Re-authenticating...")
        auth.login(auth.email, auth.password)

        headers = auth.get_auth_header()
        headers["accept"] = "application/json"

        response = requests.get(url, headers=headers, params=params)

    response.raise_for_status()
    data = response.json()

    # ✅ Keep only required fields
    cleaned_data = []
    for staff in data.get("data", []):
        cleaned_data.append({
            "id": staff.get("id"),
            "first_name": staff.get("first_name"),
            "last_name": staff.get("last_name"),
            "staff_uuid": staff.get("staff_uuid"),
            "branch_id": staff.get("branch_id"),
            "department_id": staff.get("department_id"),
            "role_id": staff.get("role_id"),
            "block_user": staff.get("block_user"),
            "staff_type": staff.get("staff_type"),
            "active_status": staff.get("active_status"),
        })

    data["data"] = cleaned_data
    data.pop("Active_Data", None)
    return data

if __name__ == "__main__":
    print(get_attendances().get("data")[0])