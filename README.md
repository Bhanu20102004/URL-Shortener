1.**Setup and running**
    create and activate a virtual environment
    -->python -m venv .venv
    -->.venv\Scripts\activate
    -->pip install -r requirements.txt
    -->python manage.py migrate
    -->python manage.py test
    -->python manage.py runserver 8080


  **Configuration**

All settings are read from environment variables. Each one has a default, so the project runs locally without setting anything.

- **`SECRET_KEY`**: a private key Django uses to sign data.
  Default: `dev-only-insecure-key`. This is only for local use, so set your own in any real deployment.

- **`DEBUG`**: shows detailed error pages when something breaks.
  Default: `True`. Set it to `False` in production.

- **`ALLOWED_HOSTS`**: the website addresses the server will answer to, separated by commas, for example `localhost,127.0.0.1`.
  Default: empty. You must set it when `DEBUG` is `False`.

- **`DATABASE_PATH`**: where the database file is stored.
  Default: `db.sqlite3` in the project folder.

- **`BASE_URL`**: the start of every short link, for example `http://localhost:8080/aZ3kP9`.
  Default: `http://localhost:8080`. It should use the same port as the server.

The port is chosen when you start the server: `python manage.py runserver 8080`.

2.**Language and Framework**

**Language**:Python. I am most comfortable with Python, which let me spend my time on the design of the service (validation, error handling, data modelling) instead of on learning a new language. Its readable syntax also keeps the code easy to review and explain.

**Framework:** Django. I have been learning Django recently, and this project let me apply it to a real problem. Django is a Python web framework that includes many features out of the box, which kept the project small and focused:

- an ORM and a migration system for defining and changing the database schema in Python,
- a built-in test runner,
- URL routing and JsonResponse for building a JSON API,
- built-in security protections, such as protection against SQL injection through the ORM, and CSRF protection.


3.**Generating short codes and Handling collisions**

**How the code is generated**
--->7 characters, picked at random, from letters (a-z, A-Z) and digits (0-9). That's 62 possible characters.

--->It uses Python's secrets module, which gives unpredictable random values, so codes can't be guessed in sequence.

--->Letters and digits are URL-safe, and 7 is within the 6 to 8 characters the brief asks for.

--->The number of possible codes is 62^7, about 3.5 trillion, so collisions are rare.

**How the collisions are handled**
--->Before a code is used, the code checks the database for an existing link with the same code. This is the .exists() check in utils.py.

--->If the code is taken, it generates a new one and checks again, until it finds a free one.

--->The code column also has a unique constraint in the database, so the database will never store two identical codes.

4.**Trade-offs and Assumptions**

**TRADE-OFFS**

--->I used SQLite instead of Postgress or Mysql beacause it is easy to run without setup.The whole database is one file,so anyone can run the project immediately.This is fine for a small servo=ice,but under heavy traffic requests,I would move to Postgress or Mysql

--->A new code every time the same URL is shortened.Each request creates its own short link, even if the URL was shortened before. I chose this because every link has its own expiry date and click statistics, and reusing one code would mix them together. The cost is that the same URL can be stored more than once.

--->Recording each click during the redirect. Every click is saved to the database before the visitor is redirected. I chose this because it keeps the statistics accurate and the code simple. The cost is that each redirect waits for a database write, so it is slightly slower, and a failed write would break the redirect.

**ASSUMPTIONS**
--->Only http and https URLs are valid.
--->A date in expiresAt without a time zone is treated as UTC, and it must be in the future.
--->There is no login, so anyone can create, list or delete any link. The brief doesn't mention authentication.
-->The service runs as one server with low traffic.

5.**Scaling to 1 million redirects a day**

1 million redirects a day is about 12 per second on average, with higher peaks. The first things I would change are:

--->Move from SQLite to postgress or mysql which handles many simultaneous writes.
--->Cache the short code lookups.Right now every redirect asks the database "which URL belongs to this code?". Most visits go to the same popular links, so I would keep recent code-to-URL pairs in a fast in-memory store such as Redis, and only ask the database when the code is not there. This makes redirects faster and takes most of the read load off the database. The cache entry must also respect the link's expiry date and be removed when a link is deleted.
--->Record clicks in the background.Right now the redirect waits for the click to be saved before it sends the visitor on. Instead, I would put each click in a queue (for example with Celery and Redis) and let a separate worker save the clicks in batches. The visitor is redirected immediately, and the clicks are saved a moment later. The cost is that the statistics can be a few seconds behind.

6.**Use of AI tools**

I used ChatGPT (an AI assistant) while working on this project, for:

--->reviewing my code against the assignment requirements,
---> explaining concepts such as environment variables, .gitignore and race conditions,
-->help with a few small code changes and with wording this README.

I wrote the core of the service myself.I went through each change I took from the assistant and I can explain how it works.
