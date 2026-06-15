import streamlit as st
import pandas as pd
import numpy as np

# ページ全体のデザイン設定
st.set_page_config(
    page_title="対話型自炊ロボット「ココ」",
    page_icon="🤖",
    layout="wide"
)

# 音声合成関数 (JavaScript)
def robot_speak(text):
    if text:
        js_code = f"""
        <script>
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                var msg = new SpeechSynthesisUtterance({repr(text)});
                msg.lang = 'ja-JP';
                msg.rate = 1.0;
                window.speechSynthesis.speak(msg);
            }}
        </script>
        """
        st.components.v1.html(js_code, height=0, width=0)

# --- セッション状態（記憶）の初期化 ---
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = [{"role": "assistant", "content": "もっち、こんにちは！手元にある食材を左側に入力して、『計算を実行』を押してね。準備ができたら一緒に料理を始めよう！"}]
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = -1  # -1は開始前
if 'calculated' not in st.session_state:
    st.session_state['calculated'] = False

# --- ヘッダー領域 ---
st.title("🤖 対話型自炊サポートロボット『ココ』")
st.caption("⚡ Kumamoto University - Information Fusion / Interactive HRI Prototype")
st.markdown("---")

# --- サイドバー：ユーザー状態の識別 ---
st.sidebar.header("👤 ユーザー状態の識別 (AI推論)")
user_name = st.sidebar.text_input("ユーザー名", value="もっち")
user_level = st.sidebar.radio("料理レベル", ["料理初心者", "経験者"], index=0)
motivation = st.sidebar.slider("料理モチベーション", 1, 5, 3)
target_servings = st.sidebar.number_input("作りたい人数 (人前)", min_value=0.1, max_value=4.0, value=1.0, step=0.1)

# モード判定
mode = "support" if motivation <= 2 else "active"

# --- レシピごとの調理ステップデータ（ビッグデータ連携の模倣） ---
recipe_steps = {
    "肉じゃが (基本2人前)": [
        "ステップ1：鍋に油をひいて、豚肉と玉ねぎを軽く色が変わるまで炒めよう！炒め終わったら『次』って教えてね。",
        "ステップ2：次に人参を加えよう。全体に油が回ったら、画面に表示されている最適化された【調味料と水】をすべて投入してね！できたら『次』だよ。",
        "ステップ3：落とし蓋をして弱火で約15分煮込むよ。ココがタイマーを計っておくから、もっちは少し休憩しててね。煮込み終わったら『次』へ進もう！",
        "ステップ4：じゃがいもが柔らかくなったら火を止めて、味を染み込ませたら完成！お皿に盛り付けてね！"
    ],
    "豚の生姜焼き (基本2人前)": [
        "ステップ1：玉ねぎをくし形に切ろう。初心者モードだから言うけど、目に染みないように気をつけてね！できたら『次』って言ってね。",
        "ステップ2：フライパンに油を熱して、豚肉と玉ねぎを炒めるよ。お肉に火が通るまでしっかり炒めよう。終わったら『次』！",
        "ステップ3：ここで画面に表示された黄金比率の『生姜焼きのタレ』をフライパンに回し入れよう！強火で一気に絡めるのがコツだよ。できたら教えて！"
    ],
    "野菜炒め (基本2人前)": [
        "ステップ1：フライパンに油とごま油を熱して、まずは火の通りにくい豚肉から炒めよう！炒まったら『次』だよ。",
        "ステップ2：次にもやしやキャベツなどの野菜を一気に投入！強火でシャキッと炒めるのがポイントだよ。炒められたら『次』へ！",
        "ステップ3：最後に画面に表示された調味料（鶏ガラスープの素など）を入れて、全体に味を馴染ませたら完成だよ！"
    ]
}

# --- 画面構成（左右２カラム） ---
col_left, col_right = st.columns([1, 1.2])

# 【左カラム】食材入力と調味料の可視化
with col_left:
    st.subheader("📥 1. 食材・レシピの最適化")
    selected_recipe = st.selectbox("料理を選択", list(recipe_steps.keys()))
    
    # データエディタ
    ingredient_data = pd.DataFrame([
        {"食材名": "豚肉", "量": 120.0, "単位": "g"},
        {"食材名": "玉ねぎ", "量": 0.5, "単位": "個"},
        {"食材名": "人参", "量": 0.3, "単位": "本"}
    ])
    edited_ingredients = st.data_editor(ingredient_data, num_rows="dynamic", use_container_width=True)
    
    if st.button("✨ 食材量・調味料の最適化計算を実行", type="primary", use_container_width=True):
        st.session_state['calculated'] = True
        st.session_state['current_recipe'] = selected_recipe
        st.session_state['current_step'] = -1  # 計算し直したらステップをリセット
        
        # 最初の挨拶を上書き
        init_msg = f"最適化が完了したよ！{target_servings}人前の【{selected_recipe}】に合わせた調味料比率を計算したよ。下のチャットで『スタート』って入力するか、『調理開始』ボタンを押してね！"
        st.session_state['chat_history'] = [{"role": "assistant", "content": init_msg}]
        robot_speak(init_msg)

    # 計算結果の可視化表示
    if st.session_state['calculated']:
        st.markdown("---")
        st.markdown(f"#### 📊 {target_servings}人前の最適化調味料（Quantity Regression）")
        
        ratio = target_servings / 2.0
        adj = 1.2 if target_servings <= 0.5 else 1.0
        
        m1, m2 = st.columns(2)
        m1.metric("メイン調味料（比率）", f"{round(2.0 * ratio * adj, 2)} 大さじ")
        m2.metric("必要水分量", f"{round(200 * ratio * (1.4 if target_servings <= 0.5 else 1.0), 1)} ml")
        
        # 技術ログ
        with st.expander("🛠️ バックエンドAIログ"):
            st.json({
                "状態識別": mode,
                "適用アルゴリズム": "Quantity Regression (蒸発率補正型)",
                "他ユーザーのアレンジ参照": "クックパッド上位20%のアレンジを抽出済"
            })

# 【右カラム】対話型ロボットウインドウ（ここがメインの対話エンジン）
with col_right:
    st.subheader("💬 2. ココと対話しながら調理")
    
    # チャット履歴の表示
    for message in st.session_state['chat_history']:
        with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
            st.write(message["content"])
            
    # 調理をナビゲートするコントロールボタン（チャット入力の代わりにもなる）
    st.markdown("---")
    c1, c2 = st.columns(2)
    
    # ユーザー入力を処理する共通関数
    def advance_cooking(user_text):
        # ユーザーの発言を履歴に追加
        st.session_state['chat_history'].append({"role": "user", "content": user_text})
        
        if not st.session_state['calculated']:
            reply = "まずは左側のボタンを押して、食材の最適化計算をしてね！"
            st.session_state['chat_history'].append({"role": "assistant", "content": reply})
            robot_speak(reply)
            return

        steps = recipe_steps[st.session_state['current_recipe']]
        current = st.session_state['current_step']
        
        # 進行ロジック
        if "スタート" in user_text or "開始" in user_text:
            st.session_state['current_step'] = 0
            reply = f"了解！調理を開始するよ。{steps[0]}"
            if mode == "support":
                reply += " 今日はしんどいモードだから、ゆっくりマイペースで炒めていこうね。"
        elif current >= 0 and current < len(steps) - 1:
            st.session_state['current_step'] += 1
            next_step = st.session_state['current_step']
            reply = f"おっけー、次へ進むよ！{steps[next_step]}"
            
            # クックパッドの人気アレンジなどを途中で挟む（行動変容アプローチ）
            if next_step == 1:
                reply += " 【クックパッド豆知識】ここで隠し味にごま油を数滴垂らすアレンジが、一人暮らしの学生に大人気みたいだよ！"
        elif current == len(steps) - 1:
            reply = "これですべての手順が完了だよ！もっち、最高の料理ができたね！自炊大成功、お疲れ様！🎉"
            st.session_state['current_step'] = -2  # 完了状態
        else:
            reply = "調理は完了しているよ！新しく作るときは左側からもう一度計算してね。"

        st.session_state['chat_history'].append({"role": "assistant", "content": reply})
        robot_speak(reply)

    # クイック操作ボタン
    if st.session_state['current_step'] == -1:
        if c1.button("▶️ 調理開始（スタート）", use_container_width=True):
            advance_cooking("調理を開始するよ")
            st.rerun()
    elif st.session_state['current_step'] >= 0:
        if c1.button("⏭️ 次のステップへ（できた！）", use_container_width=True):
            advance_cooking("次へ進んで")
            st.rerun()
            
    if c2.button("🗑️ 会話をリセット", use_container_width=True):
        st.session_state['chat_history'] = [{"role": "assistant", "content": "会話をリセットしたよ。準備ができたら声をかけてね！"}]
        st.session_state['current_step'] = -1
        st.rerun()

    # チャット入力欄（キーボードや音声入力の代わり）
    if user_input := st.chat_input("ココに『スタート』や『次』などと話しかけてね"):
        advance_cooking(user_input)
        st.rerun()
