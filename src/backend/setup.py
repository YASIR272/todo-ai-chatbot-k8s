from setuptools import setup, find_packages

setup(
    name="todo-backend",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "sqlmodel==0.0.16",
        "pydantic==2.5.0",
        "pydantic-settings==2.1.0",
        "uvicorn==0.24.0",
        "pyjwt==2.8.0",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "python-dotenv==1.0.1",
        "asyncpg==0.29.0",
    ],
)