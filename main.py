import os
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
import google.generativeai as genai
import math

# --- 設定 ---
API_KEY = os.environ.get("GEMINI_API_KEY")
JST = timezone(timedelta(hours=9), 'JST')

# ★全エリア解放
TARGET_AREAS = {
    "hakodate": {
        "name": "北海道 函館市",
        "lat": 41.7687, "lon": 140.7288,
        "feature": "日本有数の観光都市。夜景と海鮮が人気。異国情緒あふれる街並み。クルーズ船の寄港地でもある。"
    },
    "osaka_hokusetsu": {
        "name": "大阪 北摂 (豊中・新大阪)",
        "lat": 34.7809, "lon": 135.4624,
        "feature": "伊丹空港や新大阪駅があり移動拠点となる。治安が良く落ち着いた住宅街も多い。"
    },
    "osaka_kita": {
        "name": "大阪 キタ (梅田)",
        "lat": 34.7025, "lon": 135.4959,
        "feature": "西日本最大のビジネス街兼繁華街。グランフロントや地下街が発達。"
    },
    "osaka_minami": {
        "name": "大阪 ミナミ (難波)",
        "lat": 34.6655, "lon": 135.5011,
        "feature": "インバウンド人気No.1。道頓堀、グリコ、食い倒れの街。夜の需要が高い。"
    },
    "osaka_bay": {
        "name": "大阪 ベイエリア (USJ)",
        "lat": 34.6654, "lon": 135.4323,
        "feature": "USJや海遊館がある海沿いのエリア。風の影響を受けやすく、イベント依存度が高い。"
    },
    "osaka_tennoji": {
        "name": "大阪 天王寺・阿倍野",
        "lat": 34.6477, "lon": 135.5135,
        "feature": "あべのハルカスと通天閣(新世界)が共存するエリア。新旧の文化が入り混じる。"
    }
}

# --- 天気コードを絵文字に変換 ---
def get_weather_emoji(code):
    if code == 0: return "☀️" # 快晴
    if code in [1, 2]: return "🌤️" # 晴れ時々曇り
    if code == 3: return "☁️" # 曇り
    if code in [45, 48]: return "🌫️" # 霧
    if code in [51, 53, 55]: return "🌧️" # 小雨
    if code in [61, 63, 65]: return "☔" # 雨
    if code in [80, 81, 82]: return "⛈️" # にわか雨
    if code in [71, 73, 75, 77, 85, 86]: return "⛄" # 雪
    if code >= 95: return "⛈️" # 雷雨
    return "☁️" # デフォルト

# --- 降水確率を10%単位に丸める ---
def round_prob(prob):
    return math.ceil(prob / 10) * 10

# --- 天気取得関数 (強化版: 絵文字、午前/午後確率) ---
def get_real_weather(lat, lon, date_obj):
    date_str = date_obj.strftime('%Y-%m-%d')
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation_probability,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia%2FTokyo&start_date={date_str}&end_date={date_str}"
    
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode())
                daily = data['daily']
                hourly = data['hourly']
                
                # 午前(6-12時)と午後(12-18時)の最大降水確率を計算
                prob_am = round_prob(max(hourly['precipitation_probability'][6:12]))
                prob_pm = round_prob(max(hourly['precipitation_probability'][12:18]))
                rain_str = f"午前{prob_am}% / 午後{prob_pm}%"

                main_weather = {
                    "max_temp": daily['temperature_2m_max'][0],
                    "min_temp": daily['temperature_2m_min'][0],
                    "rain_str": rain_str,
                    "code": daily['weather_code'][0],
                    "emoji": get_weather_emoji(daily['weather_code'][0])
                }
                
                # 時間別データ（ピンポイント抽出＆絵文字化）
                morning = {
                    "temp": hourly['temperature_2m'][8],
                    "rain": hourly['precipitation_probability'][8],
                    "emoji": get_weather_emoji(hourly['weather_code'][8])
                }
                daytime = {
                    "temp": hourly['temperature_2m'][13],
                    "rain": hourly['precipitation_probability'][13],
                    "emoji": get_weather_emoji(hourly['weather_code'][13])
                }
                night = {
                    "temp": hourly['temperature_2m'][19],
                    "rain": hourly['precipitation_probability'][19],
                    "emoji": get_weather_emoji(hourly['weather_code'][19])
                }
                
                return {"main": main_weather, "morning": morning, "daytime": daytime, "night": night}

        except Exception as e:
            print(f"⚠️ 天気API取得エラー(試行{attempt+1}): {e}", flush=True)
            time.sleep(2)

    return None

# --- モデル選択 (Google検索を有効化) ---
def get_model():
    genai.configure(api_key=API_KEY)
    target_model = "models/gemini-2.5-flash"
    # ★ここで tools='google_search_retrieval' を指定して検索機能をONにする
    tools = 'google_search_retrieval'
    try:
        print(f"Testing model: {target_model} with Google Search", flush=True)
        return genai.GenerativeModel(target_model, tools=tools)
    except:
        print("Fallback to 1.5-flash with Google Search", flush=True)
        target_model = 'models/gemini-1.5-flash'
        return genai.GenerativeModel(target_model, tools=tools)

# --- AI生成 (プロンプト大改造) ---
def get_ai_advice(area_key, area_data, target_date, days_offset):
    if not API_KEY: return None

    date_str = target_date.strftime('%Y年%m月%d日')
    weekday_int = target_date.weekday()
    weekday_str = ["月", "火", "水", "木", "金", "土", "日"][weekday_int]
    full_date = f"{date_str} ({weekday_str})"
    
    real_weather = get_real_weather(area_data["lat"], area_data["lon"], target_date)
    
    main_condition = "不明"
    w_info = "天気データ取得失敗。今の時期の気候を推測してください。"
    
    if real_weather:
        main_condition = real_weather['main']['emoji'] # 絵文字を使う
        w_info = f"""
        【実況天気予報データ (信頼度高)】
        全体: {real_weather['main']['emoji']} 最高{real_weather['main']['max_temp']}℃ / 最低{real_weather['main']['min_temp']}℃ / 降水確率: {real_weather['main']['rain_str']}
        朝(08:00): {real_weather['morning']['emoji']} {real_weather['morning']['temp']}℃ / 降水{real_weather['morning']['rain']}%
        昼(13:00): {real_weather['daytime']['emoji']} {real_weather['daytime']['temp']}℃ / 降水{real_weather['daytime']['rain']}%
        夜(19:00): {real_weather['night']['emoji']} {real_weather['night']['temp']}℃ / 降水{real_weather['night']['rain']}%
        """
    else:
        print(f"⚠️ {area_data['name']} の天気データが取得できませんでした。", flush=True)

    print(f"🤖 [AI予測] {area_data['name']} / {full_date} 生成開始(Google検索実行中)...", flush=True)

    # ★プロンプトを大幅強化
    prompt = f"""
    あなたは「{area_data['name']}」の地域特性に精通し、Google検索を駆使して最新情報を収集できる高度な観光コンサルタントAIです。
    Target Date: {full_date}
    Area Feature: {area_data['feature']}
    
    【重要指令】
    1. **Google検索を積極的に活用し、裏付けのある情報を取得せよ。**
       - 検索クエリ例: "{area_data['name']} イベント {date_str}", "{area_data['name']} クルーズ船 入港予定 {date_str[:7]}", "{area_data['name']} 交通規制 {date_str}"
    2. **ランク判定の厳格化 (特に函館):**
       - 平日({weekday_str}曜)は、Google検索で**明確な大規模イベントやクルーズ船寄港**が確認できない限り、原則としてランクを「C(閑散)」または「B(普通)」とせよ。安易に「A」をつけてはならない。
    3. **天気情報の絶対遵守:**
       - 以下の実況天気予報データに基づき、矛盾のないアドバイスを行え。特に雨や雪の影響を考慮せよ。
       {w_info}

    【出力要件 (JSON形式のみ)】
    - `rank`: S/A/B/C のいずれか。根拠に基づき厳格に判定。
    - `weather_overview`: `condition`(絵文字), `high`(最高気温), `low`(最低気温), `rain`(午前/午後の確率文字列) を正確に記載。
    - `daily_schedule_and_impact`: **ここが重要。** Google検索で得た具体的なイベント、クルーズ船の着岸・離岸時間、それらが交通や店舗に与える影響、注意点を時系列で詳細に記述せよ。情報がない場合は「特段のイベント情報なし」と記載。
    - `timeline`: 朝・昼・夜の天気絵文字、気温、降水確率と、以下の全職業に対する具体的アドバイス。
      - 対象職業: タクシー, 飲食店, ホテル, 小売店, 物流, コンビニ, 建設・現場, デリバリー, イベント・警備

    ```json
    {{
        "date": "{full_date}", "is_long_term": false, "rank": "...",
        "weather_overview": {{ 
            "condition": "{main_condition}", 
            "high": "{real_weather['main']['max_temp'] if real_weather else '-'}℃", 
            "low": "{real_weather['main']['min_temp'] if real_weather else '-'}℃", 
            "rain": "{real_weather['main']['rain_str'] if real_weather else '-'}%" 
        }},
        "daily_schedule_and_impact": "Google検索結果に基づく、具体的なイベント時間、クルーズ船情報、交通影響などの詳細な記述...",
        "timeline": {{
            "morning": {{ 
                "weather": "{real_weather['morning']['emoji'] if real_weather else '-'}", 
                "temp": "{real_weather['morning']['temp'] if real_weather else '-'}℃", 
                "rain": "{real_weather['morning']['rain'] if real_weather else '-'}%", 
                "advice": {{ "taxi": "...", "restaurant": "...", "hotel": "...", "shop": "...", "logistics": "...", "conveni": "...", "construction": "...", "delivery": "...", "security": "..." }} 
            }},
            "daytime": {{ 
                "weather": "{real_weather['daytime']['emoji'] if real_weather else '-'}", 
                "temp": "{real_weather['daytime']['temp'] if real_weather else '-'}℃", 
                "rain": "{real_weather['daytime']['rain'] if real_weather else '-'}%", 
                "advice": {{ "taxi": "...", "restaurant": "...", "hotel": "...", "shop": "...", "logistics": "...", "conveni": "...", "construction": "...", "delivery": "...", "security": "..." }} 
            }},
            "night": {{ 
                "weather": "{real_weather['night']['emoji'] if real_weather else '-'}", 
                "temp": "{real_weather['night']['temp'] if real_weather else '-'}℃", 
                "rain": "{real_weather['night']['rain'] if real_weather else '-'}%", 
                "advice": {{ "taxi": "...", "restaurant": "...", "hotel": "...", "shop": "...", "logistics": "...", "conveni": "...", "construction": "...", "delivery": "...", "security": "..." }} 
            }}
        }}
    }}
    ```
    """
    
    try:
        model = get_model()
        res = model.generate_content(prompt)
        return json.loads(res.text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        print(f"⚠️ AI生成エラー(Google検索含む): {e}", flush=True)
        return None

# --- 簡易予測 ---
def get_simple_forecast(target_date):
    date_str = target_date.strftime('%Y年%m月%d日')
    weekday_str = ["月", "火", "水", "木", "金", "土", "日"][target_date.weekday()]
    full_date = f"{date_str} ({weekday_str})"
    rank = "C"
    if target_date.weekday() == 5: rank = "B" # 土曜はB
    elif target_date.weekday() == 6: rank = "C" # 日曜はC
    elif target_date.weekday() == 4: rank = "B" # 金曜はB
    
    return {
        "date": full_date, "is_long_term": True, "rank": rank,
        "weather_overview": { "condition": "☁️", "high": "-", "low": "-", "rain": "-" },
        "daily_schedule_and_impact": "簡易予測モードのため詳細情報なし。",
        "timeline": None
    }

# --- メイン ---
if __name__ == "__main__":
    today = datetime.now(JST)
    print(f"🦅 Eagle Eye 全国版(Google検索・厳格ランク・絵文字天気) 起動: {today.strftime('%Y/%m/%d')}", flush=True)
    
    master_data = {}
    
    for area_key, area_data in TARGET_AREAS.items():
        print(f"\n📍 エリア処理開始: {area_data['name']}", flush=True)
        area_forecasts = []
        
        for i in range(90):
            target_date = today + timedelta(days=i)
            # 直近3日のみAI（Google検索）を使用
            if i < 3:
                data = get_ai_advice(area_key, area_data, target_date, i)
                if data:
                    area_forecasts.append(data)
                    time.sleep(2) # 検索負荷を考慮して少し待つ
                else:
                    print("⚠️ 生成失敗。簡易版を適用。", flush=True)
                    area_forecasts.append(get_simple_forecast(target_date))
            else:
                area_forecasts.append(get_simple_forecast(target_date))
        
        master_data[area_key] = area_forecasts

    if len(master_data) > 0:
        with open("eagle_eye_data.json", "w", encoding="utf-8") as f:
            json.dump(master_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 全エリアデータ保存完了", flush=True)
    else:
        exit(1)
