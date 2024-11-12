# Authease

Authease is a lightweight, flexible authentication package for Django applications. It provides essential tools for handling user authentication, including JWT-based authentication, making it easy for developers to integrate into their Django projects without building an authentication system from scratch.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Example Setup](#example-setup)
- [Advanced Configuration](#advanced-configuration)
- [Documentation](#documentation)
- [Issues](#issues)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Features

- User registration and login
- Password management (reset, change, and confirmation)
- JWT-based authentication for secure token management
- Easy configuration and integration with Django settings
- Built-in views and serializers to get started immediately

## Requirements

To use Authease, the following packages will be installed in your Django environment:

- Django
- djangorestframework
- python-dotenv
- django-environ
- djangorestframework-simplejwt
- google-api-python-client
- coreapi
- environs
- marshmallow

Note: All necessary dependencies will be installed automatically if not already present.

## Installation

To install Authease, use the following command:

```bash
pip install authease
```

## Configuration
### 1. Add to Installed Apps

Add **Authease** to your `INSTALLED_APPS` list in your Django `settings.py` file:

```python
INSTALLED_APPS = [
    # Other Django apps
    'rest_framework',  # For Django REST Framework
    'authease.authcore',
    'authease.oauth'
]
```
### 2. Update the `AUTH_USER_MODEL` Setting
Authease provides a custom user model that must be set in your Django project. In your `settings.py`, add the following line:
```python
AUTH_USER_MODEL = 'auth_core.User'
```
This step is essential for Authease's authentication functionalities to work properly. Ensure this is configured before running migrations or creating any user-related data in the database.

### 3. Migrate Database

Run the migrations to set up the necessary database tables for **Authease**:
```python
python manage.py migrate
```
### 4. Configure Environment Variables
**Authease** requires several environment variables for configuration. Add the following variables to your `settings.py` or `.env` file:
```python
# Email Settings
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' # Test locally on console
EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend' # For production stage

EMAIL_HOST=<your_email_host>
EMAIL_PORT=<your_email_port>
EMAIL_USE_TLS=True  # Or False depending on your email provider's requirements
EMAIL_HOST_USER=<your_email_host_user>
EMAIL_HOST_PASSWORD=<your_email_host_password>
DEFAULT_FROM_EMAIL=<your_default_from_email>

# For Google OAuth
GOOGLE_CLIENT_ID=<your_google_client_id>
GOOGLE_CLIENT_SECRET=<your_google_client_secret>

# For GitHub OAuth
GITHUB_CLIENT_ID=<your_github_client_id>
GITHUB_CLIENT_SECRET=<your_github_client_secret>

# Django Secret Key
SECRET_KEY=<your_secret_key>
```
Replace `<your_google_client_id>`, `<your_google_client_secret>`, `<your_github_client_id>`, `<your_github_client_secret>`, and `<your_secret_key>` with the actual credentials.

Ensure these values are correctly set to allow account verification and OAuth functionalities in Authease.

## Usage
#### Authease provides built-in views for user authentication, including:

- Registration
- Login
- Password Reset
- Google OAuth
- GitHub OAuth

### Example Setup:
### 1. Include the Auth Routes
Add the following URL patterns to your main `urls.py` to enable Authease’s authentication routes in your project:
```python
from django.urls import path, include

urlpatterns = [
    # Other URL patterns for your project
    path('auth/', include('auth_core.urls')),  # Authease authentication routes
    path('oauth/', include('oauth.urls')),  # Authease o-auth routes
]
```
### 2. Using Individual Views
If you want to set up specific routes individually, you can include each view as needed:
- **Register View Example**

  Use Authease's built-in `RegisterUserView` for user login:
  ```python
  from authease.auth_core.views import RegisterUserView

  urlpatterns = [
      path('register/', RegisterUserView.as_view(), name='register'),  # Register a user
  ]
  ```


- #### OAuth Integration Example
  To enable Google and GitHub OAuth in your application, include their respective views:
  ```python
  from authease.oauth.views import GoogleSignInView, GithubSignInView
  
  urlpatterns = [
      path('auth/google/', GoogleSignInView.as_view(), name='google_auth'),
      path('auth/github/', GithubSignInView.as_view(), name='github_auth'),
  ]
  ```

## Advanced Configuration
Also, To enable JWT token-based authentication, configure djangorestframework-simplejwt in your `settings.py`:
```python
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

## Documentation
https://pypi.org/project/authease/#description

## Issues
If you encounter any issues or bugs while using Authease, please check the following before reporting:

1. **Ensure Compatibility:** Verify that you are using compatible versions of Python and Django.
2. **Configuration Review:** Double-check that all necessary environment variables are set up correctly in your `settings.py` and `.env` file.
3. **Check Logs:** Review your server or Django logs for any specific error messages that may indicate missing configurations or dependencies.
4. **Documentation:** Refer to the documentation to ensure that all steps for installation and setup have been followed.

**Reporting Issues**

If the issue persists, please follow these steps to report it:

1. **Search Existing Issues:** First, check if someone has already reported the issue on the [GitHub Issues page](https://github.com/Oluwatemmy/authease/issues).
2. **Open a New Issue:** If no existing issue matches yours, create a new issue providing as much detail as possible. Include:
- A clear title and description.
- Steps to reproduce the issue.
- Expected and actual behavior.
- Any relevant logs or error messages.
3. **Environment Details:** Include your environment details such as OS, Python version, Django version, and any other relevant setup information.

## Contributing
We welcome contributions to Authease! Please fork the repository, create a new branch, and submit a pull request. Be sure to review the contribution guidelines before submitting.

## License
Authease is licensed under the MIT License. See [LICENSE](https://github.com/Oluwatemmy/authease/blob/main/LICENSE) for more information.

## Contact
For questions or feedback, please contact the package author, **Oluwaseyi Ajayi**, at [oluwaseyitemitope456@gmail.com](oluwaseyitemitope456@gmail.com).