import json
import os
import sys

import anthropic

BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

THEMES = [
    "思考・マインドセット",
    "経営者のメンタル・孤独",
    "お金・価格・売上の考え方",
    "習慣・行動",
    "人間関係・信頼",
]

SYSTEM_PROMPT = """あなたは「イセ サトシ（ise_satoshi）」というペルソナで、Threads投稿を書くライターです。

【ペルソナ】
- 名前：イセ サトシ
- 美容師歴27年、サロン経営者
- 経営の本質とマインドを発信している
- 算命学も活用したマインドコーチング

【ターゲット】
サロン経営者・美容師・独立を考えている美容のプロ

【文体ルール】
- 一人称は「僕」
- 27年の現場経験から語る体験談ベース
- タメ口で親しみやすく、でも深みのある内容
- 読んだ人が「あるある」「そうか」と思える内容
- ハッシュタグ不要
- 100〜250文字程度
- 絵文字不要"""


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

    if len(queue) >= 10:
        print(f"[INFO] キュー十分（{len(queue)}件）。生成スキップ。")
        sys.exit(0)

    print(f"[INFO] キュー残り{len(queue)}件。投稿を補充します。")
    api_key = load_credentials()
    new_posts = generate_posts(api_key, 20)

    next_id = max((p.get("id", 0) for p in queue), default=0) + 1
    for p in new_posts:
        p["id"] = next_id
        next_id += 1
        queue.append(p)

    save_json(queue_path, queue)
    print(f"[OK] {len(new_posts)}件追加。キュー合計: {len(queue)}件")


if __name__ == "__main__":
    main()
