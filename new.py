import calendar
import re
from datetime import datetime, timedelta
from flask import  url_for, send_file

def is_sql_safe(sql: str) -> bool:
    """
    Checks whether a generated SQL query is safe by enforcing a whitelist approach.
    Only SELECT queries and WITH (CTEs) are allowed. All known harmful patterns are blocked.
    """
    sql = sql.strip().lower()

    # Allow only SELECT queries or WITH CTEs
    if not (sql.startswith("select") or sql.startswith("with")):
        return False

    # Blacklisted patterns to block dangerous operations
    blacklist_patterns = [
        r"\bdrop\s+table\b",
        r"\bdelete\s+from\b",
        r"\bupdate\s+\w+\s+set\b",
        r"\binsert\s+into\b",
        r"\balter\s+table\b",
        r"\bexec\s+\w+",                 # exec procedure
        r";.*--",                        # stacked queries
        r"--[^\n]*$",                    # SQL comment at end
        r"\btruncate\b",
        r"\bxp_cmdshell\b",              # shell access
        r"union\s+select",               # common injection trick
    ]

    for pattern in blacklist_patterns:
        if re.search(pattern, sql):
            return False

    return True


import re

def detectpattern(text):
    chart_data = []

    stop_words = {
        "distributed", "summarized", "sources", "calls", "categorized",
        "related", "from", "as follows", "are", "follows", "with", "has",
        "tickets", "there", "the", "as", "highest", "types of", "data shows"
    }

    def is_valid_label(label):
        label = label.strip().strip('"“”‘’')
        if not label or len(label) > 40:
            return False
        label_words = set(label.lower().split())
        return stop_words.isdisjoint(label_words)

    def add_matches(matches, label_first=True):
        for item in matches:
            label, count = item if label_first else (item[1], item[0])
            label = label.strip().strip('"“”‘’')
            if is_valid_label(label):
                try:
                    value = int(count.replace(",", "").strip())
                    chart_data.append({"label": label, "value": value})
                except ValueError:
                    continue

    patterns = [
        (r'([A-Za-z0-9\s\-\/&]+?)\s*[-:]\s*([\d,]+)', True),  
        (r'([A-Za-z0-9\s\-\/&]+?)\s+has\s+([\d,]+)', True),  
        (r'([A-Za-z0-9\s\-\/&]+?)\s+(?:with|accounted for|contributed)\s+([\d,]+)\s+tickets?', True),
        (r'([A-Za-z0-9\s\-\/&]+?)\s+leads\s+with\s+([\d,]+)', True),
        (r'([\d,]+)\s+from\s+([A-Za-z0-9\s\-\/&]+?)(?:,|\.|$)', False),
        (r'([A-Za-z0-9\s\-\/&]+?)\s+calls\s+(?:are\s+|with\s+)([\d,]+)', True),
        (r'([A-Za-z0-9\s\-\/&]+?)\s+are the highest\s+with\s+([\d,]+)', True),
        (r'there\s+were\s+([\d,]+)\s+calls\s+(?:related to|categorized as|for)\s+([A-Za-z0-9\s\-\/&]+)', False),
        (r'"([^"]+)"\s*\(\s*([\d,]+)\s+counts?\)', True),
    ]

    for pattern, label_first in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        add_matches(matches, label_first)

    # Remove duplicates
    seen = set()
    unique_data = []
    for item in chart_data:
        key = (item["label"].lower(), item["value"])
        if key not in seen:
            unique_data.append(item)
            seen.add(key)

    return unique_data if unique_data else None

# Export the Data in Various Format
def get_export_urls():
    return {
        'csv': url_for('export_csv', _external=True),
        'excel': url_for('export_excel', _external=True),
        'pdf': url_for('export_pdf', _external=True),
    }
