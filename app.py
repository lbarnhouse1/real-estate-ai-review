from flask import Flask, request, jsonify, render_template_string
import openai
import os

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>AI Real Estate Review</title>
  <style>
    body { font-family: sans-serif; padding: 20px; background: #f4f7fa; }
    .container { max-width: 600px; margin: auto; background: white; padding: 30px; box-shadow: 0 0 10px #ccc; }
    input, button { padding: 12px; width: 100%; margin-top: 10px; font-size: 16px; }
    .output { margin-top: 20px; background: #eef; padding: 15px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <div class="container">
    <h2>Real Estate AI Review</h2>
    <input id="addressInput" placeholder="Enter property address" />
    <button onclick="getReview()">Get AI Review</button>
    <div id="aiOutput" class="output"></div>
  </div>
  <script>
    async function getReview() {
      const address = document.getElementById("addressInput").value;
      document.getElementById("aiOutput").innerText = "Loading...";
      const response = await fetch("/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address })
      });
      const data = await response.json();
      document.getElementById("aiOutput").innerText = data.review || "Error.";
    }
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/review", methods=["POST"])
def review():
    address = request.json.get("address", "").strip()
    if not address:
        return jsonify({"error": "Address required"}), 400

    prompt = f"""You are a real estate investment advisor.
Give a property investment review of:
{address}

Include:
- Rent estimate
- PITI estimate
- Net cash flow
- Risk factors (flood, crime, schools)
- Recommendation (buy/hold/sell)"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # safer fallback model
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        review = response.choices[0].message.content.strip()
        return jsonify({"review": review})
    except Exception as e:
        print("🔴 OpenAI API call failed:", e)
        traceback.print_exc()  # prints full traceback to logs
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
