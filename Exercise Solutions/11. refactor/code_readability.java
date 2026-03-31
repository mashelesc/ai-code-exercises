import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.regex.Pattern;

/**
 * Manages user registration and retrieval, backed by an in-memory cache
 * and a persistent database connection.
 */
public class UserManager {

    private static final int MIN_USERNAME_LENGTH = 3;
    private static final int MIN_PASSWORD_LENGTH = 8;
    private static final Pattern EMAIL_PATTERN =
        Pattern.compile("^[^@]+@[^@]+\\.[^@]+$");
    private static final String INSERT_USER_SQL =
        "INSERT INTO users (username, password, email) VALUES (?, ?, ?)";

    private final List<User> userCache;
    private final DatabaseConnection databaseConnection;

    public UserManager(DatabaseConnection databaseConnection) {
        this.databaseConnection = databaseConnection;
        this.userCache = new ArrayList<>();
    }

    /**
     * Registers a new user after validating input and checking for duplicates.
     *
     * @param username the desired username (minimum 3 characters)
     * @param password the desired password (minimum 8 characters)
     * @param email    a valid email address
     * @return true if registration succeeded, false if validation failed,
     *         the username is already taken, or the database insert failed
     */
    public boolean registerUser(String username, String password, String email) {
        if (!isValidUsername(username)) return false;
        if (!isValidPassword(password)) return false;
        if (!isValidEmail(email)) return false;
        if (isUsernameTaken(username)) return false;

        User newUser = new User(username, password, email);
        userCache.add(newUser);

        return databaseConnection.execute(INSERT_USER_SQL, username, password, email);
    }

    /**
     * Finds a user by username, checking the in-memory cache first.
     *
     * @param username the username to search for
     * @return an Optional containing the User if found, or empty if not found
     */
    public Optional<User> findUserByUsername(String username) {
        return userCache.stream()
            .filter(user -> user.getUsername().equals(username))
            .findFirst();
    }

    private boolean isValidUsername(String username) {
        return username != null && username.length() >= MIN_USERNAME_LENGTH;
    }

    private boolean isValidPassword(String password) {
        return password != null && password.length() >= MIN_PASSWORD_LENGTH;
    }

    private boolean isValidEmail(String email) {
        return email != null && EMAIL_PATTERN.matcher(email).matches();
    }

    private boolean isUsernameTaken(String username) {
        return userCache.stream()
            .anyMatch(user -> user.getUsername().equals(username));
    }
}

/**
 * Represents a registered user with credentials and contact information.
 */
public class User {

    private final String username;
    private final String password;
    private final String email;

    public User(String username, String password, String email) {
        this.username = username;
        this.password = password;
        this.email = email;
    }

    public String getUsername() { return username; }
    public String getPassword() { return password; }
    public String getEmail()    { return email; }
}