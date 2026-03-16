# Sample Inspection App

A desktop application for managing sample inspections.
Loads sample data and standard values from CSV files, then automatically judges whether measured values exceed the standards.
Developed based on hands-on experience in environmental analysis and quality control, with basic LIMS functionality in mind.

## Features

- Load sample CSV and standard value CSV
- Automatic judgment of standard exceedance (is_exceeded)
- GUI result display with color coding (exceeded rows in red, passed rows in green)
- Aggregation by sample_id (exceeded count, total items, overall judgment)
- SQLite log storage for judgment history (timestamp, total count, exceeded count)
- Data search and filtering by sample_id, law, and exceeded-only option

## Technologies & Libraries

- Python 3.x
- tkinter (GUI)
- pandas (data processing & aggregation)
- sqlite3 (history log storage)
- datetime (timestamp recording)

## File Structure
```
project/
├── app.py
├── samples.csv        # Sample data (columns: sample_id, value, law)
└── standards.csv      # Standard values (columns: law, standard)
```

### CSV Format Examples

**samples.csv**
```
sample_id,value,law
A-001,0.5,lead
A-001,1.2,arsenic
A-002,0.3,lead
```

**standards.csv**
```
law,standard
lead,1.0
arsenic,1.0
```

## Getting Started
```bash
python3 app.py
```

1. Click the "選択" button next to "検体CSV" and select samples.csv
2. Click the "選択" button next to "基準値CSV" and select standards.csv
3. Click the "判定実行" button to run the judgment
4. Results will appear in the detail table and summary table
5. Use the search area to filter by sample_id, law, or exceeded-only

## Planned Features

- Data visualization with graphs (matplotlib)
- CSV export of search results
- Alert function for automatic detection of out-of-spec data
- Advanced history search using SQL