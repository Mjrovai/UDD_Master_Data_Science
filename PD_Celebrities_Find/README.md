# clase-flask

Ejemplo para la clase de Producto de Datos del Magister de Data Science de la Universidad del Desarrollo.

Autores: Alonso Astroza y Paulo Sandoval.

# Installation

- Make sure you're running Python3
- Run 'pip install -r requirements.txt' to install the python packages needed
- Copy .env.example to .env and replace API_URL and API_KEY to fit your needs
- Run 'flask run' to start server in localhost:5000

# Running env on Heroku

- heroku config:set FLASK_APP=main.py
- heroku config:set API_URL="https://westus.api.cognitive.microsoft.com/vision/v2.0/analyze?visualFeatures=Faces&details=Celebrities&language=en"
- heroku config:set API_KEY=yourkey
- git push heroku master
- heroku ps:scale web=1