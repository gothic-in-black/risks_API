from app import create_app
from app.routes import routes


# Create an instance of the Flask application
app = create_app()
# Registering a blueprint (route module) in the application
app.register_blueprint(routes)

# Check if this file is the entry point of the program
if __name__ == '__main__':
    # Run the application
    app.run(host='127.0.0.1', port=5000)
