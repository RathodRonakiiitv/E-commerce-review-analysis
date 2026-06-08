"""Extract and analyze the __INITIAL_STATE__ JSON from Flipkart review page."""
import json
import re
import sys

with open("debug_review_page.html", "r", encoding="utf-8") as f:
    html = f.read()

# Extract __INITIAL_STATE__
start = html.find("window.__INITIAL_STATE__ = {")
if start == -1:
    print("Could not find __INITIAL_STATE__")
    sys.exit(1)

end = html.find("</script>", start)
json_str = html[start + len("window.__INITIAL_STATE__ = "):end].rstrip().rstrip(";")

data = json.loads(json_str)
print(f"Parsed __INITIAL_STATE__, top keys: {list(data.keys())[:10]}")

# Recursive search for review-related keys
def find_reviews(obj, depth=0, path="root"):
    if depth > 8:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if "review" in k.lower():
                if isinstance(v, list) and len(v) > 0:
                    print(f"\n  LIST at {path}.{k} (length={len(v)})")
                    if isinstance(v[0], dict):
                        print(f"    First item keys: {list(v[0].keys())[:15]}")
                        # Show first review content
                        first = v[0]
                        for fk, fv in first.items():
                            val_str = str(fv)[:120] if not isinstance(fv, (dict, list)) else f"[{type(fv).__name__}]"
                            print(f"      {fk}: {val_str}")
                elif isinstance(v, dict):
                    print(f"\n  DICT at {path}.{k} (keys={list(v.keys())[:8]})")
            find_reviews(v, depth + 1, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:3]):
            find_reviews(item, depth + 1, f"{path}[{i}]")

print("\nSearching for review data...")
find_reviews(data)

# Also search for specific widget types
if "multiWidgetState" in data:
    mws = data["multiWidgetState"]
    if "widgetState" in mws:
        ws = mws["widgetState"]
        print(f"\n\nWidget state keys: {list(ws.keys())[:20]}")
        for wk, wv in ws.items():
            if isinstance(wv, dict):
                inner_keys = list(wv.keys())[:5]
                print(f"  Widget '{wk}': {inner_keys}")
                # Check if this widget has review data
                wv_str = json.dumps(wv)[:200]
                if "review" in wv_str.lower() or "certified" in wv_str.lower():
                    print(f"    ^^ CONTAINS REVIEW DATA")
                    # Dump structure
                    for ik, iv in wv.items():
                        if isinstance(iv, dict):
                            print(f"    {ik}: dict keys={list(iv.keys())[:8]}")
                        elif isinstance(iv, list):
                            print(f"    {ik}: list len={len(iv)}")
                        else:
                            print(f"    {ik}: {str(iv)[:80]}")
