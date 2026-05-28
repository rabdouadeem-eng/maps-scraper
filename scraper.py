# =====================================================================
# PROFESSIONAL DATA EXTRACTION SYSTEM - ABDellah VENTURES LLC (c) 2026
# Target: Western Markets (USA / UK / Canada / Australia / Europe)
# Uses: Google Places API (New) v1
# =====================================================================

import requests
import pandas as pd
import time
import json
import gspread
from google.colab import auth, userdata
from google.auth import default

print("="*50)
print("🔐 PROFESSIONAL DATA EXTRACTION - ABDellah VENTURES LLC")
print("="*50)

# 1. API Key
GOOGLE_MAPS_API_KEY = userdata.get('GOOGLE_MAPS_API_KEY').strip()
print("✅ Google Maps API Key loaded from Secrets.")

# 2. Google Sheets Auth
print("\n🔑 Authenticating with Google Cloud...")
auth.authenticate_user()
creds, _ = default()
gc = gspread.authorize(creds)
print("✅ Connected to Google Sheets & Google Drive.")

# 3. Settings
SHEET_NAME    = "Data_Collection"
OUTPUT_CSV    = "extracted_data.csv"
OUTPUT_JSON   = "extracted_data.json"
TARGET_CITY   = "New York"   # Change: London / Toronto / Sydney / Paris
MAX_RESULTS   = 60           # New API: max 20/request x 3 pages

SEARCH_QUERIES = {
    "Lawyers":     f"lawyer in {TARGET_CITY}",
    "Doctors":     f"doctor clinic in {TARGET_CITY}",
    "Cafes":       f"cafe in {TARGET_CITY}",
    "Restaurants": f"restaurant in {TARGET_CITY}",
}

# 4. Fetch using New Places API
def fetch_places(query, api_key, max_results=MAX_RESULTS):
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.currentOpeningHours,places.location,nextPageToken"
    }
    results = []
    page_token = None
    print(f"\n📡 Fetching: '{query}'...")

    while len(results) < max_results:
        body = {"textQuery": query, "languageCode": "en", "maxResultCount": 20}
        if page_token:
            body["pageToken"] = page_token

        resp = requests.post(url, headers=headers, json=body, timeout=15)
        data = resp.json()

        if "error" in data:
            print(f"❌ Error: {data['error'].get('message', 'Unknown error')}")
            break

        places = data.get("places", [])
        if not places:
            break

        results.extend(places)
        print(f"   └─ Added {len(places)} places (Total: {len(results)})")

        page_token = data.get("nextPageToken")
        if not page_token or len(results) >= max_results:
            break
        time.sleep(2)

    return results[:max_results]

# 5. Process data
def process_data(raw, category):
    cleaned = []
    for p in raw:
        loc = p.get("location", {})
        oh  = p.get("currentOpeningHours", {})
        cleaned.append({
            "Category":      category,
            "Name":          p.get("displayName", {}).get("text", "N/A"),
            "Address":       p.get("formattedAddress", "N/A"),
            "Rating":        p.get("rating", "N/A"),
            "Total Reviews": p.get("userRatingCount", 0),
            "Status":        "Open Now" if oh.get("openNow") else "Closed/Unknown",
            "Latitude":      loc.get("latitude", ""),
            "Longitude":     loc.get("longitude", ""),
            "Place ID":      p.get("id", ""),
            "City":          TARGET_CITY,
        })
    return cleaned

# 6. Save to Google Sheets
def save_to_sheets(data, name, gc):
    try:
        try:
            sh = gc.open(name)
            ws = sh.get_worksheet(0)
        except:
            sh = gc.create(name)
            ws = sh.get_worksheet(0)
            print(f"📁 Created sheet: {name}")
        df = pd.DataFrame(data)
        ws.clear()
        ws.update('A1', [df.columns.tolist()] + df.values.tolist())
        print(f"✅ Saved {len(data)} records to Sheets: {name}")
    except Exception as e:
        print(f"❌ Sheets error: {e}")

# 7. Save CSV / JSON
def save_csv(data, f):
    pd.DataFrame(data).to_csv(f, index=False, encoding='utf-8-sig')
    print(f"💾 CSV saved: {f}")

def save_json(data, f):
    with open(f, 'w', encoding='utf-8') as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    print(f"📦 JSON saved: {f}")

# 8. Report
def report(data):
    df = pd.DataFrame(data)
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
    print("\n" + "="*50)
    print("📈 EXTRACTION REPORT - ABDellah VENTURES LLC")
    print("="*50)
    print(f"City         : {TARGET_CITY}")
    print(f"Total Records: {len(df)}")
    if not df.empty:
        print(f"\nBy Category:\n{df['Category'].value_counts().to_string()}")
        print(f"\nAvg Rating   : {df['Rating'].mean():.2f}")
        print(f"Total Reviews: {df['Total Reviews'].sum()}")
        print(f"Open Now     : {df[df['Status']=='Open Now'].shape[0]}")
    print("="*50)

# 9. Main
print(f"\n🚀 Starting extraction for: {TARGET_CITY}...")
all_data = []

for category, query in SEARCH_QUERIES.items():
    raw = fetch_places(query, GOOGLE_MAPS_API_KEY)
    if raw:
        all_data.extend(process_data(raw, category))
    time.sleep(1.5)

if not all_data:
    print("\n⚠️ No data extracted. Check API key, billing, and Places API (New) in Google Cloud.")
else:
    save_csv(all_data, OUTPUT_CSV)
    save_json(all_data, OUTPUT_JSON)
    save_to_sheets(all_data, SHEET_NAME, gc)
    report(all_data)
    print("\n🎉 Done! Data is ready.")
    print(f"📥 Download CSV & JSON from the Colab Files panel.")
    print(f"📊 Google Sheets: '{SHEET_NAME}'")
