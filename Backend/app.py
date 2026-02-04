from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
import google.generativeai as genai
from flask_sqlalchemy import SQLAlchemy


load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY','fallback-secret-key') #Get from env or use fallback
CORS(app)

# ----------------------------
# PROMPT ENHANCER CONFIG
# ----------------------------

GEMINI_API_KEY = os.getenv("NANOBANANA_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("NANOBANANA_KEY not found in .env file")

genai.configure(api_key=GEMINI_API_KEY)
prompt_model = genai.GenerativeModel("gemini-2.5-flash")


# ======================================================
#  DATABASE CONFIGURATION
# ======================================================
# GET database URL from environment variable 
# Falls back to SQLITE if not set
DATABASE_URL =os.getenv('DATABASE_URL','sqlite:///default.db')
print(DATABASE_URL)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Connection pool setting (for production)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] ={
    'pool_size':10,  #Number of connection tokeep open
    'pool_recycle':3600, #Reccycle connection adter 1 hour
    'pool_pre_ping':True,#Check connecton validitty before using
}

db = SQLAlchemy(app)


# =============================================================================
# MODEL
# =============================================================================
class History(db.Model):
    __tablename__ = "history"

    id=db.Column(db.Integer,primary_key=True)
    tool_name=db.Column(db.String(200),nullable=False)
   
    input_text= db.Column(db.Text)
    input_img= db.Column(db.String(400))
    
    output_text=db.Column(db.Text)
    output_img=db.Column(db.String(400))



# ----------------------------
# PATH CONFIG
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_FOLDER = os.path.join(BASE_DIR, "generated")

# Ensure folder exists
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# ----------------------------
# HEALTH CHECK
# ----------------------------
@app.route("/")
def home():
    return jsonify({"status": "Flask backend running"})






@app.route("/api/history", methods=["GET"])
def get_history():
    records = History.query.order_by(History.id.asc()).all()
    return jsonify([
        {
            "id": r.id,
            "tool_name": r.tool_name,
            "input_text": r.input_text,
            "input_img": r.input_img,
            "output_text": r.output_text,
            "output_img": r.output_img
        }
        for r in records
    ])



# ----------------------------
# SERVE GENERATED IMAGES
# ----------------------------
@app.route("/generated/<path:filename>")
def serve_generated(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

# ======================================================
# EXISTING: PROMPT → IMAGE (KEEP AS IS)
# ======================================================
@app.route("/api/prompt-to-image", methods=["POST"])
def prompt_to_image():

    data = request.json
    prompt = data.get("prompt")
    style = data.get("style", "clean")

    image_path = os.path.join(GENERATED_FOLDER, "test.jpg")

    if not os.path.exists(image_path):
        return jsonify({"error": "test.jpg not found"}), 404
    



    save_history(
    tool_name="prompt_to_image",
    input_text=prompt,
    output_img="test.jpg"
)

    return jsonify({
        "success": True,
        "prompt": prompt,
        "style": style,
        "image_url": "http://127.0.0.1:5000/generated/test.jpg"
    })







# ======================================================
# ✅ NEW: IMAGE → STYLE (FOR YOUR FRONTEND FILE)
# ======================================================
@app.route("/api/image-to-style", methods=["POST"])
def image_to_style():
    """
    TEMPORARY MOCK API
    - Accepts uploaded image
    - Accepts optional prompt
    - Accepts style
    - Returns test.jpg URL
    """

    # 1️⃣ Get uploaded image
    image_file = request.files.get("image")

    # 2️⃣ Get optional fields
    prompt = request.form.get("prompt", "")
    style = request.form.get("style", "cinematic")

    if not image_file:
        return jsonify({"error": "Image file is required"}), 400

    # 3️⃣ TEMP: Ignore uploaded image (for now)
    # Later: you will process it with AI

    test_image_path = os.path.join(GENERATED_FOLDER, "test.jpg")

    if not os.path.exists(test_image_path):
        return jsonify({
            "error": "test.jpg not found",
            "details": "Place test.jpg inside backend/generated folder"
        }), 404
    filename = image_file.filename
    image_file.save(os.path.join(GENERATED_FOLDER, filename))
    
    
    save_history(
    tool_name="image_to_style",
    input_img=filename,   # ✅ real file
    input_text=prompt,
    output_img="test.jpg"
)


    return jsonify({
        "success": True,
        "message": "Image styled successfully (mock)",
        "prompt": prompt,
        "style": style,
        "image_url": "http://127.0.0.1:5000/generated/test.jpg"
    })


# ======================================================
# ✅ NEW: SPECS TRY-ON (MOCK)
# ======================================================
@app.route("/api/specs-tryon", methods=["POST"])
def specs_tryon():
    """
    MOCK SPECS TRY-ON API
    - Requires face image
    - Requires specs image
    - Optional prompt
    - Returns test.jpg
    """

    face_image = request.files.get("face")
    specs_image = request.files.get("specs")
    prompt = request.form.get("prompt", "")

    # 🔴 VALIDATION
    if not face_image or not specs_image:
        return jsonify({
            "success": False,
            "error": "Face image and Specs image are required"
        }), 400

    test_image_path = os.path.join(GENERATED_FOLDER, "test.jpg")

    if not os.path.exists(test_image_path):
        return jsonify({
            "success": False,
            "error": "test.jpg not found in generated folder"
        }), 404
    
    face_image = request.files.get("face")
    specs_image = request.files.get("specs")
    face_name = face_image.filename
    specs_name = specs_image.filename
    
    face_image.save(os.path.join(GENERATED_FOLDER, face_name))
    specs_image.save(os.path.join(GENERATED_FOLDER, specs_name))
    
    
    save_history(
    tool_name="specs_tryon",
     input_text=prompt,
    input_img=f"{face_name},{specs_name}",  # ✅ real files
    output_img="test.jpg"
)


    return jsonify({
        "success": True,
        "message": "Specs try-on successful (mock)",
        "prompt": prompt,
        "image_url": "http://127.0.0.1:5000/generated/test.jpg"
    })


# ======================================================
# ✅ NEW: HAIRCUT PREVIEW (MOCK)
# ======================================================
@app.route("/api/haircut-preview", methods=["POST"])
def haircut_preview():
    """
    MOCK HAIRCUT PREVIEW API
    - Requires user photo
    - Requires haircut sample image
    - Optional prompt
    - Returns test.jpg
    """

    # 1️⃣ Get uploaded files
    user_image = request.files.get("you")
    sample_image = request.files.get("sample")

    # 2️⃣ Optional prompt
    prompt = request.form.get("prompt", "")

    # 3️⃣ Validation
    if not user_image or not sample_image:
        return jsonify({
            "success": False,
            "error": "Both user image and haircut sample are required"
        }), 400

    # 4️⃣ TEMP MOCK OUTPUT
    test_image_path = os.path.join(GENERATED_FOLDER, "test.jpg")

    if not os.path.exists(test_image_path):
        return jsonify({
            "success": False,
            "error": "test.jpg not found in generated folder"
        }), 404
    
    
    user_name = user_image.filename
    sample_name = sample_image.filename
    user_image.save(os.path.join(GENERATED_FOLDER, user_name))
    sample_image.save(os.path.join(GENERATED_FOLDER, sample_name))
    
    
    save_history(
    tool_name="haircut_preview",
    input_text=prompt,
    input_img=f"{user_name},{sample_name}",  
    output_img="test.jpg"
)



    return jsonify({
        "success": True,
        "message": "Haircut preview generated (mock)",
        "prompt": prompt,
        "image_url": "http://127.0.0.1:5000/generated/test.jpg"
    })


# ======================================================
# ✅ NEW: INSTA STORY TEMPLATE (MOCK)
# ======================================================
@app.route("/api/insta-story-template", methods=["POST"])
def insta_story_template():
    """
    MOCK Insta Story Generator
    - Accepts overlay text
    - Accepts template style
    - Returns test.jpg
    """

    data = request.json
    overlay_text = data.get("overlay_text", "")
    print(overlay_text)
    template = data.get("template", "minimal")
    print(template)
    if not overlay_text:
        return jsonify({
            "success": False,
            "error": "Overlay text is required"
        }), 400
    
    test_image_path = os.path.join(GENERATED_FOLDER, "test.jpg")

    if not os.path.exists(test_image_path):
        return jsonify({
            "success": False,
            "error": "test.jpg not found in generated folder"
        }), 404
    

    save_history(
    tool_name="insta_story",
    input_text=overlay_text,
    output_img="test.jpg"
)


    return jsonify({
        "success": True,
        "message": "Insta story generated (mock)",
        "overlay_text": overlay_text,
        "template": template,
        "image_url": "http://127.0.0.1:5000/generated/test.jpg"
    })



# ======================================================
# ✅ NEW: PROMPT ENHANCER (AI)
# ======================================================
@app.route("/api/enhance-prompt", methods=["POST"])
def enhance_prompt():
    try:
        data = request.get_json()
        simple_prompt = data.get("prompt", "").strip()

        if not simple_prompt:
            return jsonify({
                "success": False,
                "error": "Prompt cannot be empty"
            }), 400

        instruction = f"""
You are an expert prompt engineer for AI image generation models.

Enhance the following simple prompt into a vivid, professional, high-quality image generation prompt.

Include:
- Visual style
- Lighting and mood
- Color palette
- Composition
- Quality keywords (cinematic, ultra-detailed, professional)

Simple prompt:
{simple_prompt}

Respond with ONLY the enhanced prompt.
Limit to 1–2 sentences.
"""

        response = prompt_model.generate_content(instruction)
        enhanced_prompt = response.text.strip()


        save_history(
    tool_name="prompt_enhancer",
    input_text=simple_prompt,
    output_text=enhanced_prompt
)

        return jsonify({
            "success": True,
            "original_prompt": simple_prompt,
            "enhanced_prompt": enhanced_prompt
        })

    except Exception as e:
        print("[ERROR] Prompt Enhancer:", str(e))
        return jsonify({

            "success": False,
            "error": str(e)
        }), 500
    
     
    # ======================================================
# ✅ NEW: INSTA POST GENERATOR (MOCK)
# ======================================================
@app.route("/api/insta-post-generator", methods=["POST"])
def insta_post_generator():

    image = request.files.get("image")
    prompt = request.form.get("prompt", "").strip()

    has_text = bool(prompt)
    has_image = image is not None

    test_image_path = os.path.join(GENERATED_FOLDER, "test.jpg")

    if not os.path.exists(test_image_path):
        return jsonify({
            "success": False,
            "error": "test.jpg not found in generated folder"
        }), 404

    # ✅ SAVE INPUT IMAGE (THIS WAS MISSING)
    filename = None
    if image:
        filename = image.filename
        image.save(os.path.join(GENERATED_FOLDER, filename))

    # ----------------------------
    # OUTPUT LOGIC (KEEP AS IS)
    # ----------------------------
    caption = ""
    hashtags = ""
    tips = "💡 Engage with your audience by asking a question."

    if has_image and not has_text:
        caption = "A peaceful moment captured to inspire calm and clarity."
        hashtags = "#VisualStory #Aesthetic #InstaPost"
        tips = (
            "📸 Use natural light images for better reach\n"
            "⏰ Best time: 7–9 AM\n"
            "💬 Ask a question to boost engagement"
        )
    else:
        caption = (
            "In the quiet of the Himalayas, devotion and peace flow together. "
            "this post reminds us that peace begins within."
        )
        hashtags = "#GanpatiBappa #Faith #InnerPeace"
        tips = "📍 Location-based hashtags help reach more people"

    combined_output = f"""
Caption:
{caption}

Hashtags:
{hashtags}

Tips:
{tips}
"""

    # ✅ SAVE HISTORY CORRECTLY
    save_history(
        tool_name="insta_post",
        input_img=filename,   # ✅ now valid
        input_text=prompt,
        output_text=combined_output,
        output_img="test.jpg"
    )

    return jsonify({
        "success": True,
        "image_url": "http://127.0.0.1:5000/generated/test.jpg",
        "caption": caption,
        "hashtags": hashtags,
        "tips": tips
    })

# ======================================================
# ✅ Safety Gear Try ON
# ======================================================


@app.route("/api/safety-gear", methods=["POST"])
def safety_gear():
    try:
        image_file = request.files.get("image")
        prompt = request.form.get("prompt", "").strip()

        if not image_file:
            return jsonify({"success": False, "error": "Image file is required"}), 400

        if not prompt:
            return jsonify({"success": False, "error": "Prompt is required"}), 400

        test_image_path = os.path.join(GENERATED_FOLDER, "test.jpg")

        if not os.path.exists(test_image_path):
            return jsonify({"success": False, "error": "test.jpg not found"}), 404

        instruction = f"""
You are a helpful assistant.
Suggest commonly used safety gear for the activity below.

Activity: {prompt}

Give 2–3 short lines.
"""
        filename = image_file.filename
        image_file.save(os.path.join(GENERATED_FOLDER, filename))
            

        try:
            response = prompt_model.generate_content(instruction)
            advice_text = response.text.strip()

        except Exception as gemini_error:
            print("⚠ Gemini quota exceeded, using fallback")
            advice_text = (
                "For safety, use a certified helmet, gloves, and protective clothing. "
                "Ensure visibility with reflective gear and follow basic safety precautions."
            )
           
        save_history(
    tool_name="safety_gear",
    input_text=prompt,
    input_img=filename,
    output_text=advice_text,
    output_img="test.jpg"
        )
        
        
        
        return jsonify({
            "success": True,
            "advice": advice_text,
            "image_url": "http://127.0.0.1:5000/generated/test.jpg"
        })

    except Exception as e:
        print("❌ Safety Gear Error:", str(e))
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500




# ======================================================
# ✅ Story Image Generator
# ======================================================

@app.route("/api/story-image-generater", methods=["POST"])
def story_image_generater():
    try:
        data = request.get_json() or {}
        prompt = data.get("prompt", "").strip()

        if not prompt:
            return jsonify({
                "success": False,
                "error": "Prompt is required"
            }), 400

        image_path = os.path.join(GENERATED_FOLDER, "test.jpg")

        if not os.path.exists(image_path):
            return jsonify({
                "success": False,
                "error": "test.jpg not found"
            }), 404
        

        save_history(
    tool_name="story_image",
    input_text=prompt,
    output_img="test.jpg"
)


        return jsonify({
            "success": True,
            "prompt": prompt,
            "image_url": "http://127.0.0.1:5000/generated/test.jpg"
        })

    except Exception as e:
        print("Story Image Generator Error:", e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500






# ======================================================
# ✅ Healthy Posture Analyser
# ======================================================



@app.route("/api/posture-analyze", methods=["POST"])
def posture_analyze():
    try:
        image_file = request.files.get("image")

        if not image_file:
            return jsonify({
                "success": False,
                "error": "Image is required"
            }), 400

        # ---------------------------------
        # TEMP: Always return test.jpg
        # ---------------------------------
        test_image_path = os.path.join(GENERATED_FOLDER, "test.jpg")

        if not os.path.exists(test_image_path):
            return jsonify({
                "success": False,
                "error": "test.jpg not found"
            }), 404

        # ---------------------------------
        # SAVE INPUT IMAGE
        # ---------------------------------
        filename = image_file.filename
        image_file.save(os.path.join(GENERATED_FOLDER, filename))

        # ---------------------------------
        # AI INSTRUCTION
        # ---------------------------------
        instruction = """
You are a posture correction expert.

Analyze the posture and give 3 short improvement tips.
Keep it beginner-friendly.
"""

        # ---------------------------------
        # GEMINI WITH FALLBACK
        # ---------------------------------
        try:
            response = prompt_model.generate_content(instruction)
            suggestions = response.text.strip()

        except Exception as e:
            print("⚠ Gemini quota exceeded:", e)
            suggestions = (
                "• Keep your spine straight and shoulders relaxed\n"
                "• Adjust screen height to eye level\n"
                "• Avoid bending your neck forward for long periods"
            )

        # ---------------------------------
        # ALWAYS SAVE HISTORY ✅
        # ---------------------------------
        save_history(
            tool_name="posture_analyzer",
            input_img=filename,
            output_text=suggestions,
            output_img="test.jpg"
        )

        # ---------------------------------
        # RESPONSE
        # ---------------------------------
        return jsonify({
            "success": True,
            "corrected_image_url": "http://127.0.0.1:5000/generated/test.jpg",
            "suggestions": suggestions,
            "scores": {
                "spine": 80,
                "neck": 45,
                "shoulder": 70
            }
        })

    except Exception as e:
        print("❌ Posture Analyze Error:", e)
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


def init_db():
    with app.app_context():
        db.create_all()
        print(f'Database initialized! Using: {DATABASE_URL}')



def save_history(tool_name, input_text=None, input_img=None,
                 output_text=None, output_img=None):
    history = History(
        tool_name=tool_name,
        input_text=input_text,
        input_img=input_img,
        output_text=output_text,
        output_img=output_img
    )
    db.session.add(history)
    db.session.commit()



# ----------------------------
# RUN SERVER
# ----------------------------
if __name__ == "__main__":
    init_db()  # ✅ create tables before server starts

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=os.getenv("FLASK_DEBUG", "True") == "True"
    )