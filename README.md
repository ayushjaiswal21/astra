# Astralearn - AI-Powered Course Generator

Astralearn is a dynamic web application built with Django that leverages AI to automatically generate entire courses, complete with modules and lessons, based on a user-provided topic.

This project uses a dual-AI strategy:
1.  A local Ollama model (`phi3:mini`) is used for the high-level course structure (titles, modules, lesson titles).
2.  The Google Generative AI API (Gemini) is used to generate the detailed content for each individual lesson.

Asynchronous tasks are managed by Celery with a Redis broker to ensure the user experience is fast and non-blocking while the AI works in the background.

## Key Features

- **AI-Powered Course Creation**: Enter any topic and get a full course structure in minutes.
- **Asynchronous Generation**: Uses Celery and Redis to generate course content in the background without tying up the web server.
- **Dual-LLM Strategy**: Utilizes both local and cloud-based LLMs for different tasks.
- **User-Friendly Interface**: Simple and intuitive UI for creating and viewing courses.

## Technology Stack

- **Backend**: Django 5.2
- **Asynchronous Tasks**: Celery 5.5
- **Message Broker**: Redis
- **Database**: PostgreSQL (for production), SQLite (for local development)
- **AI (Structure)**: Ollama (running the `phi3:3.8b-mini-4k-instruct-q4_0` model)
- **AI (Content)**: Google Generative AI (Gemini API)
- **Deployment**: Gunicorn, Whitenoise

---

## Local Development Setup

To run this project locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd astralearn
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Set up Environment Variables:**
    - Create a file named `.env` in the project root.
    - Add the necessary environment variables (see section below).

4.  **Run Database Migrations:**
    ```bash
    python manage.py migrate
    ```

5.  **Ensure Services are Running:**
    - Make sure your local **Redis** server is running.
    - Make sure your local **Ollama** server is running.

6.  **Start the Celery Worker:**
    - In a new terminal, activate the virtual environment and run:
    ```bash
    # On Windows, use the -P solo flag
    celery -A astralearn worker -l info -P solo 
    ```

7.  **Start the Django Development Server:**
    - In another new terminal, activate the virtual environment and run:
    ```bash
    python manage.py runserver
    ```

## Environment Variables

Create a `.env` file in the root directory and add the following:

```
# A strong, random string for Django's security features.
SECRET_KEY='your_django_secret_key_goes_here'

# Set to False in production
DEBUG=True

# Your secret API key from Google AI Studio
GEMINI_API_KEY='your_new_secret_gemini_api_key_goes_here'
```
