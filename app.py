import streamlit as st
import pandas as pd
import numpy as np

# ページ全体のデザイン設定
st.set_page_config(
    page_title="次世代対話型自炊サポートロボット「ココ」",
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

# 🎙️ ハンズフリー音声認識用コンポーネント（Reactライフサイクル対策版）
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
                statusSpan.innerHTML = "👂 <b>ココが耳を傾けています（自由な言葉で話しかけてね！）</b><br><span style='font-size:12px; font-weight:normal;'>例:「スタート」「次何する？」「終わったよ」「もう一回言って」</span>";
                micBtn.innerText = "🛑 ハンズフリーモードを終了する";
                micBtn.style.backgroundColor = "#d32f2f";
            };

            recognition.onresult = (event) => {
                const resultIndex = event.resultIndex;
                const text = event.results[resultIndex][0].transcript.trim();
                statusSpan.innerHTML = "🗣 聞き取った言葉: 「<b>" + text + "</b>」";

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

# --- 🧠 自然言語処理：意図解釈（インテント識別）エンジン ---
def parse_user_intent(user_message):
    msg = user_message.lower()
    
    # 次に進める意図の解釈（口語表現の揺らぎを網羅）
    next_keywords = ["次", "つぎ", "なんする", "何する", "できた", "終わった", "おわった", "おk", "オッケー", "おっけー", "進めて", "進む", "完了", "next", "いいよ", "おーけー"]
    if any(k in msg for k in next_keywords):
        return "NEXT_STEP"
        
    # 聞き返しの意図の解釈
    repeat_keywords = ["もう一回", "もう一度", "聞き取れ", "え？", "なんて", "リピート", "聞こえなかった", "もう一度言って", "は？"]
    if any(k in msg for k in repeat_keywords):
        return "REPEAT_STEP"
        
    # 開始・リセット
    if any(k in msg for k in ["スタート", "開始", "はじめ", "やろう", "作ろう"]):
        return "START_COOKING"
    if any(k in msg for k in ["リセット", "最初から", "やり直し"]):
        return "RESET_COOKING"
        
    return "CHAT_OR_QUESTION"

# --- 🍳 ドメイン知識：食材の特性（調理の常識）を考慮した動的レシピ生成 ---
def generate_intelligent_recipes(ingredients_list):
    if not ingredients_list:
        return {}
        
    main_item = ingredients_list[0]
    sub_items_clean = "、".join(ingredients_list[1:]) if len(ingredients_list) > 1 else main_item
    
    # 🌟「卵」が含まれているかを常識判定システムが検知
    has_egg = any("卵" in item for item in ingredients_list)
    recipes = {}
    
    # 提案1: 炒め物系
    r1_name = f"🍳 AI特製：{main_item}のおかずスタミナ炒め"
    if has_egg:
        # 卵の特性（火が通りやすく煮込むと固くなる）を考慮した常識的な手順に自動組み替え
        r1_steps = [
            f"ステップ1：まずは卵の処理からいくよ！フライパンに油を強火で熱して、溶いた卵を一気に入れよう。半熟状になったら、一度お皿に取り出してね。できたら教えて！",
            f"ステップ2：同じフライパンで【{main_item}】と【{sub_items_clean}】（卵以外）を中火でしっかり炒めていこう。炒め終わったら次何するか聞いてね。",
            f"ステップ3：最後に、最初に取り出した半熟卵をフライパンに戻し、左に表示されている最適化調味料を入れてサッと全体を合わせたら完成だよ！これなら卵が固くならないよ！"
        ]
    else:
        r1_steps = [
            f"ステップ1：フライパンに油をひいて、まずは火の通りにくい【{main_item}】を中火で炒めよう！終わったら教えてね。",
            f"ステップ2：次に残りの具材【{sub_items_clean}】を投入して、全体に火が通るまで炒めるよ。できたら次！",
            f"ステップ3：仕上げに、左に表示されている最適化されたタレを一気に回し入れて、強火でサッと絡めたら完成だよ！"
        ]
    recipes[r1_name] = {"condiments": {"醤油": "2.0", "みりん": "1.0", "酒": "1.0", "砂糖": "0.5"}, "steps": r1_steps}
    
    # 提案2: スープ・煮込み系
    r2_name = f"🍲 AI特製：あったか{main_item}のとろみ中華スープ煮"
    if has_egg:
        r2_steps = [
            f"ステップ1：鍋に【お水と鶏ガラスープの素】を入れて沸騰させよう。その間に【{main_item}】などの具材を一口大に切ってね。できたら教えて！",
            f"ステップ2：鍋に切った具材（※卵はまだ入れちゃダメだよ！）を入れて、中火でコトコト煮込むよ。煮込み終わったら次へ進もう。",
            f"ステップ3：ここがココの常識ロジック！火を止める直前に、溶き卵をスープの表面に円を描くように細く回し入れよう。卵がふわっと浮いてきたら完成だよ！"
        ]
    else:
        r2_steps = [
            f"ステップ1：鍋に水とスープの素を入れて沸騰させよう。その間に具材を食べやすい大きさに切ってね。できたら教えて！",
            f"ステップ2：鍋に【{main_item}】などの具材を入れて、全体が柔らかくなるまで中火でコトコト煮込もう。終わったら次へ進むよ。",
            f"ステップ3：最後に味付けをして、全体に味が馴染んだら完成だよ！"
        ]
    recipes[r2_name] = {"condiments": {"お水": "300.0", "鶏ガラスープの素": "1.5", "醤油": "0.5", "ごま油": "0.5"}, "steps": r2_steps}
    
    return recipes

# --- セッション状態の初期化 ---
if 'generated_recipes' not in st.session_state:
    st.session_state['generated_recipes'] = {}
if 'suggested_options' not in st.session_state:
    st.session_state['suggested_options'] = []
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = [{"role": "assistant", "content": "もっち、こんにちは！不具合を完全に修正したよ。左側で食材を自由に入力して、下の『料理を複数提案してもらう』ボタンを押してね！"}]
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
    st.markdown("**【手順A】手持ちの食材を入力・編集する**")
    
    # 🌟 バグ修正の核心：第一引数には固定の初期値を渡し、代入ループを完全撤廃。
    # Streamlit内部がkeyを通じて1回目から完璧に値をホールドします。
    INITIAL_DF = pd.DataFrame([
        {"食材名": "豚肉", "量": 120.0, "単位": "g"},
        {"食材名": "玉ねぎ", "量": 0.5, "単位": "個"},
        {"食材名": "人参", "量": 0.3, "単位": "本"}
    ])
    
    edited_ingredients = st.data_editor(
        INITIAL_DF, 
        num_rows="dynamic", 
        use_container_width=True,
        key="perfect_ingredients_editor"
    )
    
    # 手順B: 提案実行ボタン
    if st.button("🔍 【手順B】この食材から料理を複数提案してもらう", type="secondary", use_container_width=True):
        ingredients_list = edited_ingredients["食材名"].dropna().tolist()
        ingredients_list = [i for i in ingredients_list if i.strip() != ""]
        
        if not ingredients_list:
            st.error("⚠️ 食材名が入力されていません。")
        else:
            recipes_result = generate_intelligent_recipes(ingredients_list)
            st.session_state['generated_recipes'] = recipes_result
            st.session_state['suggested_options'] = list(recipes_result.keys())
            st.session_state['calculated'] = False  
            
            proposal_msg = "もっち、食材を解析したよ！新しく追加された食材の調理特性に合わせて手順を組んだからね。下のリストから選んで！"
            st.session_state['chat_history'].append({"role": "assistant", "content": proposal_msg})
            st.session_state['latest_reply'] = proposal_msg
    

    st.markdown("---")
    st.markdown("**【手順C】提案された選択肢から料理を選んで最適化する**")
    selected_recipe = st.selectbox("ココのおススメ料理選択肢", st.session_state['suggested_options'])
    
    if st.button("✨ 【手順D】この料理の調味料比率を計算する", type="primary", use_container_width=True):
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
            
            # 🌟 自由な発話から意図（インテント）を識別
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
                    reply = "これで全工程が完了だよ！ココの言う通りにやったら卵もフワフワで大成功のはず！お疲れ様！🎉"
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
                # 🌟 意図が「質問や雑談」だった場合の動的相槌ロジック
                if "火" in user_message or "火力" in user_message:
                    reply = "基本的には中火で大丈夫だよ！焦げそうだったら少し弱めて、ココに『次』って教えてね。"
                elif "卵" in user_message:
                    reply = "そうそう、卵は固まりやすいからココの指示のタイミング通りに入れるのが一番美味しくなるよ！"
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
