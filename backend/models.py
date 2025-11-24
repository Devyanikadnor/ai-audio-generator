from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


# =====================================================
# USER MODEL
# =====================================================

class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)

    credits = db.Column(db.Integer, default=100)

    # ✅ Admin flag (NEW)
    is_admin = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    audio_history = db.relationship("AudioHistory", backref="user", lazy=True)
    payments = db.relationship("Payment", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.email} | Credits: {self.credits} | Admin: {self.is_admin}>"


# =====================================================
# AUDIO HISTORY MODEL
# =====================================================

class AudioHistory(db.Model):
    __tablename__ = "audio_history"

    id = db.Column(db.Integer, primary_key=True)

    text_preview = db.Column(db.String(255), nullable=False)
    audio_filename = db.Column(db.String(255), nullable=False)
    lang = db.Column(db.String(10), default="en")

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"<AudioHistory {self.audio_filename} - {self.lang}>"


# =====================================================
# PAYMENT MODEL
# =====================================================

class Payment(db.Model):
    __tablename__ = "payment"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    plan_id = db.Column(db.String(50), nullable=False)
    plan_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # in rupees
    credits_added = db.Column(db.Integer, nullable=False)

    razorpay_order_id = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100), unique=True)
    razorpay_signature = db.Column(db.Text)

    status = db.Column(db.String(50), default="pending")  # pending / success / failed

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<Payment {self.plan_name} | ₹{self.amount} | "
            f"{self.credits_added} credits | {self.status}>"
        )
