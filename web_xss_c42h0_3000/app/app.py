from flask import Flask, request, make_response
import urllib.request, urllib.parse

app = Flask(__name__)

@app.get("/")
def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Message Board</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; color: #333; }
    h1 { color: #2c3e50; }
    .card { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; }
    textarea { width: 100%; box-sizing: border-box; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; font-family: monospace; }
    button { background: #3498db; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; font-size: 1rem; margin-top: 0.5rem; }
    button:hover { background: #2980b9; }
    iframe { width: 100%; height: 200px; border: 1px dashed #bdc3c7; background: #fff; margin-top: 1rem; }
    .report-section { border-top: 2px solid #ecf0f1; padding-top: 2rem; }
    input[type="url"] { width: 70%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Message Board</h1>
  <p>Leave a message for others. You can preview how your HTML message will render before submitting that can help your maybe.</p>
  
  <div class="card">
    <form action="/">
      <textarea name="html" rows="5" placeholder="<b>input your message???</b>"></textarea>
      <button type="submit">Preview Message</button>
    </form>

    <div id="iframe-wrapper"></div>
  </div>

  <div class="report-section">
    <h2>Report Malicious Message</h2>
    <p>If you find a malicious guestbook link, please report it to the admin bot.</p>
    <form action="/visit" method="GET" target="_blank">
      <input type="url" name="url" placeholder="bot will visit this url" required>
      <button type="submit" style="background: #e74c3c;">Report to Admin</button>
    </form>
  </div>

  <script type="module">
    const blob = await fetch("/render" + location.search, {
      headers: { "X-F-Script": "1" },
    }).then((r) => r.blob());
    if (blob.size) {
      document.forms[0].html.value = await blob.text();
      const iframe = document.createElement("iframe");
      iframe.setAttribute("sandbox", "");
      iframe.src = URL.createObjectURL(blob);
      document.getElementById("iframe-wrapper").append(iframe);
    }
  </script>
</body>
</html>
    """.strip()


@app.get("/render")
def render():
    if not request.headers.get("X-F-Script", ""): return "Use script", 400 ; 
    res = make_response(request.args.get("html", "")); return res

@app.get("/visit")
def proxy_visit():
    url = request.args.get("url")
    if not url: return "No URL provided", 400
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:5000/visit?url={urllib.parse.quote(url)}")
        return req.read(), req.getcode()
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)