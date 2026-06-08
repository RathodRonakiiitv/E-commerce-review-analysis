"""Deep dive into __INITIAL_STATE__ widget structure."""
import json
import sys

with open("debug_review_page.html", "r", encoding="utf-8") as f:
    html = f.read()

start = html.find("window.__INITIAL_STATE__ = {")
end = html.find("</script>", start)
json_str = html[start + len("window.__INITIAL_STATE__ = "):end].rstrip().rstrip(";")
data = json.loads(json_str)

mws = data.get("multiWidgetState", {})
print(f"multiWidgetState keys: {list(mws.keys())}")

# Check widgetState
ws = mws.get("widgetState", {})
print(f"\nwidgetState: {len(ws)} widgets")

for wk, wv in ws.items():
    if not isinstance(wv, dict):
        continue
    # Convert to string and check for review-related content
    wv_json = json.dumps(wv)
    has_review = "review" in wv_json.lower()[:500]
    has_rating = "rating" in wv_json.lower()[:500]
    has_text = len(wv_json) > 1000
    
    marker = ""
    if has_review:
        marker += " [REVIEW]"
    if has_rating:
        marker += " [RATING]"
    
    print(f"  {wk}: {len(wv_json)} chars{marker}")
    
    if has_review or has_rating:
        # Dump top-level structure of this widget
        for ik, iv in wv.items():
            if isinstance(iv, dict):
                inner_size = len(json.dumps(iv))
                print(f"    .{ik}: dict ({inner_size} chars) keys={list(iv.keys())[:6]}")
                # Go one level deeper for large dicts
                if inner_size > 500:
                    for ik2, iv2 in iv.items():
                        if isinstance(iv2, dict):
                            print(f"      .{ik2}: dict keys={list(iv2.keys())[:8]}")
                        elif isinstance(iv2, list):
                            print(f"      .{ik2}: list len={len(iv2)}")
                            if iv2 and isinstance(iv2[0], dict):
                                print(f"        first item keys: {list(iv2[0].keys())[:10]}")
                                # Show first item preview
                                for fk, fv in list(iv2[0].items())[:8]:
                                    if isinstance(fv, str):
                                        print(f"          {fk}: {fv[:80]}")
                                    elif isinstance(fv, (int, float, bool)):
                                        print(f"          {fk}: {fv}")
                                    else:
                                        print(f"          {fk}: [{type(fv).__name__}]")
                        else:
                            val = str(iv2)[:80]
                            print(f"      .{ik2}: {val}")
            elif isinstance(iv, list):
                print(f"    .{ik}: list (len={len(iv)})")
                if iv and isinstance(iv[0], dict):
                    print(f"      first item keys: {list(iv[0].keys())[:10]}")
            else:
                val = str(iv)[:60]
                print(f"    .{ik}: {val}")
