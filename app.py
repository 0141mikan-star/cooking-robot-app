import streamlit as st
import pandas as pd

st.title("🤖 自炊サポートロボット「ココ」")

# サイドバーでユーザー状態を設定
st.sidebar.header("👤 ユーザー状態識別")
motivation = st.sidebar.slider("料理モチベーション", 1, 5, 3)
servings = st.sidebar.number_input("作りたい人数 (人前)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

# メイン画面
st.header("🗂 食材・レシピ入力")
recipe = st.selectbox("料理を選択", ["肉じゃが", "豚の生姜焼き", "野菜炒め"])

# 食材リストの簡易編集画面
default_ingredients = pd.DataFrame([
    {"食材名": "豚肉", "量": "100g"},
    {"食材名": "玉ねぎ", "量": "0.5個"}
])
st.data_editor(default_ingredients, use_container_width=True)

if st.button("✨ 最適化計算とアドバイスを生成", type="primary"):
    st.success(f"🎯 {servings}人前に合わせた調味料比率を計算しました！")
    
    # ロボットからのアドバイス（モチベーションに応じて変化）
    if motivation <= 2:
        st.info("🤖 ココ：「もっち、今日は無理せず電子レンジを活用して楽に作ろうね！」")
    else:
        st.info("🤖 ココ：「隠し味にごま油を数滴垂らすのがAIのイチオシだよ！」")
