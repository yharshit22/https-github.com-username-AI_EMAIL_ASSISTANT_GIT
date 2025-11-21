# AI Email Automation & Reply Assistant

A comprehensive, production-ready web application for intelligent email management using AI-powered sentiment analysis, priority classification, and automated reply generation.

## 🚀 Features

### Core Functionality
- **Email Fetching**: Connect to IMAP servers (Gmail, Outlook, etc.) to fetch emails
- **AI Sentiment Analysis**: Automatically analyze email sentiment (positive, negative, neutral)
- **Priority Classification**: Smart email prioritization using rules and ML techniques
- **AI Reply Generation**: Generate context-aware replies using OpenAI GPT models
- **Email Management**: Complete CRUD operations with advanced filtering and search
- **User Authentication**: Secure login system with session management
- **Responsive Design**: Modern, mobile-friendly interface using Bootstrap 5

### Advanced Features
- **Bulk Operations**: Process multiple emails simultaneously
- **Real-time Analytics**: Dashboard with charts and statistics
- **Attachment Support**: Handle email attachments and metadata
- **Background Processing**: CLI tools for scheduled email fetching
- **API Endpoints**: RESTful API for programmatic access
- **Production Ready**: Deployable to Heroku, Render, Railway, or VPS

## 🛠 Technology Stack

### Backend
- **Python 3.9+** - Programming language
- **Flask 2.3+** - Web framework
- **SQLAlchemy** - ORM and database toolkit
- **Flask-Login** - User authentication
- **Flask-Migrate** - Database migrations
- **Flask-WTF** - Form handling and validation

### AI & Analysis
- **TextBlob** - Sentiment analysis
- **OpenAI API** - GPT models for reply generation
- **NLTK** - Natural language processing
- **Custom Rules Engine** - Priority classification

### Frontend
- **Bootstrap 5** - CSS framework
- **Vanilla JavaScript** - Interactive functionality
- **Chart.js** - Data visualization
- **Bootstrap Icons** - Icon library

### Database
- **SQLite** - Development database
- **PostgreSQL/MySQL** - Production databases (supported)

## 📁 Project Structure

```
ai_email_assistant/
├── app/                          # Main application package
│   ├── __init__.py              # App factory and initialization
│   ├── models.py                # SQLAlchemy models
│   ├── email_client.py          # IMAP/SMTP email handling
│   ├── sentiment.py             # Sentiment analysis module
│   ├── priority.py              # Priority classification
│   ├── ai_reply.py              # AI reply generation
│   ├── auth/                    # Authentication blueprint
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── main/                    # Main application blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── api/                     # API blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── templates/               # Jinja2 templates
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── main/
│   │   └── partials/
│   └── static/                  # Static files
│       ├── css/
│       └── js/
├── migrations/                  # Database migrations
├── logs/                      # Application logs
├── config.py                  # Configuration classes
├── run.py                     # Development server
├── wsgi.py                    # WSGI entry point
├── fetch_emails.py           # CLI email fetching tool
├── Procfile                   # Heroku deployment
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## 🚦 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip (Python package installer)
- Git
- Email account with IMAP/SMTP access
- OpenAI API key (optional, for AI replies)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai_email_assistant
   ```

2. **Create virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Access the application**
   - Open browser to `http://localhost:5000`
   - Register a new account or login
   - Configure email settings in the .env file
   - Click "Fetch Emails" to start processing

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=sqlite:///email_assistant.db
# For production: DATABASE_URL=postgresql://user:password@localhost/dbname

# Email Configuration (Gmail Example)
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USERNAME=your-email@gmail.com
IMAP_PASSWORD=your-app-password

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# AI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Application Settings
AUTO_FETCH_ENABLED=false
FETCH_INTERVAL_MINUTES=30
```

### Email Setup

#### Gmail Configuration
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the app password in IMAP_PASSWORD and SMTP_PASSWORD
4. Enable IMAP in Gmail settings

#### Other Email Providers
- **Outlook**: Use imap-mail.outlook.com and smtp-mail.outlook.com
- **Yahoo**: Use imap.mail.yahoo.com and smtp.mail.yahoo.com
- **Custom**: Configure your provider's IMAP/SMTP settings

## 📊 Usage

### Dashboard
- View email statistics and analytics
- Quick access to high-priority emails
- Charts showing sentiment and priority distribution

### Email Management
- **Filter emails** by priority, sentiment, status, or search
- **Bulk operations** for processing multiple emails
- **Detailed view** with AI analysis and generated replies
- **Reply generation** using AI with manual editing option

### AI Features
- **Sentiment Analysis**: Automatically detects email tone
- **Priority Classification**: Identifies urgent emails
- **Smart Replies**: Generates contextual responses
- **Regeneration**: Create alternative reply options

## 🔧 Development

### Running in Development
```bash
# With debug mode and auto-reload
FLASK_ENV=development python run.py

# Or using Flask command
flask run --debug
```

### Database Migrations
```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Downgrade migration
flask db downgrade
```

### Testing
```bash
# Run with testing configuration
FLASK_ENV=testing python run.py
```

## 🚀 Production Deployment

### Heroku Deployment
1. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```

2. **Set environment variables**
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=your-production-secret
   heroku config:set DATABASE_URL=your-postgres-database-url
   # Add other required environment variables
   ```

3. **Deploy**
   ```bash
   git push heroku main
   ```

4. **Run database migrations**
   ```bash
   heroku run flask db upgrade
   ```

### Railway Deployment
1. Connect your GitHub repository
2. Configure environment variables in Railway dashboard
3. Deploy automatically on push to main branch

### VPS Deployment (DigitalOcean, AWS, etc.)
1. **Setup server**
   ```bash
   # Install Python, pip, virtualenv
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   ```

2. **Deploy application**
   ```bash
   # Clone repository
   git clone <your-repo-url>
   cd ai_email_assistant
   
   # Setup virtual environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Setup environment variables
   cp .env.example .env
   # Edit .env file
   ```

3. **Configure Gunicorn**
   ```bash
   # Create systemd service
   sudo nano /etc/systemd/system/email-assistant.service
   ```

4. **Configure Nginx**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /static {
           alias /path/to/your/app/static;
       }
   }
   ```

## 🔄 Background Tasks

### Scheduled Email Fetching
Use the CLI tool with cron for automated email fetching:

```bash
# Edit crontab
crontab -e

# Add cron job to fetch emails every 15 minutes
*/15 * * * * cd /path/to/ai_email_assistant && python fetch_emails.py --all-users --limit=20

# Or fetch for specific user every hour
0 * * * * cd /path/to/ai_email_assistant && python fetch_emails.py --user-id=1 --limit=50
```

### CLI Usage
```bash
# Fetch emails for all users
python fetch_emails.py --all-users --limit=50 --since-days=7

# Fetch emails for specific user
python fetch_emails.py --user-id=1 --limit=100 --since-days=14

# Run with custom logging
python fetch_emails.py --all-users 2>&1 | tee logs/fetch_$(date +%Y%m%d_%H%M%S).log
```

## 🔒 Security Considerations

### Best Practices
1. **Use environment variables** for sensitive data
2. **Enable HTTPS** in production
3. **Use strong passwords** and 2FA for email accounts
4. **Regular security updates** for dependencies
5. **Limit database access** with proper user permissions
6. **Monitor logs** for suspicious activity

### Email Security
- Use app passwords instead of main email passwords
- Enable 2FA on email accounts
- Regularly rotate email passwords
- Monitor email account for unauthorized access

## 📈 Monitoring & Maintenance

### Logging
- Application logs: `logs/email_assistant.log`
- Email fetch logs: `logs/email_fetcher.log`
- Log rotation configured for production

### Performance Optimization
- Use PostgreSQL for better performance
- Implement caching for frequently accessed data
- Optimize database queries
- Use CDN for static files

### Backup Strategy
- Regular database backups
- Environment variables backup
- Email configuration backup
- Application code backup (Git)

## 🐛 Troubleshooting

### Common Issues

1. **Email Connection Failed**
   - Check IMAP/SMTP settings
   - Verify email credentials
   - Ensure IMAP is enabled
   - Check firewall settings

2. **AI Reply Generation Failed**
   - Verify OpenAI API key
   - Check API quota/limitations
   - Review API logs

3. **Database Connection Error**
   - Check database URL
   - Verify database is running
   - Check user permissions

4. **Deployment Issues**
   - Check environment variables
   - Review application logs
   - Verify database migrations
   - Check server resources

### Debug Mode
Enable debug logging:
```python
# In config.py
LOG_LEVEL = 'DEBUG'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Flask Community** - Excellent web framework
- **OpenAI** - GPT models for AI replies
- **Bootstrap Team** - Great CSS framework
- **TextBlob** - Sentiment analysis library
- **SQLAlchemy** - Database toolkit

## 📞 Support

For support or questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review application logs for specific errors

---

**Built with ❤️ using Python, Flask, and AI**