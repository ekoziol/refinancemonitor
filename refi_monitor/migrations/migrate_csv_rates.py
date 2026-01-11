"""
Migration script to load historical mortgage rate data from CSV files into PostgreSQL.

This script reads CSV files containing historical mortgage rate data and loads them
into the MortgageRate model. It handles data validation, duplicate checking, and
provides detailed logging of the migration process.

Usage:
    python -m refi_monitor.migrations.migrate_csv_rates

CSV Format Expected:
    Date,type,rate
    09/10/21,30 YR FRM,0.0294
    09/09/21,15 YR FRM,0.0238
    ...

Note: CSV data represents national averages, so zip_code is set to '00000'
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from refi_monitor import init_app as create_app, db
from refi_monitor.models import MortgageRate


# Rate type to term months mapping
RATE_TYPE_TO_TERM_MONTHS = {
    '30 YR FRM': 360,      # 30-year fixed rate mortgage
    '15 YR FRM': 180,      # 15-year fixed rate mortgage
    '5/1 YR ARM': 60,      # 5/1 ARM (5-year initial fixed period)
    'FHA 30 YR': 360,      # FHA 30-year fixed
    'JUMBO 30 YR': 360,    # Jumbo 30-year fixed
}

# National average zip code (used since CSV doesn't have location data)
NATIONAL_ZIP = '00000'

# Date range for validation (2021 data based on CSV inspection)
MIN_EXPECTED_DATE = datetime(2021, 1, 1)
MAX_EXPECTED_DATE = datetime(2022, 1, 1)

# Rate range validation (reasonable mortgage rates)
MIN_RATE = 0.01  # 1%
MAX_RATE = 0.20  # 20%


def parse_csv_date(date_str):
    """
    Parse date from CSV format (MM/DD/YY) to datetime.

    Args:
        date_str: Date string in MM/DD/YY format

    Returns:
        datetime object

    Raises:
        ValueError: If date format is invalid
    """
    try:
        # Parse MM/DD/YY format, assuming 20xx for years
        return datetime.strptime(date_str, '%m/%d/%y')
    except ValueError as e:
        raise ValueError(f"Invalid date format '{date_str}': {e}")


def validate_rate(rate, rate_type, date_str):
    """
    Validate that rate is within reasonable bounds.

    Args:
        rate: Rate value as float
        rate_type: Type of mortgage rate
        date_str: Date string for error reporting

    Raises:
        ValueError: If rate is outside acceptable range
    """
    if rate < MIN_RATE or rate > MAX_RATE:
        raise ValueError(
            f"Rate {rate} for {rate_type} on {date_str} is outside "
            f"acceptable range ({MIN_RATE} - {MAX_RATE})"
        )


def validate_date(date_obj, date_str):
    """
    Validate that date is within expected range.

    Args:
        date_obj: datetime object
        date_str: Original date string for error reporting

    Raises:
        ValueError: If date is outside expected range
    """
    if date_obj < MIN_EXPECTED_DATE or date_obj > MAX_EXPECTED_DATE:
        print(
            f"Warning: Date {date_str} ({date_obj}) is outside expected range "
            f"({MIN_EXPECTED_DATE.date()} - {MAX_EXPECTED_DATE.date()})"
        )


def read_csv_file(file_path):
    """
    Read and parse CSV file containing mortgage rate data.

    Args:
        file_path: Path to CSV file

    Returns:
        List of tuples: (date, rate_type, rate_value)

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV format is invalid
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    rates_data = []

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)

        # Verify required columns
        if not {'Date', 'type', 'rate'}.issubset(reader.fieldnames):
            raise ValueError(
                f"CSV file {file_path} missing required columns. "
                f"Expected: Date, type, rate. Found: {reader.fieldnames}"
            )

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            try:
                date_str = row['Date'].strip()
                rate_type = row['type'].strip()
                rate_str = row['rate'].strip()

                # Parse and validate
                date_obj = parse_csv_date(date_str)
                validate_date(date_obj, date_str)

                rate_value = float(rate_str)
                validate_rate(rate_value, rate_type, date_str)

                # Verify rate type is recognized
                if rate_type not in RATE_TYPE_TO_TERM_MONTHS:
                    raise ValueError(f"Unknown rate type: {rate_type}")

                rates_data.append((date_obj, rate_type, rate_value))

            except (ValueError, KeyError) as e:
                print(f"Error parsing row {row_num} in {file_path}: {e}")
                print(f"Row data: {row}")
                raise

    return rates_data


def create_mortgage_rate_records(rates_data):
    """
    Convert parsed CSV data to MortgageRate model instances.

    Args:
        rates_data: List of tuples (date, rate_type, rate_value)

    Returns:
        List of MortgageRate instances (not yet added to session)
    """
    records = []
    now = datetime.utcnow()

    for date_obj, rate_type, rate_value in rates_data:
        term_months = RATE_TYPE_TO_TERM_MONTHS[rate_type]

        record = MortgageRate(
            zip_code=NATIONAL_ZIP,
            term_months=term_months,
            rate=rate_value,
            rate_date=date_obj,
            created_on=now,
            updated_on=now
        )
        records.append(record)

    return records


def get_existing_rates(app):
    """
    Query database for existing rate records to avoid duplicates.

    Args:
        app: Flask app instance

    Returns:
        Set of tuples: (zip_code, term_months, rate_date) for existing records
    """
    with app.app_context():
        existing = db.session.query(
            MortgageRate.zip_code,
            MortgageRate.term_months,
            MortgageRate.rate_date
        ).all()

        # Convert to set of tuples for fast lookup
        return {(r[0], r[1], r[2]) for r in existing}


def filter_duplicates(records, existing_rates):
    """
    Filter out records that already exist in database.

    Args:
        records: List of MortgageRate instances
        existing_rates: Set of existing (zip_code, term_months, rate_date) tuples

    Returns:
        Tuple of (new_records, duplicate_count)
    """
    new_records = []
    duplicate_count = 0

    for record in records:
        key = (record.zip_code, record.term_months, record.rate_date)
        if key in existing_rates:
            duplicate_count += 1
        else:
            new_records.append(record)

    return new_records, duplicate_count


def insert_records(app, records, batch_size=100):
    """
    Bulk insert records into database.

    Args:
        app: Flask app instance
        records: List of MortgageRate instances to insert
        batch_size: Number of records to insert per batch

    Returns:
        Number of records inserted
    """
    if not records:
        return 0

    with app.app_context():
        inserted = 0

        # Insert in batches for better performance
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            db.session.bulk_save_objects(batch)
            db.session.commit()
            inserted += len(batch)

            print(f"Inserted batch {i//batch_size + 1}: {len(batch)} records "
                  f"({inserted}/{len(records)} total)")

        return inserted


def verify_migration(app, expected_count):
    """
    Verify migration success by checking record counts.

    Args:
        app: Flask app instance
        expected_count: Expected number of records
    """
    with app.app_context():
        total_count = db.session.query(MortgageRate).count()
        national_count = db.session.query(MortgageRate).filter_by(
            zip_code=NATIONAL_ZIP
        ).count()

        print(f"\nPost-migration verification:")
        print(f"  Total records in database: {total_count}")
        print(f"  National average records (zip={NATIONAL_ZIP}): {national_count}")
        print(f"  Expected new records: {expected_count}")

        # Get date range
        date_range = db.session.query(
            db.func.min(MortgageRate.rate_date),
            db.func.max(MortgageRate.rate_date)
        ).filter_by(zip_code=NATIONAL_ZIP).first()

        if date_range[0] and date_range[1]:
            print(f"  Date range: {date_range[0].date()} to {date_range[1].date()}")

        # Sample some records
        sample = db.session.query(MortgageRate).filter_by(
            zip_code=NATIONAL_ZIP
        ).limit(5).all()

        print(f"\nSample records:")
        for record in sample:
            print(f"  {record}")


def main():
    """Main migration function."""
    print("=" * 80)
    print("Mortgage Rate CSV Migration Script")
    print("=" * 80)

    # Find CSV files
    project_root = Path(__file__).parent.parent.parent
    csv_file = project_root / 'data' / 'processed' / '20210911_mortgage_rate_daily_processed.csv'

    print(f"\nLooking for CSV file: {csv_file}")

    if not csv_file.exists():
        print(f"ERROR: CSV file not found: {csv_file}")
        print("\nSearching for alternative CSV files...")

        # Try to find any CSV files in data directories
        data_dir = project_root / 'data'
        if data_dir.exists():
            csv_files = list(data_dir.rglob('*.csv'))
            if csv_files:
                print(f"Found {len(csv_files)} CSV file(s):")
                for f in csv_files:
                    print(f"  - {f}")
                print("\nPlease update the csv_file path in the script.")
            else:
                print("No CSV files found in data directory.")
        else:
            print(f"Data directory not found: {data_dir}")

        sys.exit(1)

    print(f"Found CSV file: {csv_file}")

    # Create Flask app
    print("\nInitializing Flask app...")
    app = create_app()

    # Read and parse CSV
    print(f"\nReading CSV file...")
    try:
        rates_data = read_csv_file(csv_file)
        print(f"Successfully parsed {len(rates_data)} rate records from CSV")
    except Exception as e:
        print(f"ERROR reading CSV: {e}")
        sys.exit(1)

    # Create model instances
    print("\nCreating MortgageRate records...")
    records = create_mortgage_rate_records(rates_data)
    print(f"Created {len(records)} MortgageRate instances")

    # Check for existing records
    print("\nChecking for existing records in database...")
    existing_rates = get_existing_rates(app)
    print(f"Found {len(existing_rates)} existing rate records")

    # Filter duplicates
    new_records, duplicate_count = filter_duplicates(records, existing_rates)
    print(f"Filtered out {duplicate_count} duplicates")
    print(f"Ready to insert {len(new_records)} new records")

    if not new_records:
        print("\nNo new records to insert. Migration complete.")
        verify_migration(app, 0)
        return

    # Insert records
    print("\nInserting records into database...")
    try:
        inserted = insert_records(app, new_records)
        print(f"\nSuccessfully inserted {inserted} records")
    except Exception as e:
        print(f"ERROR during insertion: {e}")
        sys.exit(1)

    # Verify migration
    verify_migration(app, inserted)

    print("\n" + "=" * 80)
    print("Migration completed successfully!")
    print("=" * 80)


if __name__ == '__main__':
    main()
