import os
from app import app, db
from models import User, AudioHistory, Payment
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLITE_URI = "sqlite:///" + os.path.join(BASE_DIR, "site.db")

# SQLite engine & session (source)
sqlite_engine = create_engine(SQLITE_URI)
SQLiteSession = sessionmaker(bind=sqlite_engine)
sqlite_session = SQLiteSession()


def migrate_users():
    print("Migrating users...")
    sqlite_users = sqlite_session.query(User).all()
    for u in sqlite_users:
        if not User.query.filter_by(email=u.email).first():
            db.session.add(
                User(
                    id=u.id,
                    username=u.username,
                    email=u.email,
                    password_hash=u.password_hash,
                    credits=u.credits,
                    is_admin=u.is_admin,
                    created_at=u.created_at,
                )
            )
    db.session.commit()
    print(f"  -> {len(sqlite_users)} users processed")


def migrate_audio_history():
    print("Migrating audio history...")
    sqlite_hist = sqlite_session.query(AudioHistory).all()
    for h in sqlite_hist:
        if not AudioHistory.query.filter_by(id=h.id).first():
            db.session.add(
                AudioHistory(
                    id=h.id,
                    text_preview=h.text_preview,
                    audio_filename=h.audio_filename,
                    lang=h.lang,
                    timestamp=h.timestamp,
                    user_id=h.user_id,
                )
            )
    db.session.commit()
    print(f"  -> {len(sqlite_hist)} history rows processed")


def migrate_payments():
    print("Migrating payments...")
    sqlite_payments = sqlite_session.query(Payment).all()
    for p in sqlite_payments:
        if not Payment.query.filter_by(id=p.id).first():
            db.session.add(
                Payment(
                    id=p.id,
                    user_id=p.user_id,
                    plan_id=p.plan_id,
                    plan_name=p.plan_name,
                    amount=p.amount,
                    credits_added=p.credits_added,
                    razorpay_order_id=p.razorpay_order_id,
                    razorpay_payment_id=p.razorpay_payment_id,
                    razorpay_signature=p.razorpay_signature,
                    status=p.status,
                    timestamp=p.timestamp,
                )
            )
    db.session.commit()
    print(f"  -> {len(sqlite_payments)} payments processed")


if __name__ == "__main__":
    with app.app_context():
        migrate_users()
        migrate_audio_history()
        migrate_payments()
        print("✅ Migration from SQLite to the configured database complete.")
