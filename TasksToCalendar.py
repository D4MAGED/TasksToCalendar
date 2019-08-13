from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

# If modifying these scopes, delete the file sam.json.
SCOPES = ('https://www.googleapis.com/auth/tasks.readonly ' + 'https://www.googleapis.com/auth/calendar')
TASKS_MAINLIST = 'MTUxMzA0MjIzMDQ1NDk1MDg0NjM6MDow'


def main(token):
    """Shows basic usage of the Tasks API.
    Prints the title and ID of the first 10 task lists.
    """
    store = file.Storage(token)
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    tasks_service = build('tasks', 'v1', http=creds.authorize(Http()))

    # For gettings tasks lists
    results = tasks_service.tasklists().list(maxResults=10).execute()
    task_lists = results.get('items', [])

    if not task_lists:
        return "No task lists found"

    calendar_service = build('calendar', 'v3', http=creds.authorize(Http()))

    calendars_result = calendar_service.calendarList().list().execute()
    calendars = calendars_result.get('items', [])

    if not calendars:
        print('No calendars found.')

    to_remove = []
    for calendar in calendars:
        match_found = False
        for task_list in task_lists:
            if calendar['summary'] == task_list['title']:
                match_found = True

        if not match_found:
            to_remove.append(calendar)

    for calendar in to_remove:
        calendars.remove(calendar)

    for task_list in task_lists:
        results = tasks_service.tasks().list(tasklist=task_list['id']).execute()
        tasks = results.get('items', [])
        for task in tasks:
            if 'due' in task:
                calId = next((x for x in calendars if x['summary'] == task_list['title']), None)['id']
                events = calendar_service.events().list(calendarId=calId).execute().get('items', [])

                notes = ""
                if 'notes' in task:
                    notes = task['notes']+"\n\n"

                parent = ""
                if 'parent' in task:
                    parent = task['parent']
                for parent_test in tasks:
                    if parent_test['id'] == parent:
                        parent = parent_test['title'] + ": "

                new_event = {
                    'summary': parent+task['title'],
                    'description': notes+task['id'],
                    'start': {
                        'date': task['due'][:10],
                    },
                    'end': {
                        'date': task['due'][:10],
                    },
                    'reminders': {
                        'useDefault': True,
                    },
                }

                if not events:
                    calendar_service.events().insert(calendarId=calId, body=new_event).execute()
                else:
                    should_create = True
                    for event in events:
                        if 'description' in event and str(event['description']).endswith(task['id']):
                            if event['start']['date'] != task['due'][:10] or ('notes' in task and not str(event['description']).startswith(task['notes']+"\n\n")) or ('parent' in task and not str(event['summary']).startswith(parent)):
                                calendar_service.events().update(calendarId=calId, eventId=event['id'], body=new_event).execute()
                            should_create = False

                    if should_create:
                        calendar_service.events().insert(calendarId=calId, body=new_event).execute()


if __name__ == '__main__':
    #main("sam.json")
    main("thomass.json")

