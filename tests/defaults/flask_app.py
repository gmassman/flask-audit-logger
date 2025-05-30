import os
from dataclasses import asdict
from typing import Optional

from flask import Flask
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column

from flask_audit_logger import AuditLogger

db_user = os.environ.get("FLASK_AUDIT_LOGGER_TEST_USER", "postgres")
db_password = os.environ.get("FLASK_AUDIT_LOGGER_TEST_PASSWORD", "")
db_name = os.environ.get("FLASK_AUDIT_LOGGER_TEST_DB", "flask_audit_logger_test")
db_conn_str = f"postgresql://{db_user}:{db_password}@localhost/{db_name}"


class Base(MappedAsDataclass, DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()


class User(db.Model, UserMixin):
    __tablename__ = "user"
    __table_args__ = ({"info": {"versioned": {}}},)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    age: Mapped[Optional[int]] = mapped_column(default=None)


class Article(db.Model):
    __tablename__ = "article"
    __table_args__ = ({"info": {"versioned": {}}},)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class DynamicModificationModel(db.Model):
    __tablename__ = "dynamic_modification_model"
    __table_args__ = ({"info": {"versioned": {}}},)

    id: Mapped[int] = mapped_column(primary_key=True)


@login_manager.user_loader
def load_user(id):
    return db.session.get(User, id)


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = db_conn_str
app.config["SQLALCHEMY_ECHO"] = False
app.secret_key = "secret"
app.debug = True

db.init_app(app)
login_manager.init_app(app)

audit_logger = AuditLogger(db)
AuditLogActivity = audit_logger.activity_cls


@app.post("/article")
def create_article():
    article = Article(id=1, name="Down in the west Texas town of El Paso...")
    db.session.add(article)
    db.session.commit()
    return asdict(article)
