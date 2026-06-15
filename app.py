import streamlit as st
import pandas as pd
import numpy as np

# ページ全体のデザイン設定
st.set_page_config(
    page_title="AI動的提案ロボット「ココ」",
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

# 🎙️ ハンズフリー音声認識用コンポーネント（React対策版）
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

# --- 🧠 擬似LLM/動的レシピ生成エンジン 🧠 ---
def generate_dynamic_recipe(ingredients_list):
    """
    入力された未知の食材リストから、料理名・調味料・ステップをその場で自動生成する
    （※APIキーがあれば、ここをOpenAIやHugging FaceのAPIに差し替えることで本物のAIになります）
    """
    if not ingredients_list:
        return None
        
    main_item = ingredients_list[0]
    sub_items = "と" + "、".join(ingredients_list[1:]) if len(ingredients_list) > 1 else ""
    
    # 食材の特性に応じた料理ジャンルの動的判定
    if any(k in main_item for k in ["卵", "ご飯", "米"]):
        recipe_name = f"ココ特製 AI創作{main_item}チャーハン風御飯"
        condiments = {"醤油": "1.5", "塩コショウ": "少々", "ごま油": "1.0", "鶏ガラスープの素": "1.0"}
        steps = [
            f"ステップ1：まずはフライパンに油を熱して、細かく切った【{main_item}】をサッと炒めよう！炒め終わったら『次』って教えてね。",
            f"ステップ2：次に【{sub_items.replace('と','')}】とご飯を一気に投入して、強火でパラパラになるまで炒めるよ。できたら次！",
            f"ステップ3：仕上げに、画面左に表示されている最適化された【醤油や鶏ガラスープの素】を鍋肌から回し入れて味を整えたら完成だよ！"
        ]
    elif any(k in main_item for k in ["パスタ", "麺", "トマト", "チーズ"]):
        recipe_name = f"極旨 AI創作{main_item}のまかないパスタ"
        condiments = {"オリーブオイル": "2.0", "塩": "1.0", "ニンニク(チューブ)": "0.5", "コンソメ": "1.0"}
        steps = [
            f"ステップ1：お湯を沸かしてパスタを茹で始めよう。その間に【{main_item}】を食べやすい大きさにカットしてね。終わったら『次』だよ。",
            f"ステップ2：フライパンにオリーブオイルとニンニクを熱し、【{sub_items.replace('と','')}】をじっくり炒めて特製ソースを作るよ。できたら次！",
            f"ステップ3：茹で上がったパスタと茹で汁を少しフライパンに加え、画面左の【調味料】と一緒に全体をよく絡めたら完成だよ！"
        ]
    else:
        # 万能型の炒め・煮込み系レシピ自動生成
        recipe_name = f"冷蔵庫すっきり！AI特製 {main_item}のスタミナ炒め煮"
        condiments = {"醤油": "2.0", "みりん": "1.0", "酒": "1.0", "砂糖": "0.5", "お水": "100.0"}
        steps = [
            f"ステップ1：フライパン（または鍋）に油をひいて、火の通りにくい【{main_item}】から順番に中火で炒めていこう。終わったら『次』って教えてね。",
            f"ステップ2：全体に火が通ってきたら、残りの【{sub_items.replace('と','')}】を加えてさらにサッと炒め合わせるよ。できたら次！",
            f"ステップ3：ここで、画面左に可視化されている【醤油・みりん・お水などの黄金比率調味料】をすべてフライパンに投入して、味が染み込むまで少し煮詰めたら完成だよ！"
        ]
        
    return {"recipe_name": recipe_name, "condiments": condiments, "steps": steps}

# --- セッション状態（記憶）の初期化 ---
if 'ingredients' not in st.session_state:
    # 🌟 初期値は最小限にし、空から追加できるように設定
    st.session_state['ingredients'] = pd.DataFrame([
        {"食材名": "豚肉", "量": 120.0, "単位": "g"}
    ])
if 'generated_recipe' not in st.session_state:
    st.session_state['generated_recipe'] = None
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = [{"role": "assistant", "content": "もっち、こんにちは！左側のリストに、今冷蔵庫にある食材を何でもいいから自由に入力してみてね（行の追加もできるよ）。入力し終わったら『AIにレシピを自動検索・生成してもらう』ボタンを押してね！"}]
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = -1  
if 'latest_reply' not in st.session_state:
    st.session_state['latest_reply'] = None

# --- ヘッダー領域 ---
st.title("🤖 完全動的提案・自炊サポートロボット『ココ』")
st.caption("⚡ Kumamoto University - Information Fusion / LLM & Dataset Inference Simulation")
st.markdown("---")

# --- サイドバー：ユーザー状態の識別 ---
st.sidebar.header("👤 ユーザー状態の識別")
user_name = st.sidebar.text_input("ユーザー名", value="もっち")
motivation = st.sidebar.slider("料理モチベーション", 1, 5, 3)
target_servings = st.sidebar.number_input("作りたい人数 (人前)", min_value=0.1, max_value=4.0, value=1.0, step=0.1)

mode = "support" if motivation <= 2 else "active"

# --- 画面構成（左右２カラム） ---
col_left, col_right = st.columns([1, 1.2])

# 【左カラム】完全動的な食材入力とAI検索・数値推論
with col_left:
    st.subheader("📥 1. 冷蔵庫のリアルタイムAIスキャン")
    
    st.markdown("**【手順A】手元にある食材をすべて入力する**（何を入力してもAIが認識します）")
    
    # 編集可能なエディタ（セッション状態と直結）
    edited_ingredients = st.data_editor(st.session_state['ingredients'], num_rows="dynamic", use_container_width=True)
    st.session_state['ingredients'] = edited_ingredients
    
    # 🌟 どんな未知の食材からでも自動で探してレシピを組み立てるボタン
    if st.button("🔍 【手順B】AIにレシピを動的検索・自動生成してもらう", type="primary", use_container_width=True):
        ingredients_list = edited_ingredients["食材名"].dropna().tolist()
        ingredients_list = [i for i in ingredients_list if i.strip() != ""]
        
        if not ingredients_list:
            st.error("⚠️ 食材名が入力されていません。1つ以上入力してください。")
        else:
            # 動的生成エンジンの呼び出し
            recipe_result = generate_dynamic_recipe(ingredients_list)
            st.session_state['generated_recipe'] = recipe_result
            st.session_state['current_step'] = -1  # ステップリセット
            
            proposal_msg = f"もっち、入力された食材を元にビッグデータとLLMで動的推論したよ！今回は【{recipe_result['recipe_name']}】を作るのがベストって出たよ！右側のハンズフリーを起動して『スタート』って話しかけてね。"
            st.session_state['chat_history'].append({"role": "assistant", "content": proposal_msg})
            st.session_state['latest_reply'] = proposal_msg
            st.rerun()

    # 🌟 AIが自動生成したレシピに基づいて、数値推論（調味料の自動最適化）を可視化する
    if st.session_state['generated_recipe']:
        st.markdown("---")
        recipe = st.session_state['generated_recipe']
        st.markdown(f"#### 📊 AIがその場で算出した調味料比率\n料理名: **{recipe['recipe_name']}**")
        
        ratio = target_servings / 2.0
        # 少量・大量調理時の動的補正係数
        adj = 1.2 if target_servings <= 0.5 else 1.0
        
        # 決定された調味料ごとに分量を動的計算して表示
        for name, base_val in recipe["condiments"].items():
            if base_val == "少々":
                st.write(f"・{name}: **少々**")
            else:
                calc_val = round(float(base_val) * ratio * adj, 2)
                unit = "ml" if "水" in name else "大さじ"
                st.write(f"・{name}: **{calc_val}** {unit} (人数・蒸発率補正済)")
                
        with st.expander("🛠️ Quantity Regression 動作ログ"):
            st.json({
                "対象料理": recipe['recipe_name'],
                "入力食材": edited_ingredients["食材名"].dropna().tolist(),
                "推論エンジン": "Recipe-Generation-LLM-v2 (Dynamic Prompting)",
                "調味料補正ロジック": "人数比および少量調理時水分蒸発補正アルゴリズム適用"
            })

# 【右カラム】対話型ロボットウインドウ（自動生成されたステップをそのまま読み込む）
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
        
        if not st.session_state['generated_recipe']:
            reply = "まずは左側の手順に沿って、食材の入力とAI自動生成を実行してね！"
        else:
            # 🌟 固定データではなく、AIがその場で自動生成したステップを読み込んでナビゲートする
            steps = st.session_state['generated_recipe']["steps"]
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
                    reply = f"これですべての手順が完了だよ！もっち、最高の【{st.session_state['generated_recipe']['recipe_name']}】ができたね！自炊大成功、お疲れ様！🎉"
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
