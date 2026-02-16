from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
import google.generativeai as genai
from werkzeug.utils import secure_filename
from auth import hash_password, verify_password, create_token, get_current_user
from models import db, User, History
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from auth import get_admin_user



load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BACKEND_DIR, '..', 'Frontend'))

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
app.config['SECRET_KEY'] = 'supersecretkey'

# Connection pool setting (for production)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] ={
    'pool_size':10,  #Number of connection tokeep open
    'pool_recycle':3600, #Reccycle connection adter 1 hour
    'pool_pre_ping':True,#Check connecton validitty before using
}

# db = SQLAlchemy(app)


# # =============================================================================
# # MODEL
# # =============================================================================
# class History(db.Model):
#     __tablename__ = "history"

#     id=db.Column(db.Integer,primary_key=True)
#     tool_name=db.Column(db.String(200),nullable=False)
   
#     input_text= db.Column(db.Text)
#     input_img= db.Column(db.String(400))
    
#     output_text=db.Column(db.Text)
#     output_img=db.Column(db.String(400))
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)




# class User(db.Model):
#     __tablename__ = 'users'

#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password_hash = db.Column(db.String(256), nullable=False)
#     is_admin = db.Column(db.Boolean, default=False)

#     history = db.relationship('History', backref='owner', lazy=True)



# ----------------------------
# PATH CONFIG
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(BASE_DIR)

GENERATED_FOLDER = os.path.join(BASE_DIR, "generated")
print("==============================================a")

# --- Add this right below your PATH CONFIG section ---

def get_full_url(filename):
    """Detects if running on localhost or server and builds the full image link"""
    # request.host_url gets 'http://127.0.0.1:5000' or 'http://your-server-ip:5000'
    base_url = request.host_url.rstrip('/')
    return f"{base_url}/generated/{filename}"
# Ensure folder exists
os.makedirs(GENERATED_FOLDER, exist_ok=True)








# ----------------------------
# HEALTH CHECK
# ----------------------------

@app.route('/')
def home():
    return send_from_directory(FRONTEND_DIR, 'Home.html')
print("ddd===============================")


# 2. The Private Dashboard
@app.route('/dashboard')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/login')
def login_page():
    return send_from_directory(FRONTEND_DIR, 'login.html')

@app.route('/register')
def register_page():
    return send_from_directory(FRONTEND_DIR,'register.html')


@app.route('/admin')
def admin_page():
    return send_from_directory(FRONTEND_DIR,'admin.html')

@app.route('/<path:filename>')
def serve_frontend(filename):
    # Serve ANY file from frontend folder
    file_path = os.path.join(FRONTEND_DIR, filename)
    


    if os.path.exists(file_path):
        return send_from_directory(FRONTEND_DIR, filename)

    # Fallback → home page
    return send_from_directory(FRONTEND_DIR, 'home.html')





@app.route("/api/history", methods=["GET"])
def get_history():
    print("=====================ooo")

      # Step 1: Check if user is logged in (validate token)
    current_user, error = get_current_user()
    if error:
        return error  # Returns 401 if token is missing/invalid



    
  
    # Step 2: Get only this user's history
    records = History.query.filter_by(user_id=current_user.id).order_by(History.id.asc()).all()

    return jsonify([
        {
            "id": r.id,
            "tool_name": r.tool_name,
            "input_text": r.input_text,
            "input_img": r.input_img,
            "output_text": r.output_text,
            "output_img": r.output_img,
            "user_id": r.user_id,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None
        }
        for r in records
    ])






# =============================================================================
# AUTH API ROUTES
# =============================================================================

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'All fields required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    new_user = User(
        username=username,
        email=email,
        password_hash=hash_password(password)
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Registration successful!'}), 201



@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_token(user.id, user.is_admin)

    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin
        }
    }), 200





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
    print("=======================ooo=========================")
    prompt = data.get("prompt")
    style = data.get("style", "clean")

    image_path = os.path.join(GENERATED_FOLDER, "test.jpg")

    if not os.path.exists(image_path):
        return jsonify({"error": "test.jpg not found"}), 404

    # Step 1: Check if user is logged in (validate token)
    current_user, error = get_current_user()
    if error:
        return error  # Returns 401 if token is missing/invalid

    
    # Step 3: Save history
    save_history(
        tool_name="prompt_to_image",
        input_text=prompt,
        output_img="test.jpg",
        user_id=current_user.id
    )

    # Step 4: Send response
    return jsonify({
        "success": True,
        "prompt": prompt,
        "style": style,
        "image_url": get_full_url("test.jpg")
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

     # Step 1: Check if user is logged in (validate token)
    current_user, error = get_current_user()
    if error:
        return error  # Returns 401 if token is missing/invalid

    
    
    save_history(
    tool_name="image_to_style",
    input_img=filename,   # ✅ real file
    input_text=prompt,
    output_img="test.jpg",
    user_id=current_user.id
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
    
    # Step 1: Check if user is logged in (validate token)
    current_user, error = get_current_user()
    if error:
        return error  # Returns 401 if token is missing/invalid

    save_history(
    tool_name="specs_tryon",
     input_text=prompt,
    input_img=f"{face_name},{specs_name}",  # ✅ real files
    output_img="test.jpg",
    user_id=current_user.id
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
    
      # Step 1: Check if user is logged in (validate token)
    current_user, error = get_current_user()
    if error:
        return error  # Returns 401 if token is missing/invalid

    save_history(
    tool_name="haircut_preview",
    input_text=prompt,
    input_img=f"{user_name},{sample_name}",  
    output_img="test.jpg",
    user_id=current_user.id

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
    
      # Step 1: Check if user is logged in (validate token)
    current_user, error = get_current_user()
    if error:
        return error  # Returns 401 if token is missing/invalid


    save_history(
    tool_name="insta_story",
    input_text=overlay_text,
    output_img="test.jpg",
    user_id=current_user.id

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

        # Step 1: Check if user is logged in (validate token)
        current_user, error = get_current_user()
        if error:
            return error  # Returns 401 if token is missing/invalid

        save_history(
            tool_name="prompt_enhancer",
            input_text=simple_prompt,
            output_text=enhanced_prompt,
            user_id=current_user.id
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

    # 🔐 AUTH MUST BE FIRST
    current_user, error = get_current_user()
    if error:
        return error

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

    # SAVE INPUT IMAGE
    filename = None
    if image:
        filename = image.filename
        image.save(os.path.join(GENERATED_FOLDER, filename))

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

    save_history(
        tool_name="insta_post",
        input_img=filename,
        input_text=prompt,
        output_text=combined_output,
        output_img="test.jpg",
        user_id=current_user.id
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

            
         # Step 1: Check if user is logged in (validate token)
        current_user, error = get_current_user()
        if error:
            return error  # Returns 401 if token is missing/invalid


           
        save_history(
    tool_name="safety_gear",
    input_text=prompt,
    input_img=filename,
    output_text=advice_text,
    output_img="test.jpg",
    user_id=current_user.id

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
        

              
         # Step 1: Check if user is logged in (validate token)
        current_user, error = get_current_user()
        if error:
            return error  # Returns 401 if token is missing/invalid

        save_history(
    tool_name="story_image",
    input_text=prompt,
    output_img="test.jpg",
    user_id=current_user.id

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


                 
         # Step 1: Check if user is logged in (validate token)
        current_user, error = get_current_user()
        if error:
            return error  # Returns 401 if token is missing/invalid

        # ---------------------------------
        # ALWAYS SAVE HISTORY ✅
        # ---------------------------------
        save_history(
            tool_name="posture_analyzer",
            input_img=filename,
            output_text=suggestions,
            output_img="test.jpg",
            user_id=current_user.id

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


# db.init_app(app)

def init_db():
    with app.app_context():   # ✅ REQUIRED
        from models import User, History
        db.create_all()
        print("✅ Database tables created")


def save_history(*,tool_name, user_id,input_text=None, input_img=None,
                 output_text=None, output_img=None):
    history = History(
        tool_name=tool_name,
        input_text=input_text,
        input_img=input_img,
        output_text=output_text,
        output_img=output_img,
        user_id=user_id
    )
    db.session.add(history)
    db.session.commit()

@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    current_user, error = get_admin_user()
    if error:
        return error

    users = User.query.all()

    result = []
    for user in users:
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "created_at": user.created_at
        })

    return jsonify({"users": result})



@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Step 1: Check if user is admin
    current_user, error = get_admin_user()
    if error:
        return error

    # Step 2: Can't delete yourself
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot delete yourself'}), 400

    # Step 3: Find and delete user
    user = User.query.get_or_404(user_id)
    History.query.filter_by(user_id=user_id).delete()  # Delete user's todos first
    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': f'User {user.username} deleted'})





@app.route('/api/admin/stats', methods=['GET'])
def get_stats():
    current_user, error = get_admin_user()
    if error:
        return error

    total_users = User.query.count()
    total_history = History.query.count()

    # If you don't have a "completed" field, remove this logic
    completed_history = 0

    return jsonify({
        'total_users': total_users,
        'total_history': total_history,
        'completed_history': completed_history,
        'pending_history': total_history - completed_history
    })

@app.route('/api/admin/history', methods=['GET'])
def get_all_history():
    current_user, error = get_admin_user()
    if error:
        return error

    histories = History.query.order_by(History.created_at.asc()).all()
    result = []
    for item in histories:
        user = User.query.get(item.user_id)
        
        
        input_imgs = []
        output_imgs = []

        if item.input_img:
            input_imgs = [img.strip() for img in item.input_img.split(',') if img.strip()]
        if item.output_img:
            output_imgs = [f"/{img.strip()}" for img in item.output_img.split(',') if img.strip()]

        result.append({
            "id": item.id,
            "tool_name": item.tool_name,
            "input_text": item.input_text,
            "input_imgs": input_imgs,   
            "output_text": item.output_text,
            "output_imgs": output_imgs,  
            "created_at": item.created_at.strftime("%m-%d-%Y %H:%M:%S"),
            "username": user.username if user else "Unknown"
        })

    return jsonify({'history': result})
# ----------------------------
# RUN SERVER
# ----------------------------
# if __name__ == "__main__":
#     init_db()  # ✅ create tables before server starts

#     app.run(
#         debug=os.getenv("FLASK_DEBUG", "True") == "True"
#     )

db.init_app(app)

# MOVE THIS OUTSIDE THE __main__ BLOCK
with app.app_context():
    db.create_all()
    print("✅ Database tables verified/created")

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000, # Note: You can keep this 5000 or 8000, just match Nginx
        debug=os.getenv("FLASK_DEBUG", "True") == "True"
    )