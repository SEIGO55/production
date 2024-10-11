import streamlit as st
import pandas as pd
import random

st.markdown("""
<style>
mark {
    background-color: yellow;
    color: black;
}
</style>
""", unsafe_allow_html=True)

# 認証済みユーザー向けのメインアプリケーション
st.title('Privacy Policy Training Site version2')

# Excelファイルを自動で読み込む（ファイルパスを指定）
excel_file_path = "PII_QA2.xlsx"  # 読み込むExcelファイルを指定

# PandasでExcelファイルをデータフレームとして読み込み
try:
    df = pd.read_excel(excel_file_path)
except FileNotFoundError:
    st.error(f"エクセルファイル '{excel_file_path}' が見つかりません。ファイルパスを確認してください。")
    st.stop()

df.columns = df.columns.str.strip()  # 余分な空白を削除

# サイドバーの一番上に "Chapter" を checkbox 形式で表示
st.sidebar.header("Chapter")

# df の 'session' 列からユニークな項目を取得
sessions = df['session'].unique().tolist()

# 各セッションに対してチェックボックスを作成
selected_sessions = [session for session in sessions if st.sidebar.checkbox(session, value=True)]

# 'session' 列をフィルタリングしてデータフレームを更新
df = df[df['session'].isin(selected_sessions)]

# サイドバーに big_class と mid_class と Topic を表示
big_class = df['大分類'].unique().tolist()
selected_big_class = st.sidebar.multiselect("Chapter を選択してください", big_class, default=big_class)

# 選択された big_class に基づいて mid_class を抽出し、サイドバーに表示
mid_class = df[df['大分類'].isin(selected_big_class)]['中分類'].unique().tolist()
selected_mid_class = st.sidebar.multiselect("中分類を選択してください", mid_class, default=mid_class)

# 選択された big_class, mid_classに基づいて Topic を抽出し、サイドバーに表示
topic = df[(df['大分類'].isin(selected_big_class)) & (df['中分類'].isin(selected_mid_class))]['topic'].unique().tolist()
selected_topics = st.sidebar.multiselect("Topic を選択してください", topic, default=topic)

# 問題数をサイドバーで選択可能にする（5, 10, 15, 20, 30, 50）
num_questions_options = [5, 10, 15, 20, 30, 50]
selected_num_questions = st.sidebar.selectbox("出力する問題数を選択してください", num_questions_options, index=1)

# サイドバーに「リフレッシュボタン」を追加
if st.sidebar.button("問題をリフレッシュ"):
    # ボタンが押されたときにセッションステートをクリアして、質問を再生成
    st.session_state.pop("questions", None)

# サイドバーで選択された Chapter と Topic に基づいてフィルタリング
filtered_df = df[(df['大分類'].isin(selected_big_class)) &
                 (df['中分類'].isin(selected_mid_class)) &
                 (df['topic'].isin(selected_topics))]

# フィルタリング後のデータが存在するか確認
if filtered_df.empty:
    st.warning("選択された条件に一致する問題がありません。フィルタ条件を変更してください。")
    st.stop()

# セッションステートに質問を保存する関数
def get_questions(num_questions):
    # 各質問をJSON形式に変換
    questions = []
    for _, row in filtered_df.iterrows():
        # 選択肢をリストとして格納し、空白の選択肢を除外
        options = [row["option_1"], row["option_2"], row["option_3"], row.get("option_4", "")]
        options = [opt for opt in options if opt]

        # 選択肢の並び順をランダムにシャッフル
        random.shuffle(options)

        # 質問情報を保存
        question = {
            "category": f'[{row["大分類"]}/{row["中分類"]}/{row["topic"]}]',
            "question": row["question"],
            "options": options,
            "answer": row["correct_answer"],
            "faq": row["faq"],
            "answer_text": row["answer"],
            "q_id": row["q-id"]
        }
        questions.append(question)

    # 指定された問題数をランダムに選択
    if len(questions) > num_questions:
        return random.sample(questions, num_questions)
    else:
        return questions

# セッションステートを使って質問を保存（最初の1回のみ実行）
if ("questions" not in st.session_state or
    st.session_state.get("selected_big_class") != set(selected_big_class) or
    st.session_state.get("selected_mid_class") != set(selected_mid_class) or
    st.session_state.get("selected_topics") != set(selected_topics)):
    st.session_state["questions"] = get_questions(selected_num_questions)
    st.session_state["selected_big_class"] = set(selected_big_class)
    st.session_state["selected_mid_class"] = set(selected_mid_class)
    st.session_state["selected_topics"] = set(selected_topics)

# 各質問に対してラジオボタンを表示し、ユーザーの回答を取得
for i, item in enumerate(st.session_state["questions"]):
    # カテゴリ部分をHTML形式で青文字にして表示
    category_text = f'Q{i+1}: <span style="color:blue;">{item["category"]}</span>'
    question_text = f"{item['question']}"

    # 質問と選択肢を表示
    st.markdown(category_text, unsafe_allow_html=True)
    st.write(question_text)

    # シャッフルされた選択肢をラジオボタンで表示
    user_answer = st.radio("選択肢を選んでください:", item["options"], key=f"question_{i}")

    # ヒント表示のチェックボックスを追加
    show_hint = st.checkbox("ヒントを表示", key=f"hint_{i}")

    if show_hint:
        # ヒントを枠線で囲んで表示
        st.markdown(f"""
            <div style="border:1px solid #000; padding:10px; margin:10px 0;">
                <p><strong>FAQ:</strong><br>{item["faq"]}</p>
                <p><strong>ANSWER:</strong><br>{item["answer_text"]}</p>
                <p><strong>参考:</strong><br>{item["q_id"]}</p>
            </div>
            """, unsafe_allow_html=True)

# 問題確定ボタンを表示
if st.button("回答確定"):
    # ユーザーの回答を収集
    user_answers = []
    for i, item in enumerate(st.session_state["questions"]):
        user_answer = st.session_state.get(f"question_{i}")
        user_answers.append({
            "大分類": item["category"].split('/')[0][1:],  # 先頭の '[' を除去
            "中分類": item["category"].split('/')[1],
            "Topic": item["category"].split('/')[2][:-1],  # 末尾の ']' を除去
            "question": item["question"],
            "answer": user_answer,
            "correct_answer": item["answer"]
        })

    # 問題確定ボタンが押されたときに、正解とユーザーの回答を比較
    st.write("あなたの回答結果:")

    # 各質問と正誤判定を表示
    correct_count = 0
    for item in user_answers:
        if item["answer"] == item["correct_answer"]:
            result = "〇"  # 正解
            correct_count += 1
        else:
            result = "×"  # 不正解
        st.write(f"{item['question']}: **{item['answer']}** （正解: {item['correct_answer']}） -> {result}")

    # 総合得点の表示
    st.write(f"あなたの得点: {correct_count} / {len(user_answers)}")

    # ユーザー回答をデータフレーム化
    user_df = pd.DataFrame(user_answers)

    # 各分類ごとの集計データを作成（大分類、中分類、Topic）
    # 1. 大分類ごとの集計
    big_class_summary = user_df.groupby("大分類").agg(
        出題された問題数=("question", "count"),
        正解数=("answer", lambda x: sum(x == user_df.loc[x.index, "correct_answer"]))
    ).reset_index()
    big_class_summary["正解率"] = (big_class_summary["正解数"] / big_class_summary["出題された問題数"] * 100).round(1).astype(str) + "%"

    # 大分類合計を追加
    total_questions = big_class_summary["出題された問題数"].sum()
    total_correct = big_class_summary["正解数"].sum()
    total_accuracy = (total_correct / total_questions * 100).round(1)
    big_class_summary.loc[len(big_class_summary)] = ["合計", total_questions, total_correct, f"{total_accuracy}%"]

    # 2. 中分類ごとの集計
    mid_class_summary = user_df.groupby(["大分類", "中分類"]).agg(
        出題された問題数=("question", "count"),
        正解数=("answer", lambda x: sum(x == user_df.loc[x.index, "correct_answer"]))
    ).reset_index()
    mid_class_summary["正解率"] = (mid_class_summary["正解数"] / mid_class_summary["出題された問題数"] * 100).round(1).astype(str) + "%"

    # 中分類合計を追加
    total_questions = mid_class_summary["出題された問題数"].sum()
    total_correct = mid_class_summary["正解数"].sum()
    total_accuracy = (total_correct / total_questions * 100).round(1)
    mid_class_summary.loc[len(mid_class_summary)] = ["", "合計", total_questions, total_correct, f"{total_accuracy}%"]

    # 3. 小分類（Topic）ごとの集計
    topic_summary = user_df.groupby(["大分類", "中分類", "Topic"]).agg(
        出題された問題数=("question", "count"),
        正解数=("answer", lambda x: sum(x == user_df.loc[x.index, "correct_answer"]))
    ).reset_index()
    topic_summary["正解率"] = (topic_summary["正解数"] / topic_summary["出題された問題数"] * 100).round(1).astype(str) + "%"

    # 小分類合計を追加
    total_questions = topic_summary["出題された問題数"].sum()
    total_correct = topic_summary["正解数"].sum()
    total_accuracy = (total_correct / total_questions * 100).round(1)
    topic_summary.loc[len(topic_summary)] = ["", "", "合計", total_questions, total_correct, f"{total_accuracy}%"]

    # 各統計を表示
    st.write("### 大分類ごとの統計")
    st.table(big_class_summary)

    st.write("### 中分類ごとの統計")
    st.table(mid_class_summary)

    st.write("### 小分類（Topic）ごとの統計")
    st.table(topic_summary)














