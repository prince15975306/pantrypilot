"""Optional AWS integration: Amazon Bedrock Converse API writes a short spoken-style meal plan.
Enabled when BEDROCK_MODEL_ID is set (a Claude model ID enabled in your AWS account). Needs: pip install boto3"""
import json
import os


def enabled() -> bool:
    return bool(os.environ.get("BEDROCK_MODEL_ID"))


def meal_plan(pantry, prefs, candidates, days) -> str:
    import boto3  # imported lazily so the server runs without boto3

    client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    cands = [{"name": c["recipe"]["name"], "missing": [m["name"] for m in c["missing"]]} for c in candidates]
    prompt = (
        f"You are a kitchen assistant speaking through a voice speaker. Write a {days}-day dinner plan in under "
        "120 words, plain sentences, no markdown. Prefer items that expire soon.\n"
        f"Pantry: {json.dumps(pantry)}\nPreferences: {json.dumps(prefs)}\n"
        f"Candidate recipes (pick only from these): {json.dumps(cands)}"
    )
    out = client.converse(
        modelId=os.environ["BEDROCK_MODEL_ID"],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 400, "temperature": 0.4},
    )
    parts = out["output"]["message"]["content"]
    return " ".join(p.get("text", "") for p in parts).strip()
