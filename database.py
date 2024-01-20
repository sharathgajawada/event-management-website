import sqlite3

# Connect to the database (creates a new database if it doesn't exist)
conn = sqlite3.connect('eve-management.sqlite')

# Create the Users table
conn.execute('''
CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
    password TEXT
);
''')

# Create the Venues table
conn.execute('''
CREATE TABLE Venues (
    venue_id INTEGER PRIMARY KEY,
    club_id INTEGER,
    location TEXT,
    start_time TEXT,
    end_time TEXT,
    date TEXT,
    FOREIGN KEY (club_id) REFERENCES Clubs(club_id)
);
''')

# Create the Clubs table
conn.execute('''
CREATE TABLE Clubs (
    club_id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
    password TEXT,
    description TEXT,
    post_id INTEGER,
    FOREIGN KEY (post_id) REFERENCES Posts(post_id)
);
''')

# Create the Bookings table


# Create the Posts table
conn.execute('''
CREATE TABLE Posts (
    post_id INTEGER PRIMARY KEY,
    club_id INTEGER,
    title TEXT,
    content TEXT,
    date_posted TEXT,
    FOREIGN KEY (club_id) REFERENCES Clubs(club_id)

);
''')

conn.commit()
conn.close()
