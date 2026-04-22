from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app import db
from app.models.user import User
from app.models.security import SecurityQuestion
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='')

# Default security questions for all users
DEFAULT_SECURITY_QUESTIONS = [
    {"question": "What is your favorite colour?", "answer": "yellow"},
    {"question": "What is your favourite fruit?", "answer": "grapes"},
    {"question": "What is your favourite school subject?", "answer": "math"}
]

# Create default admin user on first run
def create_default_admin():
    """Create default admin user if it doesn't exist"""
    try:
        # Check if user exists
        existing_user = db.session.query(User).filter_by(username='jassal').first()
        
        if not existing_user:
            user = User(username='jassal', email='admin@westernsolutions.com')
            user.set_password('Western@3029')
            db.session.add(user)
            db.session.commit()
            print("Default admin user created: jassal")
            user_id = user.id
        else:
            print("Admin user already exists: jassal")
            user_id = existing_user.id
        
        # Ensure security questions exist for the user
        existing_questions = db.session.query(SecurityQuestion).filter_by(user_id=user_id).count()
        if existing_questions == 0:
            # Add security questions for user
            # Note: Answers are stored in lowercase for case-insensitive comparison
            for q in DEFAULT_SECURITY_QUESTIONS:
                sq = SecurityQuestion(
                    user_id=user_id,
                    question=q["question"],
                    answer=q["answer"].lower() if q["answer"] else ""
                )
                db.session.add(sq)
            db.session.commit()
            print("Security questions created for user: jassal")
        
    except Exception as e:
        print("Error creating default admin: {}".format(str(e)))
        db.session.rollback()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    # Ensure default admin exists
    try:
        create_default_admin()
    except Exception as e:
        print("Error ensuring default admin: {}".format(str(e)))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Create session
            session['user_id'] = user.id
            session['username'] = user.username
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            if request.is_json:
                return jsonify({'success': True, 'message': 'Login successful', 'redirect': '/admin/dashboard'})
            else:
                return redirect(url_for('admin.dashboard'))
        else:
            msg = 'Invalid username or password'
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 401
            else:
                return render_template('login.html', error=msg), 401
    
    return render_template('login.html')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page - verify username first"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            username = data.get('username', '').strip()
            
            if not username:
                return jsonify({'success': False, 'message': 'Username is required'}), 400
            
            # Query for user
            user = User.query.filter_by(username=username).first()
            
            if user:
                # Store username in session for security question verification
                session['reset_username'] = username
                session.permanent = False
                return jsonify({'success': True, 'message': 'Username verified'})
            else:
                return jsonify({'success': False, 'message': 'Username not found'}), 404
        
        except Exception as e:
            print("Error in forgot_password route: {}".format(str(e)))
            return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500
    
    return render_template('forgot_password.html')


@auth_bp.route('/verify-questions', methods=['GET', 'POST'])
def verify_questions():
    """Verify security questions for password reset"""
    if request.method == 'GET':
        # Return the verification page
        username = request.args.get('username', '')
        return render_template('verify_questions.html')
    
    # POST request - verify the answers
    try:
        data = request.get_json()
        username = data.get('username')
        answers = data.get('answers', [])
        
        if not username:
            return jsonify({'success': False, 'message': 'Username is required'}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Get security questions for this user
        questions = SecurityQuestion.query.filter_by(user_id=user.id).all()
        
        if len(questions) == 0:
            return jsonify({'success': False, 'message': 'Security questions not configured'}), 400
        
        if len(answers) != len(questions):
            return jsonify({'success': False, 'message': 'All questions must be answered'}), 400
        
        # Verify answers - compare with stored questions (case-insensitive)
        # All answers are normalized to lowercase for comparison
        all_correct = True
        for i, q in enumerate(questions):
            if i < len(answers):
                # Normalize user input: lowercase and strip whitespace
                provided_answer = answers[i].get('answer', '').lower().strip()
            else:
                provided_answer = ''
                all_correct = False
                break
            
            # Compare normalized answers (database stores answers in lowercase)
            if provided_answer != q.answer.lower().strip():
                all_correct = False
                break
        
        if all_correct:
            # Store verification in session
            session['verified_reset'] = True
            session['reset_user_id'] = user.id
            session.permanent = False
            return jsonify({'success': True, 'message': 'Answers verified', 'token': 'verified'})
        else:
            return jsonify({'success': False, 'message': 'Incorrect answers. Please try again.'}), 401
    
    except Exception as e:
        print("Error in verify_questions route: {}".format(str(e)))
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password after verification"""
    if request.method == 'GET':
        # Return the reset password page
        return render_template('reset_password.html')
    
    # POST request - update password
    if not session.get('verified_reset'):
        return jsonify({'success': False, 'message': 'Please verify security questions first'}), 401
    
    try:
        user_id = session.get('reset_user_id')
        data = request.get_json()
        new_password = data.get('newPassword')
        
        if not new_password:
            return jsonify({'success': False, 'message': 'Password is required'}), 400
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        # Clear session
        session.clear()
        
        return jsonify({'success': True, 'message': 'Password reset successful'})
    
    except Exception as e:
        print("Error in reset_password route: {}".format(str(e)))
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500


@auth_bp.route('/get-security-questions', methods=['POST'])
def get_security_questions():
    """Get security questions for a username"""
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'success': False, 'message': 'Username is required'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    questions = SecurityQuestion.query.filter_by(user_id=user.id).all()
    
    questions_list = [
        {'id': q.id, 'question': q.question}
        for q in questions
    ]
    
    if not questions_list:
        return jsonify({'success': False, 'message': 'No security questions configured'}), 400
    
    return jsonify({'success': True, 'questions': questions_list})


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/', methods=['GET'])
def index():
    """Redirect to dashboard if logged in, otherwise to login"""
    if 'user_id' in session:
        return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('auth.login'))
