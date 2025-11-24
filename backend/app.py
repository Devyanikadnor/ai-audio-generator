import os
from datetime import datetime
import hmac
import hashlib

import razorpay
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    url_for,
    redirect,
    abort,
    flash,
)
from flask_login import (
    LoginManager,
    login_user,
    current_user,
    logout_user,
    login_required,
)
from flask_bcrypt import Bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from config import get_config
from audio_engine.tts_service import text_to_speech
from models import db, User, AudioHistory, Payment

# =====================================================
# APP SETUP
# =====================================================

config = get_config()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.from_object(config)

db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# Razorpay client (TEST MODE – uses keys from config.py)
razorpay_client = razorpay.Client(
    auth=(app.config["RAZORPAY_KEY_ID"], app.config["RAZORPAY_KEY_SECRET"])
)

# =====================================================
# CONSTANTS
# =====================================================

CREDITS_PER_NEW_USER = 100
CREDITS_PER_AUDIO = 10

PLANS = {
    "starter": {"name": "Starter", "credits": 10000, "price": 299},
    "creator": {"name": "Creator", "credits": 20000, "price": 399},
    "pro": {"name": "Pro", "credits": 30000, "price": 499},
}

AUDIO_DIR = os.path.join(app.root_path, app.config["AUDIO_OUTPUT_DIR"])
os.makedirs(AUDIO_DIR, exist_ok=True)

# Webhook secret from Razorpay dashboard (TEST MODE)
RAZORPAY_WEBHOOK_SECRET = "YOUR_TEST_WEBHOOK_SECRET"

# =====================================================
# USER LOADER
# =====================================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =====================================================
# PASSWORD RESET SYSTEM
# =====================================================

def get_serializer():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"])


def generate_reset_token(user_id):
    return get_serializer().dumps(user_id)


def verify_reset_token(token, max_age=3600):
    try:
        user_id = get_serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    return User.query.get(user_id)


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/")
@login_required
def index():
    history = []

    audios = (
        AudioHistory.query
        .filter_by(user_id=current_user.id)
        .order_by(AudioHistory.timestamp.desc())
        .limit(10)
        .all()
    )

    for a in audios:
        history.append(
            {
                "audio_url": url_for("static", filename=f"audio/{a.audio_filename}"),
                "text_preview": a.text_preview,
                "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M"),
                "lang": a.lang,
            }
        )

    return render_template("index.html", history=history)


# =====================================================
# AUTH ROUTES
# =====================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    error = None

    if request.method == "POST":
        username = request.form.get("username")
        email = (request.form.get("email") or "").lower().strip()
        password = request.form.get("password")

        if not username or not email or not password:
            error = "All fields are required."
        elif User.query.filter(
            (User.username == username) | (User.email == email)
        ).first():
            error = "User already exists"
        else:
            hashed = bcrypt.generate_password_hash(password).decode("utf-8")

            user = User(
                username=username,
                email=email,
                password_hash=hashed,
                credits=CREDITS_PER_NEW_USER,
            )

            db.session.add(user)
            db.session.commit()

            login_user(user)
            return redirect(url_for("index"))

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    error = None

    if request.method == "POST":
        email = (request.form.get("email") or "").lower().strip()
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("index"))
        else:
            error = "Invalid login credentials"

    return render_template("login.html", error=error)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# =====================================================
# FORGOT PASSWORD
# =====================================================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    message = None

    if request.method == "POST":
        email = (request.form.get("email") or "").lower().strip()
        user = User.query.filter_by(email=email).first()

        if user:
            token = generate_reset_token(user.id)
            reset_link = url_for("reset_password", token=token, _external=True)
            # For dev: print in console
            print("RESET LINK (TEST):", reset_link)

        message = "If this email exists, reset instructions were generated."

    return render_template("forgot_password.html", message=message)


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = verify_reset_token(token)

    if not user:
        return render_template("reset_password.html", error="Invalid or expired token.")

    if request.method == "POST":
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if password and password == confirm:
            user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
            db.session.commit()
            return redirect(url_for("login"))

    return render_template("reset_password.html")


# =====================================================
# PRICING + PAYMENT (RAZORPAY TEST MODE)
# =====================================================

@app.route("/pricing")
@login_required
def pricing():
    return render_template(
        "pricing.html",
        plans=PLANS,
        razorpay_key_id=app.config["RAZORPAY_KEY_ID"],
    )


@app.route("/create-order/<plan_id>", methods=["POST"])
@login_required
def create_order(plan_id):
    plan = PLANS.get(plan_id)
    if not plan:
        abort(404)

    amount = plan["price"] * 100  # in paise

    order = razorpay_client.order.create(
        {
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {"user_id": current_user.id, "plan_id": plan_id},
        }
    )

    return jsonify({"order_id": order["id"], "amount": amount})


@app.route("/verify-payment", methods=["POST"])
@login_required
def verify_payment():
    data = request.get_json() or {}

    order_id = data.get("razorpay_order_id")
    payment_id = data.get("razorpay_payment_id")
    signature = data.get("razorpay_signature")
    plan_id = data.get("plan_id")

    if not all([order_id, payment_id, signature, plan_id]):
        return jsonify({"success": False, "message": "Missing details"}), 400

    plan = PLANS.get(plan_id)
    if not plan:
        return jsonify({"success": False, "message": "Invalid plan"}), 400

    # Prevent double-crediting
    existing = Payment.query.filter_by(razorpay_payment_id=payment_id).first()
    if existing:
        return jsonify({"success": False, "message": "Already credited"}), 409

    params_dict = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature,
    }

    try:
        razorpay_client.utility.verify_payment_signature(params_dict)
    except razorpay.errors.SignatureVerificationError:
        return jsonify({"success": False, "message": "Verification failed"}), 400

    # ✅ Add credits
    current_user.credits = (current_user.credits or 0) + plan["credits"]

    # ✅ Save payment record
    payment = Payment(
        user_id=current_user.id,
        plan_id=plan_id,
        plan_name=plan["name"],
        amount=plan["price"],
        credits_added=plan["credits"],
        razorpay_order_id=order_id,
        razorpay_payment_id=payment_id,
        razorpay_signature=signature,
        status="success",
    )

    db.session.add(payment)
    db.session.commit()

    flash(
        f"✅ {plan['name']} activated! {plan['credits']} credits added.",
        "success",
    )

    return jsonify({"success": True, "new_credits": current_user.credits})


# =====================================================
# RAZORPAY WEBHOOK (TEST)
# =====================================================

@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    signature = request.headers.get("X-Razorpay-Signature")
    payload = request.data

    expected_signature = hmac.new(
        bytes(RAZORPAY_WEBHOOK_SECRET, "utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    if signature != expected_signature:
        return jsonify({"error": "Invalid webhook signature"}), 400

    event = request.json

    if event.get("event") == "payment.captured":
        payment_entity = event["payload"]["payment"]["entity"]

        payment_id = payment_entity["id"]
        order_id = payment_entity["order_id"]
        plan_id = payment_entity["notes"].get("plan_id")
        user_id = payment_entity["notes"].get("user_id")

        # Already processed?
        if Payment.query.filter_by(razorpay_payment_id=payment_id).first():
            return jsonify({"message": "Already processed"}), 200

        plan = PLANS.get(plan_id)
        user = User.query.get(user_id)

        if not plan or not user:
            return jsonify({"error": "Invalid data"}), 400

        user.credits = (user.credits or 0) + plan["credits"]

        payment = Payment(
            user_id=user.id,
            plan_id=plan_id,
            plan_name=plan["name"],
            amount=plan["price"],
            credits_added=plan["credits"],
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            status="success",
        )

        db.session.add(payment)
        db.session.commit()

        print("✅ Webhook credited:", user.email)

    return jsonify({"status": "ok"})


# =====================================================
# AUDIO GENERATION (NEW IMPLEMENTATION)
# =====================================================

@app.route("/generate-audio", methods=["POST"])
@login_required
def generate_audio():
    """
    Generate TTS audio, store in history, and deduct credits.
    Works with both JSON and form-encoded requests.
    Returns:
      - audio_url
      - history (last 10 items)
      - remaining_credits
    """

    # Accept both JSON (fetch with application/json) and form (normal POST)
    data = request.get_json(silent=True)
    if not data:
        data = request.form

    text = (data.get("text") or "").strip()
    lang = (data.get("lang") or "en").strip()

    # 1) Basic validation
    if not text:
        return jsonify({"error": "Text is required."}), 400

    if len(text) > app.config["MAX_TEXT_LENGTH"]:
        return jsonify(
            {"error": f"Text too long. Max {app.config['MAX_TEXT_LENGTH']} characters."}
        ), 400

    # 2) Credits check
    if current_user.credits is None:
        current_user.credits = 0  # safety

    if current_user.credits < CREDITS_PER_AUDIO:
        return jsonify(
            {"error": "You have 0 credits left. Please buy a plan from Pricing page."}
        ), 402  # Payment Required

    try:
        # 3) Generate the audio file
        filename = text_to_speech(
            text=text,
            lang=lang,
            output_dir=AUDIO_DIR,  # uses AUDIO_DIR defined above
        )
        audio_url = url_for("static", filename=f"audio/{filename}", _external=False)

        # 4) Create AudioHistory record
        preview = text[:80] + ("..." if len(text) > 80 else "")

        history_entry = AudioHistory(
            text_preview=preview,
            audio_filename=filename,
            lang=lang,
            user_id=current_user.id,
        )

        # 5) Deduct credits
        current_user.credits = (current_user.credits or 0) - CREDITS_PER_AUDIO

        # 6) Commit both history + credits in one transaction
        db.session.add(history_entry)
        db.session.commit()

        # 7) Rebuild last 10 history items for frontend
        history_list = []
        audios = (
            AudioHistory.query.filter_by(user_id=current_user.id)
            .order_by(AudioHistory.timestamp.desc())
            .limit(10)
            .all()
        )

        for a in audios:
            history_list.append(
                {
                    "audio_url": url_for(
                        "static", filename=f"audio/{a.audio_filename}", _external=False
                    ),
                    "text_preview": a.text_preview,
                    "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M"),
                    "lang": a.lang,
                }
            )

        return jsonify(
            {
                "audio_url": audio_url,
                "history": history_list,
                "remaining_credits": current_user.credits,
            }
        )

    except Exception as e:
        print("TTS Error:", e)
        return jsonify({"error": "Failed to generate audio. Please try again."}), 500


# =====================================================
# STATIC PAGES
# =====================================================

@app.route("/about")
@login_required
def about():
    return render_template("about.html")


@app.route("/privacy")
@login_required
def privacy():
    return render_template("privacy.html")


# =====================================================
# ADMIN PAYMENTS PANEL
# =====================================================

@app.route("/admin/payments")
@login_required
def admin_payments():
    if not getattr(current_user, "is_admin", False):
        abort(403)

    payments = Payment.query.order_by(Payment.timestamp.desc()).all()
    return render_template("admin_payments.html", payments=payments)


# =====================================================
# RUN SERVER
# =====================================================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
