import os
import traceback
from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI

app = Flask(__name__)

# Initialize OpenAI client with your API key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
      document.getElementById("aiOutput").innerText = data.review || data.error || "Error.";
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

    prompt = f"""You are a real estate investment advisor that buys and rents houseing. Your are being asked to do a full review of a proprty to be sure we dont over pay for purchase or undercharge for rent. use data from zillow.com or realtor.com to get recent sales data. compare price per sqaurefootage of properties.
Give a property investment review of:
{address}

Include researched values based on comparable comps such as:
- Value based on comparable homes
- List comparable homes values based on recently sold data (show home address and value, up to 3 comparables)
- Rent estimate
- 20% down payment amount
- research current market interest rates for investment properties (range)
- use higher of the ranger of the interest rate for investment properties from previous prompt
- PITI estimate based on that interest rate
- Net cash flow
- Cash on cash return amount
- Risk factors (flood, crime, schools)

Keep your response concise"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        review_text = response.choices[0].message.content.strip()
        return jsonify({"review": review_text})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

