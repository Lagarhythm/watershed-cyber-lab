# Fictional portal lookup: query output grants a session in this toy application.
# The dataset records a separate job-runner action after the session was granted.
def lookup_user(connection, username):
    query = "SELECT username FROM users WHERE username = '" + username + "'"
    return connection.execute(query).fetchall()
