import requests
from datetime import datetime, timedelta
import time

LINE_PROVIDER_URL = 'http://localhost:8000'
BET_MAKER_URL = 'http://localhost:8001'

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

def create_event(event_id, odds, deadline, status):
    url = f'{LINE_PROVIDER_URL}/events'
    data = {
        'id': event_id,
        'odds': odds,
        'deadline': deadline.isoformat(),
        'status': status,
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print(f"Event '{event_id}' created successfully.")
    else:
        print(f"Failed to create event '{event_id}': {response.text}")

def get_available_events():
    url = f'{BET_MAKER_URL}/events'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        events = response.json()
        print("Available events:")
        for event in events:
            print(f" - ID: {event['id']}, Odds: {event['odds']}, Deadline: {event['deadline']}")
        return events
    else:
        print(f"Failed to get available events: {response.text}")
        return []

def place_bet(event_id, amount):
    url = f'{BET_MAKER_URL}/bet'
    data = {
        'event_id': event_id,
        'amount': amount,
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        bet = response.json()
        print(f"Bet placed successfully. Bet ID: {bet['id']}")
        return bet
    else:
        print(f"Failed to place bet: {response.text}")
        return None

def get_bets():
    url = f'{BET_MAKER_URL}/bets'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        bets = response.json()
        print("Current bets:")
        for bet in bets:
            print(f" - Bet ID: {bet['id']}, Event ID: {bet['event_id']}, Amount: {bet['amount']}, Status: {bet['status']}")
        return bets
    else:
        print(f"Failed to get bets: {response.text}")
        return []

def update_event_status(event_id, status):
    url = f'{LINE_PROVIDER_URL}/events/{event_id}/status'
    data = status
    response = requests.put(url, json=data, headers=headers)
    if response.status_code == 200:
        print(f"Event '{event_id}' status updated to '{status}'.")
    else:
        print(f"Failed to update event status: {response.text}")

def main():
    event_id = 'event1'
    odds = 2.5
    deadline = datetime.utcnow() + timedelta(minutes=5)
    status = 'незавершённое'
    create_event(event_id, odds, deadline, status)

    time.sleep(2)
    get_available_events()

    bet_amount = 100.00
    place_bet(event_id, bet_amount)

    get_bets()

    print("Waiting for the event deadline to pass...")
    time_to_deadline = (deadline - datetime.now()).total_seconds()
    if time_to_deadline > 0:
        time.sleep(time_to_deadline + 2)

    new_status = 'выигрыш первой команды'
    update_event_status(event_id, new_status)

    print("Waiting for bet-maker to update bet statuses...")
    time.sleep(12)

    get_bets()

if __name__ == '__main__':
    main()
