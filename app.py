import os
import traceback
from flask import Flask, request, jsonify, render_template_string, send_file
from openai import OpenAI
from io import BytesIO

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Real Estate AI Review</title>
  <style>
    body { font-family: sans-serif; padding: 20px; background: #f4f7fa; }
    .container { max-width: 800px; margin: auto; background: white; padding: 30px; box-shadow: 0 0 10px #ccc; }
    input, button, select, textarea { padding: 10px; width: 100%; margin-top: 10px; font-size: 15px; }
    .output { margin-top: 20px; background: #eef; padding: 15px; white-space: pre-wrap; }
    .compRow { display: flex; gap: 8px; margin-top: 5px; }
    .compRow input, .compRow select { flex: 1; }
  </style>
</head>
<body>
  <div class="container">
    <h2>Real Estate AI Review</h2>
    <input id="addressInput" placeholder="Property address (required)" required />
    <input id="sqftInput" placeholder="Total square footage (optional)" type="number" min="0" />
    <label for="gradeInput">Property Condition Grade:</label>
    <select id="gradeInput">
      <option value="">Select Grade (optional)</option>
      <option value="A">A - Move-in ready</option>
      <option value="B">B - Minor cosmetic updates</option>
      <option value="C">C - Moderate updates</option>
      <option value="D">D - Major renovations</option>
      <option value="F">F - Tear down</option>
    </select>
    <input id="interestRate" placeholder="Interest rate (optional, e.g., 7.25%)" type="text" />

    <h3>Comparable Sales (Optional)</h3>
    <div id="comps">
      <div class="compRow">
        <input placeholder="Address" />
        <input placeholder="Sold Price (e.g., 450000)" type="number" min="0" />
        <input placeholder="Sqft (e.g., 1800)" type="number" min="0" />
        <select>
          <option value="">Grade</option>
          <option>A</option><option>B</option><option>C</option><option>D</option><option>F</option>
        </select>
        <input placeholder="Year Sold (e.g., 2023)" type="number" min="1900" max="2099" />
      </div>
      <div class="compRow">
        <input placeholder="Address" />
        <input placeholder="Sold Price (e.g., 450000)" type="number" min="0" />
        <input placeholder="Sqft (e.g., 1800)" type="number" min="0" />
        <select><option value="">Grade</option><option>A</option><option>B</option><option>C</option><option>D</option><option>F</option></select>
        <input placeholder="Year Sold (e.g., 2023)" type="number" min="1900" max="2099" />
      </div>
      <div class="compRow">
        <input placeholder="Address" />
        <input placeholder="Sold Price (e.g., 450000)" type="number" min="0" />
        <input placeholder="Sqft (e.g., 1800)" type="number" min="0" />
        <select><option value="">Grade</option><option>A</option><option>B</option><option>C</option><option>D</option><option>F</option></select>
        <input placeholder="Year Sold (e.g., 2023)" type="number" min="1900" max="2099" />
      </div>
    </div>

    <h3>Rental Comps (Optional)</h3>
    <div id="rentComps">
      <input placeholder="Rent Comp 1 (e.g., 123 Main St - $1,900)" />
      <input placeholder="Rent Comp 2" />
      <input placeholder="Rent Comp 3" />
    </div>

    <button onclick="getReview()">Get AI Review</button>
    <button onclick="downloadTxt()">Download</button>
    <div id="aiOutput" class="output"></div>
  </div>

  <script>
    let latestReview = "";

    async function getReview() {
      const address = document.getElementById("addressInput").value.trim();
      const sqft = document.getElementById("sqftInput").value.trim();
      const grade = document.getElementById("gradeInput").value;
      const interestRate = document.getElementById("interestRate").value.trim();

      if (!address) {
        alert("Address is required.");
        return;
      }

      const compRows = document.querySelectorAll("#comps .compRow");
      const comps = Array.from(compRows).map(row => {
        const inputs = row.querySelectorAll("input, select");
        const [addr, price, sqft, grade, year] = Array.from(inputs).map(i => i.value.trim());
        if (addr || price || sqft || grade || year) {
          return { addr, price, sqft, grade, year };
        }
        return null;
      }).filter(Boolean);

      const rentInputs = document.querySelectorAll("#rentComps input");
      const rentComps = Array.from(rentInputs).map(i => i.value.trim()).filter(Boolean);

      document.getElementById("aiOutput").innerText = "Loading...";

      const response = await fetch("/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address, comps, rentComps, sqft, grade, interestRate })
      });

      const data = await response.json();
      document.getElementById("aiOutput").innerText = data.review || data.error || "Error.";
      latestReview = data.review;
    }

    function downloadTxt() {
      if (!latestReview) return;
      const blob = new Blob([latestReview], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'ai_review.txt';
      a.click();
      URL.revokeObjectURL(url);
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
    interest_rate = data.get("interestRate", "").strip()

    if not address:
        return jsonify({"error": "Address is required."}), 400

    comp_lines = []
    for comp in comps:
        line = f"Address: {comp.get('addr', '')}\n- Sold Price: ${comp.get('price', '')}\n- Size: {comp.get('sqft', '')} sqft\n- Grade: {comp.get('grade', '')}\n- Year Sold: {comp.get('year', '')}"
        comp_lines.append(line)
    comp_section = "\nComparable Sales Provided:\n" + "\n\n".join(comp_lines) if comp_lines else ""

    rent_section = "\nRental Comps Provided:\n" + "\n".join(f"- {r}" for r in rent_comps) if rent_comps else ""
    sqft_section = f"\nTotal square footage: {sqft}" if sqft else ""
    grade_section = f"\nProperty condition grade (A–F): {grade}" if grade else ""
    rate_section = f"\nUse this interest rate: {interest_rate}" if interest_rate else ""

    prompt = f"""
You are a professional real estate investment analyst.

Analyze this subject property:
- Address: {address}
{sqft_section}
{grade_section}
{rate_section}

Use the following if provided:
{comp_section}
{rent_section}

Respond in clear, professional bullet-point format. When performing calculations:
- Use realistic and explainable logic
- Show your math briefly
- Do not make assumptions outside the provided inputs

Respond with:
1. 🔍 Estimated Market Value
2. 💵 Rent Estimate
3. 📊 20% Down Payment and Loan Terms (state interest rate used)
4. 📉 Monthly PITI Breakdown
5. 💰 Net Cash Flow & Cash-on-Cash Return
6. ⚠️ Risk Factors (e.g., crime, flood zone, schools)
7. ✅ Investment Recommendation (Buy, Hold, or Sell)
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
