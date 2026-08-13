from flask import Flask, request, render_template, redirect, flash, url_for
import os
from werkzeug.utils import secure_filename
from cow_classifier import is_cow, predict_cow  # predict_cow should return your results dictionary

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = "secret123"  # Needed for flash messages

# ✅ Ensure uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def upload_file():
    if request.method == "POST":
        # Check file
        if "image" not in request.files:
            flash("No file uploaded!")
            return redirect(url_for("index"))

        file = request.files["image"]
        if file.filename == "":
            flash("No file selected!")
            return redirect(url_for("index"))

        # Save file
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # ✅ Check if it's a cow
            if not is_cow(filepath):
                os.remove(filepath)
                flash("❌ Only cow images are allowed!")
                return redirect(url_for("index"))

            # ✅ Collect cattle details from form (convert to numeric safely)
            try:
                age = float(request.form.get("age", 0))
                body_weight = float(request.form.get("body_weight", 0))
                parity = int(request.form.get("parity", 0))
                historical_milk_yield = float(request.form.get("historical_milk_yield", 0))
            except ValueError:
                flash("❌ Invalid input values!")
                return redirect(url_for("index"))

            # ✅ Run AI prediction (returns dictionary)
            try:
                results = predict_cow(filepath, age, body_weight, parity, historical_milk_yield)
            except Exception as e:
                flash(f"Prediction failed: {e}")
                return redirect(url_for("index"))

            # ✅ Render results page
            return render_template(
                "predict.html",
                image_path=url_for("static", filename="uploads/" + filename),
                age=age,
                body_weight=body_weight,
                parity=parity,
                historical_milk_yield=historical_milk_yield,
                results=results,
            )

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
