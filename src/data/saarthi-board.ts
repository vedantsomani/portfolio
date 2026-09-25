// Saarthi H7-Pro part positions, for the guided views in the hardware hall and the static board map.
// Source: Saarthi-H7-Pro-v1.kicad_pcb, candidate of 2026-09-24 (the same file the hero, X-ray and
// GLB were generated from). Coordinates are KiCad board millimetres, y pointing down; the board
// outline runs 20–110 mm on both axes. Sizes are package outlines, not courtyard.
// The view text only restates the Saarthi case study (src/content/projects/saarthi.mdx).

export type BoardGroup = 'flight' | 'safety' | 'sensors';

export interface BoardPart {
  ref: string;
  label: string;
  group: BoardGroup;
  x: number;
  y: number;
  w: number;
  h: number;
  /** Label anchor in board mm, and which side of it the text runs (SVG text-anchor). */
  lx: number;
  ly: number;
  la: 'start' | 'middle' | 'end';
}

export const BOARD = { x0: 20, y0: 20, x1: 110, y1: 110 } as const;

// 80 × 80 mm M3 pattern and 30.5 × 30.5 mm stack pattern, both centred on the board.
export const HOLES: [number, number][] = [
  [25, 25],
  [105, 25],
  [25, 105],
  [105, 105],
  [49.75, 49.75],
  [80.25, 49.75],
  [49.75, 80.25],
  [80.25, 80.25],
];

export const PARTS: BoardPart[] = [
  {
    ref: 'U201',
    label: 'STM32H753',
    group: 'flight',
    x: 42,
    y: 65,
    w: 22,
    h: 22,
    lx: 42,
    ly: 80.5,
    la: 'middle',
  },
  {
    ref: 'U301',
    label: 'STM32G431',
    group: 'safety',
    x: 41.5,
    y: 87,
    w: 7.5,
    h: 7.5,
    lx: 46.5,
    ly: 88.2,
    la: 'start',
  },
  // SERVO_1 (x 37) to SERVO_12 (x 81), 3-pin headers at 2.54 mm pitch, all at y 103.
  {
    ref: 'J1302–J1313',
    label: '12 servo outputs',
    group: 'safety',
    x: 59,
    y: 103,
    w: 47,
    h: 7.6,
    lx: 35.5,
    ly: 97.6,
    la: 'start',
  },
  {
    ref: 'J1201',
    label: 'RC input',
    group: 'safety',
    x: 105,
    y: 79,
    w: 6,
    h: 6,
    lx: 100.5,
    ly: 80.2,
    la: 'end',
  },
  {
    ref: 'J1203',
    label: 'Safety switch',
    group: 'safety',
    x: 105,
    y: 91.5,
    w: 6,
    h: 6,
    lx: 100.5,
    ly: 92.7,
    la: 'end',
  },
  {
    ref: 'U401',
    label: 'BMI088',
    group: 'sensors',
    x: 64,
    y: 62,
    w: 4.5,
    h: 3,
    lx: 64,
    ly: 59,
    la: 'middle',
  },
  {
    ref: 'U402',
    label: 'ICM-42688-P',
    group: 'sensors',
    x: 59.5,
    y: 68,
    w: 2.5,
    h: 3,
    lx: 57.5,
    ly: 69.2,
    la: 'end',
  },
  {
    ref: 'U403',
    label: 'ICM-42688-P',
    group: 'sensors',
    x: 68.5,
    y: 68,
    w: 2.5,
    h: 3,
    lx: 70.5,
    ly: 69.2,
    la: 'start',
  },
  {
    ref: 'U501',
    label: 'MS5611',
    group: 'sensors',
    x: 64,
    y: 41,
    w: 5,
    h: 3,
    lx: 60.8,
    ly: 42.2,
    la: 'end',
  },
  {
    ref: 'U502',
    label: 'DPS310',
    group: 'sensors',
    x: 69,
    y: 41,
    w: 2.5,
    h: 2,
    lx: 71,
    ly: 42.2,
    la: 'start',
  },
];

export interface BoardView {
  id: 'overview' | BoardGroup;
  title: string;
  text: string;
}

export const VIEWS: BoardView[] = [
  {
    id: 'flight',
    title: 'Flight computer',
    text: 'The STM32H753 runs the flight stack. It reads every sensor but never drives a servo pin directly.',
  },
  {
    id: 'safety',
    title: 'Safety controller',
    text: 'A separate STM32G431 owns RC input, the safety switch, and all twelve servo outputs along the bottom edge. Actuator authority stays off the flight computer.',
  },
  {
    id: 'sensors',
    title: 'Sensors',
    text: 'Three IMUs, each on its own SPI bus, and two barometers from different vendors give the firmware independent sources to cross-check.',
  },
];

export const BOARD_SOURCE =
  'Part positions from the KiCad board file of 24 September 2026. The board has not been fabricated.';
