import praw
import re
from textblob import TextBlob

# === Configuration ===
REDDIT_CLIENT_ID = "UDPJ7Hn8Bv-wXDYA6DVwtQ"
REDDIT_CLIENT_SECRET = "TRoIlOfJFN9e-lFje1a4gDY2PIm7Yw"
REDDIT_USER_AGENT = "Realistic-Ninja-7987"

# === Initialize PRAW ===
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

# === Helper Functions ===
def extract_username(url):
    match = re.search(r"reddit\.com/user/([^/]+)/?", url)
    return match.group(1) if match else None

def analyze_sentiment(text):
    return TextBlob(text).sentiment.polarity

def build_persona(username):
    redditor = reddit.redditor(username)

    posts = []
    comments = []

    try:
        # Fetch posts
        for post in redditor.submissions.new(limit=20):
            posts.append({"title": post.title, "subreddit": str(post.subreddit), "text": post.selftext})

        # Fetch comments
        for comment in redditor.comments.new(limit=20):
            comments.append({"body": comment.body, "subreddit": str(comment.subreddit)})

    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    # === Persona Construction ===
    subreddits = [p["subreddit"] for p in posts + comments]
    all_texts = [p["text"] for p in posts] + [c["body"] for c in comments]
    combined_text = " ".join(all_texts)

    persona = {
        "Username": username,
        "Top Subreddits": {},
        "Writing Style": "",
        "General Sentiment": "",
        "Topics of Interest": [],
        "Citations": {}
    }

    # Top subreddits
    from collections import Counter
    sub_count = Counter(subreddits).most_common(5)
    persona["Top Subreddits"] = {k: v for k, v in sub_count}
    persona["Citations"]["Top Subreddits"] = subreddits

    # Writing Style (avg sentence length, use of personal pronouns)
    avg_length = sum(len(t.split()) for t in all_texts) / len(all_texts) if all_texts else 0
    persona["Writing Style"] = f"Avg. sentence length: {avg_length:.2f} words"
    persona["Citations"]["Writing Style"] = all_texts[:3]

    # Sentiment
    avg_sentiment = sum(analyze_sentiment(t) for t in all_texts) / len(all_texts) if all_texts else 0
    sentiment_desc = "Positive" if avg_sentiment > 0.2 else "Negative" if avg_sentiment < -0.2 else "Neutral"
    persona["General Sentiment"] = sentiment_desc
    persona["Citations"]["General Sentiment"] = all_texts[:3]

    # Topics of interest (frequent keywords)
    from collections import defaultdict
    import string
    keywords = defaultdict(int)
    for text in all_texts:
        words = text.lower().translate(str.maketrans("", "", string.punctuation)).split()
        for word in words:
            if word not in {"the", "and", "to", "a", "of", "i", "in", "is", "it", "that", "for", "on"}:
                keywords[word] += 1
    top_keywords = sorted(keywords.items(), key=lambda x: -x[1])[:5]
    persona["Topics of Interest"] = [k for k, _ in top_keywords]
    persona["Citations"]["Topics of Interest"] = all_texts[:3]

    return persona

def save_persona(persona):
    filename = f"{persona['Username']}_persona.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"User Persona for u/{persona['Username']}\n")
        f.write("=" * 40 + "\n\n")
        f.write("Top Subreddits:\n")
        for sr, count in persona["Top Subreddits"].items():
            f.write(f"- {sr} ({count} times)\n")
        f.write("\nCited subreddits: " + ", ".join(set(persona["Citations"]["Top Subreddits"])) + "\n\n")

        f.write("Writing Style:\n")
        f.write(f"{persona['Writing Style']}\n")
        f.write("Cited examples:\n")
        for ex in persona["Citations"]["Writing Style"]:
            f.write(f" - {ex[:100]}...\n")
        f.write("\n")

        f.write("General Sentiment:\n")
        f.write(f"{persona['General Sentiment']}\n")
        f.write("Cited examples:\n")
        for ex in persona["Citations"]["General Sentiment"]:
            f.write(f" - {ex[:100]}...\n")
        f.write("\n")

        f.write("Topics of Interest:\n")
        for kw in persona["Topics of Interest"]:
            f.write(f"- {kw}\n")
        f.write("Cited examples:\n")
        for ex in persona["Citations"]["Topics of Interest"]:
            f.write(f" - {ex[:100]}...\n")
        f.write("\n")

    print(f"\n✅ Persona saved to: {filename}")


# === Main ===
if __name__ == "__main__":
    url = input("Enter Reddit profile URL: ").strip()
    username = extract_username(url)

    if username:
        persona = build_persona(username)
        if persona:
            save_persona(persona)
    else:
        print("❌ Invalid Reddit URL.")
