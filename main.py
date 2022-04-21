import os

import requests
from flask import Flask, render_template, redirect, url_for, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from data import db_session
from data.posts import Posts
from data.users import User
from forms.posts import PostsForm
from forms.user import RegisterForm, LoginForm
from static.const import SECRET_KEY, API_KEY

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/')
def main_page():
    """Главная страница"""
    return render_template('main_page.html')


@app.route('/authors')
def authors():
    """Страница с информацией об авторах"""
    return render_template('authors.html')


@app.route("/posts")
def posts():
    """Страница с отображением записей ленты"""
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        posts = db_sess.query(Posts).filter(
            (Posts.user == current_user) | (Posts.is_private != True))
    else:
        posts = db_sess.query(Posts).filter(Posts.is_private != True)
    return render_template("index.html", posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html',
                                   title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html',
                                   title='Регистрация',
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
    return render_template('register.html',
                           title='Регистрация',
                           form=form)


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
    return render_template('login.html',
                           title='Авторизация',
                           form=form)


@app.route('/logout')
@login_required
def logout():
    """Выход из Аккаунта и перенаправление на главную страницу"""
    logout_user()
    return redirect("/")


def coords(subject):
    """Функция для страниц с городом и страной.
        Отправляет запрос к геокодеру по названию сущности и возвращает координаты объекта"""
    geocoder_request = f"http://geocode-maps.yandex.ru/1.x/?" \
                       f"apikey={API_KEY}" \
                       f"&geocode={subject}&format=json"
    response = requests.get(geocoder_request)
    if response:
        json_response = response.json()

        if json_response["response"]["GeoObjectCollection"]["featureMember"]:
            """Возвращаем координаты в формате через запятую"""
            toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            toponym_coodrinates = toponym["Point"]["pos"]
            toponym_coodrinates = toponym_coodrinates.replace(' ', ',')
            return toponym_coodrinates
    else:
        """В случае ошибки печатаем сообщение"""
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
        """Если возникла ошибка, то выводим заранее заготовленное фото"""
        print("Ошибка выполнения запроса:")
        print("Http статус:", response.status_code, "(", response.reason, ")")
        return render_template('geo_right.html', obj=city.capitalize(),
                               file_place=f"{url_for('static', filename='pg_files/Paris.png')}")

    else:
        map_file = "static/pg_files/map.png"  # Запишем полученное изображение в файл.
        with open(map_file, "wb") as file:
            file.write(response.content)
        return render_template('geo_right.html', obj=city.capitalize(),
                               file_place=f"{url_for('static', filename='pg_files/map.png')}")


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
        """Если возникла ошибка, то выводим заранее заготовленное фото"""
        print("Ошибка выполнения запроса:")
        print("Http статус:", response.status_code, "(", response.reason, ")")
        return render_template('geo_errors.html', obj=country.capitalize(),
                               file_place=f"{url_for('static', filename='pg_files/Paris.png')}")
    else:
        map_file = "static/pg_files/map.png"  # Запишем полученное изображение в файл.
        with open(map_file, "wb") as file:
            file.write(response.content)
        return render_template('geo_right.html', obj=country.capitalize(),
                               file_place=f"{url_for('static', filename='pg_files/map.png')}")


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
    return render_template('posts.html',
                           title='Добавление публикации',
                           form=form)


# @app.route('/info_users', methods=['GET', 'POST'])
# def get_info_users():

@app.route('/posts/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    form = PostsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        posts = db_sess.query(Posts).filter(Posts.id == id,
                                            Posts.user == current_user
                                            ).first()
        if posts:
            form.title.data = posts.title
            form.content.data = posts.content
            form.is_private.data = posts.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        posts = db_sess.query(Posts).filter(Posts.id == id,
                                            Posts.user == current_user
                                            ).first()
        if posts:
            posts.title = form.title.data
            posts.content = form.content.data
            posts.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/posts')
        else:
            abort(404)
    return render_template('posts.html',
                           title='Редактирование публикации',
                           form=form
                           )


@app.route('/posts_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    posts = db_sess.query(Posts).filter(Posts.id == id,
                                        Posts.user == current_user
                                        ).first()
    if posts:
        db_sess.delete(posts)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/posts')


@app.route('/lk')  # Личный кабинет
def lk():
    """Страница личного кабинета"""
    return render_template('lk.html')


@app.route('/load_photo', methods=['POST', 'GET'])
def load_photo():
    file = url_for('static', filename='img/photo.jpg')
    print(12)
    if request.method == 'GET':
        return f'''<!doctype html>
                        <html lang="en">
                          <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
                            <link rel="stylesheet" type="text/css" href="{url_for('static', filename='css/style.css')}" />
                            <title>Отбор </title>
                          </head>
                          <body>
                            <h1 align="center">Загрузка фотографии</h1>
                            <h3 align="center">для участия в миссии</h3>
                            <div>
                                <form class="login_form" method="post" enctype="multipart/form-data">
                                   <div class="form-group">
                                        <label for="photo">Приложите фотографию</label>
                                        <input type="file" class="form-control-file" id="photo" name="file">
                                    </div>
                                    <img src="{file}" alt="Фото">
                                    <br>
                                    <button type="submit" class="btn btn-primary">Отправить</button>
                                </form>
                            </div>
                          </body>
                        </html>'''
    elif request.method == 'POST':
        f = request.files['file']
        with open(f'static/img/{f.filename}', 'wb') as file:
            file.write(f.read())
        file = url_for('static', filename=f'img/{f.filename}')
        return f'''<!doctype html>
                        <html lang="en">
                          <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
                            <link rel="stylesheet" type="text/css" href="{url_for('static', filename='css/style.css')}" />
                            <title>Отбор </title>
                          </head>
                          <body>
                            <h1 align="center">Загрузка фотографии</h1>
                            <h3 align="center">для участия в миссии</h3>
                            <div>
                                <form class="login_form" method="post" enctype="multipart/form-data">
                                   <div class="form-group">
                                        <label for="photo">Приложите фотографию</label>
                                        <input type="file" class="form-control-file" id="photo" name="file">
                                    </div>
                                    <img src="{file}" alt="Фото">
                                    <br>
                                    <button type="submit" class="btn btn-primary">Отправить</button>
                                </form>
                            </div>
                          </body>
                        </html>'''


if __name__ == '__main__':
    db_session.global_init("db/posts.db")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    # app.run(port=8080, host='127.0.1.1')
