# AI Recipe Chatbot
import requests
import sqlite3
import json
import re
from typing import List, Dict, Optional
import time as t
import bcrypt
import os
import dotenv

dotenv.load_dotenv()

# Configuration
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
THEMEALDB_BASE_URL = os.getenv("THEMEALDB_BASE_URL")
USDA_API_KEY = os.getenv("USDA_API_KEY")
USDA_BASE_URL = os.getenv("USDA_BASE_URL")

# ============ DATABASE HANDLER ============
class RecipeDatabase:
    def __init__(self, db_name="recipes.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash BLOB NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS saved_recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    recipe_id TEXT NOT NULL,
                    recipe_name TEXT NOT NULL,
                    api_source TEXT NOT NULL,
                    UNIQUE(user_id, recipe_id, api_source),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            conn.commit()

    def create_user(self, username: str, password: str) -> Optional[int]:
        # Hash password
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                               (username, password_hash))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def authenticate_user(self, username: str, password: str) -> Optional[int]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                user_id, password_hash = row
                if bcrypt.checkpw(password.encode(), password_hash):
                    return user_id
            return None

    def save_recipe(self, user_id: int, recipe_id: str, recipe_name: str, api_source: str) -> bool:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO saved_recipes (user_id, recipe_id, recipe_name, api_source)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, recipe_id, recipe_name, api_source))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_saved_recipes(self, user_id: int) -> List[tuple]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT recipe_id, recipe_name, api_source FROM saved_recipes
                WHERE user_id = ?
            ''', (user_id,))
            return cursor.fetchall()

    def delete_saved_recipe(self, user_id: int, recipe_index: int) -> Optional[str]:
        recs = self.get_saved_recipes(user_id)
        if 1 <= recipe_index <= len(recs):
            recipe_id, recipe_name, api_source = recs[recipe_index-1]
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM saved_recipes WHERE user_id = ? AND recipe_id = ? AND api_source = ?
                ''', (user_id, recipe_id, api_source))
                conn.commit()
            return recipe_name
        else:
            return None

# ============ RECIPE/NUTRITION API HANDLER ============
class RecipeAPI:
    def search_recipes_themealdb(self, query: str) -> List[Dict]:
        try:
            url = f"{THEMEALDB_BASE_URL}/search.php"
            params = {"s": query}
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('meals'):
                    return data['meals'][:20]
            return []
        except Exception:
            return []

    def get_recipe_details_themealdb(self, meal_id: str) -> Dict:
        try:
            url = f"{THEMEALDB_BASE_URL}/lookup.php"
            params = {"i": meal_id}
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('meals'):
                    return data['meals'][0]
            return {}
        except Exception:
            return {}

    def get_nutrition_info(self, ingredients: List[str]) -> List[Dict]:
        nutrition_data = []
        for ingredient in ingredients:
            if not ingredient or ingredient == "None" or not ingredient.strip():
                continue
            try:
                url = f"{USDA_BASE_URL}/foods/search"
                params = {
                    "api_key": USDA_API_KEY,
                    "query": ingredient,
                    "pageSize": 1
                }
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('foods') and len(data['foods']) > 0:
                        food = data['foods'][0]
                        nutrients = food.get('foodNutrients', [])
                        calories = None
                        for nutrient in nutrients:
                            if nutrient.get('nutrientId') == 1008:
                                calories = nutrient.get('value', None)
                        nutrition_data.append({
                            'ingredient': ingredient,
                            'calories': calories if calories is not None else 'N/A'
                        })
                    else:
                        nutrition_data.append({'ingredient': ingredient, 'calories': 'N/A'})
            except Exception:
                nutrition_data.append({'ingredient': ingredient, 'calories': 'Error'})
        return nutrition_data

# ============ MAIN CHATBOT ============
class RecipeChatbot:
    greet_words = ['hello', 'hi', 'hey', 'greetings']
    bye_words = ['goodbye', 'bye', 'see you', 'cya', 'exit', 'quit']
    repeat_words = ['repeat that', 'say that again', 'repeat', 'again']

    def __init__(self):
        self.db = RecipeDatabase()
        self.api = RecipeAPI()
        self.current_user_id = None
        self.current_username = None
        self.current_recipes = []
        self.current_recipe_details = None
        self.last_bot_response = ""
        self.awaiting_delete_confirm = None

    def chat_reply(self, bot_msg):
        print(bot_msg)
        self.last_bot_response = bot_msg

    def extract_food_request(self, user_input: str) -> str:
        patterns = [
            r"i want to make (?:a )?(.+)",
            r"recipe for (.+)",
            r"how to make (.+)",
            r"make (.+)",
            r"cook (.+)",
            r"show me (.+) recipes?",
            r"find (.+) recipes?",
            r"search for (.+)",
            r"(.+) recipe"
        ]
        user_input_lower = user_input.lower().strip()
        for pattern in patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                return match.group(1).strip()
        return user_input.strip()

    def display_recipes(self, recipes: List[Dict]):
        if not recipes:
            self.chat_reply("❌ Sorry, I couldn't find any recipes for that. Try a different search term.")
            return
        txt = f"\n🍽️  Found {len(recipes)} recipes:\n{'='*50}\n"
        for i, recipe in enumerate(recipes, 1):
            name = recipe.get('strMeal', 'Unknown Recipe')
            cuisine = recipe.get('strArea', 'Unknown')
            category = recipe.get('strCategory', 'Unknown')
            txt += f"{i:2d}. {name}\n    Cuisine: {cuisine} | Category: {category}\n"
        txt += "\n💡 Type a number (1-20) to see recipe details or 'new search' for something else."
        self.chat_reply(txt)

    def display_recipe_details(self, recipe: Dict):
        if not recipe:
            self.chat_reply("❌ Sorry, I couldn't get the recipe details.")
            return
        name = recipe.get('strMeal', 'Unknown Recipe')
        instructions = recipe.get('strInstructions', 'No instructions available')
        youtube_url = recipe.get('strYoutube', 'No video available')
        source_url = recipe.get('strSource', 'No source available')
        ingredients = []
        for i in range(1, 21):
            ingredient = recipe.get(f'strIngredient{i}')
            measure = recipe.get(f'strMeasure{i}')
            if ingredient and ingredient.strip():
                if measure and measure.strip():
                    ingredients.append(f"{measure.strip()} {ingredient.strip()}")
                else:
                    ingredients.append(ingredient.strip())
        txt = f"\n🍳 Recipe: {name}\n{'='*50}\n\n📝 Ingredients:\n"
        for ingredient in ingredients:
            txt += f"  • {ingredient}\n"
        txt += f"\n🔗 Instructions URL: {source_url}\n"
        if youtube_url != 'No video available':
            txt += f"📺 Video: {youtube_url}\n"
        txt += "\n🥗 Nutrition Information:\n"
        ingredient_names = [re.sub(r'^[^a-zA-Z]+', '', ing.split()[-1]) for ing in ingredients]
        nutrition_info = self.api.get_nutrition_info(ingredient_names[:10])
        total_calories = 0
        for info in nutrition_info:
            ingredient = info['ingredient']
            calories = info['calories']
            txt += f"• {ingredient}: Calories: {calories} kcal\n"
            try:
                if isinstance(calories, (int, float)) or (isinstance(calories, str) and calories.isdigit()):
                    total_calories += float(calories)
            except Exception:
                pass
        txt += f"\n🔥 Total Estimated Calories: {total_calories if total_calories else 'Unknown'} kcal"
        txt += f"\n{'='*50}\n💾 Would you like to save this recipe? (yes/no)"
        self.chat_reply(txt)

    def display_saved_recipes(self, user_id: int):
        saved_recipes = self.db.get_saved_recipes(user_id)
        if not saved_recipes:
            self.chat_reply("📚 You haven't saved any recipes yet!")
            return
        txt = f"\n📚 Your Saved Recipes:\n{'='*50}\n"
        for i, (recipe_id, recipe_name, api_source) in enumerate(saved_recipes, 1):
            txt += f"{i:2d}. {recipe_name} (from {api_source})\n"
        txt += "\n💡 Type a number to view recipe details, or 'delete N' to delete."
        self.chat_reply(txt)

    def greet(self):
        self.chat_reply(f"👋 Hi there, {self.current_username.capitalize()}!")

    def bye(self):
        self.chat_reply(f"👋 Goodbye, {self.current_username.capitalize()}! Have a tasty day!")

    def start_chat(self):
        print("👋 Welcome to the AI Recipe Chatbot!")
        print("Secure login is required. If you are new, you can register a password.")
        while True:
            mode = input("\nDo you want (login/register/quit)? ").strip().lower()
            if mode == 'quit':
                print("👋 Goodbye!")
                return
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            if mode == 'register':
                uid = self.db.create_user(username, password)
                if uid:
                    print("✅ Registration successful! You are now logged in.")
                    self.current_user_id = uid
                    self.current_username = username
                    break
                else:
                    print("❌ Username already exists. Please login or use another name.")
            elif mode == 'login':
                uid = self.db.authenticate_user(username, password)
                if uid:
                    print("✅ Login successful!")
                    self.current_user_id = uid
                    self.current_username = username
                    break
                else:
                    print("❌ Login failed. Try again or register.")
        print("\nType natural sentences to chat, or search, or manage recipes :)")
        print("Commands: 'saved', 'delete N', 'repeat that', 'bye', 'new search'")
        while True:
            user_input = input("\n💬 You: ").strip()
            # Conversational triggers
            if any(w in user_input.lower() for w in self.greet_words):
                self.greet()
                continue
            if any(w in user_input.lower() for w in self.bye_words):
                self.bye()
                break
            if any(w in user_input.lower() for w in self.repeat_words):
                print(self.last_bot_response)
                continue
            # Deletion Awaiting Confirmation
            if self.awaiting_delete_confirm is not None:
                if user_input.strip().lower() in ['yes', 'y']:
                    idx = self.awaiting_delete_confirm
                    deleted = self.db.delete_saved_recipe(self.current_user_id, idx)
                    if deleted:
                        self.chat_reply(f"🗑️ Recipe deleted: {deleted}.")
                    else:
                        self.chat_reply("❌ Could not delete recipe.")
                    self.awaiting_delete_confirm = None
                else:
                    self.chat_reply("❌ Deletion canceled.")
                    self.awaiting_delete_confirm = None
                continue
            # Saved recipes viewing
            if user_input.lower() == 'saved':
                self.display_saved_recipes(self.current_user_id)
                continue
            # Delete command
            if user_input.lower().startswith('delete'):
                try:
                    idx = int(user_input.lower().replace('delete', '').strip())
                    recs = self.db.get_saved_recipes(self.current_user_id)
                    if 1 <= idx <= len(recs):
                        name = recs[idx-1][1]
                        self.chat_reply(f"Are you sure you want to delete '{name}'? (yes/no)")
                        self.awaiting_delete_confirm = idx
                    else:
                        self.chat_reply("❌ Invalid recipe number.")
                except Exception:
                    self.chat_reply("❌ Usage: delete N (number of recipe).")
                continue
            # Recipe selection from saved
            if self.current_recipes == [] and user_input.isdigit():
                saved = self.db.get_saved_recipes(self.current_user_id)
                idx = int(user_input)
                if 1 <= idx <= len(saved):
                    recipe_id, recipe_name, api_source = saved[idx-1]
                    if api_source == 'themealdb':
                        recipe_details = self.api.get_recipe_details_themealdb(recipe_id)
                        if recipe_details:
                            self.display_recipe_details(recipe_details)
                            self.current_recipe_details = recipe_details
                    continue
            # Recipe List selection
            if self.current_recipes and user_input.isdigit():
                recipe_num = int(user_input)
                if 1 <= recipe_num <= len(self.current_recipes):
                    selected_recipe = self.current_recipes[recipe_num - 1]
                    recipe_id = selected_recipe.get('idMeal')
                    recipe_details = self.api.get_recipe_details_themealdb(recipe_id)
                    if recipe_details:
                        self.display_recipe_details(recipe_details)
                        self.current_recipe_details = recipe_details
                else:
                    self.chat_reply("❌ Invalid selection.")
                continue
            # Save recipe confirmation
            if user_input.lower() in ['yes', 'y', 'save']:
                if self.current_recipe_details:
                    recipe_id = self.current_recipe_details.get('idMeal')
                    recipe_name = self.current_recipe_details.get('strMeal')
                    success = self.db.save_recipe(self.current_user_id, recipe_id, recipe_name, 'themealdb')
                    msg = f"💾 Recipe '{recipe_name}' saved successfully!" if success else f"⚠️ You have already saved this recipe before."
                    self.chat_reply(msg)
                    self.current_recipe_details = None
                else:
                    self.chat_reply("❌ No recipe to save.")
                continue
            if user_input.lower() in ['no', 'n']:
                if self.current_recipe_details:
                    self.chat_reply("✅ Okay, recipe not saved.")
                    self.current_recipe_details = None
                continue
            # Recipe search
            if user_input.lower() in ['new search', 'search']:
                self.current_recipes = []
                self.current_recipe_details = None
                self.chat_reply("🔍 What would you like to search for?")
                continue
            food_query = self.extract_food_request(user_input)
            self.chat_reply(f"🔍 Searching for '{food_query}' recipes...")
            recipes = self.api.search_recipes_themealdb(food_query)
            self.current_recipes = recipes
            self.current_recipe_details = None
            self.display_recipes(recipes)

# ============ ENTRY POINT ============
if __name__ == "__main__":
    RecipeChatbot().start_chat()