import sqlite3

conn = sqlite3.connect('eve-management.sqlite')
cursor = conn.cursor()
cursor.execute('''
                            SELECT c.name, v.location, v.start_time, v.end_time, v.date
                            FROM Venues v
                            NATURAL JOIN Clubs c
                            WHERE v.club_id = c.club_id AND v.date >= current_date
                            GROUP BY v.date
                            ORDER BY v.start_time, v.end_time ASC;

                               ''')
allocated = cursor.fetchall()
print(allocated)