from app import create_app
from app.routes import routes



app = create_app()
app.register_blueprint(routes)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
