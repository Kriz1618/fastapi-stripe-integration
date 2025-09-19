# 🚀 FastAPI Stripe Integration

A complete FastAPI application with Stripe integration for subscription management, including webhooks, notifications, and payment processing.

## ✨ Features

- 🔐 **User Authentication** - Registration and login system
- 💳 **Stripe Integration** - Complete payment processing
- 📋 **Subscription Management** - Multiple subscription plans with filtering and sorting
- 🔔 **Webhook Notifications** - Real-time payment updates
- 📱 **Renewal Reminders** - Automatic subscription renewal notifications
- 🗄️ **Database Integration** - SQLite with SQLAlchemy ORM
- 📚 **API Documentation** - Auto-generated with FastAPI
- 🔧 **Development Tools** - Linting, formatting, and development scripts

## 🛠️ Quick Setup

### 1. Clone and Install

```bash
git clone https://github.com/Kriz1618/fastapi-stripe-integration
cd fastapi-stripe-integration
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your Stripe keys
```

### 3. Stripe Configuration

1. Get your keys from [Stripe Dashboard](https://dashboard.stripe.com):

   ```
   STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key
   STRIPE_SECRET_KEY=sk_test_your_secret_key
   ```

2. Create products in Stripe Dashboard and copy the Price IDs:

   ```
   STRIPE_BASIC_PRICE_ID=price_your_basic_price
   STRIPE_PRO_PRICE_ID=price_your_pro_price
   STRIPE_PREMIUM_PRICE_ID=price_your_premium_price
   ```

3. Configure webhook endpoint:
   - URL: `https://your-ngrok-url.ngrok.io/api/stripe/webhook`
   - Events: `checkout.session.completed`, `invoice.payment_succeeded`, `invoice.upcoming`, `customer.subscription.updated`, `customer.subscription.deleted`
   - Copy webhook secret: `STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret`

### 4. Initialize Database

```bash
# Create database tables
python scripts/create_db.py

# Optional: Add sample data for testing
python scripts/seed_data.py
```

### 5. Run the Application

```bash
# Simple start (recommended)
python start.py

# Or directly from scripts
python scripts/run.py
```

## 🔗 API Endpoints

### User Management

- `POST /api/users/register` - User registration
- `POST /api/users/login` - User login
- `GET /api/users` - Get all users (admin)
- `GET /api/users/{user_id}` - Get user by ID
- `PUT /api/users/{user_id}` - Update user information
- `DELETE /api/users/{user_id}` - Deactivate user account

### Stripe Integration

- `POST /api/stripe/create-customer` - Create Stripe customer
- `POST /api/stripe/create-checkout` - Create checkout session
- `GET /api/stripe/plans` - Get available subscription plans
- `GET /api/stripe/user/{user_id}/subscriptions` - Get user subscriptions
- `POST /api/stripe/webhook` - Handle Stripe webhooks

### Subscription Management

- `GET /api/subscriptions` - List all subscriptions with filtering and sorting
  - **Query Parameters:**
    - `status` - Filter by status (active, canceled, incomplete, etc.)
    - `user_id` - Filter by user ID
    - `start_date` - Filter subscriptions created after this date
    - `end_date` - Filter subscriptions created before this date
    - `sort_by` - Sort by field (created_at, updated_at, status, etc.)
    - `sort_order` - Sort order (asc, desc)
    - `page` - Page number for pagination
    - `per_page` - Items per page (max 100)
- `GET /api/subscriptions/{subscription_id}` - Get specific subscription details

### Notifications

- `GET /api/stripe/user/{user_id}/notifications` - Get user notifications
- `PUT /api/stripe/notifications/{notification_id}/read` - Mark notification as read
- `PUT /api/stripe/user/{user_id}/notifications/read-all` - Mark all notifications as read

## 🧪 Testing

### Test Cards (Stripe Test Mode)

| Card Number           | Description        |
| --------------------- | ------------------ |
| `4242 4242 4242 4242` | Successful payment |
| `4000 0000 0000 0002` | Declined payment   |
| `4000 0000 0000 9995` | Insufficient funds |

Use any future expiry date, any 3-digit CVC, and any postal code.

### Test Flow

1. **Register a user:**

   ```bash
   curl -X POST http://localhost:8000/api/users/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password123","full_name":"Test User"}'
   ```

2. **Create Stripe customer:**

   ```bash
   curl -X POST http://localhost:8000/api/stripe/create-customer \
     -H "Content-Type: application/json" \
     -d '{"user_id":1}'
   ```

3. **Create checkout session:**

   ```bash
   curl -X POST http://localhost:8000/api/stripe/create-checkout \
     -H "Content-Type: application/json" \
     -d '{"user_id":1,"plan":"basic"}'
   ```

4. **List subscriptions with filters:**

   ```bash
   # Get all active subscriptions, sorted by creation date
   curl -X GET "http://localhost:8000/api/subscriptions?status=active&sort_by=created_at&sort_order=desc"

   # Get subscriptions for a specific user
   curl -X GET "http://localhost:8000/api/subscriptions?user_id=1"

   # Get subscriptions with pagination
   curl -X GET "http://localhost:8000/api/subscriptions?page=1&per_page=10"
   ```

5. **Complete payment** using the checkout URL and test card

6. **Check notifications:**
   ```bash
   curl -X GET http://localhost:8000/api/stripe/user/1/notifications
   ```

## 📁 Project Structure

```
fastapi-stripe-integration/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   ├── user_api.py        # User management endpoints
│   │   ├── stripe_api.py      # Stripe integration endpoints
│   │   └── subscriptions_api.py # Subscription listing endpoints
│   ├── core/
│   │   ├── config.py          # Configuration settings
│   │   ├── database.py        # Database connection
│   │   └── validators.py      # Input validators
│   ├── models/
│   │   ├── user.py            # User model
│   │   └── subscription.py    # Subscription & Notification models
│   └── services/
│       ├── user_service.py    # User management service
│       └── stripe_service.py  # Stripe service logic
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI pipeline
├── .vscode/
│   └── settings.json          # VS Code configuration
├── data/
│   └── database.db            # SQLite database
├── logs/                      # Application logs
├── scripts/
│   ├── lint.py                # Linting and formatting script
│   ├── setup_git_hooks.py     # Git hooks configuration
│   ├── start.py               # Simple application starter
│   ├── create_db.py           # Database initialization
│   ├── reset_db.py            # Database reset
│   ├── seed_data.py           # Sample data creation
│   └── run_tests.py           # Test runner
├── .env                       # Environment variables
├── .env.example               # Environment template
├── .flake8                    # Flake8 configuration
├── .gitignore                 # Git ignore rules
├── .pre-commit-config.yaml    # Pre-commit hooks configuration
├── pyproject.toml             # Python project configuration
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

| Variable                  | Description            | Example                        |
| ------------------------- | ---------------------- | ------------------------------ |
| `DEBUG`                   | Debug mode             | `True`                         |
| `SECRET_KEY`              | JWT secret key         | `your-secret-key`              |
| `DATABASE_URL`            | Database connection    | `sqlite:///./data/database.db` |
| `STRIPE_PUBLISHABLE_KEY`  | Stripe publishable key | `pk_test_...`                  |
| `STRIPE_SECRET_KEY`       | Stripe secret key      | `sk_test_...`                  |
| `STRIPE_WEBHOOK_SECRET`   | Webhook secret         | `whsec_...`                    |
| `STRIPE_BASIC_PRICE_ID`   | Basic plan price ID    | `price_...`                    |
| `STRIPE_PRO_PRICE_ID`     | Pro plan price ID      | `price_...`                    |
| `STRIPE_PREMIUM_PRICE_ID` | Premium plan price ID  | `price_...`                    |

## 🎯 Webhook Events

The application handles these Stripe webhook events:

- `checkout.session.completed` - Creates subscription in database
- `invoice.payment_succeeded` - Updates subscription status to active
- `invoice.upcoming` - Creates renewal reminder notification
- `customer.subscription.updated` - Updates subscription details
- `customer.subscription.deleted` - Marks subscription as canceled

## 📊 Logging and Monitoring

The application generates structured logs for monitoring subscription events and webhook processing. Logs are stored in the `logs/` directory and include:

- Stripe webhook events
- Payment processing
- Subscription status changes
- User registration and authentication
- API request/response logging

Example log entry:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "event": "SUBSCRIPTION_CREATED",
  "user_id": 123,
  "subscription_id": "sub_xxx",
  "plan": "basic",
  "amount": 9.99
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Webhook signature verification fails**

   - Verify `STRIPE_WEBHOOK_SECRET` is correct
   - Check webhook endpoint URL in Stripe Dashboard

2. **Price IDs not found**

   - Ensure you're using Price IDs (start with `price_`) not Product IDs (`prod_`)
   - Verify Price IDs in your `.env` file

3. **Database errors**
   - Run: `python -c "from app.core.database import engine; from app.models import *; from app.core.database import Base; Base.metadata.create_all(bind=engine)"`

### Debug Mode

Set `DEBUG=True` in `.env` for detailed logging.

## 🛠️ Development Tools

### Available Scripts

| Script                       | Purpose                    | Usage                               |
| ---------------------------- | -------------------------- | ----------------------------------- |
| `scripts/start.py`           | Simple app starter         | `python scripts/start.py`           |
| `scripts/create_db.py`       | Initialize database        | `python scripts/create_db.py`       |
| `scripts/reset_db.py`        | Reset database             | `python scripts/reset_db.py`        |
| `scripts/seed_data.py`       | Add sample data            | `python scripts/seed_data.py`       |
| `scripts/run_tests.py`       | Run tests                  | `python scripts/run_tests.py`       |
| `scripts/lint.py`            | Run linting and formatting | `python scripts/lint.py --fix`      |
| `scripts/setup_git_hooks.py` | Configure git hooks        | `python scripts/setup_git_hooks.py` |

### Linting and Code Quality

The project includes comprehensive code quality tools:

- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Style checking
- **mypy** - Type checking
- **pre-commit** - Git hooks for automated checks

```bash
# Run all linting tools
python scripts/lint.py

# Run with auto-fix
python scripts/lint.py --fix

# Setup git hooks for automatic linting
python scripts/setup_git_hooks.py
```

### GitHub Actions

Automated CI pipeline runs on every push:

- Code linting and formatting checks
- Type checking
- Test execution
- Docker image building

## 🚀 Getting Started (Quick)

For the fastest setup experience:

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your Stripe keys

# 2. Initialize database
python scripts/create_db.py

# 3. Add sample data (optional)
python scripts/seed_data.py

# 4. Start application
python start.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

- Check the application console output for logs
- Verify Stripe keys are correct
- Ensure webhook events are configured in Stripe Dashboard
- Test with Stripe's test cards

---

**Built with ❤️ using FastAPI and Stripe**
