# FAQ Management Web Application

## Overview
This web application allows users to view, manage, and translate FAQs dynamically. It includes user authentication (login/register), an admin dashboard, and rich-text editing capabilities.

## Features
- **User Authentication**: Users can log in and register.
- **FAQ Management**: Admins can create, edit, and delete FAQs.
- **Language Translation**: FAQs can be translated dynamically using an integrated translation API.
- **Rich Text Editing**: Uses CKEditor for better formatting of FAQ content.
- **Admin Dashboard**: Allows admins to manage FAQs and users.
- **Caching with Redis**: Redis is used to cache FAQs and store session data for performance optimization.

## Technologies Used
- **Frontend**: HTML, CSS, JavaScript (Bootstrap for UI enhancements)
- **Backend**: Flask (Python)
- **Database**: SQLite / PostgreSQL (based on configuration)
- **Cache & Session Management**: Redis
- **Editor**: CKEditor for FAQ content formatting

## Installation

### Clone the repository:
```sh
git clone https://github.com/Deepak-Menan-R/FAQ-Multilingual.git
```

### Create and activate a virtual environment:
```sh
python -m venv venv
# On macOS/Linux
source venv/bin/activate
# On Windows
venv\Scripts\activate
```

### Install dependencies:
```sh
pip install -r requirements.txt
```

### Set up the database:
```sh
flask db upgrade  # If using Flask-Migrate
```

### Set up Redis (if not already installed):
Install Redis on your system and start the Redis server:
```sh
# On macOS (using Homebrew)
brew install redis
brew services start redis

# On Linux (Ubuntu/Debian)
sudo apt update
sudo apt install redis-server
sudo systemctl start redis

# On Windows (using WSL or Redis for Windows)
wsl --install -d Ubuntu
sudo apt install redis-server
```

### Run the application:
```sh
redis-server
flask run
```
Run both the commands on seperate terminals, for Flask first activate venv

### Open the application in your browser:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

## Usage
- **Home Page**: Displays FAQs with a language translation option.
- **Login/Register**: Users can authenticate to access restricted features.
- **Admin Dashboard**: Allows authorized users to manage FAQs.
- **Edit FAQ Page**: Uses CKEditor to modify FAQ content.

## API Endpoints (if applicable)
- `GET /faqs` - Fetches all FAQs.
- `POST /faqs` - Adds a new FAQ (admin only).
- `PUT /faqs/<id>` - Updates an existing FAQ.
- `DELETE /faqs/<id>` - Deletes an FAQ (admin only).
- `GET /translate?lang=<language>` - Translates FAQs.

## Configuration
- Update `config.py` to modify settings (e.g., database URI, secret keys, Redis configuration).
- Add your API keys for translation services in `.env`.
- Ensure Redis is running for caching to work.

## Assumptions
- Users must register and log in to access admin functionalities.
- Only admins have the rights to create, edit, and delete FAQs.
- The translation feature depends on a third-party API and may require an API key.
- SQLite is used by default, but PostgreSQL is supported if configured.
- The application runs locally on port `5000` unless modified.
- CKEditor is included for formatting but does not support file uploads.
- Redis must be installed and running for caching and session management.

## Contributing
1. Fork the repository.
2. Create a feature branch:  
   ```sh
   git checkout -b feature-name
   ```
3. Commit your changes:  
   ```sh
   git commit -m "Added feature"
   ```
4. Push to your fork:  
   ```sh
   git push origin feature-name
   ```
5. Create a Pull Request.
