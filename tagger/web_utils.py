from collections import defaultdict

def format_results(results):
    """Gruppiert Ergebnisse nach Verzeichnis"""
    grouped = defaultdict(list)
    for item in results:
        grouped[item['directory']].append(item)
    return dict(grouped)
