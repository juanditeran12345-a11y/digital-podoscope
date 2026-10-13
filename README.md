# Digital Podoscope

Web interface for a digital podoscope built with a transparent acrylic platform and edge lighting. It takes an image from a camera or a phone, segments the plantar contact area, calculates foot arch indices and exports a clinical PDF report.

## Features

* Live camera view with a camera selector, so a phone can be used as a webcam
* Segmentation of the illuminated contact area, shown as a clean binary mask for each foot
* Measurements: foot length, forefoot, arch and heel widths, and contact area
* Arch indices: Chippaux Smirak, Staheli and Cavanagh, with an orientative classification
* Relative pressure map based on the intensity of the contact light
* PDF report with patient data, images, results and clinical notes

All the processing runs in the browser. No image or patient data is sent to any server.

## Use it online

The page is published with GitHub Pages. Open the link shown in the repository description. The camera needs HTTPS, which GitHub Pages provides.

## Run it locally

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

On Mac or Linux the second command is `source venv/bin/activate`. Then open http://localhost:5000.

## Project structure

```
docs/index.html     Interface, processing and PDF report (served by GitHub Pages)
app.py              Local Flask server for development
requirements.txt    Python dependencies
```

## Notes

The classifications are orientative and use reference thresholds that must be validated by a clinician. The scale in pixels per centimeter is entered by hand until the automatic calibration is added.

## Roadmap

* Automatic scale calibration from the edges of the acrylic platform
* Segmentation with a trained model
* Server endpoint for the trained model

---

# Podoscopio Digital

Interfaz web para un podoscopio digital construido con una plataforma de acrílico transparente e iluminación de borde. Toma una imagen desde una cámara o un celular, segmenta la zona de contacto plantar, calcula índices del arco del pie y exporta un informe clínico en PDF.

## Funciones

* Vista de cámara en vivo con selector de cámara, para usar el celular como webcam
* Segmentación de la zona de contacto iluminada, mostrada como una máscara binaria limpia para cada pie
* Medidas: longitud del pie, anchos del antepié, arco y talón, y área de contacto
* Índices del arco: Chippaux Smirak, Staheli y Cavanagh, con una clasificación orientativa
* Mapa de presión relativa basado en la intensidad de la luz de contacto
* Informe en PDF con datos del paciente, imágenes, resultados y observaciones clínicas

Todo el procesamiento ocurre en el navegador. Ninguna imagen ni dato del paciente se envía a un servidor.

## Usarlo en línea

La página se publica con GitHub Pages. Abre el enlace que aparece en la descripción del repositorio. La cámara necesita HTTPS, que GitHub Pages ya ofrece.

## Ejecutarlo en local

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

En Mac o Linux el segundo comando es `source venv/bin/activate`. Luego abre http://localhost:5000.

## Notas

Las clasificaciones son orientativas y usan umbrales de referencia que debe validar un profesional de la salud. La escala en píxeles por centímetro se escribe a mano hasta que se agregue la calibración automática.

## Próximos pasos

* Calibración automática de la escala con los bordes de la plataforma de acrílico
* Segmentación con un modelo entrenado
* Endpoint en el servidor para el modelo entrenado
