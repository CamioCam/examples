#!/usr/bin/env python3
# Copyright 2024 Camio
# License MIT
# 
# Sample code snippets for integrating with Camio PACS Webhooks.

import requests
from datetime import datetime, timezone
import json


def read_config(config_file_path):
    # Replace with whichever way you obtain your configuration
    try:
        with open(config_file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Error reading configuration file: {config_file_path}")
        return None

def get_member_if_authorized(badge_id, reader_id):
    # Replace this with your actual retrieval of member data upon authorization check
    return {
        "id": "member123",
        "name": "John Doe",
        "email": "John.Doe@gmail.com"
    }

def notify_camio(badge_id, reader_id, member):
    now = datetime.now(timezone.utc)
    event_data = {
        "event": {
            "timestamp": now.isoformat(timespec='milliseconds'),
            "event_type": "Entry Unlocked",
            "device_id": reader_id,
            "actor_id": member["id"],
            "actor_name": member["name"],
            "actor_email": member["email"]
        }
    }
    json_data = json.dumps(event_data)    

    # config token obtained from https://camio.com/settings/integrations/pacs
    config = read_config("config.json")  # Replace "config.json" with your actual filename
    if not config:
        return
    
    token = config.get("token")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    response = requests.post('https://incoming.integrations.camio.com/pacs/webhooks', headers=headers, json=json_data)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.reason}")


def handle_access_request(badge_id, reader_id):
    member = get_member_if_authorized(badge_id, reader_id)

    if member is not None:
        notify_camio(badge_id, reader_id, member)

