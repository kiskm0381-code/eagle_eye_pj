import os
import json
import google.generativeai as genai
from datetime import datetime, timedelta, timezone

# --- 設定 ---
API_KEY = os.environ.get("GEMINI_API_KEY")

# 日本時間の現在時刻
JST = timezone(timedelta(hours=9), 'JST')
today = datetime.now(JST)
date_str = today.strftime('%Y年%m月%d日')
weekday_str = ["月", "火", "水", "木", "金", "土", "日"][today.weekday()]
full_date = f"{date_str} ({weekday_str})"

def get_ai_advice():
    if not API_KEY:
        print("エラー: APIキーが環境変数に見つかりません")
        return None

    try:
        genai.configure(api_key=API_KEY)
        
        # --- 🛠 モデル選択ロジック (2026年最新版) ---
        # まずは明示的に最新を指定してみる
        target_model = "models/gemini-2.5-flash"
        
        print(f"🔍 モデル設定: {target_model} を試行します...")
        
        try:
            model = genai.GenerativeModel(target_model)
        except:
            # ダメなら自動検索に切り替え
            print("⚠️ 指定モデルが見つかりません。自動検索します...")
            target_model = 'gemini-1.5-flash' # 仮の初期値
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    if 'gemini' in m.name:
                        target_model = m.name
                        if '2.5' in m.name or '2.0' in m.name: # 新しいバージョン優先
                            break
            print(f"✅ 自動選択されたモデル: {target_model}")
            model = genai.GenerativeModel(target_model)
        
        # ---------------------------------------------
        
        # プロンプト（命令書）
        prompt = f"""
        あなたは函館の観光コンサルタントAIです。
        今日（{full_date}）の函館の観光需要予測データを作成してください。
        
        以下の条件でJSONデータを作成してください。
        1. ランクは「S, A, B, C」のいずれか。
        2. 天気は今の時期の函館らしいもの。
        3. アドバイスは以下の職業別に具体的に（40文字以内）。
           - taxi (タクシー)
           - restaurant (飲食店)
           - hotel (ホテル)
           - shop (お土産)
           - logistics (物流)
           - conveni (コンビニ)
        4. タイムラインは朝・昼・夕・夜の4つ。交通規制などの警告があれば含める。

        出力はJSON形式のみ。Markdown記号は不要。
        """
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)

    except Exception as e:
        print(f"❌ エラー発生詳細: {e}")
        return None

# --- メイン処理 ---
if __name__ == "__main__":
    print(f"🦅 Eagle Eye 起動: {full_date}")
    
    data = get_ai_advice()
    
    if data:
        data["date"] = full_date
        with open("eagle_eye_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ データ保存完了: eagle_eye_data.json")
    else:
        print("❌ データ生成失敗")
        exit(1)
