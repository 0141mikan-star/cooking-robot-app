import streamlit as st

# ページ全体のデザイン設定
st.set_page_config(
    page_title="次世代対話型自炊サポートロボット「ココ」",
    page_icon="🍳",
    layout="wide"
)

# 🍳 ロボットの発話（音声合成）用のJavaScript
def robot_speak(text):
    if text:
        safe_text = text.replace('\n', ' ').replace('\r', '').replace("'", "\\'")
        js_code = f"""
        <script>
            var target = window.parent || window;
            if ('speechSynthesis' in target) {{
                target.speechSynthesis.cancel();
                var msg = new target.SpeechSynthesisUtterance('{safe_text}');
                msg.lang = 'ja-JP';
                msg.rate = 1.0;
                
                target.isRobotSpeaking = true;
                msg.onend = function() {{ target.isRobotSpeaking = false; }};
                msg.onerror = function() {{ target.isRobotSpeaking = false; }};
                
                target.speechSynthesis.speak(msg);
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
        let isSubmitting = false; 
        let isManualStop = false; 

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
                    isManualStop = false; 
                    try { recognition.start(); } catch(e) {}
                } else {
                    isManualStop = true; 
                    recognition.stop();
                    statusSpan.innerText = "状態: 停止中";
                    micBtn.innerText = "🟢 ハンズフリーモードを起動";
                    micBtn.style.backgroundColor = "#2e7d32";
                }
            });

            recognition.onstart = () => {
                isListening = true;
                statusSpan.innerHTML = "👂 <b>ココが耳を傾けています（自由な言葉で話しかけてね！）</b>";
                micBtn.innerText = "🛑 ハンズフリーモードを終了する";
                micBtn.style.backgroundColor = "#d32f2f";
            };

            recognition.onresult = (event) => {
                if (isSubmitting) return; 

                const targetWindow = window.parent || window;
                if (targetWindow.isRobotSpeaking) {
                    return;
                }

                const resultIndex = event.resultIndex;
                const text = event.results[resultIndex][0].transcript.trim();
                if (!text) return;

                statusSpan.innerHTML = "🗣 聞き取った言葉: 「<b>" + text + "</b>」";
                isSubmitting = true; 

                try {
                    const targetDoc = targetWindow.document;
                    const chatInput = targetDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
                    
                    if (chatInput) {
                        const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                        nativeTextAreaValueSetter.call(chatInput, text);
                        chatInput.dispatchEvent(new Event('input', { bubbles: true }));
                        
                        setTimeout(() => {
                            const sendBtn = targetDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');
                            if (sendBtn) { 
                                sendBtn.removeAttribute('disabled');
                                sendBtn.click(); 
                            }
                            setTimeout(() => { isSubmitting = false; }, 2000);
                        }, 150);
                    } else {
                        isSubmitting = false;
                    }
                } catch (e) {
                    isSubmitting = false;
                }
            };

            recognition.onerror = (event) => {
                if (event.error !== 'no-speech') {
                    statusSpan.innerText = "⚠️ エラー: " + event.error;
                }
            };

            recognition.onend = () => {
                isListening = false;
                if (!isManualStop) {
                    setTimeout(() => { try { recognition.start(); } catch(e){} }, 500);
                } else {
                    statusSpan.innerText = "状態: 停止中";
                    micBtn.innerText = "🟢 ハンズフリーモードを起動";
                    micBtn.style.backgroundColor = "#2e7d32";
                }
            };
        }
    </script>
    """
    st.components.v1.html(html_code, height=140)

# --- 🧠 自然言語処理：意図解釈（インテント識別）エンジン ---
def parse_user_intent(user_message):
    msg = user_message.lower()
    
    next_keywords = ["次", "つぎ", "なんする", "何する", "できた", "終わった", "おわった", "おk", "オッケー", "おっけー", "進めて", "進む", "完了", "next", "いいよ", "おーけー"]
    if any(k in msg for k in next_keywords):
        return "NEXT_STEP"
        
    repeat_keywords = ["もう一回", "もう一度", "聞き取れ", "え？", "なんて", "リピート", "聞こえなかった", "もう一度言って", "は？"]
    if any(k in msg for k in repeat_keywords):
        return "REPEAT_STEP"
        
    if any(k in msg for k in ["スタート", "開始", "はじめ", "やろう", "作ろう"]):
        return "START_COOKING"
    if any(k in msg for k in ["リセット", "最初から", "やり直し"]):
        return "RESET_COOKING"
        
    return "CHAT_OR_QUESTION"

# --- 📚 レシピデータセット（外部データ組み込みに向けたプロトタイプ） ---
MOCK_RECIPE_DB = [
    {
        "name": "豚肉と玉ねぎの生姜焼き",
        "ingredients": ["豚肉", "玉ねぎ"],
        "condiments": {"醤油": "2.0", "みりん": "1.0", "酒": "1.0", "生姜チューブ": "0.5"},
        "steps": [
            "ステップ1：玉ねぎを薄切りにするよ。終わったら教えてね。",
            "ステップ2：フライパンに油をひいて、豚肉と玉ねぎを中火で炒めよう。火が通ったら次へ！",
            "ステップ3：左の調味料を全部入れて、タレが絡んだら完成だよ！"
        ]
    },
    {
        "name": "豚肉と人参のオイスター炒め",
        "ingredients": ["豚肉", "人参"],
        "condiments": {"オイスターソース": "1.0", "醤油": "1.0", "酒": "1.0"},
        "steps": [
            "ステップ1：人参を細切りにするよ。できたら教えて！",
            "ステップ2：フライパンで豚肉と人参を炒めよう。豚肉の色が変わったら次へ！",
            "ステップ3：調味料を入れてサッと炒め合わせたら完成！"
        ]
    },
    {
        "name": "玉ねぎと人参のコンソメスープ",
        "ingredients": ["玉ねぎ", "人参"],
        "condiments": {"水": "300", "コンソメ": "1.0", "塩こしょう": "0.1"},
        "steps": [
            "ステップ1：玉ねぎと人参を角切りにしよう。できたら教えてね。",
            "ステップ2：鍋に水を入れて沸騰させ、切った野菜を入れて中火で煮込むよ。柔らかくなったら次へ！",
            "ステップ3：コンソメと塩こしょうで味を整えたら完成だよ！"
        ]
    }
]

# --- 🍳 ドメイン知識：データセットからレシピを検索 ---
def generate_intelligent_recipes(ingredients_list):
    if not ingredients_list:
        return {}
        
    recipes = {}
    
    for recipe in MOCK_RECIPE_DB:
        match_count = sum(1 for ing in recipe["ingredients"] if ing in ingredients_list)
        
        if match_count > 0:
            recipes[recipe["name"]] = {
                "condiments": recipe["condiments"],
                "steps": recipe["steps"]
            }
            
    if not recipes:
        main_item = ingredients_list[0]
        recipes[f"AI特製：{main_item}のシンプル炒め"] = {
            "condiments": {"塩": "0.5", "こしょう": "0.2", "油": "1.0"},
            "steps": [
                f"ステップ1：まずは【{main_item}】を食べやすい大きさに切ろう！",
                "ステップ2：フライパンを中火で熱して、しっかり火を通すよ。できたら教えてね。",
                "ステップ3：塩こしょうで味を整えたら完成だよ！"
            ]
        }
        
    return recipes

# --- セッション状態の初期化 ---
if 'generated_recipes' not in st.session_state:
    st.session_state['generated_recipes'] = {}
if 'suggested_options' not in st.session_state:
    st.session_state['suggested_options'] = []
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = [{"role": "assistant", "content": "もっち、こんにちは！データセット検索エンジンを組み込んだよ。「豚肉」「玉ねぎ」「人参」などで検索してみて！"}]
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = -1  
if 'calculated' not in st.session_state:
    st.session_state['calculated'] = False
if 'latest_reply' not in st.session_state:
    st.session_state['latest_reply'] = None

# --- サイドバー：ユーザー状態の識別 ---
st.sidebar.header("👤 ユーザー状態の識別")
user_name = st.sidebar.text_input("ユーザー名", value="もっち")
motivation = st.sidebar.slider("料理モチベーション", 1, 5, 3)
target_servings = st.sidebar.number_input("作りたい人数 (人前)", min_value=0.1, max_value=4.0, value=1.0, step=0.1)

# --- 画面構成（左右２カラム） ---
col_left, col_right = st.columns([1, 1.2])

# 【左カラム】食材入力
with col_left:
    st.subheader("📥 1. 冷蔵庫の食材入力 ＆ AI複数提案")
    st.markdown("**【手順A】手持ちの食材を入力する**")
    
    if "ingredients" not in st.session_state:
        st.session_state.ingredients = [
            {"name": "豚肉", "amount": 120.0, "unit": "g"},
            {"name": "玉ねぎ", "amount": 0.5, "unit": "個"},
            {"name": "人参", "amount": 0.3, "unit": "本"}
        ]

    if st.button("➕ 食材を追加する"):
        st.session_state.ingredients.append({"name": "", "amount": 0.0, "unit": ""})
        st.rerun()

    h_col1, h_col2, h_col3 = st.columns([3, 2, 2])
    h_col1.markdown("**食材名**")
    h_col2.markdown("**量**")
    h_col3.markdown("**単位**")

    updated_ingredients = []
    for i, ing in enumerate(st.session_state.ingredients):
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            name = st.text_input("食材名", value=ing["name"], key=f"name_{i}", label_visibility="collapsed", placeholder="食材名")
        with col2:
            amount = st.number_input("量", value=float(ing["amount"]), key=f"amount_{i}", label_visibility="collapsed", step=1.0)
        with col3:
            unit = st.text_input("単位", value=ing["unit"], key=f"unit_{i}", label_visibility="collapsed", placeholder="単位")
        
        updated_ingredients.append({"name": name, "amount": amount, "unit": unit})
    
    st.session_state.ingredients = updated_ingredients
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🔍 【手順B】この食材から料理を複数提案してもらう", type="secondary"):
        ingredients_list = [ing["name"].strip() for ing in st.session_state.ingredients if ing["name"].strip() != ""]
        
        if not ingredients_list:
            st.error("⚠️ 食材名が入力されていません。")
        else:
            recipes_result = generate_intelligent_recipes(ingredients_list)
            st.session_state['generated_recipes'] = recipes_result
            st.session_state['suggested_options'] = list(recipes_result.keys())
            st.session_state['calculated'] = False  
            
            proposal_msg = "もっち、データベースからレシピを検索したよ！下のリストから選んで！"
            st.session_state['chat_history'].append({"role": "assistant", "content": proposal_msg})
            st.session_state['latest_reply'] = proposal_msg

    st.markdown("---")
    st.markdown("**【手順C】提案された選択肢から料理を選んで最適化する**")
    selected_recipe = st.selectbox("ココのおススメ料理選択肢", st.session_state['suggested_options'])
    
    if st.button("✨ 【手順D】この料理の調味料比率を計算する", type="primary"):
        if not selected_recipe:
            st.error("⚠️ まずは【手順B】のボタンを押してね！")
        else:
            st.session_state['calculated'] = True
            st.session_state['current_recipe'] = selected_recipe
            st.session_state['current_recipe_data'] = st.session_state['generated_recipes'][selected_recipe]
            st.session_state['current_step'] = -1  
            
            init_msg = f"【{selected_recipe}】の最適化が完了したよ！右側のハンズフリーを起動して、自由な言葉で話しかけてね！"
            st.session_state['chat_history'].append({"role": "assistant", "content": init_msg})
            st.session_state['latest_reply'] = init_msg

    if st.session_state['calculated'] and 'current_recipe_data' in st.session_state:
        st.markdown("---")
        st.markdown(f"#### 📊 {target_servings}人前の最適化調味料比率")
        recipe = st.session_state['current_recipe_data']
        ratio = target_servings / 2.0
        for name, base_val in recipe["condiments"].items():
            calc_val = round(float(base_val) * ratio, 2)
            st.write(f"・{name}: **{calc_val}** 大さじ")

# 【右カラム】対話型ロボットウインドウ（インテント識別駆動）
with col_right:
    st.subheader("💬 2. 声だけで進める調理ナビ（自由対話対応）")
    
    hands_free_speech_component()
    chat_placeholder = st.container()
    user_message = None

    if chat_input := st.chat_input("ココに話しかけるか、文字を入力してね"):
        user_message = chat_input

    if user_message:
        st.session_state['chat_history'].append({"role": "user", "content": user_message})
        
        if not st.session_state['calculated']:
            reply = "まずは左側の手順に沿って、食材の提案と最適化計算をしてね！"
        else:
            steps = st.session_state['current_recipe_data']["steps"]
            current = st.session_state['current_step']
            
            intent = parse_user_intent(user_message)
            
            if intent == "START_COOKING":
                st.session_state['current_step'] = 0
                reply = f"了解！調理を開始するよ。{steps[0]}"
                
            elif intent == "NEXT_STEP":
                if current >= 0 and current < len(steps) - 1:
                    st.session_state['current_step'] += 1
                    next_step = st.session_state['current_step']
                    reply = f"はーい、次だね。{steps[next_step]}"
                elif current == len(steps) - 1:
                    reply = "これで全工程が完了だよ！お疲れ様！🎉"
                    st.session_state['current_step'] = -2  
                else:
                    reply = "調理は完了しているよ！新しく作るときはもう一度左側から計算してね。"
                    
            elif intent == "REPEAT_STEP":
                if current >= 0:
                    reply = f"あ、ごめんね！もう一回言うよ。{steps[current]}"
                else:
                    reply = "まだ調理は始まっていないよ。準備ができたら『スタート』などと声をかけてね。"
                    
            elif intent == "RESET_COOKING":
                st.session_state['current_step'] = -1
                reply = "調理手順を最初からリセットしたよ。準備ができたら『開始するよ』などと言ってね。"
                
            else:
                if "火" in user_message or "火力" in user_message:
                    reply = "基本的には中火で大丈夫だよ！焦げそうだったら少し弱めて、ココに『次』って教えてね。"
                else:
                    reply = "なるほど！もっち、料理中のその調子だよ。次の工程に進むときは『終わったよ』とか『次は何？』って話しかけてね。"
                
        st.session_state['chat_history'].append({"role": "assistant", "content": reply})
        st.session_state['latest_reply'] = reply  

    with chat_placeholder:
        for message in st.session_state['chat_history']:
            with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
                st.write(message["content"])

    if st.session_state['latest_reply']:
        robot_speak(st.session_state['latest_reply'])
        st.session_state['latest_reply'] = None
