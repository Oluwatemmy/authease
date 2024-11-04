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

To install Authease, use pip:

```bash
pip install authease
```

## Configuration
### 1. Add to Installed Apps

Add **Authease** to your `INSTALLED_APPS` list in your Django `settings.py` file:

```python
INSTALLED_APPS = [
    # Other Django apps
    'authease',
]
```
### 2.Migrate Database

Run the migrations to set up the necessary database tables for **Authease**:
```python
python manage.py migrate
```
### 3. Configure Environment Variables
**Authease** requires several environment variables for configuration. Add the following variables to your `settings.py` or `.env` file:
```python
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

## Usage
#### Authease provides built-in views for user authentication, including:

- Registration
- Login
- Password Reset
- Google OAuth
- GitHub OAuth

### Example Setup:
#### Using Login View
You can use the built-in login view in your Django templates:
```python
from auth_core.views import LoginUserView

urlpatterns = [
    path('login/', LoginUserView.as_view(), name='login'),
]
```
#### OAuth Integration Example
To enable Google and GitHub OAuth in your application, include their respective views:
```python
from authease.oauth.views import GoogleSignInView, GithubSignInView

urlpatterns = [
    path('auth/google/', GoogleSignInView.as_view(), name='google_auth'),
    path('auth/github/', GithubSignInView.as_view(), name='github_auth'),
]
```

## Advanced Configuration
**Authease** supports the following settings in your `settings.py`:

- `AUTHENTICATION_BACKENDS`: Add custom authentication backends if needed.
- `LOGIN_REDIRECT_URL`: Specify the URL where users are redirected after successful login.
- `LOGOUT_REDIRECT_URL`: Specify the URL where users are redirected after logout.

Example:
```bash
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'
```
Replace `/dashboard/` and `/login/` with the actual url name

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