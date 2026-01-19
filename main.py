import os
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
import google.generativeai as genai

# --- 設定 ---
API_KEY = os.environ.get("GEMINI_API_KEY")
JST = timezone(timedelta(hours=9), 'JST')

# ★全エリア解放
TARGET_AREAS = {
    "hakodate": {
        "name": "北海道 函館市",
        "lat": 41.7687, "lon": 140.7288,
        "feature": "日本有数の観光都市。夜景と海鮮が人気。異国情緒あふれる街並み。"
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

# --- 天気取得関数 (ケイスケさんの成功ロジック + リトライ強化) ---
def get_real_weather(lat, lon, date_obj):
    date_str = date_obj.strftime('%Y-%m-%d')
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation_probability,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia%2FTokyo&start_date={date_str}&end_date={date_str}"
    
    for attempt in range(3): # 3回リトライ
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                # 日次データ
                daily = data['daily']
                main_weather = {
                    "max_temp": daily['temperature_2m_max'][0],
                    "min_temp": daily['temperature_2m_min'][0],
                    "rain_prob": daily['precipitation_probability_max'][0],
                    "code": daily['weather_code'][0]
                }

                # 時間別データ（ピンポイント抽出）
                hourly = data['hourly']
                
                # 朝 (8時のデータを代表に)
                morning = {
                    "temp": hourly['temperature_2m'][8],
                    "rain": hourly['precipitation_probability'][8],
                    "code": hourly['weather_code'][8]
                }
                # 昼 (13時のデータを代表に)
                daytime = {
                    "temp": hourly['temperature_2m'][13],
                    "rain": hourly['precipitation_probability'][13],
                    "code": hourly['weather_code'][13]
                }
                # 夜 (19時のデータを代表に)
                night = {
                    "temp": hourly['temperature_2m'][19],
                    "rain": hourly['precipitation_probability'][19],
                    "code": hourly['weather_code'][19]
                }
                
                return {"main": main_weather, "morning": morning, "daytime": daytime, "night": night}

        except Exception as e:
            print(f"⚠️ 天気API取得エラー(試行{attempt+1}): {e}", flush=True)
            time.sleep(2) # 少し待って再挑戦

    return None

def get_weather_label(code):
    if code == 0: return "快晴"
    if code in [1, 2, 3]: return "曇り"
    if code in [45, 48]: return "霧"
    if code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: return "雨"
    if code in [71, 73, 75, 77, 85, 86]: return "雪"
    if code >= 95: return "雷雨"
    return "曇り"

# --- モデル選択 (ケイスケさんの成功ロジック) ---
def get_model():
    genai.configure(api_key=API_KEY)
    # 本命: 2.5 (models/付き)
    target_model = "models/gemini-2.5-flash"
    try:
        print(f"Testing model: {target_model}", flush=True)
        return genai.GenerativeModel(target_model)
    except:
        # フォールバック: 1.5 (models/付きにして安全策)
        print("Fallback to 1.5-flash", flush=True)
        target_model = 'models/gemini-1.5-flash'
        return genai.GenerativeModel(target_model)

# --- AI生成 ---
def get_ai_advice(area_key, area_data, target_date, days_offset):
    if not API_KEY: return None

    # 日付整形
    date_str = target_date.strftime('%Y年%m月%d日')
    weekday_str = ["月", "火", "水", "木", "金", "土", "日"][target_date.weekday()]
    full_date = f"{date_str} ({weekday_str})"
    
    # ★実況天気取得
    real_weather = get_real_weather(area_data["lat"], area_data["lon"], target_date)
    
    # 天気情報の文字列作成
    main_condition = "不明"
    w_info = "天気データ取得失敗。今の時期の気候を推測してください。"
    
    if real_weather:
        main_condition = get_weather_label(real_weather['main']['code'])
        w_info = f"""
        【実況天気予報データ】
        全体: 最高{real_weather['main']['max_temp']}℃ / 最低{real_weather['main']['min_temp']}℃ / 降水確率{real_weather['main']['rain_prob']}%
        朝(08:00): 気温{real_weather['morning']['temp']}℃ / 降水{real_weather['morning']['rain']}% / 天気コード{real_weather['morning']['code']}
        昼(13:00): 気温{real_weather['daytime']['temp']}℃ / 降水{real_weather['daytime']['rain']}% / 天気コード{real_weather['daytime']['code']}
        夜(19:00): 気温{real_weather['night']['temp']}℃ / 降水{real_weather['night']['rain']}% / 天気コード{real_weather['night']['code']}
        ※天気コード: 0=晴, 1-3=曇, 50番台60番台=雨, 70番台=雪
        """
    else:
        print(f"⚠️ {area_data['name']} の天気データが取得できませんでした。", flush=True)

    print(f"🤖 [AI予測] {area_data['name']} / {full_date} 生成開始...", flush=True)

    prompt = f"""
    あなたは「{area_data['name']}」の地域特性に精通した観光コンサルタントAIです。
    {full_date}の観光需要予測データを作成してください。
    エリア特徴: {area_data['feature']}
    
    絶対に以下の実況天気予報に基づいてアドバイスを行ってください。
    {w_info}
    
    以下のJSON形式で出力してください（Markdown記号なし）。
    {{
        "date": "{full_date}", "is_long_term": false, "rank": "S/A/B/C",
        "weather_overview": {{ 
            "condition": "{main_condition}", 
            "high": "{real_weather['main']['max_temp'] if real_weather else '-'}℃", 
            "low": "{real_weather['main']['min_temp'] if real_weather else '-'}℃", 
            "rain": "{real_weather['main']['rain_prob'] if real_weather else '-'}%" 
        }},
        "events_info": {{ "event_name": "イベント名", "time_info": "規模感", "traffic_warning": "影響" }},
        "timeline": {{
            "morning": {{ 
                "weather": "概況", "high": "{real_weather['morning']['temp'] if real_weather else '-'}℃", "low": "-", "rain": "{real_weather['morning']['rain'] if real_weather else '-'}%", 
                "advice": {{ "taxi": "...", "restaurant": "...", "hotel": "...", "shop": "...", "logistics": "...", "conveni": "..." }} 
            }},
            "daytime": {{ 
                "weather": "概況", "high": "{real_weather['daytime']['temp'] if real_weather else '-'}℃", "low": "-", "rain": "{real_weather['daytime']['rain'] if real_weather else '-'}%", 
                "advice": {{ "taxi": "...", "restaurant": "...", "hotel": "...", "shop": "...", "logistics": "...", "conveni": "..." }} 
            }},
            "night": {{ 
                "weather": "概況", "high": "{real_weather['night']['temp'] if real_weather else '-'}℃", "low": "-", "rain": "{real_weather['night']['rain'] if real_weather else '-'}%", 
                "advice": {{ "taxi": "...", "restaurant": "...", "hotel": "...", "shop": "...", "logistics": "...", "conveni": "..." }} 
            }}
        }}
    }}
    """
    
    # ケイスケさんのロジックでモデル取得
    try:
        model = get_model()
        res = model.generate_content(prompt)
        return json.loads(res.text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        print(f"⚠️ AI生成エラー: {e}", flush=True)
        return None

# --- 簡易予測 (バックアップ) ---
def get_simple_forecast(target_date):
    date_str = target_date.strftime('%Y年%m月%d日')
    weekday_str = ["月", "火", "水", "木", "金", "土", "日"][target_date.weekday()]
    full_date = f"{date_str} ({weekday_str})"
    rank = "C"
    if target_date.weekday() == 5: rank = "A"
    elif target_date.weekday() in [4, 6]: rank = "B"
    return {
        "date": full_date, "is_long_term": True, "rank": rank,
        "weather_overview": { "condition": "予報待ち", "high": "-", "low": "-", "rain": "-" },
        "events_info": { "event_name": "ー", "time_info": "", "traffic_warning": "" },
        "timeline": None
    }

# --- メイン ---
if __name__ == "__main__":
    today = datetime.now(JST)
    print(f"🦅 Eagle Eye 全国版(過去成功ロジック適用) 起動: {today.strftime('%Y/%m/%d')}", flush=True)
    
    master_data = {}
    
    for area_key, area_data in TARGET_AREAS.items():
        print(f"\n📍 エリア処理開始: {area_data['name']}", flush=True)
        area_forecasts = []
        
        for i in range(90):
            target_date = today + timedelta(days=i)
            
            if i < 3: # 直近3日はAI
                data = get_ai_advice(area_key, area_data, target_date, i)
                if data:
                    area_forecasts.append(data)
                    time.sleep(1) # 成功したら1秒待機
                else:
                    print("⚠️ 生成失敗。簡易版を適用。", flush=True)
                    area_forecasts.append(get_simple_forecast(target_date))
            else:
                area_forecasts.append(get_simple_forecast(target_date))
        
        master_data[area_key] = area_forecasts

    if len(master_data) > 0:
        with open("eagle_eye_data.json", "w",
