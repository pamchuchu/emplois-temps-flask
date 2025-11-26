\
    import os
    from flask import Flask, render_template, request, jsonify
    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy.exc import IntegrityError
    from dotenv import load_dotenv
    from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
    from werkzeug.security import generate_password_hash, check_password_hash
    from flask_cors import CORS

    load_dotenv()

    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret')

    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

    CORS(app)
    db = SQLAlchemy(app)
    jwt = JWTManager(app)

    # Models
    class User(db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String, unique=True, nullable=False)
        full_name = db.Column(db.String, nullable=False)
        role = db.Column(db.String, default='teacher')
        phone = db.Column(db.String)
        password_hash = db.Column(db.String)

        def set_password(self, pwd):
            self.password_hash = generate_password_hash(pwd)

        def check_password(self, pwd):
            return check_password_hash(self.password_hash, pwd)

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
        day_of_week = db.Column(db.Integer, nullable=False)
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

    # Routes - simple UI
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/admin')
    def admin():
        return render_template('admin.html')

    @app.route('/teacher')
    def teacher_view():
        return render_template('teacher.html')

    # Auth
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        data = request.json or request.form
        email = data.get('email'); full_name = data.get('full_name'); pwd = data.get('password'); role = data.get('role','teacher')
        if not email or not pwd or not full_name:
            return jsonify({'error':'email, full_name and password required'}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({'error':'Email already registered'}), 400
        u = User(email=email, full_name=full_name, role=role)
        u.set_password(pwd)
        db.session.add(u); db.session.commit()
        return jsonify({'id': u.id})

    @app.route('/api/auth/login', methods=['POST'])
    def login():
        data = request.json or request.form
        email = data.get('email'); pwd = data.get('password')
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(pwd):
            return jsonify({'error':'Invalid credentials'}), 401
        token = create_access_token(identity={'id': user.id, 'role': user.role, 'email': user.email})
        return jsonify({'access_token': token, 'user': {'id': user.id, 'email': user.email, 'full_name': user.full_name, 'role': user.role}})

    # CRUD endpoints
    @app.route('/api/classes', methods=['GET','POST'])
    def api_classes():
        if request.method == 'GET':
            data = [dict(id=c.id, name=c.name, level=c.level) for c in Class.query.all()]
            return jsonify(data)
        payload = request.json or request.form
        c = Class(name=payload.get('name'), level=payload.get('level'), capacity=payload.get('capacity'))
        db.session.add(c); db.session.commit()
        return jsonify({'id': c.id})

    @app.route('/api/subjects', methods=['GET','POST'])
    def api_subjects():
        if request.method == 'GET':
            data = [dict(id=s.id, name=s.name) for s in Subject.query.all()]
            return jsonify(data)
        payload = request.json or request.form
        s = Subject(name=payload.get('name'))
        db.session.add(s); db.session.commit()
        return jsonify({'id': s.id})

    @app.route('/api/rooms', methods=['GET','POST'])
    def api_rooms():
        if request.method == 'GET':
            data = [dict(id=r.id, name=r.name, capacity=r.capacity) for r in Room.query.all()]
            return jsonify(data)
        payload = request.json or request.form
        r = Room(name=payload.get('name'), capacity=payload.get('capacity'))
        db.session.add(r); db.session.commit()
        return jsonify({'id': r.id})

    @app.route('/api/timeslots', methods=['GET','POST'])
    def api_timeslots():
        if request.method == 'GET':
            data = [dict(id=t.id, day_of_week=t.day_of_week, start_time=t.start_time, end_time=t.end_time, label=t.label) for t in Timeslot.query.order_by(Timeslot.day_of_week, Timeslot.start_time).all()]
            return jsonify(data)
        payload = request.json or request.form
        t = Timeslot(day_of_week=payload.get('day_of_week'), start_time=payload.get('start_time'), end_time=payload.get('end_time'), label=payload.get('label'))
        db.session.add(t); db.session.commit()
        return jsonify({'id': t.id})

    @app.route('/api/users', methods=['GET','POST'])
    def api_users():
        if request.method == 'GET':
            data = [dict(id=u.id, email=u.email, full_name=u.full_name, role=u.role) for u in User.query.all()]
            return jsonify(data)
        payload = request.json or request.form
        u = User(email=payload.get('email'), full_name=payload.get('full_name'), role=payload.get('role'))
        u.set_password(payload.get('password','password123'))
        db.session.add(u); db.session.commit()
        return jsonify({'id': u.id})

    @app.route('/api/schedule', methods=['GET','POST','DELETE'])
    @jwt_required(optional=True)
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
