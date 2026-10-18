# Demo Project

A demo Django/Wagtail project for the `wagtail-streamfield-standalone` package.

## Setup and Running

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

From the `demo/` directory:

```bash
pip install -r requirements.txt
```

This installs the parent package in editable mode along with Django and Wagtail.

### 3. Apply database migrations

```bash
python manage.py migrate
```

### 4. Create a superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username, email, and password.

### 5. Start the development server

```bash
python manage.py runserver
```

### 6. Log in to the admin

Open your browser and go to [http://localhost:8000/cms/](http://localhost:8000/cms/) and log in with the superuser credentials you created.

### 7. Try out the StreamField

Go to the root page at [http://localhost:8000/](http://localhost:8000/) to see the StreamField in action.
