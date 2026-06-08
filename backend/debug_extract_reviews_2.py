"""Extract review JSON path."""
import json
import re
import sys

with open("debug_review_page.html", "r", encoding="utf-8") as f:
    html = f.read()

start = html.find("window.__INITIAL_STATE__ = {")
end = html.find("</script>", start)
json_str = html[start + len("window.__INITIAL_STATE__ = "):end].rstrip().rstrip(";")
data = json.loads(json_str)

slots = data["multiWidgetState"]["widgetsData"]["slots"]

reviews_found = 0

for i, slot in enumerate(slots):
    # Find all 'text' and 'title' keys recursively
    def find_review_dict(obj, path=""):
        global reviews_found
        if isinstance(obj, dict):
            if "text" in obj and "title" in obj and "rating" in obj:
                reviews_found += 1
                print(f"Found review at: {path}")
                print(f"  Title: {obj['title']}")
                print(f"  Text: {obj['text'][:50]}...")
                print(f"  Rating: {obj['rating']}")
                if "author" in obj:
                    print(f"  Author: {obj['author']}")
                return
            for k, v in obj.items():
                find_review_dict(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                find_review_dict(item, f"{path}[{idx}]")

    find_review_dict(slot, f"slots[{i}]")

print(f"Total reviews found: {reviews_found}")
