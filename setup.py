from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    documentation = f.read()

setup(
    name='authease',       # Package name
    version='3.0.1',        # Version of the package
    description='Authease is a lightweight and flexible authentication package for Django, offering essential tools for secure user authentication, including JWT support, with minimal setup required.',
    author='Oluwaseyi Ajayi', 
    author_email='oluwaseyitemitope456@gmail.com',
    url='https://github.com/Oluwatemmy/authease',  # URL to the GitHub repo
    packages=find_packages(exclude=['*.tests', '*.tests.*']),
    include_package_data=True,          # Include other files like migrations
    install_requires=[
        'Django>=5.0.6',
        'djangorestframework>=3.15.1',
        'djangorestframework-simplejwt>=5.3.1',
        'google-api-python-client>=2.136.0',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Framework :: Django',
        'Development Status :: 3 - Alpha',
    ],
    long_description=documentation,
    long_description_content_type='text/markdown',
    python_requires='>=3.6',        # Python version compatibility

    project_urls={                   # Optional: additional URLs
        'Documentation': 'https://github.com/Oluwatemmy/authease#readme',
        'Source': 'https://github.com/Oluwatemmy/authease',
        'Issues': 'https://github.com/Oluwatemmy/authease/issues',
    },
)
