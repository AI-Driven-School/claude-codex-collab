const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

const FRAMES_DIR = path.join(__dirname, 'viral-frames');
const OUTPUT_GIF = path.join(__dirname, 'viral-demo.gif');
const OUTPUT_MP4 = path.join(__dirname, 'viral-demo.mp4');
const DEMO_HTML = path.join(__dirname, 'demo-viral.html');

// Recording settings
const WIDTH = 1280;
const HEIGHT = 720;
const FRAME_RATE = 30;
const DEMO_DURATION = 47000; // 47s (45s demo + 2s buffer)
const FRAME_INTERVAL = 1000 / FRAME_RATE;

async function recordViral() {
  console.log('🎬 Starting viral demo recording...');
  console.log(`   Resolution: ${WIDTH}x${HEIGHT}`);
  console.log(`   Frame rate: ${FRAME_RATE}fps`);
  console.log(`   Duration:   ${DEMO_DURATION / 1000}s`);

  // Create frames directory
  if (fs.existsSync(FRAMES_DIR)) {
    fs.rmSync(FRAMES_DIR, { recursive: true });
  }
  fs.mkdirSync(FRAMES_DIR);

  // Launch browser
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: { width: WIDTH, height: HEIGHT },
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    args: [`--window-size=${WIDTH},${HEIGHT}`, '--no-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: WIDTH, height: HEIGHT });

  // Load demo page with autostart parameter
  console.log('📄 Loading demo page...');
  await page.goto(`file://${DEMO_HTML}?autostart`);
  await sleep(500);

  // Capture frames
  console.log(`📸 Capturing frames (${FRAME_RATE}fps, ${DEMO_DURATION / 1000}s)...`);

  const startTime = Date.now();
  let frameCount = 0;

  while (Date.now() - startTime < DEMO_DURATION) {
    const frameNumber = String(frameCount).padStart(5, '0');
    const framePath = path.join(FRAMES_DIR, `frame_${frameNumber}.png`);

    await page.screenshot({ path: framePath });
    frameCount++;

    // Progress indicator every 5 seconds
    const elapsed = Date.now() - startTime;
    if (frameCount % (FRAME_RATE * 5) === 0) {
      console.log(`   ${Math.round(elapsed / 1000)}s / ${DEMO_DURATION / 1000}s (${frameCount} frames)`);
    }

    // Wait for next frame
    const nextFrameTime = frameCount * FRAME_INTERVAL;
    const waitTime = Math.max(0, nextFrameTime - elapsed);
    if (waitTime > 0) {
      await sleep(waitTime);
    }
  }

  console.log(`✅ Captured ${frameCount} frames`);
  await browser.close();

  // Convert to MP4
  console.log('🔄 Converting to MP4...');
  try {
    execSync(
      `ffmpeg -y -framerate ${FRAME_RATE} -i "${FRAMES_DIR}/frame_%05d.png" ` +
      `-c:v libx264 -pix_fmt yuv420p -crf 20 -preset slow ` +
      `-vf "scale=${WIDTH}:${HEIGHT}" "${OUTPUT_MP4}"`,
      { stdio: 'inherit' }
    );
    console.log(`✅ MP4 created: ${OUTPUT_MP4}`);
  } catch (e) {
    console.error('MP4 conversion error:', e.message);
  }

  // Convert to GIF
  console.log('🔄 Converting to GIF...');
  const hasGifski = hasCommand('gifski');

  if (hasGifski) {
    console.log('   Using gifski (high quality)...');
    try {
      execSync(
        `gifski --fps 15 --width ${WIDTH} --quality 90 -o "${OUTPUT_GIF}" "${FRAMES_DIR}"/frame_*.png`,
        { stdio: 'inherit' }
      );
      console.log(`✅ GIF created (gifski): ${OUTPUT_GIF}`);
    } catch (e) {
      console.error('gifski error, falling back to ffmpeg:', e.message);
      convertGifFfmpeg();
    }
  } else {
    console.log('   Using ffmpeg (install gifski for better quality)...');
    convertGifFfmpeg();
  }

  // Cleanup frames
  console.log('🧹 Cleaning up temp files...');
  fs.rmSync(FRAMES_DIR, { recursive: true });

  // Report
  console.log('\n🎉 Recording complete!');
  reportFile('GIF', OUTPUT_GIF);
  reportFile('MP4', OUTPUT_MP4);
}

function convertGifFfmpeg() {
  try {
    execSync(
      `ffmpeg -y -framerate ${FRAME_RATE} -i "${FRAMES_DIR}/frame_%05d.png" ` +
      `-vf "fps=15,scale=${WIDTH}:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer" ` +
      `-loop 0 "${OUTPUT_GIF}"`,
      { stdio: 'inherit' }
    );
    console.log(`✅ GIF created (ffmpeg): ${OUTPUT_GIF}`);
  } catch (e) {
    console.error('GIF conversion error:', e.message);
  }
}

function hasCommand(cmd) {
  try {
    execSync(`which ${cmd}`, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

function reportFile(label, filePath) {
  if (fs.existsSync(filePath)) {
    const sizeMB = (fs.statSync(filePath).size / 1024 / 1024).toFixed(2);
    console.log(`   ${label}: ${filePath} (${sizeMB} MB)`);
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

recordViral().catch(console.error);
