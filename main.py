import os
import json
import time
import urllib.request
import urllib.error
import math
import re
from datetime import datetime, timedelta, timezone
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 設定 ---
API_KEY = os.environ.get("GEMINI_API_KEY")
JST = timezone(timedelta(hours=9), 'JST')

# --- 2026年 祝日定義 ---
HOLIDAYS_2026 = {
    "2026-01-01", "2026-01-12", "2026-02-11", "2026-02-23", "2026-03-20",
    "2026-04-29", "2026-05-03", "2026-05-04", "2026-05-05", "2026-05-06",
    "2026-07-20", "2026-08-11", "2026-09-21", "2026-09-22", "2026-09-23",
    "2026-10-12", "2026-11-03", "2026-11-23", "2026-11-24"
}

# --- 戦略的30地点定義 ---
TARGET_AREAS = {
    "hakodate": { "name": "北海道 函館", "jma_code": "014100", "amedas_code": "23411", "lat": 41.7687, "lon": 140.7288, "feature": "観光・夜景・海鮮。冬は雪の影響大。クルーズ船寄港地。" },
    "sapporo": { "name": "北海道 札幌", "jma_code": "016000", "amedas_code": "14163", "lat": 43.0618, "lon": 141.3545, "feature": "北日本最大の歓楽街ススキノ。雪まつり等のイベント。" },
    "sendai": { "name": "宮城 仙台", "jma_code": "040000", "amedas_code": "34392", "lat": 38.2682, "lon": 140.8694, "feature": "東北のビジネス拠点。国分町の夜間需要。" },
    "tokyo_marunouchi": { "name": "東京 丸の内・東京駅", "jma_code": "130000", "amedas_code": "44132", "lat": 35.6812, "lon": 139.7671, "feature": "日本のビジネス中心地。出張・接待・富裕層需要。" },
    "tokyo_ginza": { "name": "東京 銀座・新橋", "jma_code": "130000", "amedas_code": "44132", "lat": 35.6701, "lon": 139.7630, "feature": "夜の接待需要とサラリーマンの聖地。高級店多し。" },
    "tokyo_shinjuku": { "name": "東京 新宿・歌舞伎町", "jma_code": "130000", "amedas_code": "44132", "lat": 35.6914, "lon": 139.7020, "feature": "世界一の乗降客数と眠らない街。タクシー需要最強。" },
    "tokyo_shibuya": { "name": "東京 渋谷・原宿", "jma_code": "130000", "amedas_code": "44132", "lat": 35.6580, "lon": 139.7016, "feature": "若者とインバウンド、IT企業の街。トレンド発信地。" },
    "tokyo_roppongi": { "name": "東京 六本木・赤坂", "jma_code": "130000", "amedas_code": "44132", "lat": 35.6641, "lon": 139.7336, "feature": "富裕層、外国人、メディア関係者の夜の移動。" },
    "tokyo_ikebukuro": { "name": "東京 池袋", "jma_code": "130000", "amedas_code": "44132", "lat": 35.7295, "lon": 139.7109, "feature": "埼玉方面への玄関口、サブカルチャー。" },
    "tokyo_shinagawa": { "name": "東京 品川・高輪", "jma_code": "130000", "amedas_code": "44132", "lat": 35.6285, "lon": 139.7397, "feature": "リニア・新幹線拠点。ホテルとビジネス需要。" },
    "tokyo_ueno": { "name": "東京 上野", "jma_code": "130000", "amedas_code": "44132", "lat": 35.7141, "lon": 139.7741, "feature": "北の玄関口、美術館、アメ横。観光客多し。" },
    "tokyo_asakusa": { "name": "東京 浅草", "jma_code": "130000", "amedas_code": "44132", "lat": 35.7119, "lon": 139.7983, "feature": "インバウンド観光の絶対王者。人力車や食べ歩き。" },
    "tokyo_akihabara": { "name": "東京 秋葉原・神田", "jma_code": "130000", "amedas_code": "44132", "lat": 35.6983, "lon": 139.7731, "feature": "オタク文化とビジネスの融合。電気街。" },
    "tokyo_omotesando": { "name": "東京 表参道・青山", "jma_code": "130000", "amedas_code": "44132", "lat": 35.6652, "lon": 139.7123, "feature": "ファッション、富裕層のランチ・買い物需要。" },
    "tokyo_ebisu": { "name": "東京 恵比寿・代官山", "jma_code": "130000", "amedas_code": "44132", "lat": 35.6467, "lon": 139.7101, "feature": "オシャレな飲食需要、タクシー利用率高め。" },
    "tokyo_odaiba": { "name": "東京 お台場・有明", "jma_code": "130000", "amedas_code": "44132", "lat": 35.6278, "lon": 139.7745, "feature": "ビッグサイトのイベント、観光、デートスポット。" },
    "tokyo_toyosu": { "name": "東京 豊洲・湾岸", "jma_code": "130000", "amedas_code": "44132", "lat": 35.6568, "lon": 139.7960, "feature": "タワマン住民の生活需要と市場関係。" },
    "tokyo_haneda": { "name": "東京 羽田空港エリア", "jma_code": "130000", "amedas_code": "44166", "lat": 35.5494, "lon": 139.7798, "feature": "旅行・出張客の送迎需要。天候による遅延影響。" },
    "chiba_maihama": { "name": "千葉 舞浜(ディズニー)", "jma_code": "120000", "amedas_code": "45156", "lat": 35.6329, "lon": 139.8804, "feature": "ディズニーリゾート。イベントと天候への依存度極大。" },
    "kanagawa_yokohama": { "name": "神奈川 横浜", "jma_code": "140000", "amedas_code": "46106", "lat": 35.4437, "lon": 139.6380, "feature": "みなとみらい観光とビジネスが融合。中華街。" },
    "aichi_nagoya": { "name": "愛知 名古屋", "jma_code": "230000", "amedas_code": "51106", "lat": 35.1815, "lon": 136.9066, "feature": "トヨタ系ビジネスと独自の飲食文化。車社会。" },
    "osaka_kita": { "name": "大阪 キタ (梅田)", "jma_code": "270000", "amedas_code": "62078", "lat": 34.7025, "lon": 135.4959, "feature": "西日本最大のビジネス街兼繁華街。地下街発達。" },
    "osaka_minami": { "name": "大阪 ミナミ (難波)", "jma_code": "270000", "amedas_code": "62078", "lat": 34.6655, "lon": 135.5011, "feature": "インバウンド人気No.1。食い倒れの街。" },
    "osaka_hokusetsu": { "name": "大阪 北摂", "jma_code": "270000", "amedas_code": "62078", "lat": 34.7809, "lon": 135.4624, "feature": "伊丹空港/新幹線・ビジネス・高級住宅街。" },
    "osaka_bay": { "name": "大阪 ベイエリア(USJ)", "jma_code": "270000", "amedas_code": "62078", "lat": 34.6654, "lon": 135.4323, "feature": "USJや海遊館。海風強くイベント依存度高い。" },
    "osaka_tennoji": { "name": "大阪 天王寺・阿倍野", "jma_code": "270000", "amedas_code": "62078", "lat": 34.6477, "lon": 135.5135, "feature": "ハルカス/通天閣。新旧文化の融合。" },
    "kyoto_shijo": { "name": "京都 四条河原町", "jma_code": "260000", "amedas_code": "61286", "lat": 35.0037, "lon": 135.7706, "feature": "世界最強の観光都市。インバウンド需要が桁違い。" },
    "hyogo_kobe": { "name": "兵庫 神戸(三宮)", "jma_code": "280000", "amedas_code": "63518", "lat": 34.6946, "lon": 135.1956, "feature": "オシャレな港町。観光とビジネス。" },
    "hiroshima": { "name": "広島", "jma_code": "340000", "amedas_code": "67437", "lat": 34.3853, "lon": 132.4553, "feature": "平和公園・宮島。欧米系インバウンド多い。" },
    "fukuoka": { "name": "福岡 博多・中洲", "jma_code": "400000", "amedas_code": "82182", "lat": 33.5902, "lon": 130.4017, "feature": "アジアの玄関口。屋台文化など夜の需要が強い。" },
    "okinawa_naha": { "name": "沖縄 那覇", "jma_code": "471000", "amedas_code": "91197", "lat": 26.2124, "lon": 127.6809, "feature": "国際通り。観光客メイン。台風等の天候影響大。" },
}

# --- 天気予報コード変換 (雪を☃️に修正) ---
def get_weather_emoji(code):
    try:
        c = int(code)
        # 晴れ系
        if c in [100, 101, 123, 124, 0]: return "☀️"
        if c in [102, 103, 104, 105, 106, 107, 108, 110, 111, 112, 1, 2, 3]: return "🌤️"
        # 曇り系
        if c in [200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 45, 48]: return "☁️"
        # 雨系
        if 300 <= c < 350: return "☔" # 雨
        if c in [51, 53, 55, 61, 63, 65, 80, 81, 82]: return "☔"
        # 雪系 (範囲拡大)
        if 350 <= c < 500: return "☃️" # 雪・みぞれ
        if c in [71, 73, 75, 77, 85, 86]: return "☃️"
        # 荒天
        if c >= 95: return "⛈️"
    except: pass
    return "☁️"

# --- AMeDAS 実況値取得 (今日0時〜現在のMax/Minを算出) ---
def get_amedas_daily_stats(amedas_code):
    """
    今日0時から現在までのアメダス実測値を取得し、本当の最高/最低気温を算出する。
    1時間ごとのデータ(_1h.json)を使うことで、過去の気温を確実に拾う。
    """
    today_str = datetime.now(JST).strftime('%Y%m%d')
    # 1時間ごとの履歴データ
    url = f"https://www.jma.go.jp/bosai/amedas/data/point/{amedas_code}/{today_str}_1h.json"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as res:
            data = json.loads(res.read().decode('utf-8'))
            
            # dataは { "01": {"temp": [10.5, 0]}, "02": ... } の形式
            temps = []
            for hour, vals in data.items():
                if "temp" in vals and vals["temp"][0] is not None:
                    temps.append(vals["temp"][0])
            
            if temps:
                return {"max": max(temps), "min": min(temps)}
    except Exception as e:
        # print(f"AMeDAS Error: {e}")
        pass
    
    return None

# --- JMA データ取得機能 ---
def get_jma_forecast_data(area_code):
    forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    warning_url = f"https://www.jma.go.jp/bosai/warning/data/warning/{area_code}.json"
    
    daily_db = {} 

    try:
        with urllib.request.urlopen(forecast_url, timeout=15) as res:
            data = json.loads(res.read().decode('utf-8'))
            
            # --- 詳細予報 (data[0]) ---
            ts_weather = data[0]["timeSeries"][0]
            codes = ts_weather["areas"][0]["weatherCodes"]
            dates_w = ts_weather["timeDefines"]
            for i, d in enumerate(dates_w):
                date_key = d.split("T")[0]
                if date_key not in daily_db: daily_db[date_key] = {}
                daily_db[date_key]["code"] = codes[i]

            # 降水確率
            ts_rain = data[0]["timeSeries"][1]
            pops = ts_rain["areas"][0]["pops"]
            dates_r = ts_rain["timeDefines"]
            for i, d in enumerate(dates_r):
                date_key = d.split("T")[0]
                if date_key not in daily_db: continue
                if "rain_raw" not in daily_db[date_key]: daily_db[date_key]["rain_raw"] = []
                daily_db[date_key]["rain_raw"].append(pops[i])

            # 気温 (時系列)
            ts_temp = data[0]["timeSeries"][2]
            temps = ts_temp["areas"][0]["temps"]
            dates_t = ts_temp["timeDefines"]
            for i, d in enumerate(dates_t):
                date_key = d.split("T")[0]
                if date_key not in daily_db: continue
                if "temp_raw" not in daily_db[date_key]: daily_db[date_key]["temp_raw"] = []
                daily_db[date_key]["temp_raw"].append(temps[i])

            # --- 週間予報 (data[1]) ---
            if len(data) > 1:
                weekly = data[1]["timeSeries"]
                dates_wk = weekly[0]["timeDefines"]
                w_codes = weekly[0]["areas"][0]["weatherCodes"]
                w_pops = weekly[0]["areas"][0]["pops"] 
                w_min = weekly[1]["areas"][0]["tempsMin"]
                w_max = weekly[1]["areas"][0]["tempsMax"]
                
                for i, d in enumerate(dates_wk):
                    date_key = d.split("T")[0]
                    if date_key not in daily_db: daily_db[date_key] = {}
                    
                    if "code" not in daily_db[date_key]: daily_db[date_key]["code"] = w_codes[i]
                    
                    val = w_pops[i] if i < len(w_pops) else "-"
                    if val != "-": 
                        if "rain_raw" not in daily_db[date_key]: daily_db[date_key]["rain_raw"] = [val]
                    
                    t_min_val = w_min[i] if i < len(w_min) and w_min[i]!="" else None
                    t_max_val = w_max[i] if i < len(w_max) and w_max[i]!="" else None
                    
                    if t_min_val or t_max_val:
                        daily_db[date_key]["temp_summary"] = {"min": t_min_val, "max": t_max_val}

    except Exception as e:
        print(f"JMA Parse Error ({area_code}): {e}")

    warning_text = "特になし"
    try:
        with urllib.request.urlopen(warning_url, timeout=5) as res:
            w_data = json.loads(res.read().decode('utf-8'))
            if "warnings" in w_data:
                names = []
                for w in w_data["warnings"]:
                    if w["status"] not in ["発表なし", "解除"]:
                        names.append("注意報・警報あり")
                        break
                if names: warning_text = "気象警報・注意報 発表中"
    except: pass

    return daily_db, warning_text

# --- Gemini API ---
def call_gemini_search(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    headers = { "Content-Type": "application/json" }
    payload = {
        "contents": [{ "parts": [{"text": prompt}] }],
        "tools": [{ "googleSearch": {} }],
        "generationConfig": { "temperature": 0.7 }
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        if res.status_code == 200:
            data = res.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                return data["candidates"][0]["content"]["parts"][0]["text"]
    except: pass
    return None

def call_gemini_json(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    headers = { "Content-Type": "application/json" }
    payload = {
        "contents": [{ "parts": [{"text": prompt}] }],
        "generationConfig": { "temperature": 0.7, "responseMimeType": "application/json" }
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        if res.status_code == 200:
            data = res.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                return data["candidates"][0]["content"]["parts"][0]["text"]
    except: pass
    return None

def extract_json_block(text):
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match: return match.group(0)
    except: pass
    return text

def get_long_term_text_safe(area_name):
    prompt = f"""
    エリア: {area_name}
    向こう3ヶ月(2-4月)の気象傾向とイベントをGoogle検索し、
    「〜でしょう。」「〜が予定されています。」という自然な日本語の文章でまとめて。
    JSON形式や辞書形式の出力は禁止。読みやすいMarkdownテキストのみ出力せよ。
    """
    res = call_gemini_search(prompt)
    if not res: return "長期予報データの取得に失敗しました。平年並みの傾向を参考にしてください。"
    return res

# --- AI生成 (7日間) ---
def get_ai_advice(area_key, area_data, target_date, daily_db, warning_text):
    if not API_KEY: return None

    today_dt = datetime.now(JST)
    # 日付比較 (時間情報を除外)
    is_today = (target_date.date() == today_dt.date())
    
    date_str = target_date.strftime('%Y-%m-%d')
    date_display = target_date.strftime('%m月%d日')
    weekday_str = ["月", "火", "水", "木", "金", "土", "日"][target_date.weekday()]
    full_date = f"{date_display} ({weekday_str})"
    
    day_data = daily_db.get(date_str, {})
    w_code = day_data.get("code", "200")
    w_emoji = get_weather_emoji(w_code)
    
    # --- 【最強の気温決定ロジック】 ---
    summary = day_data.get("temp_summary", {})
    high_val = summary.get("max")
    low_val = summary.get("min")
    
    # (1) 予報データからの取得・補完
    t_raw = day_data.get("temp_raw", [])
    valid_t = []
    for x in t_raw:
        try: valid_t.append(float(x))
        except: pass
    
    if valid_t:
        if not high_val: high_val = max(valid_t)
        if not low_val: low_val = min(valid_t)

    # (2) アメダス実測値で補完・上書き (今日のみ)
    if is_today:
        amedas_stats = get_amedas_daily_stats(area_data.get("amedas_code", ""))
        if amedas_stats:
            actual_min = amedas_stats["min"]
            actual_max = amedas_stats["max"]
            
            # 最低気温: 予報がない or 予報が高すぎる(現在の気温になっている)場合、実測の最低を採用
            if low_val is None or (low_val > actual_min): 
                low_val = actual_min
            
            # 最高気温: 予報がない or 実測の方が高い場合、実測の最高を採用
            if high_val is None or (actual_max > high_val):
                high_val = actual_max

    # 文字列化 (℃除去)
    str_high = f"{high_val}" if high_val is not None else "-"
    str_low = f"{low_val}" if low_val is not None else "-"
    
    # 万が一、それでも同じ値で "-" でない場合 (アメダス失敗時など)
    if str_high == str_low and str_high != "-":
        # 暫定的に最低気温を空にするか、AIに推測させる
        str_low = "-" 

    # --- 降水確率 ---
    r_raw = day_data.get("rain_raw", [])
    rain_val = "-"
    if r_raw:
        # 最大値を採用してリスク表示
        try: 
            vals = [int(x) for x in r_raw if x != "-"]
            if vals: rain_val = f"{max(vals)}%"
        except: pass
    
    # 表示用文字列
    rain_display = rain_val

    print(f"🤖 {area_data['name']} / {full_date} ", end="", flush=True)

    print("🔍", end="", flush=True)
    # 【修正】ニュース・交通情報を強力に検索
    search_prompt = f"""
    エリア: {area_data['name']}
    日付: {date_str}
    
    以下のキーワードでニュースや運行情報を徹底的に検索せよ:
    「{area_data['name']} 交通情報」「{area_data['name']} イベント」「{area_data['name']} 運行状況」「{area_data['name']} 通行止め」「{area_data['name']} 大雪」「{area_data['name']} 遅延」
    
    特に、悪天候によるJR、地下鉄、バス、飛行機の運休・遅延情報、道路の通行止め情報を最優先で探せ。
    イベントは開催中か、中止かを含めて探せ。
    """
    search_res = call_gemini_search(search_prompt) or "特段の検索結果なし"

    print("📝", end="", flush=True)
    
    # タイムライン用気温 (最高/最低 を一律セット)
    temp_full_str = f"最高{str_high}℃ / 最低{str_low}℃"
    
    # プロンプト更新
    json_prompt = f"""
    あなたは世界屈指の戦略コンサルタントです。
    指定の職業のユーザーが、仕事の意思決定において最も頼りにするような、正確で洞察に満ちたアドバイスを提供してください。
    
    【条件】
    エリア: {area_data['name']}
    日時: {full_date}
    天気: {w_emoji}, 最高気温: {str_high}℃, 最低気温: {str_low}℃, 降水確率: {rain_display}
    
    【検索された重要事実（Event & Traffic）】
    {search_res}
    
    【重要指令】
    1. **ランク判定:** 平日は原則「C」か「B」。ただし、上記検索結果で「大規模イベント」や「深刻な交通麻痺（大雪など）」が確認された場合は、需要増減を加味して「A」または「S」とせよ。
    2. **文章の品質:** - ユーザー目線で、読みやすく、論理的な文章にせよ。
       - 重要な事実は**太文字**や色を活用せずとも伝わるよう、段落を分けて記述せよ。
       - 命令口調（〜してください）は禁止。「〜するとよいでしょう」「〜が推奨されます」という提案型にせよ。
    3. **Event & Traffic欄:** 検索結果にある具体的な交通トラブル（運休、通行止め）やイベント名を必ず記載せよ。フェイクニュースは書くな。
    4. **タイムライン詳細:**
       - **降水確率:** 「午前/午後」と書くな。「30%」のように単一の数値のみ書け。
       - **気温:** 朝・昼・夜すべての欄に「{temp_full_str}」と記載せよ（ユーザーが1日の寒暖差を常に意識できるようにするため）。
    
    5. **JSON出力:**
    {{
        "date": "{full_date}",
        "is_long_term": false,
        "rank": "S/A/B/C",
        "weather_overview": {{ 
            "condition": "{w_emoji}", 
            "high": "最高{str_high}℃", "low": "最低{str_low}℃", "rain": "{rain_display}",
            "warning": "{warning_text}"
        }},
        "daily_schedule_and_impact": "【{date_display}のレポート】\\n\\n**■Event & Traffic**\\n(検索された交通・イベント情報を要約)...\\n\\n**■総括**\\n(コンサルタントとしての分析)...\\n\\n**■推奨戦略**\\n・(具体的なアクション)...", 
        "timeline": {{
            "morning": {{ "weather": "{w_emoji}", "temp": "{temp_full_str}", "rain": "{rain_display}", "advice": {{ "taxi": "...", "restaurant": "...", "hotel": "...", "shop": "...", "logistics": "...", "conveni": "...", "construction": "...", "delivery": "...", "security": "..." }} }},
            "daytime": {{ "weather": "{w_emoji}", "temp": "{temp_full_str}", "rain": "{rain_display}", "advice": {{ "taxi": "...", "restaurant": "...", "hotel": "...", "shop": "...", "logistics": "...", "conveni": "...", "construction": "...", "delivery": "...", "security": "..." }} }},
            "night": {{ "weather": "{w_emoji}", "temp": "{temp_full_str}", "rain": "{rain_display}", "advice": {{ "taxi": "...", "restaurant": "...", "hotel": "...", "shop": "...", "logistics": "...", "conveni": "...", "construction": "...", "delivery": "...", "security": "..." }} }}
        }}
    }}
    """
    
    res = call_gemini_json(json_prompt)
    if res:
        try:
            j = json.loads(extract_json_block(res))
            print("OK")
            return j
        except: pass
    
    print("NG")
    return None

def get_smart_forecast(target_date, long_term_text):
    date_str = target_date.strftime('%Y-%m-%d')
    date_display = target_date.strftime('%m月%d日')
    weekday_str = ["月", "火", "水", "木", "金", "土", "日"][target_date.weekday()]
    full_date = f"{date_display} ({weekday_str})"
    
    rank = "C"
    if target_date.weekday() == 5: rank = "B" 
    elif target_date.weekday() == 4: rank = "B" 
    if date_str in HOLIDAYS_2026: rank = "B"
    next_day = (target_date + timedelta(days=1)).strftime('%Y-%m-%d')
    if next_day in HOLIDAYS_2026: rank = "B"

    # カレンダー用のアドバイス欄にイベント情報を入れるためのプレースホルダー
    # AI生成ではないため、ここには具体的なイベントは入らないが、フォーマットは合わせる
    return {
        "date": full_date, "is_long_term": True, "rank": rank,
        "weather_overview": { "condition": "☁️", "high": "-", "low": "-", "rain": "-", "warning": "-" },
        "daily_schedule_and_impact": f"【{date_display}の長期予測】\n\n**■Event & Traffic**\n詳細は直近の予測をご確認ください。\n\n**■長期傾向**\n{long_term_text}",
        "timeline": None
    }

# --- 並列処理ラッパー ---
def process_single_area(item):
    area_key, area_data = item
    print(f"\n📍 {area_data['name']} 開始", flush=True)
    daily_db, warning_text = get_jma_forecast_data(area_data["jma_code"])
    long_term_text = get_long_term_text_safe(area_data["name"])
    
    area_forecasts = []
    today_dt = datetime.now(JST)
    for i in range(90):
        target_date = today_dt + timedelta(days=i)
        if i < 7: 
            data = get_ai_advice(area_key, area_data, target_date, daily_db, warning_text)
            if data: area_forecasts.append(data)
            else: area_forecasts.append(get_smart_forecast(target_date, long_term_text))
        else:
            area_forecasts.append(get_smart_forecast(target_date, long_term_text))
    print(f"✅ {area_data['name']} 完了")
    return area_key, area_forecasts

if __name__ == "__main__":
    today = datetime.now(JST)
    print(f"🦅 Eagle Eye v4.0 (AMeDAS+Pro) 起動: {today.strftime('%Y/%m/%d')}", flush=True)
    
    master_data = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_single_area, item) for item in TARGET_AREAS.items()]
        for future in as_completed(futures):
            try:
                key, data = future.result()
                master_data[key] = data
            except Exception as e: print(f"Err: {e}")

    with open("eagle_eye_data.json", "w", encoding="utf-8") as f:
        json.dump(master_data, f, ensure_ascii=False, indent=2)
    print("\n✅ 全工程完了", flush=True)
