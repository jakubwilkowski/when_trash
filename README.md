# Waste Collection Schedule

This project automates the process of fetching and displaying upcoming waste collection dates for different types of waste. It uses data from a local waste management API to create a calendar of events and maintain an up-to-date schedule.

## Features

- Fetches waste collection data from a local API
- Creates and updates an iCalendar file with collection events
- Maintains a SQLite database to track processed events
- Generates an up-to-date markdown file with upcoming collection dates
- Runs daily via GitHub Actions to ensure the schedule is always current

## Setup

To set up this project locally:

1. Clone the repository:
   ```
   git clone https://github.com/your-username/waste-collection-schedule.git
   cd waste-collection-schedule
   ```

2. Install uv (if not already installed):
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Set up the Python environment:
   ```
   uv sync --all-extras --dev
   ```

4. Run the script:
   ```
   python when.py
   ```

This will create the SQLite database, fetch the latest data, and update the `upcoming.md` file.

## Usage

After setup, the script will:
- Fetch the latest waste collection data
- Update the SQLite database with new events
- Generate an updated `waste_collection_schedule.ics` file (if there are new events)
- Update the `upcoming.md` file with the next collection dates for each waste type

To view the upcoming waste collection dates, check the [Upcoming Waste Collection Dates](upcoming.md) file.

## Automated Updates

This project uses GitHub Actions to run the script daily, ensuring that the waste collection schedule is always up-to-date. The workflow file can be found in `.github/workflows/update_waste_schedule.yml`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
