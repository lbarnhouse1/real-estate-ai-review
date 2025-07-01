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
    <input id="sqftInput" placeholder="Total square footage (optional)" />
    <label for="gradeInput">Property Condition Grade:</label>
    <select id="gradeInput">
      <option value="">Select Grade (optional)</option>
      <option value="A">A - Move-in ready</option>
      <option value="B">B - Minor cosmetic updates</option>
      <option value="C">C - Moderate updates</option>
      <option value="D">D - Major renovations</option>
      <option value="F">F - Tear down</option>
    </select>
    <input id="interestRate" placeholder="Interest rate (optional, e.g., 7.25%)" />

    <h3>Comparable Sales (Optional)</h3>
    <div id="comps">
      <div class="compRow">
        <input placeholder="Address" />
        <input placeholder="Sold Price (e.g., 450000)" />
        <input placeholder="Sqft (e.g., 1800)" />
        <select><option value="">Grade</option><option>A</option><option>B</option><option>C</option><option>D</option><option>F</option></select>
        <select><option value="">Year Sold</option><option>2020</option><option>2021</option><option>2022</option><option>2023</option><option>2024</option><option>2025</option></select>
      </div>
      <div class="compRow">
        <input placeholder="Address" />
        <input placeholder="Sold Price (e.g., 450000)" />
        <input placeholder="Sqft (e.g., 1800)" />
        <select><option value="">Grade</option><option>A</option><option>B</option><option>C</option><option>D</option><option>F</option></select>
        <select><option value="">Year Sold</option><option>2020</option><option>2021</option><option>2022</option><option>2023</option><option>2024</option><option>2025</option></select>
      </div>
      <div class="compRow">
        <input placeholder="Address" />
        <input placeholder="Sold Price (e.g., 450000)" />
        <input placeholder="Sqft (e.g., 1800)" />
        <select><option value="">Grade</option><option>A</option><option>B</option><option>C</option><option>D</option><option>F</option></select>
        <select><option value="">Year Sold</option><option>2020</option><option>2021</option><option>2022</option><option>2023</option><option>2024</option><option>2025</option></select>
      </div>
    </div>

    <h3>Rental Comps (Optional)</h3>
    <div id="rentComps">
      <div class="compRow">
        <input placeholder="Address" />
        <input placeholder="Monthly Rent (e.g., 1900)" />
        <input placeholder="Sqft" />
        <select><option value="">Beds</option><option>1</option><option>2</option><option>3</option><option>4</option><option>5</option></select>
        <select><option value="">Baths</option><option>1</option><option>1.5</option><option>2</option><option>2.5</option><option>3</option></select>
      </div>
      <div class="compRow">
        <input placeholder="Address" />
        <input placeholder="Monthly Rent (e.g., 1900)" />
        <input placeholder="Sqft" />
        <select><option value="">Beds</option><option>1</option><option>2</option><option>3</option><option>4</option><option>5</option></select>
        <select><option value="">Baths</option><option>1</option><option>1.5</option><option>2</option><option>2.5</option><option>3</option></select>
      </div>
      <div class="compRow">
        <input placeholder="Address" />
        <input placeholder="Monthly Rent (e.g., 1900)" />
        <input placeholder="Sqft" />
        <select><option value="">Beds</option><option>1</option><option>2</option><option>3</option><option>4</option><option>5</option></select>
        <select><option value="">Baths</option><option>1</option><option>1.5</option><option>2</option><option>2.5</option><option>3</option></select>
      </div>
    </div>

    <button onclick="getReview()">Get AI Review</button>
    <div id="aiOutput" class="output"></div>
  </div>

  <script>
    async function getReview() {
      const address = document.getElementById("addressInput").value.trim();
      const sqft = document.getElementById("sqftInput").value.trim();
      const grade = document.getElementById("gradeInput").value;
      const interestRate = document.getElementById("interestRate").value.trim();

      const compRows = document.querySelectorAll("#comps .compRow");
      const comps = Array.from(compRows).map(row => {
        const inputs = row.querySelectorAll("input, select");
        const [addr, price, sqft, grade, year] = Array.from(inputs).map(i => i.value.trim());
        if (addr || price || sqft || grade || year) {
          return { addr, price, sqft, grade, year };
        }
        return null;
      }).filter(Boolean);

      const rentRows = document.querySelectorAll("#rentComps .compRow");
      const rentComps = Array.from(rentRows).map(row => {
        const inputs = row.querySelectorAll("input, select");
        const [addr, rent, sqft, beds, baths] = Array.from(inputs).map(i => i.value.trim());
        if (addr || rent || sqft || beds || baths) {
          return { addr, rent, sqft, beds, baths };
        }
        return null;
      }).filter(Boolean);

      document.getElementById("aiOutput").innerText = "Loading...";

      const response = await fetch("/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address, comps, rentComps, sqft, grade, interestRate })
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
    interest_rate = data.get("interestRate", "").strip()

    if not address:
        return jsonify({"error": "Address is required."}), 400

    comp_lines = []
    for comp in comps:
        line = f"Address: {comp.get('addr', '')}\n- Sold Price: ${comp.get('price', '')}\n- Size: {comp.get('sqft', '')} sqft\n- Grade: {comp.get('grade', '')}\n- Year Sold: {comp.get('year', '')}"
        comp_lines.append(line)
    comp_section = "\nComparable Sales Provided:\n" + "\n\n".join(comp_lines) if comp_lines else ""

    rent_lines = []
    for rent in rent_comps:
        line = f"Address: {rent.get('addr', '')}\n- Rent: ${rent.get('rent', '')}\n- Size: {rent.get('sqft', '')} sqft\n- Beds: {rent.get('beds', '')}\n- Baths: {rent.get('baths', '')}"
        rent_lines.append(line)
    rent_section = "\nRental Comps Provided:\n" + "\n\n".join(rent_lines) if rent_lines else ""

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

Your response should include:

1. 🔍 **Estimated Market Value** based on comparable sales and square footage. Clearly state the approach used (e.g., average $/sqft, adjusted for condition).
2. 💵 **Rent Estimate**, using provided rent comps or market averages if unavailable.
3. 📊 **20% Down Payment** and estimated **loan details**:
   - Assume a 30-year fixed mortgage
   - Use a realistic interest rate and state what you used
   - Property tax = 1.25% annually
   - Insurance = 0.35% annually
4. 📉 **Monthly PITI Estimate**
5. 💰 **Net Cash Flow** and **Cash-on-Cash Return**
6. ⚠️ **Risk Factors**: Include local crime, flood zone risk, and school quality.
7. ✅ **Investment Recommendation**:
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
