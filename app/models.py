from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="worker")  # owner | worker

    # Relationships
    tasks = db.relationship(
        "Task",
        backref="assignee",
        lazy=True,
        foreign_keys="Task.assignee_id",
    )
    created_tasks = db.relationship(
        "Task",
        backref="creator",
        lazy=True,
        foreign_keys="Task.created_by_id",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_owner(self) -> bool:
        return self.role == "owner"

    def is_admin(self) -> bool:
        return self.role == "admin"

    def is_manager(self) -> bool:
        return self.role in {"owner", "admin"}


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.String(20), nullable=False, default="todo"
    )  # todo | in_progress | done
    priority = db.Column(db.String(20), nullable=False, default="medium")  # low|medium|high
    due_date = db.Column(db.Date, nullable=True)

    assignee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)

    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])


class TaskCompletionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    requested_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    note = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending|approved|rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    decision_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    decision_note = db.Column(db.Text, nullable=True)
    decision_at = db.Column(db.DateTime, nullable=True)

    task = db.relationship("Task", foreign_keys=[task_id])
    requested_by = db.relationship("User", foreign_keys=[requested_by_id])
    decision_by = db.relationship("User", foreign_keys=[decision_by_id])
