from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
from datetime import datetime
import joblib
import pandas as pd
import random
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for session

# Load Machine Learning Models and Data
print("Loading Custom ML Models...")
try:
    diet_model = joblib.load("diet_model.pkl")
    df_food = joblib.load("diet_dataframe.pkl")
    df_workout = joblib.load("workout_dataframe.pkl")
    print("Models loaded successfully!")
except Exception as e:
    print(f"Error loading models: {e}. Please run python train_models.py first.")
    diet_model, df_food, df_workout = None, None, None

def calculate_calories(data):
    # Mifflin-St Jeor Equation
    weight = float(data.get('weight', 70))
    height = float(data.get('height', 170))
    age = datetime.now().year - int(data.get('dob', '2000').split('-')[0])
    gender = data.get('gender', 'male')
    
    if gender == 'male':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        
    activity_multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'extra_active': 1.9
    }
    
    activity = data.get('activity_level', 'moderate')
    tdee = bmr * activity_multipliers.get(activity, 1.55)
    
    # Goal Adjustment
    goal = data.get('goal', 'maintain')
    if goal == 'lose_weight':
        return int(tdee - 500)
    elif goal == 'gain_muscle':
        return int(tdee + 300)
    return int(tdee)


def generate_ml_plan(data, total_calories):
    if diet_model is None or df_food is None or df_workout is None:
        return None, "ML Models not loaded. Please train them first."
        
    try:
        experience_level = data.get('strength_level', 'intermediate')
        equipment_pref = data.get('equipment', 'Any')
        diet_type = data.get('diet_type', 'none')
        allergies = data.get('allergies', [])
        
        # Build NLP blacklist
        blacklist = []
        if diet_type == 'vegan':
            blacklist += ['chicken', 'fish', 'egg', 'paneer', 'milk', 'curd', 'ghee', 'butter', 'mutton', 'beef', 'prawn', 'meat']
        elif diet_type == 'vegetarian':
            blacklist += ['chicken', 'fish', 'mutton', 'beef', 'prawn', 'meat', 'egg']
        elif diet_type == 'keto':
            blacklist += ['rice', 'roti', 'naan', 'potato', 'sugar', 'jaggery', 'dosa', 'idli', 'chapati', 'paratha', 'puri']
        
        if 'peanuts' in allergies:
            blacklist += ['peanut', 'groundnut']
        if 'milk' in allergies:
            blacklist += ['milk', 'curd', 'paneer', 'ghee', 'butter', 'cheese', 'creamy']
        if 'fish' in allergies:
            blacklist += ['fish', 'prawn', 'shrimp', 'seafood']
        if 'eggs' in allergies:
            blacklist += ['egg', 'omelette']
        if 'gluten' in allergies:
            blacklist += ['wheat', 'roti', 'naan', 'bread', 'sooji', 'semolina', 'pasta', 'bhatura']
            
        # --- DIET GENERATION ---
        # 1. Determine Target Macros based on Goal
        goal = data.get('goal', 'maintain')
        if goal == 'gain_muscle':
            protein_target = (total_calories * 0.30) / 4 # 30% protein
            fat_target = (total_calories * 0.25) / 9     # 25% fat
            carbs_target = (total_calories * 0.45) / 4    # 45% carbs
        elif goal == 'lose_weight':
            protein_target = (total_calories * 0.40) / 4 # 40% protein (high for satiety)
            fat_target = (total_calories * 0.30) / 9
            carbs_target = (total_calories * 0.30) / 4
        else:
            protein_target = (total_calories * 0.25) / 4
            fat_target = (total_calories * 0.30) / 9
            carbs_target = (total_calories * 0.45) / 4

        # Split into 4 meals roughly (Breakfast 25%, Lunch 35%, Dinner 30%, Snack 10%)
        meal_distributions = {
            'Breakfast': 0.25,
            'Lunch': 0.35,
            'Dinner': 0.30,
            'Snack': 0.10
        }
        
        meals_output = []
        
        for meal_name, percentage in meal_distributions.items():
            t_cal = total_calories * percentage
            t_pro = protein_target * percentage
            t_fat = fat_target * percentage
            t_carb = carbs_target * percentage
            
            # Predict nearest foods
            distances, indices = diet_model.kneighbors([[t_cal, t_pro, t_fat, t_carb]])
            options = df_food.iloc[indices[0]]
            
            # Apply blacklist filter to options
            if blacklist:
                pattern = '|'.join(blacklist)
                filtered_options = options[~options['food_name'].str.contains(pattern, case=False, na=False)]
                if not filtered_options.empty:
                    options = filtered_options
            
            # Try to match the meal type from our NLP tags
            if meal_name == 'Breakfast':
                filtered = options[options['Meal_Type'].isin(['Breakfast', 'Any'])]
            elif meal_name == 'Snack':
                filtered = options[options['Meal_Type'].isin(['Snack', 'Any'])]
            else:
                filtered = options[options['Meal_Type'].isin(['Main', 'Any'])]
                
            if len(filtered) > 0:
                best_food = filtered.iloc[0]
            else:
                best_food = options.iloc[0] # Fallback to absolute nearest math match
                
            meals_output.append({
                "name": meal_name,
                "calories": int(best_food['calories']),
                "description": f"{best_food['food_name'].title()} ({round(best_food['protein_g'], 1)}g Protein, {round(best_food['carbs_g'], 1)}g Carbs, {round(best_food['fat_g'], 1)}g Fat)"
            })


        # --- WORKOUT GENERATION ---
        workout_output = []
        # Create a dynamic Sets & Reps matrix based on goal
        if goal == 'lose_weight':
            sets_reps = "3 sets x 15 reps"
            cardio = True
        elif goal == 'gain_muscle':
            sets_reps = "4 sets x 8-10 reps"
            cardio = False
        else:
            sets_reps = "3 sets x 10-12 reps"
            cardio = False
            
        schedule = [
            {"day": "Monday", "split": ["Chest", "Triceps"]},
            {"day": "Wednesday", "split": ["Back", "Biceps"]},
            {"day": "Friday", "split": ["Legs", "Shoulders"]}
        ]
        
        for day in schedule:
            exercises_list = []
            for muscle in day['split']:
                # Filter workout dataset
                # The dataset uses different names, let's do soft contain matching
                possible_exercises = df_workout[df_workout['muscle_gp'].str.contains(muscle, case=False, na=False)]
                
                if not possible_exercises.empty:
                    # Filter by Level
                    if 'Level' in df_workout.columns:
                        level_match = possible_exercises[possible_exercises['Level'].str.contains(experience_level, case=False, na=False)]
                        if not level_match.empty:
                            possible_exercises = level_match
                            
                    # Filter by Equipment
                    if equipment_pref != 'Any' and 'Equipment' in df_workout.columns:
                        if equipment_pref == 'Body Only':
                            equip_match = possible_exercises[possible_exercises['Equipment'].str.contains('Body', case=False, na=False)]
                        else:
                            equip_match = possible_exercises[possible_exercises['Equipment'].str.contains(equipment_pref, case=False, na=False)]
                            
                        if not equip_match.empty:
                            possible_exercises = equip_match
                            
                    # Pick 2 highly rated exercises per muscle group
                    sampled = possible_exercises.sample(min(2, len(possible_exercises)))
                    for _, row in sampled.iterrows():
                        desc = str(row.get('Desc', ''))
                        if desc == 'nan' or not desc:
                            desc = 'No description available for this exercise.'
                        exercises_list.append({"name": f"{row['Exercise_Name']} ({sets_reps})", "desc": desc})
                else:
                    exercises_list.append({"name": f"Basic {muscle} Exercise ({sets_reps})", "desc": "A foundational movement."})
                    
            if cardio:
                exercises_list.append({"name": "20 Minutes Moderate Cardio (Treadmill/Bike)", "desc": "Keep a steady effort to burn extra calories and improve heart health."})
                
            workout_output.append({
                "day": day['day'],
                "focus": " & ".join(day['split']),
                "exercises": exercises_list
            })

        # --- CONSTRUCT FINAL JSON ---
        plan = {
            "meals": meals_output,
            "total_calories": total_calories,
            "workout": workout_output,
            "tips": [
                f"Your goal is {goal.replace('_', ' ')}. Stick to your weekly average.",
                f"Calorie Cycling: Eat ~{int(total_calories * 1.1)} kcal on workout days and ~{int(total_calories * 0.9)} kcal on rest days.",
                "Drink plenty of water, especially on workout days.",
                "These meals were selected specifically to match your ideal macro ratio."
            ]
        }
        return plan, None
        
    except Exception as e:
        print(f"ML Generation error: {e}")
        return None, str(e)


def generate_local_plan(data, calories, error_message=None):
    # Safe Fallback if ML models crash
    plan = {
        "meals": [
            {"name": "Breakfast", "calories": int(calories * 0.25), "description": "Oatmeal with berries and nuts (Local Fallback)"},
            {"name": "Lunch", "calories": int(calories * 0.35), "description": "Grilled chicken salad with quinoa"},
            {"name": "Dinner", "calories": int(calories * 0.30), "description": "Baked salmon with steamed vegetables"},
            {"name": "Snack", "calories": int(calories * 0.10), "description": "Greek yogurt or an apple"}
        ],
        "total_calories": calories,
        "workout": [
            {"day": "Monday", "focus": "Full Body", "exercises": [{"name": "Squats, Pushups, Rows (3x12)", "desc": "General full body local fallback."}]},
            {"day": "Wednesday", "focus": "Cardio & Core", "exercises": [{"name": "30min Jog, Planks, Crunches", "desc": "General cardio and core local fallback."}]},
            {"day": "Friday", "focus": "Full Body", "exercises": [{"name": "Lunges, Overhead Press, Deadlifts (3x12)", "desc": "General full body local fallback."}]}
        ],
        "tips": [
            "Stay hydrated! Drink at least 3L of water.",
            "Sleep 7-8 hours for recovery.",
            "Consistency is key."
        ]
    }
    if error_message:
        plan['api_error'] = str(error_message)
    return plan

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_plan():
    data = request.json
    calories = calculate_calories(data)
    
    # Use our Custom ML Pipeline!
    plan, error = generate_ml_plan(data, calories)
    
    # Fallback if ML fails
    if not plan:
        print(f"Falling back to simple local generation. Error: {error}")
        plan = generate_local_plan(data, calories, error_message=error)
    
    # Store in session
    session['plan'] = plan
        
    return jsonify({"status": "success"})

@app.route('/result')
def result():
    plan = session.get('plan')
    if not plan:
        return redirect(url_for('index'))
    return render_template('result.html', plan=plan)

if __name__ == '__main__':
    app.run(debug=True)
