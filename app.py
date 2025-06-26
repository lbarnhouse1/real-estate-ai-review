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
    input, button, textarea { padding: 12px; width: 100%; margin-top: 10px; font-size: 16px; }
    .output { margin-top: 20px; background: #eef; padding: 15px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <div class="container">
    <h2>Real Estate AI Review</h2>
    <input id="addressInput" placeholder="Enter property address (required)" required />

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

      const compInputs = document.querySelectorAll("#comps input");
      const comps = Array.from(compInputs).map(i => i.value.trim()).filter(Boolean);

      const rentInputs = document.querySelectorAll("#rentComps input");
      const rentComps = Array.from(rentInputs).map(i => i.value.trim()).filter(Boolean);

      document.getElementById("aiOutput").innerText = "Loading...";

      const response = await fetch("/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address, comps, rentComps })
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

    if not address:
        return jsonify({"error": "Address is required."}), 400

    comp_section = "\nUser-provided comparable sales:\n" + "\n".join(f"- {c}" for c in comps) if comps else ""
    rent_section = "\nUser-provided rent comps:\n" + "\n".join(f"- {r}" for r in rent_comps) if rent_comps else ""

    prompt = f"""You are a real estate investment advisor.
Give a property investment review of:
{address}

Use the following structure:

{comp_section}
{rent_section}

Provide:
- Estimated value based on comps
- List up to 3 recent comparable homes with address and value
- Rent estimate (use rent comps if provided)
- 20% down payment amount
- Estimated interest rate used for loan calculation
- PITI estimate (based on the interest rate)
- Net cash flow
- Cash-on-cash return
- Risk factors (flood, crime, schools)

Respond clearly and concisely in bullet points.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700,
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
