"""Find actual review data in Flipkart's __INITIAL_STATE__."""
import json
import sys

with open("debug_review_page.html", "r", encoding="utf-8") as f:
    html = f.read()

start = html.find("window.__INITIAL_STATE__ = {")
end = html.find("</script>", start)
json_str = html[start + len("window.__INITIAL_STATE__ = "):end].rstrip().rstrip(";")
data = json.loads(json_str)

mws = data.get("multiWidgetState", {})

# Check all top-level keys and their sizes
for k, v in mws.items():
    size = len(json.dumps(v)) if isinstance(v, (dict, list)) else len(str(v))
    print(f"  {k}: {type(v).__name__} ({size} chars)")

# Look at widgetsData
wd = mws.get("widgetsData", {})
if isinstance(wd, dict):
    print(f"\nwidgetsData has {len(wd)} entries")
    for wk, wv in wd.items():
        size = len(json.dumps(wv)) if isinstance(wv, (dict, list)) else len(str(wv))
        print(f"  {wk}: {size} chars")
        if size > 1000:
            # Check for review content
            sample = json.dumps(wv)[:300]
            if any(kw in sample.lower() for kw in ["review", "rating", "certified", "buyer"]):
                print(f"    ^^ REVIEW CONTENT DETECTED")
elif isinstance(wd, list):
    print(f"\nwidgetsData is a list with {len(wd)} entries")
    for i, item in enumerate(wd):
        size = len(json.dumps(item))
        print(f"  [{i}]: {size} chars - {type(item).__name__}")
        if isinstance(item, dict):
            print(f"    keys: {list(item.keys())[:8]}")
            sample = json.dumps(item)[:300]
            if any(kw in sample.lower() for kw in ["review", "rating", "certified"]):
                print(f"    ^^ REVIEW CONTENT DETECTED")
                # Show structure
                for ik, iv in item.items():
                    if isinstance(iv, (dict, list)):
                        print(f"    .{ik}: {type(iv).__name__} ({len(json.dumps(iv))} chars)")
                    else:
                        print(f"    .{ik}: {str(iv)[:60]}")

# Also check pageDataResponse
pdr = mws.get("pageDataResponse", {})
if pdr:
    print(f"\npageDataResponse: {type(pdr).__name__}")
    if isinstance(pdr, dict):
        for k, v in pdr.items():
            size = len(json.dumps(v)) if isinstance(v, (dict, list)) else len(str(v))
            print(f"  {k}: {size} chars")

# Check viewModel
vm = mws.get("viewModel", {})
if vm:
    print(f"\nviewModel: {type(vm).__name__} ({len(json.dumps(vm))} chars)")
    if isinstance(vm, dict):
        for k, v in vm.items():
            size = len(json.dumps(v)) if isinstance(v, (dict, list)) else len(str(v))
            print(f"  {k}: {size} chars")

# Brute force: search the entire JSON for review-like content
full_json = json.dumps(data)
# Find all occurrences of text that looks like reviews
import re
# Look for "Certified Buyer" in JSON
cb_matches = [m.start() for m in re.finditer(r"Certified Buyer", full_json, re.IGNORECASE)]
print(f"\n'Certified Buyer' in JSON: {len(cb_matches)} occurrences")
if cb_matches:
    for pos in cb_matches[:3]:
        context = full_json[max(0, pos-200):pos+200]
        print(f"  Context: ...{context}...")

# Look for review text patterns
text_matches = [m.start() for m in re.finditer(r'"text"\s*:\s*"[^"]{20,}', full_json)]
print(f"\n'text' fields with 20+ chars: {len(text_matches)} occurrences")
if text_matches:
    for pos in text_matches[:5]:
        context = full_json[pos:pos+150]
        print(f"  {context[:150]}")
