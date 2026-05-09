import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

def extract_links(page_url):
    response = requests.get(page_url, timeout=5)
    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        text = tag.get_text(strip=True)
        if href.startswith("http"):
            links.append({"url": href, "text": text})
    return links

def get_action(url, link_text=""):
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    path = parsed.path.lower()
    rules = {
        "github.com":        lambda p: "View Pull Request"  if "/pull/"       in p else
                                       "View Issue"          if "/issues/"     in p else
                                       "Open Repository",
        "youtube.com":       lambda p: "Watch Video",
        "docs.google.com":   lambda p: "Open Document"      if "document"     in p else
                                       "Open Spreadsheet"   if "spreadsheet"  in p else
                                       "Open Presentation",
        "twitter.com":       lambda p: "View Tweet"         if "/status/"     in p else "View Profile",
        "x.com":             lambda p: "View Tweet"         if "/status/"     in p else "View Profile",
        "linkedin.com":      lambda p: "View Job Posting"   if "/jobs/"       in p else "View Profile",
        "amazon.com":        lambda p: "Buy Product",
        "stackoverflow.com": lambda p: "Read Answer",
        "medium.com":        lambda p: "Read Article",
        "reddit.com":        lambda p: "View Post"          if "/comments/"   in p else "Browse Subreddit",
        "figma.com":         lambda p: "Open Design File",
        "notion.so":         lambda p: "Open Notion Page",
        "drive.google.com":  lambda p: "Open in Google Drive",
    }
    for pattern, action_fn in rules.items():
        if pattern in domain:
            return action_fn(path)
    if link_text:
        return f"Open: {link_text[:40]}"
    return "Open Link"

@app.route("/extract", methods=["POST"])
def extract():
    data = request.json
    page_url = data.get("url")
    if not page_url:
        return jsonify({"error": "No URL provided"}), 400
    try:
        links = extract_links(page_url)
        results = []
        for link in links:
            action = get_action(link["url"], link["text"])
            results.append({
                "url":    link["url"],
                "text":   link["text"],
                "action": action
            })
        return jsonify({"source": page_url, "links": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
