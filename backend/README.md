@backend

⭐ E. If the project uses uv
Install uv:
pip install uv

Install dependencies:
uv sync

Run:
uv run python main.py

@frontend

npm install --global yarn

@cd frontend/react_sql_app

yarn install

yarn start

yarn dev

yarn build

@Check your frontend package.json → "scripts" section to see available commands.

@alembic for prod deploy

<!--
if any database table changes run below
This:
adds the column
preserves data
works across environments
is repeatable and auditable

Development
if ENV != "production":
    SQLModel.metadata.create_all(engine)

Production
alembic upgrade head  -> run in PS
 -->

alembic revision --autogenerate -m "add email to user"
alembic upgrade head
