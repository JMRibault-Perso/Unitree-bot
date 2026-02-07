#!/usr/bin/env python3
"""
Simple 3D SLAM map viewer (PCD) using Three.js.
Serves a local HTML UI and a PCD file over HTTP.

Usage:
  python3 slam_map_viewer.py --map ./data/test_maps/slam_map_latest.pcd --port 8000
"""

import argparse
import http.server
import os
import socketserver
from pathlib import Path

HTML_PAGE = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>G1 SLAM Map Viewer</title>
  <style>
    html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #0b0f14; color: #e6e6e6; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
    #ui { position: absolute; top: 12px; left: 12px; z-index: 10; background: rgba(12, 16, 22, 0.85); border: 1px solid #1f2a37; border-radius: 8px; padding: 10px 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.35); }
    #ui h1 { font-size: 14px; margin: 0 0 6px 0; font-weight: 600; }
    #ui .row { display: flex; gap: 8px; align-items: center; margin-top: 6px; }
    #ui button, #ui input { background: #111827; color: #e5e7eb; border: 1px solid #374151; border-radius: 6px; padding: 6px 10px; font-size: 12px; }
    #ui button:hover { border-color: #4b5563; }
    #status { font-size: 12px; color: #9ca3af; margin-top: 6px; }
    #canvas { width: 100%; height: 100%; display: block; }
  </style>
</head>
<body>
  <div id=\"ui\">
    <h1>G1 SLAM Map Viewer</h1>
    <div class=\"row\">
      <button id=\"reloadBtn\">Reload Map</button>
      <label style=\"font-size:12px;\"><input id=\"autoReload\" type=\"checkbox\" /> Auto reload (2s)</label>
    </div>
    <div id=\"status\">Loading…</div>
  </div>
  <canvas id=\"canvas\"></canvas>

  <script type=\"module\">
    import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
    import { OrbitControls } from 'https://unpkg.com/three@0.160.0/examples/jsm/controls/OrbitControls.js';
    import { PCDLoader } from 'https://unpkg.com/three@0.160.0/examples/jsm/loaders/PCDLoader.js';

    const canvas = document.getElementById('canvas');
    const statusEl = document.getElementById('status');
    const reloadBtn = document.getElementById('reloadBtn');
    const autoReload = document.getElementById('autoReload');

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b0f14);

    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.01, 500);
    camera.position.set(2, 2, 2);

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio || 1);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;

    const grid = new THREE.GridHelper(10, 20, 0x334155, 0x1f2937);
    scene.add(grid);

    const axes = new THREE.AxesHelper(0.5);
    scene.add(axes);

    let currentPoints = null;

    async function loadPCD() {
      statusEl.textContent = 'Loading map…';
      const loader = new PCDLoader();
      const url = `/map.pcd?ts=${Date.now()}`;
      loader.load(
        url,
        (points) => {
          if (currentPoints) scene.remove(currentPoints);
          currentPoints = points;
          currentPoints.material.size = 0.01;
          currentPoints.material.vertexColors = true;
          scene.add(currentPoints);

          // Center camera
          const box = new THREE.Box3().setFromObject(currentPoints);
          const size = box.getSize(new THREE.Vector3());
          const center = box.getCenter(new THREE.Vector3());
          controls.target.copy(center);
          const maxDim = Math.max(size.x, size.y, size.z);
          camera.position.set(center.x + maxDim, center.y + maxDim, center.z + maxDim);
          controls.update();

          statusEl.textContent = `Loaded ${currentPoints.geometry.attributes.position.count} points`;
        },
        undefined,
        (err) => {
          statusEl.textContent = 'Map not found. Run the mapper and try again.';
          console.error(err);
        }
      );
    }

    reloadBtn.addEventListener('click', loadPCD);

    let intervalId = null;
    autoReload.addEventListener('change', () => {
      if (autoReload.checked) {
        intervalId = setInterval(loadPCD, 2000);
      } else {
        clearInterval(intervalId);
        intervalId = null;
      }
    });

    function onResize() {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }
    window.addEventListener('resize', onResize);

    function animate() {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }
    animate();

    loadPCD();
  </script>
</body>
</html>
"""


class MapHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, map_path: Path, **kwargs):
        self.map_path = map_path
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path.startswith("/map.pcd"):
            if not self.map_path.exists():
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.end_headers()
            with open(self.map_path, "rb") as f:
                self.wfile.write(f.read())
            return

        if self.path == "/" or self.path.startswith("/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
            return

        return super().do_GET()


def main():
    parser = argparse.ArgumentParser(description="3D SLAM Map Viewer (PCD)")
    parser.add_argument("--map", default="./data/test_maps/slam_map_latest.pcd", help="Path to PCD map file")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port")
    args = parser.parse_args()

    map_path = Path(args.map).resolve()
    if not map_path.exists():
        print(f"⚠️  Map not found: {map_path}")
        print("   Run the mapper to generate a map, then refresh the page.")

    handler = lambda *h_args, **h_kwargs: MapHandler(*h_args, map_path=map_path, **h_kwargs)

    with socketserver.TCPServer(("", args.port), handler) as httpd:
        print("=" * 60)
        print("G1 SLAM Map Viewer")
        print(f"Map file: {map_path}")
        print(f"Open: http://localhost:{args.port}")
        print("=" * 60)
        httpd.serve_forever()


if __name__ == "__main__":
    main()
