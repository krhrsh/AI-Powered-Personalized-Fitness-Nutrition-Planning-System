import pandas as pd
from sklearn.neighbors import NearestNeighbors
import joblib
import os

def create_diet_model():
    print("Loading diet dataset...")
    # Load ONLY Indian foods dataset
    if os.path.exists("Indian_food_Nutrition_Processed.csv"):
        print("Using Indian foods dataset...")
        df_indian = pd.read_csv("Indian_food_Nutrition_Processed.csv")
        df_indian = df_indian.rename(columns={
            'Dish Name': 'food_name',
            'Calories (kcal)': 'calories',
            'Protein (g)': 'protein_g',
            'Fats (g)': 'fat_g',
            'Carbohydrates (g)': 'carbs_g'
        })
        req_cols = ['food_name', 'calories', 'protein_g', 'fat_g', 'carbs_g']
        df_food = df_indian[req_cols].copy()
    else:
        raise FileNotFoundError("Indian_food_Nutrition_Processed.csv not found!")
    
    # NLP Categorization for Meal Types
    # Make everything lowercase for matching
    food_names_lower = df_food['food_name'].str.lower()
    
    breakfast_keywords = ['oat', 'egg', 'cereal', 'pancake', 'waffle', 'toast', 'bagel', 'yogurt', 'milk', 'breakfast', 'smoothie', 'upma', 'poha', 'idli', 'dosa']
    dinner_keywords = ['chicken', 'beef', 'steak', 'salmon', 'fish', 'rice', 'pasta', 'pork', 'turkey', 'lamb', 'salad', 'curry', 'soup', 'pizza', 'burger', 'dal', 'paneer', 'roti', 'naan', 'biryani']
    snack_keywords = ['apple', 'banana', 'nuts', 'protein bar', 'almond', 'cookie', 'chips', 'popcorn', 'snack', 'orange', 'grapes', 'berries', 'samosa', 'bhel', 'chaat']
    
    def categorize_meal(name):
        if any(word in name for word in breakfast_keywords):
            return 'Breakfast'
        elif any(word in name for word in dinner_keywords):
            return 'Main'
        elif any(word in name for word in snack_keywords):
            return 'Snack'
        else:
            return 'Any'
            
    print("Categorizing foods into meal types...")
    df_food['Meal_Type'] = food_names_lower.apply(categorize_meal)
    
    # Fill NAs with 0 for numeric columns
    numeric_cols = ['calories', 'protein_g', 'fat_g', 'carbs_g']
    df_food[numeric_cols] = df_food[numeric_cols].fillna(0)
    
    # We want to fit NearestNeighbors on calories, protein, fat, carbs
    print("Training NearestNeighbors model for Diet...")
    nn_model = NearestNeighbors(n_neighbors=50, algorithm='auto')
    nn_model.fit(df_food[numeric_cols])
    
    # Save the dataframe and the model
    joblib.dump(df_food, "diet_dataframe.pkl")
    joblib.dump(nn_model, "diet_model.pkl")
    print("Diet model saved successfully!")

def create_workout_model():
    print("Loading gym dataset...")
    df_gym = pd.read_csv("megaGymDataset.csv")
    
    # Clean the dataset
    df_gym = df_gym.rename(columns={
        'Title': 'Exercise_Name',
        'BodyPart': 'muscle_gp'
    })
    
    df_gym = df_gym.dropna(subset=['Exercise_Name', 'muscle_gp'])
    
    # Basic cleaning
    df_gym['Exercise_Name'] = df_gym['Exercise_Name'].str.title()
    df_gym['Equipment'] = df_gym['Equipment'].fillna('Bodyweight')
    df_gym['Level'] = df_gym['Level'].fillna('Intermediate')
    
    # Save the cleaned dataframe
    joblib.dump(df_gym, "workout_dataframe.pkl")
    print("Workout logic dataframe saved successfully!")

if __name__ == "__main__":
    if os.path.exists("Indian_food_Nutrition_Processed.csv"):
        create_diet_model()
    else:
        print("Indian_food_Nutrition_Processed.csv not found!")
        
    if os.path.exists("megaGymDataset.csv"):
        create_workout_model()
    else:
        print("megaGymDataset.csv not found!")
    
    print("All models processed.")
