# 🍽️ Foodie - AI Recipe Chatbot

A conversational AI-powered recipe discovery and management system that helps users find, explore, and save recipes with nutritional information. The chatbot features secure user authentication, natural language processing for recipe searches, and integrates with multiple food APIs to provide comprehensive recipe data.

## ✨ Features

### 🔐 User Authentication
- **Secure Registration**: Create new accounts with encrypted password storage using bcrypt
- **Login System**: Authenticate existing users with secure password verification
- **Session Management**: Maintain user sessions throughout the chat experience

### 🔍 Recipe Discovery
- **Natural Language Search**: Use conversational phrases like:
  - "I want to make pasta"
  - "Recipe for chocolate cake"
  - "How to make pizza"
  - "Show me Italian recipes"
- **Intelligent Query Processing**: Automatically extracts food items from natural language input
- **Multiple Search Results**: Display up to 20 recipes per search with cuisine and category information

### 📖 Recipe Details
- **Complete Recipe Information**:
  - Detailed ingredient lists with measurements
  - Instructions URL for cooking steps
  - YouTube video links (when available)
  - Source website links
- **Nutritional Analysis**: 
  - Individual ingredient calorie information via USDA API
  - Total estimated calories per recipe
  - Comprehensive nutrition data

### 💾 Recipe Management
- **Save Recipes**: Bookmark favorite recipes to your personal collection
- **View Saved Recipes**: Access your saved recipe library anytime
- **Delete Recipes**: Remove recipes from your collection with confirmation prompts
- **Duplicate Prevention**: Prevents saving the same recipe multiple times

### 💬 Conversational Interface
- **Natural Interactions**: Responds to greetings, farewells, and casual conversation
- **Command Recognition**: Understands various command formats
- **Repeat Function**: Ask the bot to repeat its last response
- **Context Awareness**: Maintains conversation context for smooth interactions

## 🛠️ Technical Architecture

### Database Layer (`RecipeDatabase`)
- **SQLite Database**: Local storage for user data and saved recipes
- **User Management**: Secure user registration and authentication
- **Recipe Storage**: Personal recipe collections with API source tracking
- **Data Integrity**: Foreign key relationships and unique constraints

### API Integration Layer (`RecipeAPI`)
- **TheMealDB**: Primary recipe search and details provider
- **USDA FoodData Central**: Nutritional information for ingredients
- **Error Handling**: Robust API error handling and timeout management
- **Rate Limiting**: Respectful API usage with proper request management

### Chatbot Engine (`RecipeChatbot`)
- **Natural Language Processing**: Pattern matching for food-related queries
- **State Management**: Tracks current recipes, user sessions, and conversation context
- **Command Processing**: Handles various user commands and interactions
- **Response Generation**: Dynamic, contextual responses with emoji formatting

## 📋 Prerequisites

- Python 3.7+
- Internet connection for API access
- Required Python packages (see Installation)

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Foodie-V3
   ```

2. **Install required packages**:
   ```bash
   pip install requests sqlite3 bcrypt python-dotenv
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```env
   SPOONACULAR_API_KEY=your_spoonacular_key_here
   THEMEALDB_BASE_URL=https://www.themealdb.com/api/json/v1/1
   USDA_API_KEY=your_usda_api_key_here
   USDA_BASE_URL=https://api.nal.usda.gov/fdc/v1
   ```

4. **Obtain API Keys**:
   - **USDA API Key**: Register at [FoodData Central](https://fdc.nal.usda.gov/api-guide.html)
   - **TheMealDB**: Free tier available at [TheMealDB](https://www.themealdb.com/api.php)
   - **Spoonacular** (optional): Get key from [Spoonacular](https://spoonacular.com/food-api)

## 🎮 Usage

1. **Start the chatbot**:
   ```bash
   python recipe-chatbot.py
   ```

2. **Create account or login**:
   - Choose `register` to create a new account
   - Choose `login` to access existing account
   - Choose `quit` to exit

3. **Search for recipes**:
   ```
   💬 You: I want to make lasagna
   💬 You: Recipe for chocolate chip cookies
   💬 You: How to cook salmon
   ```

4. **Navigate results**:
   - Type a number (1-20) to view recipe details
   - Type `new search` to start a new search

5. **Manage saved recipes**:
   - Type `yes` to save a recipe when prompted
   - Type `saved` to view your saved recipes
   - Type `delete N` to remove recipe number N

## 🎯 Available Commands

| Command | Description |
|---------|-------------|
| `saved` | View your saved recipes |
| `delete N` | Delete recipe number N from saved list |
| `new search` | Start a new recipe search |
| `repeat that` | Repeat the last bot response |
| `hello/hi/hey` | Greet the bot |
| `goodbye/bye/quit` | Exit the chatbot |
| `yes/y/save` | Save current recipe |
| `no/n` | Don't save current recipe |

## 🗂️ File Structure

```
Foodie-V3/
├── recipe-chatbot.py    # Main application file
├── recipes.db          # SQLite database (auto-generated)
├── .env               # Environment variables (create this)
├── .gitignore         # Git ignore file
└── README.md          # This file
```

## 🔧 Configuration

The application uses environment variables for API configuration. Ensure your `.env` file contains:

- `THEMEALDB_BASE_URL`: TheMealDB API endpoint
- `USDA_API_KEY`: Your USDA FoodData Central API key
- `USDA_BASE_URL`: USDA API endpoint
- `SPOONACULAR_API_KEY`: Optional Spoonacular API key

## 🛡️ Security Features

- **Password Encryption**: Uses bcrypt for secure password hashing
- **SQL Injection Protection**: Parameterized queries prevent SQL injection
- **Input Validation**: Sanitized user inputs and error handling
- **Session Management**: Secure user session handling

## 🚨 Error Handling

The application includes comprehensive error handling for:
- API connection failures
- Database connection issues
- Invalid user inputs
- Network timeouts
- Missing environment variables

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [TheMealDB](https://www.themealdb.com/) for providing free recipe data
- [USDA FoodData Central](https://fdc.nal.usda.gov/) for nutritional information
- [bcrypt](https://pypi.org/project/bcrypt/) for secure password hashing

## 📞 Support

If you encounter any issues or have questions, please open an issue in the GitHub repository.

---

**Enjoy cooking with AI! 🍳👨‍🍳👩‍🍳**
