# from flask import Flask, request, jsonify
# import datetime
# import pickle
# import os.path
# from googleapiclient.discovery import build
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
#
# # If modifying these scopes, delete the file token.pickle.
# SCOPES = ['https://www.googleapis.com/auth/calendar']
#
# app = Flask(__name__)
#
#
# def main(summary, start, end):
#     """Creates a Google Calendar event with the given summary."""
#     start_datetime = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%SZ')
#     end_datetime = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%SZ')
#
#     start_str = start_datetime.isoformat() + 'Z'
#     end_str = end_datetime.isoformat() + 'Z'
#
#     print("-----", start_str)
#     print("-----", end_str)
#
#     # Create event dictionary with string formatted dates
#     event = {
#         'summary': summary,
#         'start': {'dateTime': start_str},
#         'end': {'dateTime': end_str},
#         "conferenceData": {
#             "createRequest": {
#                 "conferenceSolutionKey": {
#                     "type": "hangoutsMeet"
#                 },
#                 "requestId": "medcare."
#             },
#         },
#     }
#
#     creds = None
#     if os.path.exists('token.pickle'):
#         with open('token.pickle', 'rb') as token:
#             creds = pickle.load(token)
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 'client_secret.json', SCOPES)
#             creds = flow.run_local_server(port=0)
#         with open('token.pickle', 'wb') as token:
#             pickle.dump(creds, token)
#
#     service = build('calendar', 'v3', credentials=creds)
#
#     # Insert the event into the calendar
#     event = service.events().insert(calendarId='primary', conferenceDataVersion=1, body=event).execute()
#
#     return event.get('hangoutLink'), event.get('id')
#
#
# @app.route('/create-event', methods=['POST'])
# def create_event():
#     """Handler for creating a Google Calendar event."""
#     summary = request.json.get('summary')
#     start = request.json.get('start')
#     end = request.json.get('end')
#
#     print("-----",start)
#     print("-----", end)
#     if summary and start and end:
#         hangout_link, event_id = main(summary,start,end)
#         return jsonify({'hangout_link': hangout_link, 'event_id': event_id}), 200
#     else:
#         return jsonify({'error': 'Summary is required'}), 400
#
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5001)


from flask import Flask, request, jsonify, send_file
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import tempfile

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

app = Flask(__name__)


def main(summary, start, end):
    """Creates a Google Calendar event with the given summary."""
    start_datetime = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%SZ')
    end_datetime = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%SZ')

    start_str = start_datetime.isoformat() + 'Z'
    end_str = end_datetime.isoformat() + 'Z'

    # Create event dictionary with string formatted dates
    event = {
        'summary': summary,
        'start': {'dateTime': start_str},
        'end': {'dateTime': end_str},
        "conferenceData": {
            "createRequest": {
                "conferenceSolutionKey": {
                    "type": "hangoutsMeet"
                },
                "requestId": "medcare."
            },
        },
    }

    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Insert the event into the calendar
    event = service.events().insert(calendarId='primary', conferenceDataVersion=1, body=event).execute()

    return event.get('hangoutLink'), event.get('id')


def generate_ics_file(summary, start, end):
    """Generates an iCalendar file (.ics) containing the event details."""
    cal_content = f"""BEGIN:VCALENDAR
    VERSION:2.0
    PRODID:-//MedCare//Appointment//EN
    BEGIN:VEVENT
    SUMMARY:{summary}
    DTSTART:{start}
    DTEND:{end}
    LOCATION:Google Meet
    DESCRIPTION:Medcare appointment with Hangouts Meet link
    END:VEVENT
    END:VCALENDAR"""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ics") as temp_file:
        temp_file.write(cal_content.encode("utf-8"))
        temp_file_path = temp_file.name

    return temp_file_path


@app.route('/create-event', methods=['POST'])
def create_event():
    """Handler for creating a Google Calendar event."""
    summary = request.json.get('summary')
    start = request.json.get('start')
    end = request.json.get('end')
    recipient_email = request.json.get('recipient_email')

    if summary and start and end and recipient_email:
        hangout_link, event_id = main(summary, start, end)

        # Generate iCalendar file
        ics_file_path = generate_ics_file(summary, start, end)

        # Send the file to the Go route
        with open(ics_file_path, "rb") as f:
            files = {"file": f}
            data = {"hangout_link": hangout_link, "event_id": event_id}
            response = requests.post("http://localhost:5001/send-event", files=files, data=data)

        return jsonify({'hangout_link': hangout_link, 'event_id': event_id}), 200
    else:
        return jsonify({'error': 'Summary, start, end, and recipient_email are required'}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
