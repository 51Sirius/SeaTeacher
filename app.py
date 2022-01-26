from flask import Flask, render_template, request, redirect, url_for, abort, flash
import os
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from functions.models import Users, db, Lesson
from functions.forms import *
from cfg import *
from flask_migrate import Migrate
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = S_KEY
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size = 16 megaByte
db.init_app(app)
login = LoginManager(app)
login.init_app(app)
migrate = Migrate(app, db)


@login.user_loader
def load_user(id):
    return Users.query.get(int(id))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/')
def index():
    return render_template('index.html', title='MainPage')


@app.errorhandler(403)
def not_found_error(error):
    return render_template('errors/403.html'), 403


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 403


@app.route('/authentication', methods=['GET', 'POST'])
def authentication():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    forms = LoginForm()
    register_form = Registration()
    if forms.validate_on_submit() and register_form.email.data is None:
        nick = forms.username.data
        password = forms.password.data
        user = Users.query.filter_by(username=nick).first()
        user_mail = Users.query.filter_by(email=nick).first()
        if not (user and user.check_password(password)):
            if user_mail and user_mail.check_password(password):
                login_user(user_mail, remember=forms.remember_me)
                return redirect(url_for('roadmap'))
            abort(403)
        login_user(user, remember=forms.remember_me)
        return redirect(url_for('roadmap'))
    elif register_form.validate_on_submit() and register_form.username.data:
        email, name, password = register_form.email.data, register_form.username.data, register_form.password.data
        first_name, second_name = register_form.firstName.data, register_form.secondName.data
        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            abort(400)
        user = Users(username=name, email=email, firstName=first_name, secondName=second_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        user = Users.query.filter_by(username=name).first()
        login_user(user, remember=forms.remember_me)
        return redirect(url_for('roadmap'))
    return render_template('authentication.html', form=forms, reg_form=register_form)


@app.route('/user/<int:user_id>')
def profile(user_id):
    user = Users.query.filter_by(id=user_id).first()
    image = 'images/users/' + user.image_url
    achievements = user.get_achievement_list()
    return render_template('user.html', title=user.username, user=user, url_img=image, achievements_list=achievements)


@app.route('/roadmap')
def roadmap():
    lesson_list = Lesson.query.all()
    return render_template('roadmap.html', title='Roadmap', user=current_user, lessons=lesson_list)


@app.route('/lesson/<int:lesson_id>')
def lesson(lesson_id):
    lessons = Lesson.query.filter_by(id=lesson_id).first()
    if lessons is None:
        return render_template('errors/404.html'), 403
    return render_template('lesson.html', title='Lesson', lesson_format=lessons)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    settings = Settings()
    if settings.is_submitted():
        image, username = settings.image.data, settings.username.data
        if settings.image.validate(Settings):
            filename = secure_filename(image.filename)
            filename = str(current_user.id) + '.' + filename.split('.')[1]
            image.save(os.path.join(
                app.instance_path[0:-9], 'static\\images\\users', filename
            ))
        existing_user = Users.query.filter_by(username=username).first()
        if existing_user:
            flash('Человекс с таким именем уже есть')
        else:
            if username != '':
                current_user.username = username
                db.session.commit()
        return redirect(url_for('roadmap'))
    return render_template('settings.html', title='Settings', form=settings)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if current_user.is_admin:
        return 'You are admin'
    else:
        return render_template('errors/403.html'), 403


if __name__ == '__main__':
    app.run()
