"""Extract the exact review structure from widgetsData.slots."""
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

# slots is likely a dict or list of widget slot data
print(f"slots type: {type(slots).__name__}")
if isinstance(slots, dict):
    print(f"slots keys: {list(slots.keys())[:10]}")
    # Navigate deeper
    for sk, sv in slots.items():
        if isinstance(sv, dict):
            size = len(json.dumps(sv))
            sample = json.dumps(sv)[:200]
            has_review = "review" in sample.lower() or '"text"' in sample
            print(f"  {sk}: dict ({size} chars) {'[HAS REVIEWS]' if has_review else ''}")
            if has_review and size > 1000:
                # Go deeper
                for ik, iv in sv.items():
                    if isinstance(iv, (dict, list)):
                        isize = len(json.dumps(iv))
                        print(f"    .{ik}: {type(iv).__name__} ({isize} chars)")
                    else:
                        print(f"    .{ik}: {str(iv)[:60]}")
        elif isinstance(sv, list):
            print(f"  {sk}: list (len={len(sv)})")
elif isinstance(slots, list):
    print(f"slots length: {len(slots)}")
    for i, item in enumerate(slots):
        if isinstance(item, dict):
            size = len(json.dumps(item))
            sample = json.dumps(item)[:200]
            has_review = '"text"' in sample and '"title"' in sample
            print(f"  [{i}]: dict ({size} chars) keys={list(item.keys())[:6]} {'[HAS REVIEWS]' if has_review else ''}")

# Try to find the review array directly
full_json = json.dumps(slots)

# Find objects with "text" and "title" pattern (review-like)
# Use a different approach - search for the review pattern
pattern = r'"text"\s*:\s*"[^"]+",\s*"title"\s*:\s*"[^"]+"'
matches = list(re.finditer(pattern, full_json))
print(f"\nReview-like objects found: {len(matches)}")

# Extract one full review object to understand structure
if matches:
    # Go back to find the start of the object containing this text
    pos = matches[0].start()
    # Walk back to find opening brace
    depth = 0
    obj_start = pos
    for p in range(pos, max(0, pos - 2000), -1):
        if full_json[p] == '}':
            depth += 1
        elif full_json[p] == '{':
            if depth == 0:
                obj_start = p
                break
            depth -= 1
    
    # Walk forward to find closing brace
    depth = 0
    obj_end = pos + 100
    for p in range(obj_start, min(len(full_json), obj_start + 5000)):
        if full_json[p] == '{':
            depth += 1
        elif full_json[p] == '}':
            depth -= 1
            if depth == 0:
                obj_end = p + 1
                break
    
    review_json = full_json[obj_start:obj_end]
    try:
        review_obj = json.loads(review_json)
        print(f"\nSample review object keys: {list(review_obj.keys())}")
        for rk, rv in review_obj.items():
            if isinstance(rv, str):
                print(f"  {rk}: \"{rv[:80]}\"")
            elif isinstance(rv, (int, float, bool)):
                print(f"  {rk}: {rv}")
            elif isinstance(rv, dict):
                print(f"  {rk}: dict keys={list(rv.keys())[:6]}")
            elif isinstance(rv, list):
                print(f"  {rk}: list len={len(rv)}")
            elif rv is None:
                print(f"  {rk}: null")
    except json.JSONDecodeError:
        print(f"  Raw JSON (first 500 chars): {review_json[:500]}")
