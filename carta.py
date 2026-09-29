"""Corazon -> carta con musica. Un solo archivo, sin instalar nada.

Pon en la MISMA carpeta que este archivo:
  Boton (png o jpg)  tu corazon de fotos, es lo primero que se ve
  carta (png o jpg)  tu carta en imagen
  cualquier .mp3     la cancion
(no importa si hay mayusculas o espacios en el nombre)

Ejecuta:  python carta.py
"""
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CARPETA = os.path.dirname(os.path.abspath(__file__))
EXT_IMAGEN = (".png", ".jpg", ".jpeg", ".webp")
TIPOS = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
         ".webp": "image/webp", ".mp3": "audio/mpeg"}


def buscar(base, extensiones):
    """Busca en la carpeta un archivo cuyo nombre (sin espacios ni
    mayusculas) sea `base` con una de las extensiones."""
    for nombre in os.listdir(CARPETA):
        limpio = nombre.lower().replace(" ", "")
        raiz, ext = os.path.splitext(limpio)
        if ext in extensiones and (raiz == base or base == ""):
            return os.path.join(CARPETA, nombre)
    return None


def ruta_de(url):
    if url == "/boton":
        return buscar("boton", EXT_IMAGEN)
    if url == "/carta":
        return buscar("carta", EXT_IMAGEN)
    if url == "/cancion":
        return buscar("", (".mp3",))
    return None

PAGINA = r'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Para ti</title>
<style>
:root{ --fondo:#9e1327; --fondo-carta:#000; } /* rojo al inicio, negro al abrir la carta */
*{box-sizing:border-box}
html,body{margin:0;min-height:100%}
body{
  background:var(--fondo);transition:background .8s;
  display:flex;min-height:100vh;
  font-family:Georgia,serif;
}
main{width:100%;max-width:820px;margin:auto;padding:16px 16px 40px;text-align:center}

body.abierta{background:var(--fondo-carta)}
#inicio{border:0;padding:0;background:none;cursor:pointer;width:100%;max-width:520px;margin:0 auto;
  transition:opacity .6s,transform .6s}
#inicio img{display:block;width:100%;height:auto;animation:latido 1.6s ease-in-out infinite}
@keyframes latido{0%,100%{transform:scale(1)}50%{transform:scale(1.04)}}
#inicio.oculto{opacity:0;transform:scale(.9);pointer-events:none;position:absolute}

#carta{display:none}
#carta.ver{display:block;animation:abrir .9s cubic-bezier(.2,.8,.2,1) both}
@keyframes abrir{from{opacity:0;transform:translateY(40px) scale(.92)}to{opacity:1;transform:none}}
#carta img{display:block;width:100%;height:auto;border-radius:4px;
  box-shadow:0 30px 60px rgba(0,0,0,.45)}
#musica{margin-top:20px;background:none;border:1px solid rgba(255,255,255,.6);
  color:#fff;border-radius:99px;padding:8px 16px;font:inherit;font-size:.9rem;cursor:pointer}
</style>
</head>
<body>
<main>
  <button id="inicio" type="button" aria-label="Abrir la carta">
    <img src="/boton" alt="Corazon de fotos">
  </button>

  <section id="carta">
    <img src="/carta" alt="Carta">
    <button id="musica" type="button">Pausar música</button>
  </section>
</main>

<audio id="cancion" src="/cancion" loop preload="auto"></audio>

<script>
var cancion = document.getElementById('cancion');
var inicio = document.getElementById('inicio');
var carta = document.getElementById('carta');
var musica = document.getElementById('musica');

inicio.addEventListener('click', function () {
  inicio.classList.add('oculto');
  document.body.classList.add('abierta');
  carta.style.display = 'block';
  void carta.offsetWidth;
  carta.classList.add('ver');
  var p = cancion.play();
  if (p && p.catch) p.catch(function () {});
});

musica.addEventListener('click', function () {
  if (cancion.paused) { cancion.play(); musica.textContent = 'Pausar música'; }
  else { cancion.pause(); musica.textContent = 'Reanudar música'; }
});
</script>
</body>
</html>
'''


class Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            datos = PAGINA.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(datos)))
            self.end_headers()
            self.wfile.write(datos)
            return
        ruta = ruta_de(self.path)
        if ruta:
            tipo = TIPOS.get(os.path.splitext(ruta)[1].lower(), "application/octet-stream")
            self.enviar_archivo(ruta, tipo)
            return
        self.send_error(404)

    def enviar_archivo(self, ruta, tipo):
        total = os.path.getsize(ruta)
        inicio, fin = 0, total - 1
        rango = self.headers.get("Range")
        if rango and rango.startswith("bytes="):
            a, _, b = rango[6:].partition("-")
            inicio = int(a) if a else 0
            fin = int(b) if b else total - 1
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {inicio}-{fin}/{total}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(fin - inicio + 1))
        self.end_headers()
        with open(ruta, "rb") as f:
            f.seek(inicio)
            self.wfile.write(f.read(fin - inicio + 1))

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    servidor = ThreadingHTTPServer(("127.0.0.1", 5000), Manejador)
    print("Abre http://127.0.0.1:5000  (Ctrl+C para cerrar)")
    webbrowser.open("http://127.0.0.1:5000")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass