from app import create_app


app = create_app()


if __name__ == "__main__":
    # For local development; in production use gunicorn
    app.run(host="0.0.0.0", port=5000)

