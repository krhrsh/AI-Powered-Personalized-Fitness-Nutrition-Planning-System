from app import calculate_calories, generate_local_plan, generate_ai_plan
import os

# Mock Data
data = {
    'weight': 75,
    'height': 180,
    'age': 25,
    'gender': 'male',
    'activity_level': 'moderate',
    'goal': 'lose_weight',
    'allergies': ['peanuts'],
    'diet_type': 'none'
}

print("Testing Calorie Calculation...")
calories = calculate_calories(data)
print(f"Calculated Calories: {calories}")
assert calories > 1500, "Calories seem too low"

print("\nTesting Local Generation...")
local_plan = generate_local_plan(data, calories)
print("Local Plan Keys:", local_plan.keys())
assert 'meals' in local_plan
assert 'workout' in local_plan

print("\nTesting AI Generation (if key exists)...")
if os.getenv("GEMINI_API_KEY"):
    try:
        ai_plan = generate_ai_plan(data, calories)
        if ai_plan:
            print("AI Plan Generated Successfully")
            print("AI Plan Keys:", ai_plan.keys())
        else:
            print("AI Plan returned None (API Error?)")
    except Exception as e:
        print(f"AI Test Failed: {e}")
else:
    print("Skipping AI Test (No API Key)")

print("\nVerification Complete.")
