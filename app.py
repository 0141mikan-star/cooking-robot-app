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
                statusSpan.innerHTML = "🗣 聞き取った言葉: 「<b>" + text + "</b>」";

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

# --- 🧠 複数レシピ動的自動生成エンジン ---
def generate_multiple_dynamic_recipes(ingredients_list):
    if not ingredients_list:
        return {}
    main_item = ingredients_list[0]
    sub_items_clean = "、".join(ingredients_list[1:]) if len(ingredients_list) > 1 else main_item
    
    recipes = {}
    
    # 提案1
    r1_name = f"🍳 AI創作：{main_item}の旨辛スタミナ炒め"
    recipes[r1_name] = {
        "condiments": {"醤油": "2.0", "みりん": "1.0", "酒": "1.0", "砂糖": "0.5", "おろしニンニク": "0.5"},
        "steps": [
            f"ステップ1：フライパンに油をひいて、まずは【{main_item}】を中火で色が変わるまで炒めよう！炒め終わったら『次』って教えてね。",
            f"ステップ2：次に【{sub_items_clean}】を投入して、全体に火が通るまでさらに炒めるよ。できたら次！",
            f"ステップ3：仕上げに、左に表示されている最適化された【醤油やみりんのタレ】を一気に回し入れて、強火でサッと絡めたら完成だよ！"
        ]
    }
    # 提案2
    r2_name = f"🍚 AI創作：具だくさん{main_item}特製パラパラチャーハン"
    recipes[r2_name] = {
        "condiments": {"醤油": "1.0", "塩コショウ": "少々", "ごま油": "1.0", "鶏ガラスープの素": "1.0"},
        "steps": [
            f"ステップ1：【{main_item}】と【{sub_items_clean}】を細かく刻んでおこう。器に卵を溶きほぐしたら『次』だよ。",
            f"ステップ2：フライパンにごま油を熱して卵とご飯を入れ、パラパラになるまで炒めたら、刻んだ具材を投入してね。終わったら『次』！",
            f"ステップ3：仕上げに【鶏ガラスープの素】を振り、鍋肌から醤油を回し入れてサッと炒めたら完成！"
        ]
    }
    # 提案3
    r3_name = f"🍲 AI創作：あったか{main_item}の中華風とろみスープ煮"
    recipes[r3_name] = {
        "condiments": {"お水": "300.0", "鶏ガラスープの素": "1.5", "醤油": "0.5", "ごま油": "0.5", "片栗粉(とろみ用)": "1.0"},
        "steps": [
            f"ステップ1：鍋に【お水と鶏ガラスープの素】を入れて沸騰させよう。その間に食材を食べやすい大きさに切ってね。できたら『次』！",
            f"ステップ2：鍋に【{main_item}】と【{sub_items_clean}】を入れて、具材が柔らかくなるまで中火でコトコト煮込むよ。終わったら『次』へ。",
            f"ステップ3：水溶き片栗粉でとろみをつけて、仕上げにごま油を少し垂らしたら完成だよ！"
        ]
    }
    return recipes

# --- 🌟 セッション状態（記憶）の初期化 🌟 ---
if 'base_ingredients' not in st.session_state:
    # 1. マスターとなる初期配置データフレーム（ここを固定の起点にします）
    st.session_state['base_ingredients'] = pd.DataFrame([
        {"食材名": "豚肉", "量": 120.0, "単位": "g"},
        {"食材名": "玉ねぎ", "量": 0.5, "単位": "個"},
        {"食材名": "人参", "量": 0.3, "単位": "本"}
    ])
if 'generated_recipes' not in st.session_state:
    st.session_state['generated_recipes'] = {}
if 'suggested_options' not in st.session_state:
    st.session_state['suggested_options'] = []
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = [{"role": "assistant", "content": "もっち、こんにちは！左側の食材リストを自由に編集して、下の『料理を複数提案してもらう』ボタンを押してね！"}]
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = -1  
if 'calculated' not in st.session_state:
    st.session_state['calculated'] = False
if 'latest_reply' not in st.session_state:
    st.session_state['latest_reply'] = None

# --- ヘッダー領域 ---
st.title("🤖 完全動的・複数提案自炊サポートロボット『ココ』")
st.caption("⚡ Kumamoto University - Information Fusion / Lifecycle Bug Fixed")
st.markdown("---")

# --- サイドバー：ユーザー状態の識別 ---
st.sidebar.header("👤 ユーザー状態の識別")
user_name = st.sidebar.text_input("ユーザー名", value="もっち")
motivation = st.sidebar.slider("料理モチベーション", 1, 5, 3)
target_servings = st.sidebar.number_input("作りたい人数 (人前)", min_value=0.1, max_value=4.0, value=1.0, step=0.1)

mode = "support" if motivation <= 2 else "active"

# --- 画面構成（左右２カラム） ---
col_left, col_right = st.columns([1, 1.2])

# 【左カラム】食材入力
with col_left:
    st.subheader("📥 1. 冷蔵庫の食材入力 ＆ AI複数提案")
    st.markdown("**【手順A】手持ちの食材を入力・編集する**")
    
    # 🌟【修正の核】セッション状態のループ上書きを完全廃止し、
    # 常にベースDFを渡しつつ一意のkeyで編集状態をStreamlitに直接ホールドさせます。
    edited_ingredients = st.data_editor(
        st.session_state['base_ingredients'], 
        num_rows="dynamic", 
        use_container_width=True,
        key="stable_ingredients_editor"
    )
    
    # 手順B: 提案実行ボタン
    if st.button("🔍 【手順B】この食材から料理を複数提案してもらう", type="secondary", use_container_width=True):
        ingredients_list = edited_ingredients["食材名"].dropna().tolist()
        ingredients_list = [i for i in ingredients_list if i.strip() != ""]
        
        if not ingredients_list:
            st.error("⚠️ 食材名が入力されていません。")
        else:
            recipes_result = generate_multiple_dynamic_recipes(ingredients_list)
            st.session_state['generated_recipes'] = recipes_result
            st.session_state['suggested_options'] = list(recipes_result.keys())
            st.session_state['calculated'] = False  
            
            proposal_msg = f"もっち、食材をスキャンしたよ！今ある材料から、炒め物、ご飯物、スープ煮込みの【3つの選択肢】を作ったよ！下のリストからどれにしたいか選んでね。"
            st.session_state['chat_history'].append({"role": "assistant", "content": proposal_msg})
            st.session_state['latest_reply'] = proposal_msg
            st.rerun()

    st.markdown("---")
    st.markdown("**【手順C】提案された選択肢から料理を選んで最適化する**")
    selected_recipe = st.selectbox("ココのおススメ料理選択肢（3種）", st.session_state['suggested_options'])
    
    if st.button("✨ 【手順D】選んだ料理の調味料比率を計算する", type="primary", use_container_width=True):
        if not selected_recipe:
            st.error("⚠️ まずは【手順B】のボタンを押して、料理を提案させてね！")
        else:
            st.session_state['calculated'] = True
            st.session_state['current_recipe'] = selected_recipe
            st.session_state['current_recipe_data'] = st.session_state['generated_recipes'][selected_recipe]
            st.session_state['current_step'] = -1  
            
            init_msg = f"【{selected_recipe}】の調味料最適化が完了したよ！右側のハンズフリーを起動して『スタート』って話しかけてね！"
            st.session_state['chat_history'].append({"role": "assistant", "content": init_msg})
            st.session_state['latest_reply'] = init_msg
            st.rerun()

    # 調味料の自動最適化の可視化
    if st.session_state['calculated'] and 'current_recipe_data' in st.session_state:
        st.markdown("---")
        recipe = st.session_state['current_recipe_data']
        st.markdown(f"#### 📊 {target_servings}人前の最適化調味料比率")
        
        ratio = target_servings / 2.0
        adj = 1.2 if target_servings <= 0.5 else 1.0
        
        for name, base_val in recipe["condiments"].items():
            if base_val == "少々":
                st.write(f"・{name}: **少々**")
            else:
                calc_val = round(float(base_val) * ratio * adj, 2)
                unit = "ml" if "水" in name else "大さじ"
                st.write(f"・{name}: **{calc_val}** {unit}")

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
            steps = st.session_state['current_recipe_data']["steps"]
            current = st.session_state['current_step']
            
            if any(k in user_message for k in ["もう一回", "もう一度", "聞き取れ", "え？", "なんて", "リピート"]):
                if current >= 0:
                    reply = f"あ、ごめんごめん！もう一回言うね。{steps[current]}"
                else:
                    reply = "まだ調理は始まっていないよ。準備ができたら『スタート』って言ってね。"
            elif "スタート" in user_message or "開始" in user_message:
                st.session_state['current_step'] = 0
                reply = f"了解！調理を開始するよ。{steps[0]}"
            elif any(k in user_message for k in ["次", "つぎ", "できた", "おk", "すすめて"]):
                if current >= 0 and current < len(steps) - 1:
                    st.session_state['current_step'] += 1
                    next_step = st.session_state['current_step']
                    reply = f"はーい、次だね。{steps[next_step]}"
                elif current == len(steps) - 1:
                    reply = f"これですべての手順が完了だよ！もっち、最高の料理ができたね！自炊大成功、お疲れ様！🎉"
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
