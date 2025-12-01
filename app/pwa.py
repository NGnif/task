from flask import Blueprint, Response, current_app, render_template, url_for
import io

try:
    from PIL import Image, ImageDraw
except Exception:  # Pillow may not be installed yet
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore


pwa_bp = Blueprint("pwa", __name__)


@pwa_bp.route("/manifest.webmanifest")
def manifest():
    # Minimal manifest for installable PWA
    manifest_json = {
        "name": "Task Manager",
        "short_name": "Tasks",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#171207",
        "theme_color": "#000000",
        "icons": [
            {"src": "/icons/192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/icons/512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    import json

    return Response(
        json.dumps(manifest_json),
        mimetype="application/manifest+json",
    )


@pwa_bp.route("/service-worker.js")
def service_worker():
    # Basic offline caching: precache core assets, network-first for navigations
    css = url_for("static", filename="styles.css") + "?v=13"
    assets = [
        "/",
        "/tasks",
        css,
        "/icons/192.png",
        "/icons/512.png",
        "/manifest.webmanifest",
        "/offline",
    ]

    js = f"""
    const CACHE_NAME = 'tm-cache-v13';
    const ASSETS = {assets};

    self.addEventListener('install', (event) => {{
      event.waitUntil((async () => {{
        const cache = await caches.open(CACHE_NAME);
        await cache.addAll(ASSETS);
        self.skipWaiting();
      }})());
    }});

    self.addEventListener('activate', (event) => {{
      event.waitUntil((async () => {{
        const names = await caches.keys();
        await Promise.all(names.filter(n => n !== CACHE_NAME).map(n => caches.delete(n)));
        self.clients.claim();
      }})());
    }});

    self.addEventListener('fetch', (event) => {{
      const req = event.request;
      const url = new URL(req.url);

      // Only same-origin GET requests
      if (req.method !== 'GET' || url.origin !== location.origin) return;

      // HTML navigations: network first with offline fallback
      if (req.mode === 'navigate') {{
        event.respondWith((async () => {{
          try {{
            const fresh = await fetch(req);
            const cache = await caches.open(CACHE_NAME);
            cache.put(req, fresh.clone());
            return fresh;
          }} catch (err) {{
            const cache = await caches.open(CACHE_NAME);
            return (await cache.match(req)) || (await cache.match('/offline'));
          }}
        }})());
        return;
      }}

      // Static assets: cache first
      event.respondWith((async () => {{
        const cache = await caches.open(CACHE_NAME);
        const cached = await cache.match(req);
        if (cached) return cached;
        try {{
          const fresh = await fetch(req);
          cache.put(req, fresh.clone());
          return fresh;
        }} catch (err) {{
          return cached || Response.error();
        }}
      }})());
    }});
    """.replace("{assets}", str(assets))

    return Response(js, mimetype="application/javascript")


@pwa_bp.route("/icons/<int:size>.png")
def icon(size: int):
    # Generate a simple PNG icon on the fly to avoid storing binaries
    # Colors match the app's theme
    size = max(64, min(size, 1024))
    if Image is None:
        # Fallback: tiny 1x1 transparent PNG
        b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
        )
        import base64

        return Response(base64.b64decode(b64), mimetype="image/png")

    img = Image.new("RGBA", (size, size), "#4f46e5")  # primary color
    draw = ImageDraw.Draw(img)
    padding = size // 8
    draw.rounded_rectangle(
        (padding, padding, size - padding, size - padding),
        radius=size // 6,
        outline="#ffffff",
        width=max(2, size // 24),
    )
    # diagonal accent
    draw.line(
        (padding, size - padding, size - padding, padding),
        fill="#a5b4fc",
        width=max(6, size // 20),
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="image/png")


@pwa_bp.route("/offline")
def offline():
    return render_template("offline.html")
