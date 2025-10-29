
# Sprachbausteine Bot 🇩🇪🤖

**Sprachbausteine Bot** is a Telegram bot for practicing grammar and vocabulary for the German language.  
Built with `aiogram`, it provides interactive settings and tracks user performance through a database.

---

## 🚀 Features

- 📩 Telegram bot with command and message handlers  
- ⚙️ User settings management via inline keyboards  
- 📊 Personal training statistics per category  
- 🛠 Editor/admin mode for managing tasks  
- 📁 Task categories and difficulty levels  

---

## 🧰 Tech Stack

| Technology      | Role                              |
|----------------|-----------------------------------|
| Python 3.10+    | Core programming language         |
| aiogram 3.x     | Telegram bot framework (asyncio)  |
| SQLAlchemy      | Database ORM                      |
| pytest          | Unit testing framework            |
| python-dotenv   | Environment variable management   |

---

## 🗂 Project Structure

```
Sprachbausteine bot/
├── app/               # Core bot logic
│   ├── bot.py         # Bot and dispatcher initialization
│   ├── handlers/      # Command/message handlers
│   ├── db/            # Database models and session
│   ├── keyboards/     # Inline/Reply keyboards
│   ├── services/      # Business logic
├── main.py            # Entry point
├── tests/             # Unit/integration tests
├── .env               # Environment variables
├── requirements.txt   # Dependencies
```

---

## 📈 Current vs Planned

### ✅ Completed
- Telegram bot core functionality with `aiogram`
- Command handling and routing (users, editors)
- Inline keyboards for settings and interactions
- SQLAlchemy integration for persistent storage
- User statistics tracking and presentation
- Category-based task management

### 🛠 Planned
- Multilingual UI support (e.g., English interface)
- Admin panel to manage tasks dynamically
- Statistics dashboard (possibly web-based)
- Docker support for easier deployment
- More advanced unit and integration tests

---

## 👤 Author

Created by **Roman Samoilov**  
Telegram Bot: [@Sprachbausteine_bot](https://t.me/Sprachbausteine_bot)
