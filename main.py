from flask import Flask, render_template, redirect, url_for
import requests
from data import db_session
from data.posts import Posts
from data.users import User
from forms.user import RegisterForm, LoginForm
import os
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/page')
def page():
    return r"""<!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <link rel="stylesheet"
                  href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta1/dist/css/bootstrap.min.css"
                  integrity="sha384-giJF6kkoqNQ00vy+HMDP7azOuL0xtbfIcaT9wjKHr8RbDVddVHyTfAAsrekwKmP1"
                  crossorigin="anonymous">
            <title>Проект</title>
            </head>
                <body>
                <h1>Доступные страницы:</h1>
                <div class="alert alert-dark" role="alert">
                    \promotion
                </div>
                <div class="alert alert-success" role="alert">
                    \authors
                </div>
                </body>
                </html>"""


# @app.route('/<title>')
# @app.route('/index/<title>')
# def index_base(title):
#     return render_template('base.html', title=title)


@app.route('/authors')
def authors():
    return 'Страница с информацией об авторах'


@app.route("/")
def index():
    db_sess = db_session.create_session()
    posts = db_sess.query(Posts).filter(Posts.is_private != True)
    if current_user.is_authenticated:
        news = db_sess.query(Posts).filter(
            (Posts.user == current_user) | (Posts.is_private != True))
    else:
        news = db_sess.query(Posts).filter(Posts.is_private != True)
    return render_template("index.html", posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/promotion')
def promotion_image():
    return f"""<!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <link rel="stylesheet"
                  href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta1/dist/css/bootstrap.min.css"
                  integrity="sha384-giJF6kkoqNQ00vy+HMDP7azOuL0xtbfIcaT9wjKHr8RbDVddVHyTfAAsrekwKmP1"
                  crossorigin="anonymous">
            <title>Проект</title>
            </head>
                <body>
                <h1>Страница с приминением bootstrap</h1>
                <div class="alert alert-dark" role="alert">
                    Человечество вырастает из детства.
                </div>
                <div class="alert alert-success" role="alert">
                    Человечеству мала одна планета.
                </div>
                </body>
                </html>"""


API_KEY = '40d1649f-0493-4b70-98ba-98533de7710b'


def coords(city):
    geocoder_request = f"http://geocode-maps.yandex.ru/1.x/?apikey={API_KEY}&geocode={city}&format=json"
    response = requests.get(geocoder_request)
    if response:
        json_response = response.json()

        if json_response["response"]["GeoObjectCollection"]["featureMember"]:
            toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            toponym_coodrinates = toponym["Point"]["pos"]
            return toponym_coodrinates.replace(' ', ',')
    else:
        print("Ошибка выполнения запроса:")
        print(geocoder_request)
        print("Http статус:", response.status_code, "(", response.reason, ")")
        return False


@app.route('/ground/<type_map>/<city>')
def image_mars(type_map, city):
    api_server = "http://static-maps.yandex.ru/1.x/"
    params = {
        "ll": coords(city),
        "spn": '0.1,0.1',
        "l": type_map
    }
    response = requests.get(api_server, params=params)
    print(params)
    if not response:
        print("Ошибка выполнения запроса:")
        print("Http статус:", response.status_code, "(", response.reason, ")")
        return f"""<title>Привет, {city.capitalize()}!</title>
                    <h1>Мы не нашли город "{city.capitalize()}", Он существует?<h1>
                    <img src="{url_for('static', filename='pg_files/Paris.png')}" 
                                           alt="здесь должна была быть картинка, но не нашлась">
                                    <h4>Вот Вам Париж вместо "{city.capitalize()}"</h4>"""
    else:
        map_file = "static/pg_files/map.png"  # Запишем полученное изображение в файл.
        with open(map_file, "wb") as file:
            file.write(response.content)
        return f'''<title>Привет, {city.capitalize()}!</title>
                <img src="{url_for('static', filename='pg_files/map.png')}" 
                       alt="здесь должна была быть картинка, но не нашлась">
                <h4>{city.capitalize()}</h4>'''


# @app.route('/lk') # Личный кабинет
# def lk():


if __name__ == '__main__':
    db_session.global_init("db/posts.db")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
