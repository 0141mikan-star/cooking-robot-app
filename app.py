import streamlit as st
import pandas as pd
import numpy as np

# ページ全体のデザイン設定
st.set_page_config(
    page_title="対話型自炊ロボット「ココ」",
    page_icon="🤖",
    layout="wide"
)

# 🤖 機能1: ロボットの発話（音声合成）用のJavaScript
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

# 🎙️ 機能2: ユーザーの音声入力（音声認識）用のHTML/JavaScriptコンポーネント
def speech_recognition_component():
    html_code = """
    <div style="margin-bottom: 15px;">
        <button id="mic-btn" style="
            background-color: #ff4b4b; 
            color: white; 
            border: none; 
            padding: 12px 24px; 
            border-radius: 24px; 
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.2s;
        ">
            🎙️ 声でココに指示を出す（クリックして話す）
        </button>
        <div id="status" style="font-size: 13px; color: #555; margin-top: 8px; font-weight: bold;"></div>
    </div>

    <script>
        const micBtn = document.getElementById('mic-btn');
        const statusSpan = document.getElementById('status');

        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            statusSpan.innerText = "❌ お使いのブラウザは音声認識に対応していません。Chromeを推奨します。";
            micBtn.disabled = true;
            micBtn.style.backgroundColor = "#ccc";
        } else {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            recognition.lang = 'ja-JP';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            micBtn.addEventListener('click', () => {
                try {
                    recognition.start();
                    statusSpan.innerText = "👂 聞いています...（『スタート』や『次』と話しかけてね）";
                    micBtn.style.backgroundColor = "#d32f2f";
                    micBtn.style.transform = "scale(0.98)";
                } catch (e) {
                    recognition.stop();
                }
            });

            recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                statusSpan.innerText = "🗣️ 認識結果: 「" + text + "」";
                micBtn.style.backgroundColor = "#ff4b4b";
                micBtn.style.transform = "none";

                // 親画面（Streamlit）のチャット入力欄（textarea）を探して値を流し込む
                try {
                    const parentDoc = window.parent.document;
                    const chatInput = parentDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
                    
                    if (chatInput) {
                        chatInput.value = text;
                        chatInput.dispatchEvent(new Event('input', { bubbles: true }));
                        
                        // 送信ボタンを自動でクリック
                        setTimeout(() => {
                            const sendBtn = parentDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');
                            if (sendBtn) { sendBtn.click(); }
                        }, 300);
                    }
                } catch (e) {
                    statusSpan.innerText = "⚠️ テキストの自動送信に失敗しました。手動でEnterを押してください。認識: " + text;
                }
            };

            recognition.onerror = (event) => {
                statusSpan.innerText = "❌ エラー: " + event.error + " (マイクの許可を確認してください)";
                micBtn.style.backgroundColor = "#ff4b4b";
                micBtn.style.transform = "none";
            };

            recognition.onend = () => {
                if(statusSpan.innerText.includes("聞いています")) {
                    statusSpan.innerText = "🛑 終了しました。";
                    micBtn.style.backgroundColor = "#ff4b4b";
                    micBtn.style.transform = "none";
                }
            };
        }
    </script>
    """
    st.components.v1.html(html_code, height=90)

# --- セッション状態（記憶）の初期化 ---
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = [{"role": "assistant", "content": "もっち、こんにちは！手元にある食材を左側に入力して、『計算を実行』を押してね。準備ができたら一緒に料理を始めよう！"}]
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = -1  
if 'calculated' not in st.session_state:
    st.session_state['calculated'] = False
if 'latest_reply' not in st.session_state:
    st.session_state['latest_reply'] = None

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

mode = "support" if motivation <= 2 else "active"

# --- 調理ステップデータ ---
recipe_steps = {
    "肉じゃが (基本2人前)": [
        "ステップ1：鍋に油をひいて、豚肉と玉ねぎを軽く色が変わるまで炒めよう！炒め終わったら『次』って教えてね。",
        "ステップ2：次に人参を加えよう。全体に油が回ったら、画面左に表示されている最適化された【調味料と水】をすべて投入してね！できたら次だよ。",
        "ステップ3：落とし蓋をして弱火で約15分煮込むよ。ココがタイマーを計っておくから、もっちは少し休憩しててね。煮込み終わったら次へ進もう！",
        "ステップ4：じゃがいもが柔らかくなったら火を止めて、味を染み込ませたら完成！お皿に盛り付けてね！"
    ],
    "豚の生姜焼き (基本2人前)": [
        "ステップ1：玉ねぎをくし形に切ろう。目に染みないように気をつけてね！できたら次って言ってね。",
        "ステップ2：フライパンに油を熱して、豚肉と玉ねぎを炒めるよ。お肉に火が通るまでしっかり炒めよう。終わったら次！",
        "ステップ3：ここで画面に表示された黄金比率の『生姜焼きのタレ』をフライパンに回し入れよう！強火で一気に絡めるのがコツだよ。できたら教えて！"
    ],
    "野菜炒め (基本2人前)": [
        "ステップ1：フライパンに油とごま油を熱して、まずは火の通りにくい豚肉から炒めよう！炒まったら次だよ。",
        "ステップ2：次にもやしやキャベツなどの野菜を一気に投入！強火でシャキッと炒めるのがポイントだよ。炒められたら次へ！",
        "ステップ3：最後に画面に表示された調味料を入れて、全体に味を馴染ませたら完成だよ！"
    ]
}

# --- 画面構成（左右２カラム） ---
col_left, col_right = st.columns([1, 1.2])

# 【左カラム】食材入力と調味料の可視化
with col_left:
    st.subheader("📥 1. 食材・レシピの最適化")
    selected_recipe = st.selectbox("料理を選択", list(recipe_steps.keys()))
    
    ingredient_data = pd.DataFrame([
        {"食材名": "豚肉", "量": 120.0, "単位": "g"},
        {"食材名": "玉ねぎ", "量": 0.5, "単位": "個"},
        {"食材名": "人参", "量": 0.3, "単位": "本"}
    ])
    edited_ingredients = st.data_editor(ingredient_data, num_rows="dynamic", use_container_width=True)
    
    if st.button("✨ 食材量・調味料の最適化計算を実行", type="primary", use_container_width=True):
        st.session_state['calculated'] = True
        st.session_state['current_recipe'] = selected_recipe
        st.session_state['current_step'] = -1  
        
        init_msg = f"最適化が完了したよ！{target_servings}人前の【{selected_recipe}】に合わせた調味料比率を計算したよ。右側のマイクボタンかチャットで『スタート』って話しかけてね！"
        st.session_state['chat_history'] = [{"role": "assistant", "content": init_msg}]
        st.session_state['latest_reply'] = init_msg
        st.rerun()

    if st.session_state['calculated']:
        st.markdown("---")
        st.markdown(f"#### 📊 {target_servings}人前の最適化調味料（Quantity Regression）")
        
        ratio = target_servings / 2.0
        adj = 1.2 if target_servings <= 0.5 else 1.0
        
        m1, m2 = st.columns(2)
        m1.metric("メイン調味料（比率）", f"{round(2.0 * ratio * adj, 2)} 大さじ")
        m2.metric("必要水分量", f"{round(200 * ratio * (1.4 if target_servings <= 0.5 else 1.0), 1)} ml")

# 【右カラム】対話型ロボットウインドウ
with col_right:
    st.subheader("💬 2. ココと対話しながら調理")
    
    # 🌟 ユーザー音声入力用コンポーネントを配置
    speech_recognition_component()
    
    # チャットの表示エリア
    chat_placeholder = st.container()
    user_message = None
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    
    if st.session_state['current_step'] == -1:
        if c1.button("▶️ 調理開始（スタート）", use_container_width=True):
            user_message = "スタート"
    elif st.session_state['current_step'] >= 0:
        if c1.button("⏭️ 次のステップへ（できた！）", use_container_width=True):
            user_message = "次"
            
    if c2.button("🗑️ 会話をリセット", use_container_width=True):
        st.session_state['chat_history'] = [{"role": "assistant", "content": "会話をリセットしたよ。準備ができたら声をかけてね！"}]
        st.session_state['current_step'] = -1
        st.session_state['latest_reply'] = None
        st.rerun()

    if chat_input := st.chat_input("ココに『スタート』や『次』などと話しかけてね"):
        user_message = chat_input

    # 状態更新ロジック
    if user_message:
        st.session_state['chat_history'].append({"role": "user", "content": user_message})
        
        if not st.session_state['calculated']:
            reply = "まずは左側のボタンを押して、食材の最適化計算をしてね！"
        else:
            steps = recipe_steps[st.session_state['current_recipe']]
            current = st.session_state['current_step']
            
            # 音声認識の揺らぎに対応（「次」「つぎ」「次に」など）
            if "スタート" in user_message or "開始" in user_message:
                st.session_state['current_step'] = 0
                reply = f"了解！調理を開始するよ。{steps[0]}"
                if mode == "support":
                    reply += " 今日はしんどいモードだから、もっちのペースでゆっくりやっていこう。"
            elif any(k in user_message for k in ["次", "つぎ", "できた", "おk", "進めて"]):
                if current >= 0 and current < len(steps) - 1:
                    st.session_state['current_step'] += 1
                    next_step = st.session_state['current_step']
                    reply = f"おっけー、次へ進むよ！{steps[next_step]}"
                    if next_step == 1:
                        reply += " 【クックパッドアレンジ情報】ここで隠し味にごま油を数滴垂らすのが人気みたいだよ！"
                elif current == len(steps) - 1:
                    reply = "これですべての手順が完了だよ！もっち、最高の料理ができたね！自炊大成功、お疲れ様！🎉"
                    st.session_state['current_step'] = -2  
                else:
                    reply = "調理は完了しているよ！新しく作るときは左側からもう一度計算してね。"
            else:
                reply = "「スタート」や「次」と声をかけてくれたら、調理の案内をすすめるよ！"
                
        st.session_state['chat_history'].append({"role": "assistant", "content": reply})
        st.session_state['latest_reply'] = reply  
        st.rerun()  

    with chat_placeholder:
        for message in st.session_state['chat_history']:
            with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
                st.write(message["content"])

    if st.session_state['latest_reply']:
        robot_speak(st.session_state['latest_reply'])
        st.session_state['latest_reply'] = None
