from app import generate_ai_plan
from dotenv import load_dotenv
import os

# Force reload .env
load_dotenv(override=True)

data = {
    'weight': 75,
    'height': 180,
    'gender': 'male',
    'goal': 'lose_weight',
    'activity_level': 'moderate',
    'strength_level': 'intermediate',
    'allergies': ['peanuts'],
    'diet_type': 'none'
}
calories = 2200

print(f"Checking API Key: {os.getenv('GEMINI_API_KEY')[:5]}...")

print("Attempting AI Generation...")
plan = generate_ai_plan(data, calories)

if plan:
    print("SUCCESS: Plan generated via API!")
    print(f"Meal 1: {plan['meals'][0]['name']} - {plan['meals'][0]['description']}")
else:
    print("FAILURE: API generation failed. Check logs for details.")
