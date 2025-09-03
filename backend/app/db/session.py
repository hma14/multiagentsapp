from sqlmodel import create_engine, Session

#DATABASE_URL = "mssql+pyodbc://@localhost/YourDBName?driver=ODBC+Driver+17+for+SQL+Server"
DATABASE_URL = "mssql+pyodbc://sa:Bilibalabon12345@webserver,1433/MultiAgents?driver=ODBC+Driver+17+for+SQL+Server"


engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
