@app.route('/api/users/register', methods=['POST'])

def register_user():
    """
    Register a new user account in the system.

    This endpoint handles user registration by accepting user credentials,
    validating input data, checking for existing accounts, and creating a new
    user record in the database. A confirmation token is generated and a
    confirmation email is sent to activate the account (errors in email sending
    do not block registration).

    HTTP Method: POST
    Endpoint: /api/users/register
    Content-Type: application/json

    Request Body:
        {
            "username": str - Unique username (required)
            "email": str - Valid email address (required), will be lowercased
            "password": str - Password, minimum 8 characters (required)
        }

    Response Success (201 Created):
        {
            "message": "User registered successfully",
            "user": {
                "id": int - New user ID
                "username": str - Username
                "email": str - Lowercased email
                "created_at": str - ISO format timestamp
                "role": str - Default role "user"
            }
        }

    Response Errors:
        400 Bad Request:
            - Missing required field: username, email, or password not provided
              {"error": "Missing required field", "message": "<field> is required"}
            - Invalid email format: email does not match standard format
              {"error": "Invalid email", "message": "Please provide a valid email address"}
            - Weak password: password less than 8 characters
              {"error": "Weak password", "message": "Password must be at least 8 characters long"}

        409 Conflict:
            - Username already taken: username exists in database
              {"error": "Username taken", "message": "Username is already in use"}
            - Email already exists: email exists in database
              {"error": "Email exists", "message": "An account with this email already exists"}

        500 Internal Server Error:
            - Database or unexpected errors during registration
              {"error": "Server error", "message": "Failed to register user"}

    Validation Rules:
        - username: Must be unique, no format restrictions
        - email: Must match regex ^[^@]+@[^@]+\.[^@]+$ (basic email format)
                 Stored as lowercase for consistency
        - password: Minimum 8 characters, hashed using password hashing library

    Side Effects:
        - Creates new User record in database
        - Hashes password using industry-standard hashing (pbkdf2)
        - Generates confirmation token for email verification
        - Attempts to send confirmation email (errors logged, non-blocking)
        - Logs registration errors to app logger

    Security Considerations:
        - Password returned in response: NO (excluded from response)
        - Password stored as: Hashed (not plaintext)
        - Email validation: Basic format check only (users must confirm email)
        - Database transaction: Rolled back on any error to maintain consistency

    Examples:
        curl -X POST http://localhost:5000/api/users/register \\
             -H "Content-Type: application/json" \\
             -d '{
                 "username": "john_doe",
                 "email": "john@example.com",
                 "password": "SecurePass123"
             }'

    Notes:
        - Confirmation email sending failures are logged but do not prevent registration
        - Multiple registration attempts with same username/email will fail appropriately
        - User role defaults to "user" on registration
        - created_at timestamp set to UTC time at registration
    """
    data = request.get_json()

    # Validate required fields
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'error': 'Missing required field',
                'message': f'{field} is required'
            }), 400

    # Check if username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({
            'error': 'Username taken',
            'message': 'Username is already in use'
        }), 409

    if User.query.filter_by(email=data['email']).first():
        return jsonify({
            'error': 'Email exists',
            'message': 'An account with this email already exists'
        }), 409

    # Validate email format
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", data['email']):
        return jsonify({
            'error': 'Invalid email',
            'message': 'Please provide a valid email address'
        }), 400

    # Validate password strength
    if len(data['password']) < 8:
        return jsonify({
            'error': 'Weak password',
            'message': 'Password must be at least 8 characters long'
        }), 400

    # Create new user
    try:
        # Hash password
        password_hash = generate_password_hash(data['password'])

        # Create user object
        new_user = User(
            username=data['username'],
            email=data['email'].lower(),
            password_hash=password_hash,
            created_at=datetime.utcnow(),
            role='user'
        )

        # Add user to database
        db.session.add(new_user)
        db.session.commit()

        # Generate confirmation token
        confirmation_token = generate_confirmation_token(new_user.id)

        # Send confirmation email
        try:
            send_confirmation_email(new_user.email, confirmation_token)
        except Exception as e:
            # Log email error but continue
            app.logger.error(f"Failed to send confirmation email: {str(e)}")

        # Create response without password
        user_data = {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'created_at': new_user.created_at.isoformat(),
            'role': new_user.role
        }

        return jsonify({
            'message': 'User registered successfully',
            'user': user_data
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error registering user: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'message': 'Failed to register user'
        }), 500