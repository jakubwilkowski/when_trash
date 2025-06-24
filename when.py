import httpx
from datetime import datetime


def fetch_data():
    # Execute the API call
    url = 'https://warszawa19115.pl/harmonogramy-wywozu-odpadow?p_p_id=portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=ajaxResource&p_p_cacheability=cacheLevelPage&_portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ_addressPointId=27053109'
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


def get_next_events(data):
    # Sort by date and get the next event for each waste type
    current_date = datetime.now().strftime('%Y-%m-%d')
    next_events = {}
    
    for item in data:
        name = item['name']
        date = item['date']
        if date >= current_date:
            if name not in next_events or date < next_events[name]:
                next_events[name] = date
    
    # Convert to sorted list of tuples
    return sorted(next_events.items(), key=lambda x: x[1])


def show_table(data):
    # Displaying the results in a table format
    print(f"{'Name':<30} {'Date':<15}")
    print('-' * 45)
    for result in data:
        print(f"{result['name']:<30} {result['date']:<15}")


def update_markdown(next_events):
    table_content = "| Waste Type | Next Collection Date |\n|------------|----------------------|\n"
    for event_name, next_date in next_events:
        table_content += f"| {event_name} | {next_date} |\n"
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open('waste_table.md', 'w') as f:
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
    data = fetch_data()
    data = extract_data(data)
    show_table(data)
    
    next_events = get_next_events(data)
    update_markdown(next_events)
    update_waste_table(next_events)
    
    print("\nNext upcoming events have been written to waste_table.md and waste_table.html")
