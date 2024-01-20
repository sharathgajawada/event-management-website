from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'


# Login route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        user_type = authenticate_user(name, email, password)
        if user_type[0] == 'club':
            session['user_type'] = 'club'
            session['username'] = user_type[1]
            session['user_id'] = user_type[2]
            return redirect('/club')
        elif user_type[0] == 'user':
            session['user_type'] = 'user'
            session['username'] = user_type[1]
            session['user_id'] = user_type[2]
            return redirect('/user')
        else:
            error_message = "Invalid credentials. Please try again."
            return render_template('login.html', error_message=error_message)
    return render_template('login.html')


# Club interface route
@app.route('/club')
def club_interface():
    if session.get('user_type') == 'club':
        username = session.get('username')
        user_id = session.get('user_id')
        conn = sqlite3.connect('eve-management.sqlite')
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT p.title, p.content, p.date_posted, v.location, v.start_time, v.end_time, v.date 
               FROM Posts AS p 
               NATURAL JOIN Venues AS v
               WHERE p.club_id = ?''', (user_id,))
        rows = cursor.fetchall()
        return render_template('club_viewposts.html', username=username, rows=rows)


# User interface route
@app.route('/user')
def user_interface():
    if session.get('user_type') == 'user':
        username = session.get('username')
        user_id = session.get('user_id')
        conn = sqlite3.connect('eve-management.sqlite')
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT C.name,p.title, p.content, p.date_posted, v.location, v.start_time, v.end_time, v.date 
               FROM Posts AS p 
               NATURAL JOIN Venues AS v NATURAL JOIN Clubs C where p.club_id=v.club_id AND v.club_id = C.club_id ORDER BY p.date_posted DESC''')
        rows = cursor.fetchall()
        return render_template('user_viewposts.html', username=username, user_id=user_id, rows=rows)
    else:
        return redirect('/')


# Logout route
@app.route('/logout')
def logout():
    session.pop('user_type', None)
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect('/')


def authenticate_user(name, email, password):
    conn = sqlite3.connect('eve-management.sqlite')
    cursor = conn.cursor()
    # Check if the credentials belong to a club
    cursor.execute('SELECT * FROM Clubs WHERE email=? AND password=? AND name=?', (email, password, name))
    club = cursor.fetchone()
    if club:
        return ('club', club[1], club[0])
    # Check if the credentials belong to a user
    cursor.execute('SELECT * FROM Users WHERE email=? AND password=? AND name=?', (email, password, name))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return ('user', user[1], user[0])
    else:
        return None


from datetime import datetime


@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if session.get('user_type') == 'club':
        username = session.get('username')
        user_id = session.get('user_id')
        date_options = ['25/05/2023', '26/05/2023', '27/05/2023', '28/05/2023', '29/05/2023', '30/05/2023']
        MU_options = ['Auditorium', 'Courtyard', 'Convention', 'OAT']
        conn = sqlite3.connect('eve-management.sqlite')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.name, v.location, v.start_time, v.end_time, v.date
            FROM Venues v
            NATURAL JOIN Clubs c
            WHERE v.club_id = c.club_id AND v.date >= current_date
            ORDER BY v.start_time, v.end_time ASC;
        ''')
        allocated = cursor.fetchall()

        if request.method == 'POST':
            # Retrieve data from the request
            title = request.form['title']
            content = request.form['content']
            start_time_hours = int(request.form['start_time_hours'])
            start_time_minutes = int(request.form['start_time_minutes'])
            end_time_hours = int(request.form['end_time_hours'])
            end_time_minutes = int(request.form['end_time_minutes'])
            location = request.form['mu']
            date = request.form['date']

            # Convert hours and minutes to datetime objects
            start_time = datetime.strptime(f"{start_time_hours}:{start_time_minutes}", "%H:%M").time()
            end_time = datetime.strptime(f"{end_time_hours}:{end_time_minutes}", "%H:%M").time()

            # Connect to the database
            conn = sqlite3.connect('eve-management.sqlite')
            cursor = conn.cursor()

            try:
                # Check if the club has already booked on the same day
                cursor.execute('''
                    SELECT COUNT(*)
                    FROM Venues
                    WHERE club_id = ? AND date = ?
                ''', (user_id, date))
                existing_count = cursor.fetchone()[0]

                if existing_count > 0:
                    error_message = "Invalid booking. The club has already booked on the same day."
                    return render_template('club_createpost.html', username=username, date=date_options,
                                           MU=MU_options, allocated=allocated, error_message=error_message)

                # Check if there are any conflicting time slots for the selected venue
                cursor.execute('''
                    SELECT venue_id, start_time, end_time
                    FROM Venues
                    WHERE location = ? AND date = ?
                ''', (location, date))
                existing_venues = cursor.fetchall()

                for row in existing_venues:
                    existing_start_time = datetime.strptime(row[1], "%H:%M").time()
                    existing_end_time = datetime.strptime(row[2], "%H:%M").time()

                    # Compare the start and end times
                    if start_time >= existing_start_time and start_time < existing_end_time:
                        error_message = "Invalid venue. The selected start time conflicts with an existing venue."
                        return render_template('club_createpost.html', username=username, date=date_options,
                                               MU=MU_options, allocated=allocated, error_message=error_message)

                    if end_time > existing_start_time and end_time <= existing_end_time:
                        error_message = "Invalid venue. The selected end time conflicts with an existing venue."
                        return render_template('club_createpost.html', username=username, date=date_options,
                                               MU=MU_options, allocated=allocated, error_message=error_message)

                # Insert data into the Venues table
                cursor.execute('''
                    INSERT INTO Venues (club_id, location, start_time, end_time, date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, location, start_time.strftime("%H:%M"), end_time.strftime("%H:%M"), date))
                venue_id = cursor.lastrowid

                # Insert data into the Posts table
                cursor.execute('''
                    INSERT INTO Posts (club_id, title, content, date_posted, venue_id)
                    VALUES (?, ?, ?, date('now'), ?)
                ''', (user_id, title, content, venue_id))

                # Commit the changes
                conn.commit()

                # Return success message or redirect to a success page
                return redirect('/club')

            except:
                # Handle any errors
                conn.rollback()
                return redirect('/create_post')

            finally:
                # Close the connection
                conn.close()

        else:
            # Render the form with available options
            return render_template('club_createpost.html', username=username, date=date_options, MU=MU_options,
                                   allocated=allocated)


@app.route('/club_profile', methods=['GET', 'POST'])
def profile():
    if session.get('user_type') == 'club':
        username = session.get('username')
        user_id = session.get('user_id')
        conn = sqlite3.connect('eve-management.sqlite')
        cursor = conn.cursor()
        cursor.execute('''
                    SELECT name,email,description
                    FROM Clubs
                    WHERE club_id = ?
                ''', (user_id,))
        rows1 = cursor.fetchone()
        cursor.execute(
            '''SELECT p.title, p.content, p.date_posted, v.location, v.start_time, v.end_time, v.date 
               FROM Posts AS p 
               NATURAL JOIN Venues AS v
               WHERE p.club_id = ?''', (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('club_profile.html', rows1=rows1, username=username, rows=rows)


@app.route('/student_profile')
def stu_profile():
    if session.get('user_type') == 'user':
        username = session.get('username')
        user_id = session.get('user_id')
        conn = sqlite3.connect('eve-management.sqlite')
        cursor = conn.cursor()
        cursor.execute('''SELECT name, email from Users where user_id=? ''', (user_id,))
        rows = cursor.fetchone()

        cursor.close()
    return render_template('user_profile.html', username=username, rows=rows)


if __name__ == '__main__':
    app.run()
