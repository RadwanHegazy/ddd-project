from sqlalchemy import create_engine
import os
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get(
	"DATABASE_URL",
	"postgresql://defineduser:definedpassword@localhost:5432/db",
)


engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()