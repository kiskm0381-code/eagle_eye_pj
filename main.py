import os
import json
import time
import urllib.request
import urllib.error
import math
from datetime import datetime, timedelta, timezone
import google.generativeai as genai

# --- 設定 ---
API_KEY = os.environ.get("GEMINI_API_KEY")
JST = timezone(timedelta(hours=9), 'JST')

# --- 戦略的30地点定義 (JMAエリアコード修正版) ---
# 気象庁APIのエンドポイントに合わせてコードを修正 (XX0000形式が基本)
TARGET_AREAS = {
    # --- 北海道・東北 ---
    "hakodate": { "name": "北海道 函館", "jma_code": "014100", "feature": "観光・夜景・海鮮。冬は雪の影響大。" }, # 渡島・檜山
    "sapporo": { "name": "北海道 札幌", "jma_code": "016000", "feature": "北日本最大の歓楽街ススキノ。雪まつり等のイベント。" }, # 石狩・空知・後志
    "sendai": { "name": "宮城 仙台", "jma_code": "040000", "feature": "東北のビジネス拠点。国分町の夜間需要。" },
    # --- 東京・関東 (すべて東京都 130000 で取得しエリア特性でAIに判断させる) ---
    "tokyo_marunouchi": { "name": "東京 丸の内・東京駅", "jma_code": "130000", "feature": "日本のビジネス中心地。出張・接待・富裕層需要。" },
    "tokyo_ginza": { "name": "東京 銀座・新橋", "jma_code": "130000", "feature": "夜の接待需要とサラリーマンの聖地。高級店多し。" },
    "tokyo_shinjuku": { "name": "東京 新宿・歌舞伎町", "jma_code": "130000", "feature": "世界一の乗降客数と眠らない街。タクシー需要最強。" },
    "tokyo_shibuya": { "name": "東京 渋谷・原宿", "jma_code": "130000", "feature": "若者とインバウンド、IT企業の街。トレンド発信地。" },
    "tokyo_roppongi": { "name": "東京 六本木・赤坂", "jma_code": "130000", "feature": "富裕層、外国人、メディア関係者の夜の移動。" },
    "tokyo_ikebukuro": { "name": "東京 池袋", "jma_code": "130000", "feature": "埼玉方面への玄関口、サブカルチャー。" },
    "tokyo_shinagawa": { "name": "東京 品川・高輪", "jma_code": "130000", "feature": "リニア・新幹線拠点。ホテルとビジネス需要。" },
    "tokyo_ueno": { "name": "東京 上野", "jma_code": "130000", "feature": "北の玄関口、美術館、アメ横。観光客多し。" },
    "tokyo_asakusa": { "name": "東京 浅草", "jma_code": "130000", "feature": "インバウンド観光の絶対王者。人力車や食べ歩き。" },
    "tokyo_akihabara": { "name": "東京 秋葉原・神田", "jma_code": "130000", "feature": "オタク文化とビジネスの融合。電気街。" },
    "tokyo_omotesando": { "name": "東京 表参道・青山", "jma_code": "130000", "feature": "ファッション、富裕層のランチ・買い物需要。" },
    "tokyo_ebisu": { "name": "東京 恵比寿・代官山", "jma_code": "130000", "feature": "オシャレな飲食需要、タクシー利用率高め。" },
    "tokyo_odaiba": { "name": "東京 お台場・有明", "jma_code": "130000", "feature": "ビッグサイトのイベント、観光、デートスポット。" },
    "tokyo_toyosu": { "name": "東京 豊洲・湾岸", "jma_code": "130000", "feature": "タワマン住民の生活需要と市場関係。" },
    "tokyo_haneda": { "name": "東京 羽田空港エリア", "jma_code": "130000", "feature": "旅行・出張客の送迎需要。天候による遅延影響。" },
    "chiba_maihama": { "name": "千葉 舞浜(ディズニー)", "jma_code": "120000", "feature": "ディズニーリゾート。イベントと天候への依存度極大。" },
    "kanagawa_yokohama": { "name": "神奈川 横浜", "jma_code": "140000", "feature": "みなとみらい観光とビジネスが融合。中華街。" },
    # --- 中部 ---
    "aichi_nagoya": { "name": "愛知 名古屋", "jma_code": "230000", "feature": "トヨタ系ビジネスと独自の飲食文化。車社会。" },
    # --- 関西 ---
    "osaka_kita": { "name": "大阪 キタ (梅田)", "jma_code": "270000", "feature": "西日本最大のビジネス街兼繁華街。地下街発達。" },
    "osaka_minami": { "name": "大阪 ミナミ (難波)", "jma_code": "270000", "feature": "インバウンド人気No.1。食い倒れの街。" },
    "osaka_hokusetsu": { "name": "大阪 北摂", "jma_code": "270000", "feature": "伊丹空港/新幹線・ビジネス・高級住宅街。" },
    "osaka_bay": { "name": "大阪 ベイエリア(USJ)", "jma_code": "270000", "feature": "USJや海遊館。海風強くイベント依存度高い。" },
    "osaka_tennoji": { "name": "大阪 天王寺・阿倍野", "jma_code": "270000", "feature": "ハルカス/通天閣。新旧文化の融合。" },
    "kyoto_shijo": { "name": "京都 四条河原町", "jma_code": "260000", "feature": "世界最強の観光都市。インバウンド需要が桁違い。" },
    "hyogo_kobe": { "name": "兵庫 神戸(三宮)", "jma_code": "280000", "feature": "オシャレな港町。観光とビジネス。" },
    # --- 中国・九州・沖縄 ---
    "hiroshima": { "name": "広島", "jma_code": "340000", "feature": "平和公園・宮島。欧米系インバウンド多い。" },
    "fukuoka": { "name": "福岡 博多・中洲", "jma_code": "400000", "feature": "アジアの玄関口。屋台文化など夜の需要が強い。" },
    "okinawa_naha": { "name": "沖縄 那覇", "jma_code": "471000", "feature": "国際通り。観光客メイン。台風等の天候影響大。" },
}

# --- JMA API 取得・解析 ---
def get_jma_forecast(area_code):
    """気象庁APIから天気、気温、降水確率、注意報を取得"""
    forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    warning_url = f"https://www.jma.go.jp/bosai/warning/data/warning/{area_code}.json"
    
    result = {"forecasts": [], "warning": None}
    
    # 1. 予報データの取得
    try:
        with urllib.request.urlopen(forecast_url, timeout=15) as res:
            data = json.loads(res.read().decode('utf-8'))
            
            # 直近3日間のデータ抽出
            # timeSeries[0]=天気, timeSeries[1]=降水確率, timeSeries[2]=気温 (構造は変動する場合あり)
            # ※気象庁JSONは配列構造が深いので、安全に取得
            
            weather_series = data[0]["timeSeries"][0]
            rain_series = data[0]["timeSeries"][1]
            temp_series = data[0]["timeSeries"][2]
            
            # エリア0番目（代表地点）のデータを取得
            weathers = weather_series["areas"][0].get("weatherCodes", [])
            rains = rain_series["areas"][0].get("pops", [])
            temps = temp_series["areas"][0].get("temps", [])
            
            # データ補正（足りない場合はハイフン）
            def get_val(arr, idx): return arr[idx] if len(arr) > idx else "-"

            result["forecasts"] = [
                {
                    "code": get_val(weathers, 0),
                    "rain_am": get_val(rains, 0),
                    "rain_pm": get_val(rains, 1),
                    # 気温は朝夕の発表タイミングで配列の中身が変わるため、簡易的に取得
                    "high": get_val(temps, 1) if len(temps) > 1 else get_val(temps, 0), 
                    "low": get_val(temps, 0)
                }
            ]
    except Exception as e:
        print(f"JMA Forecast Error ({area_code}): {e}")
        # エラー時はダミーデータを入れて進行させる（止まらないように）
        result["forecasts"] = [{"code": "200", "rain_am": "-", "rain_pm": "-", "high": "-", "low": "-"}]

    # 2. 警報・注意報の取得
    try:
        with urllib.request.urlopen(warning_url, timeout=10) as res:
            w_data = json.loads(res.read().decode('utf-8'))
            # 簡易解析: headlineTextがあればそれを取得
            if "headlineText" in w_data and w_data["headlineText"]:
                 result["warning"] = w_data["headlineText"]
            else:
                 result["warning"] = "特になし"
    except Exception as e:
        print(f"JMA Warning Error ({area_code}): {e}")
        result["warning"] = "取得失敗"

    return result

def get_weather_emoji_jma(jma_code):
    """気象庁天気コードを絵文字に変換"""
    try:
        code = int(jma_code)
        if code in [100, 101, 123, 124]: return "☀️"
        if code in [102, 103, 104, 105, 106, 107, 108, 110, 111, 112]: return "🌤️"
        if code in [200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212]: return "☁️"
        if 300 <= code < 400: return "☔"
        if 400 <= code < 500: return "⛄"
    except:
        pass
    return "☁️"

# --- モデル選択 (JSONモード強制) ---
def get_model():
    genai.configure(api_key=API_KEY)
    
    # ★重要: response_mime_type を application/json に設定してJSONを強制する
    generation_config = {
        "temperature": 0.7,
        "response_mime_type": "application/json",
    }
    
    target_model = "models/gemini-2.5-flash"
    try:
        return genai.GenerativeModel(target_model, generation_config=generation_config)
    except:
        return genai.GenerativeModel('models/gemini-1.5-flash', generation_config=generation_config)

# --- AI生成 (コンサルタントモード) ---
def get_ai_advice(area_key, area_data, target_date, jma_data):
    if not API_KEY: return None

    date_str = target_date.strftime('%Y年%m月%d日')
    weekday_str = ["月", "火", "水", "木", "金", "土", "日"][target_date.weekday()]
    full_date = f"{date_str} ({weekday_str})"
    
    # 天気情報の整形
    forecast = jma_data["forecasts"][0]
    w_emoji = get_weather_emoji_jma(forecast.get("code", "200"))
    high_temp = forecast.get("high", "-")
    low_temp = forecast.get("low", "-")
    rain_am = forecast.get("rain_am", "-")
    rain_pm = forecast.get("rain_pm", "-")
    warning_text = jma_data.get("warning", "特になし")
    
    rain_display = f"午前{rain_am}% / 午後{rain_pm}%"

    w_info = f"""
    【気象庁発表データ】
    天気: {w_emoji} (コード:{forecast.get('code')})
    気温: 最高{high_temp}℃ / 最低{low_temp}℃
    降水確率: {rain_display}
    警報・注意報: {warning_text}
    """

    print(f"🤖 [AIコンサル] {area_data['name']} / {full_date} 戦略策定中...", flush=True)

    prompt = f"""
    あなたは世界屈指の戦略経営コンサルタントです。
    以下の条件に基づき、対象エリアの各職種に対して、利益最大化とリスク管理のための具体的かつ情熱的な戦略アドバイスを行ってください。

    【条件】
    エリア: {area_data['name']} ({area_data['feature']})
    日時: {full_date}
    気象データ: {w_info}

    【重要指令】
    1. **ランク判定の厳格化:** 平日({weekday_str}曜)は、特段のイベントや悪天候による特需がない限り、原則として「C(閑散)」または「B(普通)」とせよ。「A」や「S」を安易につけるな。
    2. **論理的整合性:** 降水確率が低い場合は「雨」と言及するな。逆に雨予報の場合は、雨を活かす戦略を提案せよ。
    3. **イベント推論:** Google検索は使用できないが、あなたの知識ベースにある「例年のこの時期のイベント」や「曜日特性」を駆使して、イベント情報を推測・補完せよ。
    4. **出力は必ず正しいJSON形式**で行うこと。Markdown記法(```json ... ```)は不要。そのままパースできるJSONのみを出力せよ。

    【出力JSONキー構成】
    {{
        "date": "{full_date}",
        "is_long_term": false,
        "rank": "S/A/B/C",
        "weather_overview": {{ 
            "condition": "{w_emoji}", 
            "high": "{high_temp}℃", "low": "{low_temp}℃", "rain": "{rain_display}",
            "warning": "{warning_text}"
        }},
        "daily_schedule_and_impact": "【導入】...\\n【戦略】...\\n【結論】...", 
        "timeline": {{
            "morning": {{ "weather": "{w_emoji}", "temp": "{low_temp}℃", "rain": "{rain_am}%", "advice": {{ "taxi": "...", "restaurant": "...", "hotel": "...", "shop": "...", "logistics": "...", "conveni": "...", "construction": "...", "delivery": "...", "security": "..." }} }},
            "daytime": {{ "weather": "{w_emoji}", "temp": "{high_temp}℃", "rain": "{rain_pm}%", "advice": {{ "taxi": "...", "restaurant": "...", "hotel": "...", "shop": "...", "logistics": "...", "conveni": "...", "construction": "...", "delivery": "...", "security": "..." }} }},
            "night": {{ "weather": "{w_emoji}", "temp": "{low_temp}℃", "rain": "{rain_pm}%", "advice": {{ "taxi": "...", "restaurant": "...", "hotel": "...", "shop": "...", "logistics": "...", "conveni": "...", "construction": "...", "delivery": "...", "security": "..." }} }}
        }}
    }}
    """
    
    try:
        model = get_model()
        res = model.generate_content(prompt)
        # JSONモードでも稀にMarkdownタグがつくことがあるので除去
        cleaned_text = res.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"⚠️ AI生成エラー: {e}", flush=True)
        return None

# --- 簡易予測 (長期用) ---
def get_simple_forecast(target_date):
    date_str = target_date.strftime('%Y年%m月%d日')
    weekday_str = ["月", "火", "水", "木", "金", "土", "日"][target_date.weekday()]
    full_date = f"{date_str} ({weekday_str})"
    rank = "C"
    if target_date.weekday() == 5: rank = "B"
    elif target_date.weekday() == 4: rank = "B"
    
    return {
        "date": full_date, "is_long_term": True, "rank": rank,
        "weather_overview": { "condition": "☁️", "high": "-", "low": "-", "rain": "-", "warning": "-" },
        "daily_schedule_and_impact": "長期予測期間です。平年並みの天候と人流を想定して準備を進めてください。",
        "timeline": None
    }

# --- メイン ---
if __name__ == "__main__":
    today = datetime.now(JST)
    print(f"🦅 Eagle Eye 30地点・戦略コンサル版 起動: {today.strftime('%Y/%m/%d')}", flush=True)
    
    master_data = {}
    
    for area_key, area_data in TARGET_AREAS.items():
        print(f"\n📍 エリア処理開始: {area_data['name']}", flush=True)
        area_forecasts = []
        
        # 直近の天気データを取得 (JMA)
        jma_data = get_jma_forecast(area_data["jma_code"])
        
        for i in range(90):
            target_date = today + timedelta(days=i)
            
            # 直近2日のみAI & JMAデータ使用
            if i < 2:
                data = get_ai_advice(area_key, area_data, target_date, jma_data)
                if data:
                    area_forecasts.append(data)
                    time.sleep(2) # 負荷軽減のため少し待機
                else:
                    print("⚠️ 生成失敗。簡易版を適用。", flush=True)
                    area_forecasts.append(get_simple_forecast(target_date))
            else:
                area_forecasts.append(get_simple_forecast(target_date))
        
        master_data[area_key] = area_forecasts

    if len(master_data) > 0:
        with open("eagle_eye_data.json", "w", encoding="utf-8") as f:
            json.dump(master_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 全30地点データ保存完了", flush=True)
    else:
        exit(1)
