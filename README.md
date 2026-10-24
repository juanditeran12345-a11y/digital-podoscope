# Digital Podoscope

Web platform for a digital podoscope built with a transparent acrylic platform and edge lighting. It takes an image from a camera or a phone, segments the plantar contact area, calculates foot arch indices, keeps a history per patient and exports a clinical PDF report.

<<<<<<< HEAD
=======
## Features

* Live camera view with a camera selector, so a phone can be used as a webcam
* Segmentation of the illuminated contact area, shown as a clean binary mask for each foot
* Measurements: foot length, forefoot, arch and heel widths, and contact area
* Arch indices: Chippaux Smirak, Staheli and Cavanagh, with an orientative classification
* Relative pressure map based on the intensity of the contact light
* PDF report with patient data, images, results and clinical notes
* Sign in for professionals and patients, with a saved history of exams

All the image processing runs in the browser. Images are never uploaded or stored. Only the calculated numbers of an exam are saved when a professional presses the save button.

## Accounts and sign in

When the platform runs with `app.py` there are two kinds of access:

* **Professional:** user and password. Registers patients, analyzes images, saves exams and reads the history.
* **Patient:** document number plus a six digit access code that the professional gives at registration. A patient can only see their own results.

The document number identifies a person but it is not a secret, so it is never used alone. Five failed attempts block an account for five minutes. Passwords and codes are stored hashed.

Create the first professional account once:

```
python crear_profesional.py
```

Data is saved in the `datos` folder (SQLite). It is listed in `.gitignore`, so it is not uploaded to GitHub. Back it up and protect it, because it holds personal health data.

## Use it online without accounts

The page in `docs` can be published with GitHub Pages. In that mode it works on its own, without sign in and without saving history, because there is no server. The camera needs HTTPS, which GitHub Pages provides. To use accounts online, the Flask server needs a host that runs Python, with HTTPS enabled and the variable `PODOSCOPIO_HTTPS=1`.

## Run it locally

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python crear_profesional.py
python app.py
```

On Mac or Linux the second command is `source venv/bin/activate`. Then open http://localhost:5000.

## Project structure

```
docs/index.html          Interface, processing and PDF report
templates/login.html     Sign in page
templates/paciente.html  Patient results page
app.py                   Flask server with accounts and history
crear_profesional.py     Creates a professional account
requirements.txt         Python dependencies
```

## Notes

The classifications are orientative and use reference thresholds that must be validated by a clinician. The scale in pixels per centimeter is entered by hand until the automatic calibration is added. Using patient data requires informed consent and compliance with the personal data protection law that applies where the platform is used.

## Roadmap

* Automatic scale calibration from the edges of the acrylic platform
* Segmentation with a trained model
* Server endpoint for the trained model

---

# Podoscopio Digital

Plataforma web para un podoscopio digital construido con una plataforma de acrílico transparente e iluminación de borde. Toma una imagen desde una cámara o un celular, segmenta la zona de contacto plantar, calcula índices del arco del pie, guarda un historial por paciente y exporta un informe clínico en PDF.

## Funciones

* Vista de cámara en vivo con selector de cámara, para usar el celular como webcam
* Segmentación de la zona de contacto iluminada, mostrada como una máscara binaria limpia para cada pie
* Medidas: longitud del pie, anchos del antepié, arco y talón, y área de contacto
* Índices del arco: Chippaux Smirak, Staheli y Cavanagh, con una clasificación orientativa
* Mapa de presión relativa basado en la intensidad de la luz de contacto
* Informe en PDF con datos del paciente, imágenes, resultados y observaciones clínicas
* Inicio de sesión para profesionales y pacientes, con historial de exámenes guardado

Todo el procesamiento de imágenes ocurre en el navegador. Las imágenes nunca se suben ni se guardan. Solo se guardan los números calculados de un examen cuando el profesional pulsa el botón de guardar.

## Cuentas e inicio de sesión

Cuando la plataforma se ejecuta con `app.py` hay dos tipos de acceso:

* **Profesional:** usuario y contraseña. Registra pacientes, analiza imágenes, guarda exámenes y consulta el historial.
* **Paciente:** número de documento y una clave de acceso de 6 dígitos que el profesional entrega al registrarlo. Cada paciente solo puede ver sus propios resultados.

El número de documento identifica a una persona pero no es un secreto, así que nunca se usa solo. Cinco intentos fallidos bloquean la cuenta durante cinco minutos. Las contraseñas y las claves se guardan cifradas con un hash.

Crea la primera cuenta de profesional una sola vez:

```
python crear_profesional.py
```

Los datos se guardan en la carpeta `datos` (SQLite). Está en `.gitignore`, así que no se sube a GitHub. Respáldala y protégela, porque contiene datos personales de salud.

## Usarlo en línea sin cuentas

La página de `docs` se puede publicar con GitHub Pages. En ese modo funciona sola, sin inicio de sesión y sin historial, porque no hay servidor. La cámara necesita HTTPS, que GitHub Pages ya ofrece. Para usar las cuentas en línea, el servidor Flask necesita un servicio que ejecute Python, con HTTPS y la variable `PODOSCOPIO_HTTPS=1`.

## Ejecutarlo en local

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python crear_profesional.py
python app.py
```

En Mac o Linux el segundo comando es `source venv/bin/activate`. Luego abre http://localhost:5000.

## Notas

Las clasificaciones son orientativas y usan umbrales de referencia que debe validar un profesional de la salud. La escala en píxeles por centímetro se escribe a mano hasta que se agregue la calibración automática. Usar datos de pacientes exige consentimiento informado y cumplir la ley de protección de datos personales que aplique donde se use la plataforma.

## Próximos pasos

* Calibración automática de la escala con los bordes de la plataforma de acrílico
* Segmentación con un modelo entrenado
* Endpoint en el servidor para el modelo entrenado
>>>>>>> e04d7b3 (Agrega inicio de sesión, historial de pacientes y portal del paciente)
