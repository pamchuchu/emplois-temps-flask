from app import db, Timeslot, Class, Room, Subject, User
# create tables and add sample data
db.create_all()

if not Timeslot.query.first():
    times = [
        (1,"07:00","08:00","1ere séance"),
        (1,"08:00","09:00","2e séance"),
        (1,"09:15","10:15","3e séance"),
        (1,"10:15","11:15","4e séance"),
        (1,"11:30","12:30","5e séance"),
        (2,"07:00","08:00","1ere séance"),
        (3,"07:00","08:00","1ere séance"),
        (4,"07:00","08:00","1ere séance"),
        (5,"07:00","08:00","1ere séance"),
        (6,"07:00","08:00","1ere séance"),
    ]
    for d,s,e,l in times:
        db.session.add(Timeslot(day_of_week=d,start_time=s,end_time=e,label=l))
if not Class.query.first():
    db.session.add(Class(name='Tle D', level='Terminale', capacity=30))
    db.session.add(Class(name='Première C', level='Première', capacity=30))
if not Room.query.first():
    db.session.add(Room(name='Salle A', capacity=40))
    db.session.add(Room(name='Salle B', capacity=30))
if not Subject.query.first():
    db.session.add(Subject(name='Maths'))
    db.session.add(Subject(name='Physique'))
    db.session.add(Subject(name='Informatique'))
if not User.query.first():
    u=User(email='admin@example.com', full_name='Admin', role='admin')
    u.set_password('password123')
    db.session.add(u)
    u2=User(email='prof1@example.com', full_name='Prof 1', role='teacher')
    u2.set_password('password123')
    db.session.add(u2)
db.session.commit()
print('DB initialized with sample data.')
