import streamlit as st
import pandas as pd
import numpy as np

# ページ設定
st.set_page_config(page_title="自炊サポートロボット ココ - プロトタイプ", layout="wide", initial_sidebar_state="expanded")

# --- タイトル・ヘッダー ---
st.title("🤖 食材量最適化・自炊サポートロボット「ココ」")
st.caption("Version 1.0 (Prototype) - Streamlit × AI 推論シミュレーション")

# --- 音声合成用JavaScriptコンポーネント (Web Speech API) ---
def speak_text(text):
    """ブラウザの音声合成機能を使ってロボットに喋らせるJS"""
    if text:
        js_code = f"""
        <script>
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                var msg = new SpeechSynthesisUtterance({repr(text)});
                msg.lang = 'ja-JP';
                msg.rate = 1.1;
                window.speechSynthesis.speak(msg);
            }}
        </script>
        """
        st.components.v1.html(js_code, height=0, width=0)

# --- サイドバー：ユーザー状態識別機能 ---
st.sidebar.header("👤 ユーザー状態の識別 (User State)")
user_level = st.sidebar.selectbox("料理レベル", ["料理初心者", "経験者"])
motivation = st.sidebar.slider("現在の料理モチベーション", 1, 5, 3, help="1: 義務感・疲弊 / 5: 高い意欲")
servings = st.sidebar.number_input("作りたい人数 (人前)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)

# 状態の簡易判定
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 ロボットの推論ステータス")
if motivation <= 2:
    st.sidebar.warning("⚠️ モチベーション低下状態：心理的サポートを優先します。")
    robot_tone = "support"
else:
    st.sidebar.success("🟢 良好状態：提案型コミュニケーションを行います。")
    robot_tone = "suggest"

# --- メインエリア：ステップ別ワークフロー ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("🗂 1. 手持ち食材・レシピの入力")
    
    # レシピ選択
    target_recipe = st.selectbox(
        "作りたい料理を選択してください", 
        ["肉じゃが (基本2人前)", "豚の生姜焼き (基本2人前)", "野菜炒め (基本2人前)"]
    )
    
    st.markdown("**冷蔵庫の余り食材を入力してください**")
    # 初期データ
    default_ingredients = pd.DataFrame([
        {"食材名": "豚肉", "量": 100.0, "単位": "g"},
        {"食材名": "玉ねぎ", "量": 0.5, "単位": "個"},
        {"食材名": "人参", "量": 0.3, "単位": "本"}
    ])
    # ユーザーが編集可能なデータエディタ
    edited_df = st.data_editor(default_ingredients, num_rows="dynamic", use_container_width=True)

    # 最適化ボタン
    calc_trigger = st.button("✨ 食材量・調味料の最適化計算を実行", type="primary")

with col2:
    st.header("📊 2. 最適化計算結果 ＆ 可視化")
    
    # ベースとなる2人前のレシピデータ
    base_recipes = {
        "肉じゃが (基本2人前)": {"醤油": 2.0, "みりん": 2.0, "酒": 2.0, "砂糖": 1.0, "水": 200.0},
        "豚の生姜焼き (基本2人前)": {"醤油": 2.0, "みりん": 1.0, "酒": 1.0, "生姜チューブ": 1.0, "水": 0.0},
        "野菜炒め (基本2人前)": {"醤油": 1.0, "酒": 1.0, "鶏ガラスープの素": 1.0, "ごま油": 1.0, "水": 0.0}
    }
    
    if calc_trigger:
        # スケーリング因子の計算 (基準2人前から指定人前へ)
        scale_factor = servings / 2.0
        
        # 数量回帰(Quantity Regression)のシミュレーション
        # 単純な割り算ではなく、少量調理時は水分の蒸発率を考慮して水分や液体系調味料を微増させる補正を行う
        adjustment_factor = 1.0
        if servings <= 0.5:
            adjustment_factor = 1.25  # 味が濃くなりすぎるのを防ぐための水分補正・比率調整
        elif servings >= 3.0:
            adjustment_factor = 0.9
            
        base_condiments = base_recipes[target_recipe]
        optimized_condiments = {}
        
        for k, v in base_condiments.items():
            if k == "水":
                # 水分は蒸発率を考慮して高めに補正
                optimized_condiments[k] = round(v * scale_factor * (1.5 if servings <= 0.5 else 1.0), 1)
            else:
                optimized_condiments[k] = round(v * scale_factor * adjustment_factor, 2)
        
        st.success(f"🎯 {servings}人前に最適化された調味料（黄金比率）を算出しました。")
        
        # グラフ用データフレーム作成
        chart_data = pd.DataFrame({
            "調味料": list(optimized_condiments.keys()),
            "最適化後の分量 (比率換算)": list(optimized_condiments.values())
        }).set_index("調味料")
        
        # 視覚的可視化（バーチャート）
        st.bar_chart(chart_data)
        
        # 具体的な分量表示
        st.markdown("**【詳細な調味料ガイド】**")
        for k, v in optimized_condiments.items():
            unit = "ml" if k in ["水", "醤油", "みりん", "酒"] else "大さじ/小さじ換算比"
            st.write(f"・{k}: **{v}** {unit}")
            
        # セッション状態に保存してロボット発話へ繋げる
        st.session_state['optimized'] = True
        st.session_state['recipe'] = target_recipe
    else:
        st.info("左側のボタンを押すと、AIモデルが文脈と人数を推論して最適な調味料比率を算出・可視化します。")

st.markdown("---")

# --- 3. ロボット「ココ」との対話(HRI)ウインドウ ---
st.header("💬 3. ロボット「ココ」の調理サポート（音声発話連動）")

if 'optimized' in st.session_state and st.session_state['optimized']:
    recipe_name = st.session_state['recipe']
    
    # ロボットの発話シナリオ分岐（行動変容アプローチ）
    robot_message = ""
    
    if robot_tone == "support":
        robot_message = f"もっち、今日もお疲れ様！{servings}人前だね。疲れているときは簡単な手順に変えるから安心してね。"
        if "肉じゃが" in recipe_name:
            robot_message += " クックパッドのデータによると、電子レンジを併用すると10分短縮できて楽ちんだよ！無理せず作ろうね。"
    else:
        robot_message = f"もっち、{recipe_name}の食材調整ができたよ！"
        if "肉じゃが" in recipe_name:
            robot_message += " 今回の人数分だと水分が飛びやすいから、お醤油を少し手前で抑えるのがAIのコツだよ。他の人はここで『隠し味に白だし』を足してアレンジしてるみたい！"
        elif "生姜焼き" in recipe_name:
            robot_message += " 1人前ならお肉をタレに漬け込まず、最後に絡めるだけで十分美味しくなるよ！"
        else:
            robot_message += " 火力が強くなりすぎないように気をつけてね。応援してるよ！"

    # HRI チャット画面の再現
    with st.chat_message("assistant", avatar="🤖"):
        st.write(f"**ココ:** {robot_message}")
        
    # 音声合成の実行
    speak_text(robot_message)
    
    # 調理達成フィードバックのシミュレーション
    st.markdown(" 💡 **調理が完了したら教えてね**")
    if st.button("🍳 料理が完成した！"):
        success_message = "素晴らしい！もっち、自炊達成おめでとう！冷蔵庫の余り食材をバッチリ消費できたから、食品ロス削減にも貢献したよ。健康的な一歩だね！"
        with st.chat_message("assistant", avatar="🤖"):
            st.write(f"**ココ:** {success_message}")
        speak_text(success_message)
        st.balloons()
else:
    with st.chat_message("assistant", avatar="🤖"):
        st.write("もっち、こんにちは！手元にある食材を上のエディタに入力して、最適化ボタンを押してみてね。一緒に料理を考えよう！")
