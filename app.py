import openai
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        review = response.choices[0].message.content.strip()
        return jsonify({"review": review})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500
