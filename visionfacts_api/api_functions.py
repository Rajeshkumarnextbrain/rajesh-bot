import requests
from visionfacts_api.auth_manager import auth

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
    heatmap_service_url = "http://10.254.10.251:7000/generate_heatmap"
    
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



