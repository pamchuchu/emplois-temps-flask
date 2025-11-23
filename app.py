import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///schedule.db')
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY

db = SQLAlchemy(app)

# Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    full_name = db.Column(db.String, nullable=False)
    role = db.Column(db.String, default='teacher')
    phone = db.Column(db.String)

class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    level = db.Column(db.String)
    capacity = db.Column(db.Integer)

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    capacity = db.Column(db.Integer)

class Timeslot(db.Model):
    __tablename__ = 'timeslots'
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.Integer, nullable=False)  # 1=Mon..6=Sat
    start_time = db.Column(db.String, nullable=False)
    end_time = db.Column(db.String, nullable=False)
    label = db.Column(db.String)

class ScheduleEntry(db.Model):
    __tablename__ = 'schedule_entries'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    timeslot_id = db.Column(db.Integer, db.ForeignKey('timeslots.id'))
    note = db.Column(db.String)

    __table_args__ = (
        db.UniqueConstraint('class_id','timeslot_id', name='u_class_timeslot'),
    )

# Pages
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    classes = Class.query.all()
    timeslots = Timeslot.query.order_by(Timeslot.day_of_week, Timeslot.start_time).all()
    subjects = Subject.query.all()
    rooms = Room.query.all()
    users = User.query.all()
    return render_template('admin.html', classes=classes, timeslots=timeslots, subjects=subjects, rooms=rooms, users=users)

@app.route('/teacher')
def teacher_view():
    return render_template('teacher.html')

# API: classes
@app.route('/api/classes', methods=['GET','POST'])
def api_classes():
    if request.method == 'GET':
        data = [dict(id=c.id, name=c.name, level=c.level) for c in Class.query.all()]
        return jsonify(data)
    payload = request.json or request.form
    c = Class(name=payload.get('name'), level=payload.get('level'), capacity=payload.get('capacity'))
    db.session.add(c); db.session.commit()
    return jsonify({'id': c.id})

# API: schedule CRUD with conflict checks
@app.route('/api/schedule', methods=['GET','POST','DELETE'])
def api_schedule():
    if request.method == 'GET':
        class_id = request.args.get('class_id')
        teacher_id = request.args.get('teacher_id')
        q = ScheduleEntry.query
        if class_id: q = q.filter_by(class_id=class_id)
        if teacher_id: q = q.filter_by(teacher_id=teacher_id)
        entries = []
        for e in q.all():
            entries.append({
                'id': e.id, 'class_id': e.class_id, 'subject_id': e.subject_id,
                'teacher_id': e.teacher_id, 'room_id': e.room_id, 'timeslot_id': e.timeslot_id, 'note': e.note
            })
        return jsonify(entries)
    if request.method == 'DELETE':
        eid = request.args.get('id')
        e = ScheduleEntry.query.get(eid)
        if not e: return jsonify({'error':'not found'}), 404
        db.session.delete(e); db.session.commit()
        return jsonify({'ok':True})
    # POST -> create with conflict checks
    payload = request.json or request.form
    class_id = payload.get('class_id'); timeslot_id = payload.get('timeslot_id')
    teacher_id = payload.get('teacher_id'); room_id = payload.get('room_id')
    if ScheduleEntry.query.filter_by(class_id=class_id, timeslot_id=timeslot_id).first():
        return jsonify({'error':'Conflit: classe déjà occupée'}), 409
    if teacher_id and ScheduleEntry.query.filter_by(teacher_id=teacher_id, timeslot_id=timeslot_id).first():
        return jsonify({'error':'Conflit: enseignant déjà occupé'}), 409
    if room_id and ScheduleEntry.query.filter_by(room_id=room_id, timeslot_id=timeslot_id).first():
        return jsonify({'error':'Conflit: salle déjà occupée'}), 409
    e = ScheduleEntry(class_id=class_id, subject_id=payload.get('subject_id'), teacher_id=teacher_id, room_id=room_id, timeslot_id=timeslot_id, note=payload.get('note'))
    db.session.add(e)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error':'Contrainte unique violée'}), 500
    return jsonify({'id': e.id})

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
