# twitter_uc_scraper.py
import undetected_chromedriver as uc
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json, os, time

COOKIES_FILE = "cookies.json"
OUTPUT_FILE = "replies.json"


def extract_replies(data, limit=100):
    tweets = []

    def parse_entries(entries):
        for entry in entries:
            content = entry.get("content", {})

            # Check for main tweet or reply
            if "itemContent" in content and "tweet_results" in content["itemContent"]:
                tweet_results = content["itemContent"]["tweet_results"]
                result = tweet_results.get("result", {})
                legacy = result.get("legacy", {})
                if legacy:
                    tweets.append({
                        "id": legacy.get("id_str"),
                        "user": legacy.get("user_id_str"),
                        "text": legacy.get("full_text"),
                        "created_at": legacy.get("created_at"),
                    })

            # Check for conversationthread (replies)
            if "items" in content:
                for item in content["items"]:
                    item_content = item.get("item", {}).get("itemContent", {})
                    tweet_results = item_content.get("tweet_results", {})
                    result = tweet_results.get("result", {})
                    legacy = result.get("legacy", {})
                    if legacy:
                        tweets.append({
                            "id": legacy.get("id_str"),
                            "user": legacy.get("user_id_str"),
                            "text": legacy.get("full_text"),
                            "created_at": legacy.get("created_at"),
                        })

            # Recursive parse for nested entries if any
            nested_entries = content.get("items") or content.get("itemContent", {}).get("conversation_items", [])
            if nested_entries:
                parse_entries(nested_entries)

    instructions = data.get("data", {}).get("threaded_conversation_with_injections_v2", {}).get("instructions", [])
    for instr in instructions:
        entries = instr.get("entries", [])
        parse_entries(entries)

    # Remove duplicates by tweet ID
    unique_tweets = {t['id']: t for t in tweets}
    
    # Return only latest `limit` replies
    sorted_tweets = sorted(unique_tweets.values(), key=lambda x: x['created_at'], reverse=True)
    return sorted_tweets[:limit]




def save_cookies(driver):
    cookies = driver.get_cookies()
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2)
    print("Cookies saved!")


def load_cookies(driver):
    if not os.path.exists(COOKIES_FILE):
        return False
    try:
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        driver.get("https://x.com")
        for c in cookies:
            c.pop("sameSite", None)
            driver.add_cookie(c)
        print("Cookies loaded.")
        return True
    except Exception as e:
        print("Cookie load failed:", e)
        return False


def main():
    print("Launching undetected Chrome...")
    caps = DesiredCapabilities.CHROME
    caps["goog:loggingPrefs"] = {"performance": "ALL"}

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_argument("--headless")  # Uncomment if you want headless

    driver = uc.Chrome(options=options, desired_capabilities=caps)
    driver.set_window_size(1280, 800)

    # Try to load existing cookies
    if not load_cookies(driver):
        driver.get("https://x.com/login")
        print("Please manually log in for first time.")
        input("After login completes, press ENTER here...")
        save_cookies(driver)

    tweet_url = input("Enter tweet URL: ").strip()
    if not tweet_url.startswith("http"):
        tweet_url = "https://x.com/" + tweet_url.lstrip("/")
    print("Opening tweet:", tweet_url)

    driver.get(tweet_url)
    time.sleep(6)
    replies = []

    # Capture network logs to extract Tweet replies
    logs = driver.get_log("performance")
    for entry in logs:
        msg = json.loads(entry["message"])["message"]
        if msg.get("method") == "Network.responseReceived":
            url = msg.get("params", {}).get("response", {}).get("url", "")
            if "TweetDetail" in url:
                try:
                    resp = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": msg["params"]["requestId"]})
                    data = json.loads(resp.get("body", "{}"))

                    # with open("raw_response.json", "w", encoding="utf-8") as f:
                    #     json.dump(data, f, indent=2, ensure_ascii=False)

                    for reply in extract_replies(data):
                        if reply not in replies:
                            replies.append(reply)
                except Exception:
                    continue

    
    replies = replies[:100]
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(replies, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(replies)} replies to {OUTPUT_FILE}")

    driver.quit()


if __name__ == "__main__":
    main()
