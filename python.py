from flask import Flask, render_template, request, jsonify
import math
import time
import threading
import pyttsx3

app = Flask(__name__)

# ==================================================
# VOICE SETTINGS
# ==================================================

voice_engine = pyttsx3.init()
voice_lock = threading.Lock()

FEEDBACK_INTERVAL = 10

last_feedback_time = {}
correct_posture = set()


def speak(message):
    """Speak a message using the computer running Flask."""

    def run_voice():
        with voice_lock:
            voice_engine.say(message)
            voice_engine.runAndWait()

    threading.Thread(target=run_voice, daemon=True).start()


# ==================================================
# EXERCISE NAMES
# ==================================================

EXERCISES = [
    "Front Arm Raise",
    "Side Arm Raise",
    "Shoulder Rolls",
    "Neck Stretch",
    "Standing Knee Raise",
    "Seated Leg Extension",
    "Ankle Rotation",
    "Mini Squat",
    "Cat Cow Stretch",
    "Straight Leg Raise"
]


# ==================================================
# EXERCISE INSTRUCTIONS
# ==================================================

INSTRUCTIONS = {
    "Front Arm Raise": [
        "Stand comfortably with your arms by your sides.",
        "Slowly raise both arms in front of you.",
        "Raise only as high as comfortable.",
        "Keep your back straight and avoid shrugging.",
        "Slowly lower your arms."
    ],

    "Side Arm Raise": [
        "Stand upright with your arms by your sides.",
        "Slowly move your arms outward.",
        "Lift them only as high as comfortable.",
        "Keep your shoulders relaxed.",
        "Slowly lower your arms."
    ],

    "Shoulder Rolls": [
        "Sit or stand comfortably.",
        "Relax both shoulders.",
        "Slowly roll your shoulders backward.",
        "Keep your neck relaxed.",
        "Return to a comfortable position."
    ],

    "Neck Stretch": [
        "Sit upright with relaxed shoulders.",
        "Slowly tilt your head to one side.",
        "Stop when you feel a gentle stretch.",
        "Do not force your neck.",
        "Return to the centre and switch sides if comfortable."
    ],

    "Standing Knee Raise": [
        "Stand upright near a stable support.",
        "Slowly lift one knee.",
        "Keep your balance.",
        "Avoid leaning excessively.",
        "Lower your foot and switch sides."
    ],

    "Seated Leg Extension": [
        "Sit securely on a chair.",
        "Slowly straighten one knee.",
        "Keep your upper body upright.",
        "Avoid locking your knee forcefully.",
        "Lower your foot slowly."
    ],

    "Ankle Rotation": [
        "Sit securely in a chair.",
        "Lift one foot slightly if comfortable.",
        "Slowly rotate your ankle.",
        "Use a small, comfortable circle.",
        "Reverse direction and switch feet."
    ],

    "Mini Squat": [
        "Stand with a stable support nearby.",
        "Keep your feet comfortably apart.",
        "Slowly bend your knees a little.",
        "Keep your back comfortable and upright.",
        "Return to standing slowly."
    ],

    "Cat Cow Stretch": [
        "Start on your hands and knees on a comfortable mat.",
        "Slowly round your back upward.",
        "Gently return and arch your back within a comfortable range.",
        "Move slowly without forcing your spine.",
        "Return to a neutral back position."
    ],

    "Straight Leg Raise": [
        "Lie on your back on a comfortable surface.",
        "Bend one knee and keep the other leg straight.",
        "Slowly lift the straight leg a short distance.",
        "Keep the knee straight without locking it forcefully.",
        "Lower the leg slowly."
    ]
}


# ==================================================
# EXERCISE PHOTOS
# ==================================================

EXERCISE_PHOTOS = {
    "Front Arm Raise":
        "https://cdn.vectorstock.com/i/1000v/29/42/man-doing-double-arm-front-raises-to-overhead-vector-48042942.jpg",

    "Side Arm Raise":
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTcd-rvrRZFCAODVRlbMSLwQLBLyItwAgakmiSs7LpK6g&s=10",

    "Shoulder Rolls":
        "https://d5sbbf6usl3xq.cloudfront.net/standing_shoulder_rolls_bent_elbows___yoga.png",

    "Neck Stretch":
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSDkPwFHfJ7kpy0yiyNcibioKujVrBARCgpDMNQ85eAng&s=10",

    "Standing Knee Raise":
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRI64cm-LVYNfp0MjgpQcGa3qMmO6E35fozd4gumgmA_g&s=10",

    "Seated Leg Extension":
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSor0IpNcM-GpvWwwLxqVp2jmBG_9K70uu7d__iz5Aigg&s=10",

    "Ankle Rotation":
        "https://spotebi.com/wp-content/uploads/2015/03/ankle-circles-exercise-illustration.jpg",

    "Mini Squat":
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRAq7EqVf4Uze09bEBC0USMxxWS15Al3qI569BYa725IHFFZX65AhsrJ_M&s=10",

    "Cat Cow Stretch":
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSTFiZU7elEBdh_U4EdR6xAA2L8h1hy3Li9l-jN6jYeR9LncVDDGeTJu1U&s=10",

    "Straight Leg Raise":
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS5CLMguoRA6Jn1lgejwJGhjBfYQ5XTARxD5pknh1TRlQ&s=10"
}


# ==================================================
# ANGLE RULES
# Demonstration ranges, not medical prescriptions.
# ==================================================

ANGLE_RULES = {
    "Front Arm Raise": ("shoulder", 30, 120),
    "Side Arm Raise": ("shoulder", 30, 120),
    "Shoulder Rolls": ("shoulder", 30, 120),
    "Neck Stretch": ("neck", 5, 45),
    "Standing Knee Raise": ("knee", 45, 120),
    "Seated Leg Extension": ("knee", 120, 180),
    "Ankle Rotation": ("ankle", 30, 150),
    "Mini Squat": ("knee", 60, 150),
    "Cat Cow Stretch": None,
    "Straight Leg Raise": ("hip", 10, 60)
}


# ==================================================
# VOICE CORRECTIONS
# ==================================================

VOICE_MESSAGES = {
    "Front Arm Raise": (
        "Raise your arms higher",
        "Lower your arms slightly"
    ),

    "Side Arm Raise": (
        "Raise your arms outward",
        "Lower your arms slightly"
    ),

    "Shoulder Rolls": (
        "Roll your shoulders gently",
        "Reduce your shoulder movement"
    ),

    "Neck Stretch": (
        "Stretch your neck gently",
        "Reduce your neck stretch"
    ),

    "Standing Knee Raise": (
        "Lift your knee higher",
        "Lower your knee slightly"
    ),

    "Seated Leg Extension": (
        "Straighten your leg more",
        "Reduce your leg extension"
    ),

    "Ankle Rotation": (
        "Move your ankle gently",
        "Reduce your ankle movement"
    ),

    "Mini Squat": (
        "Bend your knees a little more",
        "Stand up slightly"
    ),

    "Straight Leg Raise": (
        "Raise your leg a little higher",
        "Lower your leg slightly"
    )
}


# ==================================================
# SESSION DATA
# ==================================================

SESSION = {
    "active": False,
    "exercise": None,
    "duration": 0,
    "started": None
}


def reset_feedback(exercise):
    """Reset feedback when a new session starts."""

    correct_posture.discard(exercise)
    last_feedback_time.pop(exercise, None)


# ==================================================
# HOME PAGE
# ==================================================

@app.route("/")
def home():
    return render_template("index.html")


# ==================================================
# GET EXERCISES
# ==================================================

@app.route("/api/exercises")
def get_exercises():

    return jsonify([
        {
            "name": name,
            "steps": INSTRUCTIONS[name],
            "photo": EXERCISE_PHOTOS[name],
            "angle_detection_available": (
                ANGLE_RULES[name] is not None
            )
        }
        for name in EXERCISES
    ])


# ==================================================
# START SESSION
# ==================================================

@app.route("/api/session/start", methods=["POST"])
def start_session():

    data = request.get_json(silent=True) or {}

    exercise = data.get("exercise")
    duration = data.get("duration", 3)

    if exercise not in EXERCISES:
        return jsonify({
            "error": "Select a valid exercise."
        }), 400

    try:
        duration = int(duration)

        if duration < 1 or duration > 60:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Invalid session duration."
        }), 400

    reset_feedback(exercise)

    SESSION.update({
        "active": True,
        "exercise": exercise,
        "duration": duration,
        "started": time.time()
    })

    return jsonify({
        "success": True,
        "message": "Session started."
    })


# ==================================================
# STOP SESSION
# ==================================================

@app.route("/api/session/stop", methods=["POST"])
def stop_session():

    SESSION.update({
        "active": False,
        "exercise": None,
        "duration": 0,
        "started": None
    })

    return jsonify({
        "success": True,
        "message": "Session stopped."
    })


# ==================================================
# ANGLE DETECTION FEEDBACK AND VOICE
# ==================================================

@app.route("/api/feedback", methods=["POST"])
def feedback():

    data = request.get_json(silent=True) or {}

    exercise = data.get("exercise")
    angle = data.get("angle")

    if exercise not in EXERCISES:
        return jsonify({
            "error": "Invalid exercise."
        }), 400

    if (
        not SESSION["active"]
        or SESSION["exercise"] != exercise
    ):
        return jsonify({
            "error": "Start this exercise session first."
        }), 400

    # Cat Cow requires a movement-specific back detector.
    rule = ANGLE_RULES.get(exercise)

    if rule is None:
        return jsonify({
            "supported": False,
            "correct": False,
            "feedback": (
                "This exercise requires a movement-specific detector."
            ),
            "voice_message": None
        })

    now = time.time()
    message = None

    # --------------------------------------------------
    # PERSON NOT DETECTED
    # JavaScript must send angle=null when no person is seen.
    # --------------------------------------------------

    if angle is None:

        previous = last_feedback_time.get(exercise, 0)

        if now - previous >= FEEDBACK_INTERVAL:

            message = "Please come in front of the camera"

            last_feedback_time[exercise] = now

            # If the exercise was previously marked correct,
            # allow a new correction when the person returns.
            correct_posture.discard(exercise)

            speak(message)

        return jsonify({
            "supported": True,
            "correct": False,
            "feedback": "Person not detected.",
            "voice_message": message
        })

    # --------------------------------------------------
    # VALIDATE ANGLE
    # --------------------------------------------------

    try:
        angle = float(angle)

        if not math.isfinite(angle):
            raise ValueError

    except (TypeError, ValueError):
        return jsonify({
            "error": "A valid angle is required."
        }), 400

    joint, minimum, maximum = rule

    correct = minimum <= angle <= maximum

    # --------------------------------------------------
    # CORRECT ANGLE: SAY GOOD ONCE
    # --------------------------------------------------

    if correct:

        if exercise not in correct_posture:

            message = "Good"

            correct_posture.add(exercise)

            speak(message)

    # --------------------------------------------------
    # INCORRECT ANGLE: WAIT 10 SECONDS
    # --------------------------------------------------

    elif exercise not in correct_posture:

        previous = last_feedback_time.get(exercise, 0)

        if now - previous >= FEEDBACK_INTERVAL:

            low_message, high_message = VOICE_MESSAGES.get(
                exercise,
                (
                    "Increase your movement slightly",
                    "Reduce your movement slightly"
                )
            )

            if angle < minimum:
                message = low_message
            else:
                message = high_message

            last_feedback_time[exercise] = now

            speak(message)

    # --------------------------------------------------
    # RESPONSE TO WEBSITE
    # --------------------------------------------------

    return jsonify({
        "supported": True,
        "exercise": exercise,
        "joint": joint,
        "angle": angle,
        "minimum_angle": minimum,
        "maximum_angle": maximum,
        "correct": correct,
        "feedback": (
            "Good"
            if correct
            else "Adjust your movement according to the guide."
        ),
        "voice_message": message
    })


# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":

    print("Exercises loaded:", len(EXERCISES))
    print("Voice feedback: enabled")
    print("Open: http://127.0.0.1:5000")

    app.run(debug=True, use_reloader=False)