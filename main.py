import os

import requests
from flask import Flask, render_template, redirect, url_for, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from data import db_session
from data.posts import Posts
from data.users import User
from forms.posts import PostsForm
from forms.user import RegisterForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
API_KEY = '40d1649f-0493-4b70-98ba-98533de7710b'
login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/')
def main_page():
    """render_template('main_page.html')?"""
    return render_template('base.html')


@app.route('/authors')
def authors():
    """Страница с информацией об авторах"""
    return render_template('base.html')


@app.route("/posts")
def posts():
    """Страница с отображением записей ленты"""
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
            return redirect("/posts")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    """Выход из Аккаунта и перенаправление на главную страницу"""
    logout_user()
    return redirect("/")


def coords(subject):
    """Функция для страниц с городом и страной.
        Отправляет запрос к геокодеру по названию сущности и возвращает координаты объекта"""
    geocoder_request = f"http://geocode-maps.yandex.ru/1.x/?apikey={API_KEY}&geocode={subject}&format=json"
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
def image_city(type_map, city):
    """Страница вывода карты(спутникового снимка) города по названию"""
    api_server = "http://static-maps.yandex.ru/1.x/"
    params = {
        "ll": coords(city),
        "spn": '0.1,0.1',
        "l": type_map
    }
    response = requests.get(api_server, params=params)
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


@app.route('/country/<type_map>/<country>')
def image_country(type_map, country):
    """Страница вывода карты(спутникового снимка) страны по ее названию"""
    api_server = "http://static-maps.yandex.ru/1.x/"
    params = {
        "ll": coords(country),
        "spn": '0.1,0.1',
        "l": type_map
    }
    response = requests.get(api_server, params=params)
    if not response:
        print("Ошибка выполнения запроса:")
        print("Http статус:", response.status_code, "(", response.reason, ")")
        return f"""<title>Привет, {country.capitalize()}!</title>
                    <h1>Мы не нашли страну "{country.capitalize()}", Она существует?<h1>
                    <img src="{url_for('static', filename='pg_files/Paris.png')}" 
                                           alt="здесь должна была быть картинка, но не нашлась">
                                    <h4>Вот Вам Россия вместо "{country.capitalize()}"</h4>"""
    else:
        map_file = "static/pg_files/map.png"  # Запишем полученное изображение в файл.
        with open(map_file, "wb") as file:
            file.write(response.content)
        return f'''<title>Привет, {country.capitalize()}!</title>
                <img src="{url_for('static', filename='pg_files/map.png')}" 
                       alt="здесь должна была быть картинка, но не нашлась">
                <h4>{country.capitalize()}</h4>'''


@app.route('/add_posts', methods=['GET', 'POST'])
@login_required
def add_posts():
    form = PostsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        posts = Posts()  # Спорный момент
        posts.title = form.title.data
        posts.content = form.content.data
        posts.is_private = form.is_private.data
        current_user.posts.append(posts)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/posts')
    return render_template('posts.html', title='Добавление новости',
                           form=form)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = PostsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(Posts).filter(Posts.id == id,
                                           Posts.user == current_user
                                           ).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(Posts).filter(Posts.id == id,
                                           Posts.user == current_user
                                           ).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/posts')
        else:
            abort(404)
    return render_template('news.html',
                           title='Редактирование новости',
                           form=form
                           )


@app.route('/lk')  # Личный кабинет
def lk():
    """Страница личного кабинета"""
    return 'Страница личного кабинета'


if __name__ == '__main__':
    db_session.global_init("db/posts.db")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
