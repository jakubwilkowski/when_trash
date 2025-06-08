import httpx
from ics import Calendar

from ics import Event
from datetime import datetime

import sqlite3

import contextlib

@contextlib.contextmanager
def sqlite_session():
    conn = sqlite3.connect('waste_schedule.db')
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_database():
    with sqlite_session() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT NOT NULL,
                event_date TEXT NOT NULL,
                UNIQUE(event_name, event_date) -- Prevent duplicate entries
            )
        """)


def check_processed(event_name, event_date):
    with sqlite_session() as cursor:
        cursor.execute(
            """
            SELECT * FROM processed_events WHERE event_name = ? AND event_date = ?
            """,
            (event_name, event_date),
        )
        result = cursor.fetchone()
    return result is not None


def mark_processed(event_name, event_date):
    with sqlite_session() as cursor:
        cursor.execute(
            """
            INSERT INTO processed_events (event_name, event_date) VALUES (?, ?)
            """,
            (event_name, event_date),
        )


def fetch_data():
    # Execute the API call
    url = 'https://warszawa19115.pl/harmonogramy-wywozu-odpadow?p_p_id=portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=ajaxResource&p_p_cacheability=cacheLevelPage&_portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ_addressPointId=14798530'
    headers = {
        'Accept': 'application/json, text/javascript, */*',
        'Accept-Language': 'pl-PL,pl;q=0.5',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }

    response = httpx.get(url, headers=headers)
    data = response.json()[0]
    harmonogramy = data.get('harmonogramy', [])
    harmonogramyN = data.get('harmonogramyN', [])
    harmonogramyZ = data.get('harmonogramyZ', [])
    return harmonogramyZ or harmonogramyN or harmonogramy


def extract_data(data):
    results = []
    category_mapping = {
        'BK': ('Bio', True),
        'MT': ('Metal i plastik', True),
        'OP': ('Papier', True),
        'OS': ('Szkło', True),
        'OZ': ('Odpady zielone', True),
        'WG': ('Gabaryty', True),
        'ZM': ('Niesegregowane komunalne', True),
        'BG': ('Kuchenne bio', False),
    }
    for item in data:
        frakcja_id = item.get('frakcja', {}).get('id_frakcja')
        frakcja_nazwa, is_interested = category_mapping.get(frakcja_id)
        if not is_interested:
            continue
        date = item.get('data')
        if date:
            results.append({'name': frakcja_nazwa, 'date': date})
    return results


def export_calendar(data):
    # Create a calendar
    calendar = Calendar()
    any_new_events = False
    for item in data:
        # Create a calendar event

        event_name = f"🚮 {item['name']}"
        event_date = item['date']

        if not check_processed(item['name'], event_date):
            any_new_events = True
            event = Event()
            event.name = event_name
            event.begin = datetime.strptime(event_date, '%Y-%m-%d').date()  # Start date
            event.description = f'Wywóz śmieci {event.name}'
            event.make_all_day()
            calendar.events.add(event)
            mark_processed(item['name'], event_date)

    # Save calendar to a file
    if any_new_events:
        with open('waste_collection_schedule.ics', 'w') as f:
            f.writelines(calendar)


def show_table(data):
    # Displaying the results in a table format
    print(f"{'Name':<30} {'Date':<15}")
    print('-' * 45)
    for result in data:
        print(f"{result['name']:<30} {result['date']:<15}")


def get_next_events():
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    with sqlite_session() as cursor:
        results = cursor.execute("""
            SELECT event_name, MIN(event_date) as next_date
            FROM processed_events
            WHERE event_date >= :current_date
            GROUP BY event_name
            ORDER BY next_date
        """, {'current_date': current_date}).fetchall()
    
    return results


def update_upcoming_md(next_events):
    table_content = "| Waste Type | Next Collection Date |\n|------------|----------------------|\n"
    for event_name, next_date in next_events:
        table_content += f"| {event_name} | {next_date} |\n"
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open('upcoming.md', 'w') as f:
        f.write("# Upcoming Waste Collection Dates\n\n")
        f.write(table_content)
        f.write(f"\n\n*Last updated: {current_time}*\n")


def update_waste_table(next_events):
    # Read the template
    with open('template.html', 'r') as f:
        template = f.read()
    
    # Generate table rows
    table_rows = []
    for event_name, next_date in next_events:
        table_rows.append(f'                <tr><td>{event_name}</td><td>{next_date}</td></tr>')
    
    # Replace placeholders
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = template.replace('{{TABLE_ROWS}}', '\n'.join(table_rows))
    html_content = html_content.replace('{{LAST_UPDATED}}', current_time)
    
    # Write the complete HTML file
    with open('waste_table.html', 'w') as f:
        f.write(html_content)


if __name__ == '__main__':
    create_database()
    data = fetch_data()
    data = extract_data(data)
    export_calendar(data)
    show_table(data)
    
    next_events = get_next_events()
    update_upcoming_md(next_events)
    update_waste_table(next_events)
    
    print("\nNext upcoming events have been written to upcoming.md and waste_table.html")
