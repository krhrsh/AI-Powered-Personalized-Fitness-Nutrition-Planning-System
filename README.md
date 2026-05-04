# AI-Powered-Personalized-Fitness-Nutrition-Planning-System

The following outlines the technical architecture, algorithms, and implementation details of the AI Fitness Planner. The system is designed to generate highly personalized dietary and workout plans entirely offline, using local machine learning models and dataset processing, ensuring user privacy, low latency, and robustness.

## 1. Technology Stack
*   **Backend Framework:** Python with Flask
*   **Machine Learning & Data Processing:** Scikit-Learn, Pandas, Joblib
*   **Frontend:** HTML5, CSS3, Jinja2 Templating
*   **Datasets:** 
    *   `Indian_Food_Nutrition_Processed.csv` (Indian cuisine dietary dataset)
    *   `megaGymDataset.csv` (Comprehensive exercise dataset)

## 2. System Architecture & Workflow
The application operates on a local-first architecture. During initialization (`train_models.py`), the system ingests raw datasets, cleans the data, categorizes items using Natural Language Processing (NLP) heuristics, and trains a K-Nearest Neighbors (KNN) model. The trained models and processed dataframes are serialized into `.pkl` files using `joblib`. 

At runtime (`app.py`), the Flask application loads these serialized models into memory to quickly serve predictions without relying on external third-party APIs like Groq or OpenAI.

## 3. Caloric & Metabolic Calculations
Before generating plans, the system establishes a baseline for the user's energy requirements:
1.  **Basal Metabolic Rate (BMR):** Calculated using the **Mifflin-St Jeor Equation**, which factors in age, gender, weight, and height. This is widely considered the most accurate standard formula for clinical use.
2.  **Total Daily Energy Expenditure (TDEE):** The BMR is multiplied by an activity factor (ranging from 1.2 for sedentary to 1.9 for extra active) based on user input.
3.  **Goal Adjustment:** The target caloric intake is dynamically adjusted based on the user's primary goal:
    *   *Lose Weight:* TDEE - 500 kcal
    *   *Gain Muscle:* TDEE + 300 kcal
    *   *Maintain:* TDEE

## 4. Dietary Plan Generation (Machine Learning)
The diet generation pipeline utilizes a combination of Machine Learning and NLP-based filtering:
1.  **Macronutrient Distribution:** The target calories are split into a specific macro ratio depending on the goal (e.g., 40% Protein / 30% Fat / 30% Carbs for weight loss vs. 30% Protein / 25% Fat / 45% Carbs for muscle gain).
2.  **Meal Splitting:** Calories are distributed across four daily meals: Breakfast (25%), Lunch (35%), Dinner (30%), and Snack (10%).
3.  **KNN Prediction (`diet_model.pkl`):** For each meal, the system calculates the exact target calories, protein, fat, and carbs. It then queries the Scikit-Learn `NearestNeighbors` model to find the top 50 closest matching foods in the multi-dimensional nutrient space.
4.  **NLP Filtering & Blacklisting:** 
    *   The system constructs a dynamic blacklist array based on user-selected dietary preferences (Vegan, Vegetarian, Keto) and specific allergies (Peanuts, Milk, Fish, Eggs, Gluten).
    *   It filters the KNN predictions by doing a substring match against the blacklist, automatically discarding non-compliant items.
    *   Finally, it filters by `Meal_Type` (a feature engineered during the training phase using keyword classification) to ensure, for example, that a snack food is not recommended for a main course.

## 5. Workout Plan Generation
The workout module uses dynamic pandas dataframe filtering to build a personalized schedule:
1.  **Schedule & Split:** Generates a 3-day weekly split (Monday, Wednesday, Friday) targeting specific muscle groups (e.g., Chest/Triceps, Back/Biceps, Legs/Shoulders).
2.  **Sets & Reps Matrix:** Dynamically assigns sets/reps based on the goal. (e.g., *4 sets x 8-10 reps* for hypertrophy/muscle gain, *3 sets x 15 reps + Cardio* for weight loss/endurance).
3.  **Algorithmic Filtering:** 
    *   Queries `workout_dataframe.pkl` using soft-contain matching for the targeted `muscle_gp`.
    *   Filters the resulting subset based on the user's `Level` (Beginner, Intermediate, Expert).
    *   Filters further based on `Equipment` availability (e.g., strictly matching "Bodyweight" if the user has no equipment).
4.  **Randomized Selection:** Randomly samples highly-rated exercises from the final filtered subset to ensure variety in the user's routine, preventing workout fatigue.

## 6. Fault Tolerance & Fallback Mechanisms
To ensure continuous availability, the system features a heuristic fallback method (`generate_local_plan`). If the `.pkl` ML models fail to load, are corrupted, or throw a runtime exception, the application safely catches the error and generates a mathematically sound, hard-coded template for both diet and exercise. This guarantees that the user always receives a fitness plan, preventing complete application failure.

## 7. Setup & Execution Guide

To run the AI Fitness Planner locally, follow these steps:

**Prerequisites:**
*   Python 3.8+ installed on your system.

**Step 1: Install Dependencies**
Open a terminal in the project directory and install the required Python libraries using `pip`:
```bash
pip install -r requirements.txt
```
*(This installs Flask, pandas, scikit-learn, joblib, and other necessary packages).*

**Step 2: Train the Machine Learning Models**
Before running the application, you must pre-process the dataset and train the offline machine learning models. Execute the training script:
```bash
python train_models.py
```
*Expected Output: The script will load the Indian foods and gym datasets, train the K-Nearest Neighbors model, and successfully save `diet_model.pkl`, `diet_dataframe.pkl`, and `workout_dataframe.pkl` into the project directory.*

**Step 3: Run the Application**
Once the models are trained and saved, start the Flask development server:
```bash
python app.py
```

**Step 4: Access the Web Interface**
Open your web browser and navigate to the local server address:
```
http://127.0.0.1:5000
```
From here, you can input your details (age, weight, height, goal, allergies) and click "Generate Plan" to receive your personalized fitness and diet schedule entirely offline.