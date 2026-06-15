import streamlit as st
import pandas as pd
import numpy as np

# ページ全体のデザイン設定
st.set_page_config(
    page_title="完全ハンズフリー自炊ロボット「ココ」",
    page_icon="🤖",
    layout="wide"
)

# 🤖 ロボットの発話（音声合成）用のJavaScript
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

# 🎙️ ハンズフリー音声認識用コンポーネント
def hands_free_speech_component():
    html_code = """
    <div style="margin-bottom: 15px; padding: 15px; border-radius: 12px; background-color: #f0f8f5; border: 2px solid #2e7d32;">
        <button id="mic-btn" style="
            background-color: #2e7d32; 
            color: white; 
            border: none; 
            padding: 14px 28px; 
            border-radius: 24px; 
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            width: 100%;
            justify-content: center;
        ">
            🟢 ハンズフリーモードを起動（料理前に1回クリック）
        </button>
        <div id="status" style="font-size: 14px; color: #1b5e20; margin-top: 10px; font-weight: bold; text-align: center;">
            状態: 停止中
        </div>
    </div>

    <script>
        const micBtn = document.getElementById('mic-btn');
        const statusSpan = document.getElementById('status');
        let isListening = false;

        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            statusSpan.innerText = "❌ ブラウザが音声認識に対応していません。Google Chromeを使用してください。";
            micBtn.disabled = true;
            micBtn.style.backgroundColor = "#ccc";
        } else {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            
            recognition.continuous = true; 
            recognition.interimResults = false;
            recognition.lang = 'ja-JP';

            micBtn.addEventListener('click', () => {
                if (!isListening) {
                    recognition.start();
                } else {
                    recognition.stop();
                }
            });

            recognition.onstart = () => {
                isListening = true;
                statusSpan.innerHTML = "👂 <b>ココがあなたの声を聞いています...（手は使わなくてOK！）</b><br><span style='font-size:12px; font-weight:normal;'>『スタート』『次』『もう一回』『リセット』に反応します</span>";
                micBtn.innerText = "🛑 ハンズフリーモードを終了する";
                micBtn.style.backgroundColor = "#d32f2f";
            };

            recognition.onresult = (event) => {
                const resultIndex = event.resultIndex;
                const text = event.results[resultIndex][0].transcript.trim();
                statusSpan.innerHTML = "🗣 shrink_text: 「<b>" + text + "</b>」";

                if (text.includes("スタート") || text.includes("開始") || text.includes("次") || 
                    text.includes("できた") || text.includes("おk") || text.includes("リセット") || 
                    text.includes("もう一回") || text.includes("もう一度") || text.includes("なんて")) {
                    try {
                        const parentDoc = window.parent.document;
                        const chatInput = parentDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
                        
                        if (chatInput) {
                            const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                            nativeTextAreaValueSetter.call(chatInput, text);
                            chatInput.dispatchEvent(new Event('input', { bubbles: true }));
                            
                            setTimeout(() => {
                                const sendBtn = parentDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');
                                if (sendBtn) { 
                                    sendBtn.removeAttribute('disabled');
                                    sendBtn.click(); 
                                }
                            }, 100);
                        }
                    } catch (e) {
                        console.error("Streamlitへのデータ送信に失敗:", e);
                    }
                }
            };

            recognition.onerror = (event) => {
                if (event.error !== 'no-speech') {
                    statusSpan.innerText = "⚠️ エラー: " + event.error;
                }
            };

            recognition.onend = () => {
                isListening = false;
                if (micBtn.style.backgroundColor !== "rgb(46, 125, 50)") { 
                    recognition.start();
                } else {
                    statusSpan.innerText = "状態: 停止中";
                    micBtn.innerText = "🟢 ハンズフリーモードを起動";
                    micBtn.style.backgroundColor = "#2e7d32";
                }
            };
        }
    </script>
    """
    st.components.v1.html(html_code, height=120)

# --- 🌟 セッション状態（記憶）の初期化 🌟 ---
if 'ingredients' not in st.session_state:
    # 初期値（最初は自由に変えられるベースを配置。リセットされなくなります）
    st.session_state['ingredients'] = pd.DataFrame([
        {"食材名": "豚肉", "量": 120.0, "単位": "g"},
        {"食材名": "玉ねぎ", "量": 0.5, "単位": "個"},
        {"食材名": "人参", "量": 0.3, "単位": "本"}
    ])
if 'suggested_options' not in st.session_state:
    st.session_state['suggested_options'] = ["肉じゃが (基本2人前)", "豚の生姜焼き (基本2人前)", "野菜炒め (基本2人前)"]
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = [{"role": "assistant", "content": "もっち、こんにちは！左側の食材リストを今の冷蔵庫の中身に書き換えて、下の『料理を提案してもらう』ボタンを押してね！"}]
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = -1  
if 'calculated' not in st.session_state:
    st.session_state['calculated'] = False
if 'latest_reply' not in st.session_state:
    st.session_state['latest_reply'] = None

# --- ヘッダー領域 ---
st.title("🤖 完全ハンズフリー自炊ロボット『ココ』")
st.caption("⚡ Kumamoto University - Information Fusion / Interactive UX Fix")
st.markdown("---")

# --- サイドバー：ユーザー状態の識別 ---
st.sidebar.header("👤 ユーザー状態の識別")
user_name = st.sidebar.text_input("ユーザー名", value="もっち")
motivation = st.sidebar.slider("料理モチベーション", 1, 5, 3)
target_servings = st.sidebar.number_input("作りたい人数 (人前)", min_value=0.1, max_value=4.0, value=1.0, step=0.1)

mode = "support" if motivation <= 2 else "active"

# --- レシピデータマスタ ---
recipes_master = {
    "肉じゃが (基本2人前)": {
        "match_ingredients": ["豚肉", "牛肉", "玉ねぎ", "人参", "じゃがいも"],
        "steps": [
            "ステップ1：鍋に油をひいて、豚肉と玉ねぎを軽く炒めよう！炒め終わったら『次』って教えてね。",
            "ステップ2：次に人参を加えよう。全体に油が回ったら、画面左の【調味料と水】をすべて投入してね！できたら次だよ。",
            "ステップ3：落とし蓋をして弱火で約15分煮込むよ。煮込み終わったら次へ進もう！",
            "ステップ4：じゃがいもが柔らかくなったら火を止めて完成！お皿に盛り付けてね！"
        ]
    },
    "豚の生姜焼き (基本2人前)": {
        "match_ingredients": ["豚肉", "生姜", "玉ねぎ"],
        "steps": [
            "ステップ1：玉ねぎをくし形に切ろう。目に染まないように気をつけてね！できたら次って言ってね。",
            "ステップ2：フライパンに油を熱して、豚肉と玉ねぎを炒めるよ。終わったら次！",
            "ステップ3：ここで画面の『生姜焼きのタレ』をフライパンに回し入れよう！強火で一気に絡めたら完成だよ。"
        ]
    },
    "野菜炒め (基本2人前)": {
        "match_ingredients": ["キャベツ", "もやし", "豚肉", "人参", "ピーマン"],
        "steps": [
            "ステップ1：フライパンに油とごま油を熱して、まずは火の通りにくい豚肉から炒めよう！炒まったら次だよ。",
            "ステップ2：次にもやしやキャベツなどの野菜を一気に投入！強火でシャキッと炒めるのがポイントだよ。炒められたら次へ！",
            "ステップ3：最後に画面に表示された調味料を入れて、全体に味を馴染ませたら完成だよ！"
        ]
    }
}

# --- 画面構成（左右２カラム） ---
col_left, col_right = st.columns([1, 1.2])

# 【左カラム】食材入力と明確な提案手順
with col_left:
    st.subheader("📥 1. 冷蔵庫の食材入力 ＆ AI提案手順")
    
    st.markdown("**【手順A】手持ちの食材を入力・編集する**（行の追加や削除、数量変更が可能）")
    
    # 🌟 記憶されたセッション状態からデータエディタを表示し、編集内容を即座に上書き保存
    edited_ingredients = st.data_editor(st.session_state['ingredients'], num_rows="dynamic", use_container_width=True)
    st.session_state['ingredients'] = edited_ingredients
    
    # 🌟 【重要】手順を明確にするための「提案実行ボタン」
    if st.button("🔍 【手順B】この食材を適用して料理を提案してもらう", type="secondary", use_container_width=True):
        user_ingredients = edited_ingredients["食材名"].dropna().tolist()
        
        # マッチングロジックの実行
        matched_recipes = []
        for r_name, r_info in recipes_master.items():
            match_count = sum(1 for i in user_ingredients if i in r_info["match_ingredients"])
            if match_count > 0:
                matched_recipes.append((r_name, match_count))
        
        if matched_recipes:
            matched_recipes.sort(key=lambda x: x[1], reverse=True)
            st.session_state['suggested_options'] = [r[0] for r in matched_recipes]
            proposal_msg = f"もっち、食材の入力を確認したよ！今ある材料なら【{', '.join(st.session_state['suggested_options'])}】がおススメ！下のセレクトボックスから作りたい料理を選んでね。"
        else:
            st.session_state['suggested_options'] = list(recipes_master.keys())
            proposal_msg = "一致する特定の料理が見つからなかったから、全レシピから選べるようにしておいたよ！どれにする？"
            
        # ロボットに対話形式で提案させる
        st.session_state['chat_history'].append({"role": "assistant", "content": proposal_msg})
        st.session_state['latest_reply'] = proposal_msg
        st.rerun()

    st.markdown("---")
    st.markdown("**【手順C】提案された料理から選択して、最適化を実行する**")
    selected_recipe = st.selectbox("ココのおススメ料理一覧", st.session_state['suggested_options'])
    
    if st.button("✨ 【手順D】この料理の調味料比率を計算する", type="primary", use_container_width=True):
        st.session_state['calculated'] = True
        st.session_state['current_recipe'] = selected_recipe
        st.session_state['current_step'] = -1  
        
        init_msg = f"【{selected_recipe}】に合わせた調味料比率の計算ができたよ！右側のハンズフリーを起動して『スタート』って話しかけてね！"
        st.session_state['chat_history'].append({"role": "assistant", "content": init_msg})
        st.session_state['latest_reply'] = init_msg
        st.rerun()

    if st.session_state['calculated']:
        st.markdown("---")
        st.markdown(f"#### 📊 {target_servings}人前の最適化調味料")
        ratio = target_servings / 2.0
        st.metric("メイン調味料（比率）", f"{round(2.0 * ratio, 2)} 大さじ")
        st.metric("必要水分量", f"{round(200 * ratio, 1)} ml")

# 【右カラム】対話型ロボットウインドウ
with col_right:
    st.subheader("💬 2. 声だけで進める調理ナビ")
    
    hands_free_speech_component()
    
    chat_placeholder = st.container()
    user_message = None

    if chat_input := st.chat_input("ココに話しかけるか、文字を入力してね"):
        user_message = chat_input

    # 状態更新・対話ロジック
    if user_message:
        st.session_state['chat_history'].append({"role": "user", "content": user_message})
        
        if not st.session_state['calculated']:
            reply = "まずは左側の手順に沿って、食材の提案と最適化計算をしてね！"
        else:
            steps = recipes_master[st.session_state['current_recipe']]["steps"]
            current = st.session_state['current_step']
            
            if any(k in user_message for k in ["もう一回", "もう一度", "聞き取れ", "え？", "なんて", "リピート"]):
                if current >= 0:
                    reply = f"あ、ごめんごめん！もう一回言うね。{steps[current]}"
                else:
                    reply = "まだ調理は始まっていないよ。準備ができたら『スタート』って言ってね！"
            elif "スタート" in user_message or "開始" in user_message:
                st.session_state['current_step'] = 0
                reply = f"了解！調理を開始するよ。{steps[0]}"
            elif any(k in user_message for k in ["次", "つぎ", "できた", "おk", "すすめて"]):
                if current >= 0 and current < len(steps) - 1:
                    st.session_state['current_step'] += 1
                    next_step = st.session_state['current_step']
                    reply = f"はーい、次だね。{steps[next_step]}"
                elif current == len(steps) - 1:
                    reply = "これですべての手順が完了だよ！もっち、最高の料理ができたね！自炊大成功、お疲れ様！🎉"
                    st.session_state['current_step'] = -2  
                else:
                    reply = "調理は完了しているよ！新しく作るときはもう一度左側から計算してね。"
            elif "リセット" in user_message or "最初から" in user_message:
                st.session_state['current_step'] = -1
                reply = "調理手順を最初からリセットしたよ。準備ができたら『スタート』って言ってね。"
            else:
                reply = "「スタート」や「次」、「もう一回」などと声をかけてくれたらサポートするよ！"
                
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
