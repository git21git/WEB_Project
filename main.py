from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def page():
    return 'web проект'


@app.route('/<title>')
@app.route('/index/<title>')
def index(title):
    return render_template('base.html', title=title)


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
    app.run(port=8080, host='127.0.0.1')
