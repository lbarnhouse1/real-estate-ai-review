import os
import traceback
from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Real Estate AI Review</title>
  <style>
    body { font-family: sans-serif; padding: 20px; background: #f4f7fa; }
    .container { max-width: 700px; margin: auto; background: white; padding: 30px; box-shadow: 0 0 10px #ccc; }
    input, button, select, textarea { padding: 12px; width: 100%; margin-top: 10px; font-size: 16px; }
    .output { margin-top: 20px; background: #eef; padding: 15px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <div class="container">
    <h2>Real Estate AI Review</h2>
    <input id="addressInput" placeholder="Enter property address (required)" required />
    <input id="sqftInput" placeholder="Total square footage (optional)" />
    <label for="gradeInput">Property Condition Grade:</label>
    <select id="gradeInput">
      <option value="">Select Grade (optional)</option>
      <option value="A">A - Move-in ready, no work needed</option>
      <option value="B">B - Minor cosmetic updates</option>
      <option value="C">C - Moderate updates/renovation</option>
      <option value="D">D - Major renovations needed</option>
      <option value="F">F - Tear down / not livable</option>
    </select>

    <h3>Comparable Sales (Optional)</h3>
    <div id="comps">
      <input placeholder="Comp 1 (e.g., 123 Main St - $400,000)" />
      <input placeholder="Comp 2" />
      <input placeholder="Comp 3" />
      <input placeholder="Comp 4" />
      <input placeholder="Comp 5" />
    </div>

    <h3>Rental Comps (Optional)</h3>
    <div id="rentComps">
      <input placeholder="Rent Comp 1 (e.g., 456 Oak St - $1,800)" />
      <input placeholder="Rent Comp 2" />
      <input placeholder="Rent Comp 3" />
      <input placeholder="Rent Comp 4" />
      <input placeholder="Rent Comp 5" />
    </div>

    <button onclick="getReview()">Get AI Review</button>
    <div id="aiOutput" class="output"></div>
  </div>

  <script>
    async function getReview() {
      const address = document.getElementById("addressInput").value.trim();
      const sqft = document.getElementById("sqftInput").value.trim();
      const grade = document.getElementById("gradeInput").value;

      const compInputs = document.querySelectorAll("#comps input");
      const comps = Array.from(compInputs).map(i => i.value.trim()).filter(Boolean);

      const rentInputs = document.querySelectorAll("#rentComps input");
      const rentComps = Array.from(rentInputs).map(i => i.value.trim()).filter(Boolean);

      document.getElementById("aiOutput").innerText = "Loading...";

      const response = await fetch("/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address, comps, rentComps, sqft, grade })
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
    data = request.json
    address = data.get("address", "").strip()
    comps = data.get("comps", [])
    rent_comps = data.get("rentComps", [])
    sqft = data.get("sqft", "").strip()
    grade = data.get("grade", "").strip().upper()

    if not address:
        return jsonify({"error": "Address is required."}), 400

    comp_section = "\nComparable sales provided by user:\n" + "\n".join(f"- {c}" for c in comps) if comps else ""
    rent_section = "\nRental comps provided by user:\n" + "\n".join(f"- {r}" for r in rent_comps) if rent_comps else ""
    sqft_section = f"\nTotal square footage: {sqft}" if sqft else ""
    grade_section = f"\nProperty condition grade (A–F): {grade}" if grade else ""

    prompt = f"""
You are a professional real estate investment analyst.

Perform a comprehensive investment review for the following subject property:
- Address: {address}
{sqft_section}
{grade_section}

If provided, incorporate these data points into your analysis:
{comp_section}
{rent_section}

Your response should include:

1. 🔍 **Estimated Market Value** based on comparable sales and square footage. Clearly state the approach used (e.g., average $/sqft, adjusted for condition).
2. 🏠 **Top 3 Comparable Properties** (address + sale price) that support the valuation.
3. 💵 **Rent Estimate**, using provided rent comps or market averages if unavailable.
4. 📊 **20% Down Payment** and estimated **loan details**:
   - Assume a 30-year fixed mortgage
   - Use a realistic interest rate and state what you used
5. 📉 **Monthly PITI Estimate**
6. 💰 **Net Cash Flow** and **Cash-on-Cash Return**
7. ⚠️ **Risk Factors**: Include local crime, flood zone risk, and school quality.
8. 🏷️ **Zillow Listing Note** (if property is actively for sale)
   - Format: “Listed on Zillow for asking price of $XXX”

9. ✅ **Investment Recommendation**:
   - Choose from: Buy, Hold, or Sell
   - Provide 1–2 sentence rationale

Respond in clear, professional bullet-point format.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
        )
        review = response.choices[0].message.content.strip()
        return jsonify({"review": review})
    except Exception as e:
        print("🔴 OpenAI API call failed:", e)
        traceback.print_exc()
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
