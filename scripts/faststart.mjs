// Moves an MP4's index (the moov box) in front of its media data, so a browser can start playing
// while the rest downloads (what `ffmpeg -movflags +faststart` does; Blender's encoder leaves the
// index at the end). The chunk offsets in every stco/co64 table move by the index's size.

const CONTAINERS = new Set([
  'moov',
  'trak',
  'mdia',
  'minf',
  'stbl',
  'edts',
  'dinf',
  'mvex',
  'udta',
]);

/** Top-level (or nested, from `start` to `end`) boxes: type, offset, size, header length. */
function boxes(buf, start = 0, end = buf.length) {
  const out = [];
  let off = start;
  while (off + 8 <= end) {
    let size = buf.readUInt32BE(off);
    const type = buf.toString('latin1', off + 4, off + 8);
    let header = 8;
    if (size === 1) {
      size = Number(buf.readBigUInt64BE(off + 8));
      header = 16;
    } else if (size === 0) {
      size = end - off;
    }
    if (size < header) break;
    out.push({ type, off, size, header });
    off += size;
  }
  return out;
}

function shiftOffsets(moov, delta) {
  const walk = (start, end) => {
    for (const b of boxes(moov, start, end)) {
      if (CONTAINERS.has(b.type)) walk(b.off + b.header, b.off + b.size);
      else if (b.type === 'stco' || b.type === 'co64') {
        const count = moov.readUInt32BE(b.off + b.header + 4);
        let p = b.off + b.header + 8;
        for (let i = 0; i < count; i++) {
          if (b.type === 'stco') {
            moov.writeUInt32BE(moov.readUInt32BE(p) + delta, p);
            p += 4;
          } else {
            moov.writeBigUInt64BE(moov.readBigUInt64BE(p) + BigInt(delta), p);
            p += 8;
          }
        }
      }
    }
  };
  walk(0, moov.length);
}

/** Returns the file with its index first (or unchanged if it already is). */
export function faststart(buf) {
  const top = boxes(buf);
  const moov = top.find((b) => b.type === 'moov');
  const mdat = top.find((b) => b.type === 'mdat');
  if (!moov || !mdat || moov.off < mdat.off) return buf;
  const index = Buffer.from(buf.subarray(moov.off, moov.off + moov.size));
  shiftOffsets(index, moov.size);
  const parts = [];
  for (const b of top) {
    if (b === moov) continue;
    if (b === mdat) parts.push(index);
    parts.push(buf.subarray(b.off, b.off + b.size));
  }
  return Buffer.concat(parts);
}
