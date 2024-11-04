# Authease

Authease is a lightweight, flexible authentication package for Django applications. It provides essential tools for handling user authentication, including JWT-based authentication, making it easy for developers to integrate into their Django projects without building an authentication system from scratch.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Adding Authease to Django Project](#adding-authease-to-django-project)
  - [Example Setup](#example-setup)
- [API Endpoints](#api-endpoints)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

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
**Authease** requires several environment variables for configuration. Add the following variables to your .env file:
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