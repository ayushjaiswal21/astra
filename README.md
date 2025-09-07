# AstraLearn - AI-Powered Learning Platform

AstraLearn is an AI-powered tutoring platform built with Django and Django Channels that provides an interactive learning experience with AI assistance, quizzes, and spaced repetition.

## Features

- Interactive course content with modules and lessons
- Real-time AI tutor assistant
- Quizzes with automatic scoring
- Spaced repetition for better retention
- Progress tracking
- Responsive design for all devices

## Prerequisites

- Python 3.8+
- pip (Python package installer)
- Redis (for WebSocket support)

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
   GEMINI_API_KEY=your-gemini-api-key
   ```

## Running the Development Server

1. **Start Redis**
   Make sure Redis is running on your system. On most systems, you can start it with:
   ```bash
   # On Linux/macOS
   redis-server
   
   # On Windows (if installed via WSL or similar)
   redis-server
   ```

2. **Start the development server**
   ```bash
   # In one terminal, start the ASGI server
   daphne -p 8000 astralearn.asgi:application
   
   # In another terminal, start the worker
   python manage.py runworker
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
│   ├── consumers.py      # WebSocket consumers
│   ├── models.py         # Database models
│   ├── routing.py        # WebSocket routing
│   ├── signals.py        # Signal handlers
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
- `GEMINI_API_KEY`: API key for Google's Gemini AI (for AI tutor functionality)

### Database

By default, the application uses SQLite. For production, consider using PostgreSQL or MySQL by updating the `DATABASES` setting in `settings.py`.

## Deployment

For production deployment, consider using:

1. **Web Server**: Nginx or Apache
2. **ASGI Server**: Daphne or Uvicorn
3. **Process Manager**: Systemd, Supervisor, or Circus
4. **Database**: PostgreSQL or MySQL
5. **Caching**: Redis or Memcached

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
- Real-time features powered by [Django Channels](https://channels.readthedocs.io/)
- Frontend built with [Tailwind CSS](https://tailwindcss.com/)
- Icons by [Font Awesome](https://fontawesome.com/)
