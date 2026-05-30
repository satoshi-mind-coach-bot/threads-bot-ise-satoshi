import json
import os
import sys

import anthropic

BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

THEMES = [
    "プラス思考・前向きな捉え方",
    "自己成長・変化を恐れない",
    "行動力・決断する勇気",
    "メンタルの整え方・心の余裕",
    "感謝・豊かさの見つけ方",
]

SYSTEM_PROMPT = """あなたは「イセ サトシ（ise_satoshi）」というペルソナで、Threads投稿を書くライターです。

【ペルソナ】
- 名前：イセ サトシ
- 独立して7年、一人サロンを経営している（スタッフなし・一人で運営）
- お店を潰したことは一度もなく、ずっと続けてきた実績がある
- 現在はマインドやプラス思考について発信している
- 読む人の心が軽くなる・前向きになれる言葉を届けることが使命

【ターゲット】
独立して働く人・一人で事業をやっている人。日々の仕事や人間関係で消耗しがちな人に届ける。

【投稿の方向性】
- 美容・髪・施術・サロンの話題は一切出さない
- 日常の小さな気づきや体験から、マインドやプラス思考につなげる
- 読んだ人が「そうだよな」「明日からやってみよう」「ちょっと楽になった」と感じる内容
- 説教くさくなく、自分の体験・失敗・気づきとして語る

【文体ルール】
- 一人称は「僕」
- タメ口ベースで親しみやすく、でも深みがある
- 体験談や具体的なエピソードを入れる
- 最後はそっと背中を押すような締め方
- ハッシュタグ不要
- 100〜250文字程度
- 絵文字不要

【絶対に含めてはいけない内容・絶対禁止ワード】
- 「スタッフ」「従業員」「部下」「スタッフ採用」「スタッフ育成」→ 一人で運営しているため絶対禁止
- 複数人を雇っている前提の表現（「チームで」「みんなで」「一緒に働く仲間」など）
- 美容・ヘアカット・カラー・パーマ・施術・お客様の髪などの美容業に関する具体的な話
- 旅行・ホテル・マイル・航空券に関する内容
- ネットワークビジネス・MLM・勧誘を連想させる内容
- 「金」という単語でお金を表現すること（必ず「お金」と書く）"""


def load_credentials():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    env_path = os.path.join(BOT_DIR, "config", "credentials.env")
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise ValueError("ANTHROPIC_API_KEY not found")


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_posts(api_key, count=20):
    client = anthropic.Anthropic(api_key=api_key)
    posts = []

    for i in range(count):
        theme = THEMES[i % len(THEMES)]
        user_prompt = f"""テーマ「{theme}」でThreads投稿を1件作成してください。

投稿本文のみを出力してください。JSONや説明文は不要です。"""

        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = message.content[0].text.strip()
            posts.append({"text": text, "theme": theme})
            print(f"[OK] {i+1}/{count} [{theme}] {text[:30]}...")
        except Exception as e:
            print(f"[WARN] 生成失敗 ({theme}): {e}")

    return posts


def main():
    queue_path = os.path.join(BOT_DIR, "data", "post_queue.json")
    queue = load_json(queue_path)

    if len(queue) >= 20:
        print(f"[INFO] キュー十分（{len(queue)}件）。生成スキップ。")
        sys.exit(0)

    print(f"[INFO] キュー残り{len(queue)}件。投稿を補充します。")
    api_key = load_credentials()
    new_posts = generate_posts(api_key, 40)

    next_id = max((p.get("id", 0) for p in queue), default=0) + 1
    for p in new_posts:
        p["id"] = next_id
        next_id += 1
        queue.append(p)

    save_json(queue_path, queue)
    print(f"[OK] {len(new_posts)}件追加。キュー合計: {len(queue)}件")


if __name__ == "__main__":
    main()
