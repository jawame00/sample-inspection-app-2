# Sample Inspection App

A desktop application for managing sample inspections.
Loads sample data and standard values from CSV files, automatically judges exceedances,
and visualizes results with charts.
Developed based on hands-on experience in environmental analysis and quality control,
with basic LIMS functionality in mind.

## Features

- Load sample CSV and standard value CSV
- Automatic judgment of standard exceedance (is_exceeded)
- Automatic separation of control samples and regular samples (sample_type)
- GUI result display with color coding (exceeded: red, passed: green)
- Aggregation by sample_id (exceeded count, total items, overall judgment)
- SQLite log storage for judgment history (timestamp, total count, exceeded count)
- Data search and filtering by sample_id, law, and exceeded-only option
- Monthly analysis chart (bar chart)
- Monthly exceedance rate trend (line chart)
- Exceedance rate by item (horizontal bar chart)
- Control sample control chart (with UCL/LCL lines)

## Technologies & Libraries

- Python 3.11.9
- tkinter (GUI)
- pandas (data processing & aggregation)
- sqlite3 (history log storage)
- matplotlib / japanize-matplotlib (chart display)
- datetime (timestamp recording)

## File Structure
```
project/
├── app.py
├── samples.csv        # Sample data (columns: sample_id, sample_type, value, law)
└── standards.csv      # Standard values (columns: law, standard)
```

### CSV Format Examples

**samples.csv**
```
sample_id,sample_type,value,law
A001,sample,0.08,lead
A002,sample,0.12,lead
CTRL001,control,0.10,lead
```

**standards.csv**
```
law,standard
lead,0.10
arsenic,0.05
cadmium,0.03
mercury,0.005
chromium,0.20
```

## Getting Started
```bash
pip install pandas matplotlib japanize-matplotlib
python3 app.py
```

1. Click the select button next to "検体CSV" and choose samples.csv
2. Click the select button next to "基準値CSV" and choose standards.csv
3. Click "判定実行" to run the judgment
4. Results appear in the detail table and summary table
5. Use the search area to filter results and chart buttons to display graphs

## Chart Features

| Button | Content | Data Source |
|---|---|---|
| 月次グラフ | Monthly execution count and average items | SQLite log |
| 超過率トレンド | Monthly exceedance rate trend | SQLite log |
| 項目別超過率 | Exceedance rate by measurement item | Judgment result |
| 管理図 | Control sample UCL/LCL management chart | Judgment result |

## Planned Features

- CSV export of search results
- Alert function for automatic detection of out-of-spec data
- Advanced history search using SQL
- Web application version (Streamlit)