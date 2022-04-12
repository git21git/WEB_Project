from flask import Flask, render_template, redirect
from data import db_session
from data.posts import Posts
from data.users import User
from forms.user import RegisterForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route('/')
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


@app.route('/<title>')
@app.route('/index/<title>')
def index_base(title):
    return render_template('base.html', title=title)


@app.route('/authors')
def authors():
    return 'Страница с информацией об авторах'


@app.route("/index")
def index():
    db_sess = db_session.create_session()
    posts = db_sess.query(Posts).filter(Posts.is_private != True)
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


if __name__ == '__main__':
    db_session.global_init("db/posts.db")
    app.run(port=8080, host='127.0.0.1')
