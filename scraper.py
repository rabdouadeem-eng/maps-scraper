# =====================================================================
# PROFESSIONAL DATA EXTRACTION SYSTEM - ABDellah VENTURES LLC (c) 2026
# إصدار Google Colab الخالص (يعمل من الهاتف، بدون ملفات خارجية)
# الميزات: تقارير، حفظ CSV/JSON، ترحيل ذكي، مصادقة سحابية تلقائية
# Target: Western Markets (USA / UK / Canada / Australia / Europe)
# =====================================================================

# 1. تثبيت المكتبات
!pip install --upgrade gspread pandas requests --quiet

import requests
import pandas as pd
import time
import json
import gspread
from google.colab import auth
from google.colab import userdata
from google.auth import default

print("="*50)
print("🔐 PROFESSIONAL DATA EXTRACTION - ABDellah VENTURES LLC")
print("="*50)

# 2. سحب المفتاح من Colab Secrets
try:
    GOOGLE_MAPS_API_KEY = userdata.get('GOOGLE_MAPS_API_KEY')
    print("✅ Google Maps API Key loaded from Secrets.")
except Exception as e:
    raise ValueError("❌ 'GOOGLE_MAPS_API_KEY' not found in Colab Secrets. Please add it first.")

# 3. المصادقة مع Google Sheets
print("\n🔑 Authenticating with Google Cloud...")
auth.authenticate_user()
creds, _ = default()
gc = gspread.authorize(creds)
print("✅ Connected to Google Sheets & Google Drive.")

# 4. إعدادات النظام
SHEET_NAME = "Data_Collection"
OUTPUT_CSV = "extracted_data.csv"
OUTPUT_JSON = "extracted_data.json"
DEFAULT_LANGUAGE = "en"                # ✅ English for Western markets
MAX_RESULTS_PER_QUERY = 150

# 5. المدينة المستهدفة — غيّرها حسب الطلب
TARGET_CITY = "New York"               # 🌍 Change: London / Toronto / Sydney / Paris

# 6. قائمة الاستعلامات — تستهدف الغرب
SEARCH_QUERIES = {
    "Lawyers":     f"lawyer in {TARGET_CITY}",
    "Doctors":     f"doctor clinic in {TARGET_CITY}",
    "Cafes":       f"cafe in {TARGET_CITY}",
    "Restaurants": f"restaurant in {TARGET_CITY}",
}

# 7. دالة جلب البيانات مع ترحيل ذكي
def fetch_places(query, api_key, language=DEFAULT_LANGUAGE, max_results=MAX_RESULTS_PER_QUERY):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    results = []
    params = {'query': query, 'key': api_key, 'language': language}

    print(f"\n📡 Fetching: '{query}'...")

    try:
        while len(results) < max_results:
            response = requests.get(url, params=params, timeout=15).json()
            status = response.get('status')

            if status == 'REQUEST_DENIED':
                print(f"❌ Request denied: {response.get('error_message', 'Check your API key')}")
                break
            if status not in ['OK', 'ZERO_RESULTS']:
                print(f"⚠️ Unexpected status: {status}")
                break

            places = response.get('results', [])
            if not places:
                break

            results.extend(places)
            print(f"   └─ Added {len(places)} places (Total: {len(results)})")

            if len(results) >= max_results:
                results = results[:max_results]
                break

            if 'next_page_token' in response:
                time.sleep(2.5)
                params = {'pagetoken': response['next_page_token'], 'key': api_key}
            else:
                break
    except Exception as e:
        print(f"⚠️ Connection error: {str(e)}")

    return results

# 8. تنظيف البيانات
def process_data(raw_results, category):
    cleaned = []
    for place in raw_results:
        opening = place.get('opening_hours', {})
        open_now = opening.get('open_now') if opening else None
        loc = place.get('geometry', {}).get('location', {})
        cleaned.append({
            "Category":        category,
            "Name":            place.get("name", "N/A"),
            "Address":         place.get("formatted_address", "N/A"),
            "Rating":          place.get("rating", "N/A"),
            "Total Reviews":   place.get("user_ratings_total", 0),
            "Status":          "Open Now" if open_now else "Closed/Unknown",
            "Location":        f"{loc.get('lat')}, {loc.get('lng')}",
            "Place ID":        place.get("place_id", ""),
            "City":            TARGET_CITY,
        })
    return cleaned

# 9. الحفظ في Google Sheets
def save_to_google_sheets(data, sheet_name, gc):
    try:
        try:
            sh = gc.open(sheet_name)
            ws = sh.get_worksheet(0)
        except:
            sh = gc.create(sheet_name)
            ws = sh.get_worksheet(0)
            print(f"📁 Created new sheet: {sheet_name}")

        df = pd.DataFrame(data)
        ws.clear()
        ws.update('A1', [df.columns.values.tolist()] + df.values.tolist())
        print(f"✅ Saved {len(data)} records to Google Sheets: {sheet_name}")
    except Exception as e:
        print(f"❌ Sheets save failed: {e}")

# 10. الحفظ محلياً
def save_to_csv(data, filename):
    pd.DataFrame(data).to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"💾 CSV saved: {filename}")

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"📦 JSON saved: {filename}")

# 11. تقرير إحصائيات
def generate_report(all_data):
    df = pd.DataFrame(all_data)
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')  # ✅ Fix: convert to number
    print("\n" + "="*55)
    print("📈 EXTRACTION REPORT - ABDellah VENTURES LLC")
    print("="*55)
    print(f"Target City      : {TARGET_CITY}")
    print(f"Total Records    : {len(df)}")
    if df.empty:
        return
    print("\nBy Category:")
    print(df['Category'].value_counts().to_string())
    print(f"\nAverage Rating   : {df['Rating'].mean():.2f}")
    print(f"Total Reviews    : {df['Total Reviews'].sum()}")
    print(f"Currently Open   : {df[df['Status'] == 'Open Now'].shape[0]}")
    print("="*55)

# 12. التنفيذ الرئيسي
if __name__ == "__main__":
    print(f"\n🚀 Starting extraction for: {TARGET_CITY}...")
    all_data = []

    for category, query in SEARCH_QUERIES.items():
        raw = fetch_places(query, GOOGLE_MAPS_API_KEY)
        if raw:
            processed = process_data(raw, category)
            all_data.extend(processed)
        time.sleep(1.5)

    if not all_data:
        print("\n⚠️ No data extracted. Check your API key and billing in Google Cloud Platform.")
    else:
        save_to_csv(all_data, OUTPUT_CSV)
        save_to_json(all_data, OUTPUT_JSON)
        save_to_google_sheets(all_data, SHEET_NAME, gc)
        generate_report(all_data)

        print("\n🎉 Done! Data is ready.")
        print(f"📥 Download CSV & JSON from the Colab Files panel.")
        print(f"📊 Google Sheets: '{SHEET_NAME}'")
