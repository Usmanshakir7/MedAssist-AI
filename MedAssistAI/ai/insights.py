import os
from typing import List

import streamlit as st
from pydantic import BaseModel, Field
from google import genai
from google.genai import types


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)


# ============================================================
# GEMINI CLIENT
# ============================================================

@st.cache_resource
def get_gemini_client():
    """
    Create one persistent Gemini client for the Streamlit app.

    Streamlit reruns the script frequently, so keeping the client
    cached prevents the Google GenAI client from being recreated
    and accidentally closed between requests.
    """

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:

        # Also support Streamlit secrets
        try:
            api_key = st.secrets.get(
                "GEMINI_API_KEY"
            )
        except Exception:
            api_key = None

    if not api_key:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add it to your .env file or "
            ".streamlit/secrets.toml."
        )

    return genai.Client(
        api_key=api_key
    )


# ============================================================
# INSIGHT SCHEMA
# ============================================================

class Insight(BaseModel):

    summary: str = Field(
        description=(
            "Clear educational summary of the supplied "
            "laboratory results."
        )
    )

    recommendation: str = Field(
        description=(
            "General non-diagnostic guidance and "
            "doctor follow-up advice."
        )
    )


# ============================================================
# RECIPE SCHEMA
# ============================================================

class Recipe(BaseModel):

    dietary_suggestions: List[str] = Field(
        default_factory=list
    )

    recipe_name: str = ""

    ingredients: List[str] = Field(
        default_factory=list
    )

    preparation: List[str] = Field(
        default_factory=list
    )

    important_note: str = ""


# ============================================================
# FORMAT DATABASE RESULTS
# ============================================================

def _format_results(rows):

    lines = []

    for row in rows:

        test_name = row["test_name"]

        value = row["value"]

        unit = row["unit"] or ""

        reference_low = row["reference_low"]

        reference_high = row["reference_high"]

        status = row["status"] or "Unknown"

        lines.append(
            f"- {test_name}: "
            f"value={value}, "
            f"unit={unit}, "
            f"reference={reference_low} to {reference_high}, "
            f"status={status}"
        )

    return "\n".join(lines)


# ============================================================
# GENERATE AI INSIGHTS
# ============================================================

def generate_insights(
    test_results,
    language="English"
):

    results = _format_results(
        test_results
    )

    if not results:

        raise ValueError(
            "No extracted test results are available "
            "for AI analysis."
        )

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------
    
    if language == "Urdu":
     language_rules = """
Write BOTH SUMMARY and RECOMMENDATION in clear, natural, fluent Urdu.
 When language is Urdu, follow the Urdu writing rules strictly and produce clean, readable sentences.
STRICT URDU WRITING RULES:

1. Write complete, grammatical Urdu sentences.
2. Translate status words fully:
   - High → زیادہ
   - Low → کم
   - Normal → نارمل
   - Cannot assess → جائزہ نہیں لیا جا سکتا
3. NEVER write the English words High, Low, Normal.
4. NEVER put English words in parentheses.
5. Keep laboratory test names in urdu (do not translate them).
6. Place the urdu test names naturally inside the Urdu sentence.
7. Prefer this clean structure:

   "آپ کی لیبارٹری رپورٹ میں [Test1]، [Test2] اور [Test3] زیادہ ہیں۔
    [Test4] کم ہے۔
    [Test5] کا فیصد کم ہے لیکن Absolute [Test5] نارمل ہیں۔
    [Test6]، [Test7] اور [Test8] نارمل ہیں۔"

8. Group findings clearly:
   - First mention all High results together
   - Then all Low results
   - Then explain any percentage vs absolute difference
   - Finally mention important Normal results briefly

9. Do not reverse word order. Keep logical sentence flow.
10. Avoid long, complicated mixed sentences.
"""
    # --------------------------------------------------------
    # PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are MedAssistAI's laboratory-report explanation assistant.

Your job is to explain the STATUS of laboratory results in
simple, patient-friendly language.

IMPORTANT:
The actual laboratory values, units, and reference ranges are
already displayed separately in the MedAssistAI report table.

DO NOT repeat exact laboratory numbers in your summary or recommendation.

Instead, use only these classifications (translate them according to the language rules):

- Normal
- Low
- High
- Cannot assess

Examples (English):
"Haemoglobin is Normal."
"White blood cell count is High."
"Neutrophils percentage is Low."
"Absolute neutrophil count is Normal."

STRICT RULES:
1. Do not repeat exact laboratory values.
2. Do not repeat reference ranges.
3. Do not invent values or reference ranges.
4. Use the status supplied in the LAB RESULTS data.
5. Do not independently change a supplied Normal/Low/High status.
6. If status is "Unknown", say "Cannot assess".
7. Percentage results and absolute counts are separate measurements.
8. If a percentage is Low/High but the corresponding absolute count is Normal, clearly explain that these are different measurements.
9. Do not diagnose a disease.
10. Do not claim that an abnormal result proves a disease.
11. Do not prescribe medication.
12. Do not tell the user to start or stop medication.
13. Do not claim that food or a home recipe cures a disease.
14. Keep the explanation educational and cautious.
15. Focus mainly on abnormal findings rather than listing every normal test.

LANGUAGE:

{language_rules}

LABORATORY RESULTS:

{results}

OUTPUT:

Provide:

1. SUMMARY:
Give a short, easy-to-understand overview of the report.
Mention which important results are Normal, Low, or High,
but DO NOT include their numerical values.

2. RECOMMENDATION:
Give general educational guidance based on the abnormal findings.
Recommend discussing significant or persistent abnormalities
with a qualified healthcare professional.

Do not include exact numbers anywhere in the output.
"""

    # ========================================================
    # GET PERSISTENT CLIENT
    # ========================================================

    client = get_gemini_client()

    # ========================================================
    # GEMINI REQUEST
    # ========================================================

    response = client.models.generate_content(

        model=GEMINI_MODEL,

        contents=prompt,

        config=types.GenerateContentConfig(

            response_mime_type="application/json",

            response_schema=Insight,
        ),
    )

    # ========================================================
    # PARSE RESPONSE
    # ========================================================

    parsed = getattr(
        response,
        "parsed",
        None
    )

    if parsed is None:

        response_text = getattr(
            response,
            "text",
            None
        )

        if not response_text:

            raise RuntimeError(
                "Gemini returned an empty response."
            )

        parsed = Insight.model_validate_json(
            response_text
        )

    return (
        parsed.summary,
        parsed.recommendation
    )


# ============================================================
# GENERATE URDU DIETARY INFORMATION
# ============================================================

def generate_urdu_recipe(
    test_results
):

    results = _format_results(
        test_results
    )

    if not results:

        raise ValueError(
            "No extracted test results are available."
        )

    # --------------------------------------------------------
    # PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are a general nutrition-information assistant
inside MedAssistAI.

Use ONLY the supplied laboratory information to provide
cautious, general dietary education.

Write EVERYTHING in Urdu script.

IMPORTANT RULES:

1. NEVER invent a laboratory value.
2. NEVER invent a reference range.
3. NEVER say a result is normal unless:
   - a numeric result exists, AND
   - both lower and upper reference limits exist, AND
   - the result falls within those limits.
4. NEVER say a result is abnormal unless:
   - a numeric result exists, AND
   - both reference limits exist, AND
   - the result is outside those limits.
5. Treat percentage values and absolute counts as separate measurements.
6. A low/high percentage does NOT automatically mean the corresponding
   absolute count is low/high.
7. If percentage is abnormal but absolute count is normal, explicitly
   mention this distinction.
8. If the value is missing, say "value not available".
9. If the reference range is missing, say "cannot be classified from
   the supplied reference range".
10. Do not diagnose a disease from CBC results.
11. Do not claim that an abnormal result proves a specific disease.
12. Do not recommend medication.
13. Do not tell the patient to start or stop treatment.
14. Recommend professional medical review when appropriate.

If the supplied laboratory data is insufficient for a
specific dietary suggestion, provide general healthy
eating guidance instead.

LABORATORY RESULTS:

{results}

Provide:

1. 4 to 6 practical dietary suggestions.
2. One simple home recipe.
3. Ingredients.
4. Preparation steps.
5. An important safety note.

The recipe should be ordinary food and should not be
presented as a treatment or cure.
"""

    # ========================================================
    # GET SAME PERSISTENT CLIENT
    # ========================================================

    client = get_gemini_client()

    # ========================================================
    # GEMINI REQUEST
    # ========================================================

    response = client.models.generate_content(

        model=GEMINI_MODEL,

        contents=prompt,

        config=types.GenerateContentConfig(

            response_mime_type="application/json",

            response_schema=Recipe,
        ),
    )

    # ========================================================
    # PARSE RESPONSE
    # ========================================================

    parsed = getattr(
        response,
        "parsed",
        None
    )

    if parsed is None:

        response_text = getattr(
            response,
            "text",
            None
        )

        if not response_text:

            raise RuntimeError(
                "Gemini returned an empty response."
            )

        parsed = Recipe.model_validate_json(
            response_text
        )

    return parsed.model_dump()