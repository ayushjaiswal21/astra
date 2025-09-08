# AstraLearn - AI-Powered Learning Platform

AstraLearn is an AI-powered tutoring platform built with Django that provides an interactive learning experience with AI assistance and quizzes.

## Features

- Interactive course content with modules and lessons
- Real-time AI tutor assistant (powered by Ollama)
- Quizzes with automatic scoring
- Progress tracking
- Responsive design for all devices

## Prerequisites

- Python 3.8+
- pip (Python package installer)
- Ollama (for local AI assistant)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd astralearn
   ```

2. **Create and activate a virtual environment**
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (admin) account**
   ```bash
   python manage.py createsuperuser
   ```

6. **Set up environment variables**
   Create a `.env` file in the project root with the following content:
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   ```

## Running the Development Server

1. **Start Ollama**
   Make sure your Ollama server is running. You can start it with:
   ```bash
   ollama serve
   ```

2. **Start the development server**
   ```bash
   python manage.py runserver
   ```

3. **Access the application**
   Open your browser and go to:
   ```
   http://localhost:8000/
   ```

   Access the admin interface at:
   ```
   http://localhost:8000/admin/
   ```

## Project Structure

```
astralearn/
├── astralearn/            # Django project settings
├── tutor/                 # Main app
│   ├── migrations/        # Database migrations
│   ├── templates/         # HTML templates
│   ├── __init__.py
│   ├── admin.py          # Admin interface configuration
│   ├── apps.py           # App configuration
│   ├── models.py         # Database models
│   ├── urls.py          # URL routing
│   └── views.py         # View functions
├── .env                  # Environment variables
├── manage.py            # Django management script
└── requirements.txt     # Python dependencies
```

## Configuration

### Environment Variables

- `DEBUG`: Set to `False` in production
- `SECRET_KEY`: A secret key for cryptographic signing

### Database

By default, the application uses SQLite. For production, consider using PostgreSQL or MySQL by updating the `DATABASES` setting in `settings.py`.

## Deployment

For production deployment, consider using:

1. **Web Server**: Nginx or Apache
2. **ASGI Server**: Gunicorn or Uvicorn
3. **Process Manager**: Systemd, Supervisor, or Circus
4. **Database**: PostgreSQL or MySQL

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Django](https://www.djangoproject.com/)
- AI features powered by [Ollama](https://ollama.com/)
- Frontend built with [Tailwind CSS](https://tailwindcss.com/)
- Icons by [Font Awesome](https://fontawesome.com/)