// Procedural placeholder meshes for the hardware hall, used until the real GLBs exist in
// public/models/ (TODO(vedant): saarthi.glb from KiCad, setu.glb from Fusion 360). They are
// deliberately plain: proportions only, matte materials, no invented detail. 1 unit = 10 mm.
import {
  BoxGeometry,
  CylinderGeometry,
  Group,
  Mesh,
  MeshStandardMaterial,
  TorusGeometry,
  type Object3D,
} from 'three';

const matte = (color: number) => new MeshStandardMaterial({ color, roughness: 0.85, metalness: 0 });

function box(w: number, h: number, d: number, color: number, x = 0, y = 0, z = 0): Mesh {
  const m = new Mesh(new BoxGeometry(w, h, d), matte(color));
  m.position.set(x, y, z);
  return m;
}

// A 36 mm flight-controller board with 30.5 mm mounting holes, one large MCU and small sensors.
function board(): Group {
  const g = new Group();
  const T = 0.16;
  g.add(box(3.6, T, 3.6, 0x5a1e14));
  // STM32H753 package, centred.
  g.add(box(1.4, 0.12, 1.4, 0x161312, 0, T / 2 + 0.06, 0));
  // Two IMUs, two barometers, airspeed connector: small parts, rough placement only.
  g.add(box(0.3, 0.08, 0.3, 0x1f1a18, -0.95, T / 2 + 0.04, 0.2));
  g.add(box(0.3, 0.08, 0.3, 0x1f1a18, -0.95, T / 2 + 0.04, -0.3));
  g.add(box(0.2, 0.07, 0.2, 0xb8b0a8, 0.95, T / 2 + 0.035, -0.9));
  g.add(box(0.25, 0.07, 0.25, 0xb8b0a8, 0.95, T / 2 + 0.035, -0.45));
  g.add(box(0.8, 0.25, 0.35, 0xe8e0d6, 0, T / 2 + 0.125, 1.45));
  // Mounting holes on the 30.5 mm pattern: plated rings.
  for (const x of [-1.525, 1.525]) {
    for (const z of [-1.525, 1.525]) {
      const ring = new Mesh(new TorusGeometry(0.2, 0.05, 8, 24), matte(0xc9a27a));
      ring.rotation.x = Math.PI / 2;
      ring.position.set(x, T / 2 + 0.01, z);
      g.add(ring);
    }
  }
  // A few traces, 45° routing, as flat copper strips.
  const trace = (len: number, x: number, z: number, rot: number) => {
    const t = box(len, 0.012, 0.05, 0xe25964, x, T / 2 + 0.006, z);
    t.rotation.y = rot;
    g.add(t);
  };
  trace(0.9, -0.3, 1.0, 0);
  trace(0.6, -1.2, -0.95, Math.PI / 4);
  trace(0.7, 1.15, 0.2, Math.PI / 2);
  trace(0.5, 0.85, 0.95, -Math.PI / 4);
  return g;
}

// F450-class quad frame: two centre plates, four arms on the diagonals, motor bells.
function frame(): Group {
  const g = new Group();
  const plate = (y: number) => {
    const p = new Mesh(new CylinderGeometry(0.8, 0.8, 0.06, 8), matte(0x2a2320));
    p.position.y = y;
    p.rotation.y = Math.PI / 8;
    g.add(p);
  };
  plate(0);
  plate(0.4);
  for (let i = 0; i < 4; i++) {
    const a = Math.PI / 4 + (i * Math.PI) / 2;
    const arm = box(2.0, 0.28, 0.24, i < 2 ? 0xe8e0d6 : 0x5a1e14);
    arm.position.set(Math.cos(a) * 1.55, 0.2, Math.sin(a) * 1.55);
    arm.rotation.y = -a;
    g.add(arm);
    const motor = new Mesh(new CylinderGeometry(0.16, 0.16, 0.26, 20), matte(0x161312));
    motor.position.set(Math.cos(a) * 2.45, 0.47, Math.sin(a) * 2.45);
    g.add(motor);
  }
  return g;
}

export function buildModel(id: string): Object3D {
  return id === 'setu' ? frame() : board();
}
