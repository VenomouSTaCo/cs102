from bottle import route, template
import bottle


@route("/hello/<name>")
def index(name):
    return template("<b>Hello {{name}}</b>!", name=name)


app = bottle.default_app()
