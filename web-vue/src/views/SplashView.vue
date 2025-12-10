<script setup lang="ts">
import { Renderer, Program, Mesh, Color, Triangle } from 'ogl';
import { onMounted, onUnmounted, ref, useTemplateRef, watch } from 'vue';
import { useRouter } from 'vue-router'

const vertexShader = `
attribute vec2 uv;
attribute vec2 position;

varying vec2 vUv;

void main() {
  vUv = uv;
  gl_Position = vec4(position, 0, 1);
}
`;

const fragmentShader = `
precision mediump float;

uniform float uTime;
uniform vec3 uResolution;
uniform vec2 uFocal;
uniform vec2 uRotation;
uniform float uStarSpeed;
uniform float uDensity;
uniform float uHueShift;
uniform float uSpeed;
uniform vec2 uMouse;
uniform float uGlowIntensity;
uniform float uSaturation;
uniform bool uMouseRepulsion;
uniform float uTwinkleIntensity;
uniform float uRotationSpeed;
uniform float uRepulsionStrength;
uniform float uMouseActiveFactor;
uniform float uAutoCenterRepulsion;
uniform bool uTransparent;

varying vec2 vUv;

#define NUM_LAYER 2.0
#define STAR_COLOR_CUTOFF 0.2
#define MAT45 mat2(0.7071, -0.7071, 0.7071, 0.7071)
#define PERIOD 3.0

float Hash21(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float tri(float x) {
  return abs(fract(x) * 2.0 - 1.0);
}

float tris(float x) {
  float t = fract(x);
  return 1.0 - smoothstep(0.0, 1.0, abs(2.0 * t - 1.0));
}

float trisn(float x) {
  float t = fract(x);
  return 2.0 * (1.0 - smoothstep(0.0, 1.0, abs(2.0 * t - 1.0))) - 1.0;
}

vec3 hsv2rgb(vec3 c) {
  vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
  vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
  return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

float Star(vec2 uv, float flare) {
  float d = length(uv);
  float m = (0.05 * uGlowIntensity) / d;
  float rays = smoothstep(0.0, 1.0, 1.0 - abs(uv.x * uv.y * 1000.0));
  m += rays * flare * uGlowIntensity;
  uv *= MAT45;
  rays = smoothstep(0.0, 1.0, 1.0 - abs(uv.x * uv.y * 1000.0));
  m += rays * 0.3 * flare * uGlowIntensity;
  m *= smoothstep(1.0, 0.2, d);
  return m;
}

vec3 StarLayer(vec2 uv) {
  vec3 col = vec3(0.0);

  vec2 gv = fract(uv) - 0.5; 
  vec2 id = floor(uv);

  // 优化：只检查中心和四个方向，减少循环次数从9次到5次
  for (int i = 0; i < 5; i++) {
    vec2 offset;
    if (i == 0) offset = vec2(0.0, 0.0);
    else if (i == 1) offset = vec2(-1.0, 0.0);
    else if (i == 2) offset = vec2(1.0, 0.0);
    else if (i == 3) offset = vec2(0.0, -1.0);
    else offset = vec2(0.0, 1.0);
    
    vec2 si = id + offset;
    float seed = Hash21(si);
    float size = fract(seed * 345.32);
    float glossLocal = tri(uStarSpeed / (PERIOD * seed + 1.0));
    float flareSize = smoothstep(0.9, 1.0, size) * glossLocal;

    float red = smoothstep(STAR_COLOR_CUTOFF, 1.0, Hash21(si + 1.0)) + STAR_COLOR_CUTOFF;
    float blu = smoothstep(STAR_COLOR_CUTOFF, 1.0, Hash21(si + 3.0)) + STAR_COLOR_CUTOFF;
    float grn = min(red, blu) * seed;
    vec3 base = vec3(red, grn, blu);
    
    float hue = atan(base.g - base.r, base.b - base.r) / (2.0 * 3.14159) + 0.5;
    hue = fract(hue + uHueShift / 360.0);
    float sat = length(base - vec3(dot(base, vec3(0.299, 0.587, 0.114)))) * uSaturation;
    float val = max(max(base.r, base.g), base.b);
    base = hsv2rgb(vec3(hue, sat, val));

    vec2 pad = vec2(tris(seed * 34.0 + uTime * uSpeed / 10.0), tris(seed * 38.0 + uTime * uSpeed / 30.0)) - 0.5;

    float star = Star(gv - offset - pad, flareSize);
    vec3 color = base;

    float twinkle = trisn(uTime * uSpeed + seed * 6.2831) * 0.5 + 1.0;
    twinkle = mix(1.0, twinkle, uTwinkleIntensity);
    star *= twinkle;
    
    col += star * size * color;
  }

  return col;
}

void main() {
  vec2 focalPx = uFocal * uResolution.xy;
  vec2 uv = (vUv * uResolution.xy - focalPx) / uResolution.y;

  vec2 mouseNorm = uMouse - vec2(0.5);
  
  if (uAutoCenterRepulsion > 0.0) {
    vec2 centerUV = vec2(0.0, 0.0);
    float centerDist = length(uv - centerUV);
    vec2 repulsion = normalize(uv - centerUV) * (uAutoCenterRepulsion / (centerDist + 0.1));
    uv += repulsion * 0.05;
  } else if (uMouseRepulsion) {
    vec2 mousePosUV = (uMouse * uResolution.xy - focalPx) / uResolution.y;
    float mouseDist = length(uv - mousePosUV);
    vec2 repulsion = normalize(uv - mousePosUV) * (uRepulsionStrength / (mouseDist + 0.1));
    uv += repulsion * 0.05 * uMouseActiveFactor;
  } else {
    vec2 mouseOffset = mouseNorm * 0.1 * uMouseActiveFactor;
    uv += mouseOffset;
  }

  float autoRotAngle = uTime * uRotationSpeed;
  mat2 autoRot = mat2(cos(autoRotAngle), -sin(autoRotAngle), sin(autoRotAngle), cos(autoRotAngle));
  uv = autoRot * uv;

  uv = mat2(uRotation.x, -uRotation.y, uRotation.y, uRotation.x) * uv;

  vec3 col = vec3(0.0);

  for (float i = 0.0; i < 1.0; i += 1.0 / NUM_LAYER) {
    float depth = fract(i + uStarSpeed * uSpeed);
    float scale = mix(20.0 * uDensity, 0.5 * uDensity, depth);
    float fade = depth * smoothstep(1.0, 0.9, depth);
    col += StarLayer(uv * scale + i * 453.32) * fade;
  }

  if (uTransparent) {
    float alpha = length(col);
    alpha = smoothstep(0.0, 0.3, alpha);
    alpha = min(alpha, 1.0);
    gl_FragColor = vec4(col, alpha);
  } else {
    gl_FragColor = vec4(col, 1.0);
  }
}
`;

const router = useRouter()

const ctnDom = useTemplateRef('ctnDom');
const targetMousePos = ref({ x: 0.5, y: 0.5 });
const smoothMousePos = ref({ x: 0.5, y: 0.5 });
const targetMouseActive = ref(0.0);
const smoothMouseActive = ref(0.0);

let cleanup: (() => void) | null = null;

// 生成更多的数据流
const dataStreams = ref<Array<{text: string, color: string, top: number, delay: number, duration: number, fontSize: number}>>([])

function generateDataStreams() {
  const dataTypes = [
    { text: '000001.SZ +2.5%', color: 'red' },
    { text: '600036.SH -1.2%', color: 'green' },
    { text: 'BTC/USDT 45,230 ↑', color: 'red' },
    { text: 'ETH 2,345.67 ↓', color: 'green' },
    { text: 'VOL: 2.5M', color: 'blue' },
    { text: 'MA5: 3245 MA10: 3180', color: 'blue' },
    { text: 'MACD: 0.23 ↑', color: 'red' },
    { text: '601318.SH +0.8%', color: 'red' },
    { text: 'RSI: 62.5', color: 'blue' },
    { text: 'KDJ: 75.3, 68.2, 71.5', color: 'blue' },
    { text: '沪深300 +1.1%', color: 'red' },
    { text: '创业板指 -0.5%', color: 'green' },
    { text: '600519.SH +1.8%', color: 'red' },
    { text: '000858.SZ -2.1%', color: 'green' },
    { text: '601288.SH +0.6%', color: 'red' },
    { text: 'BOLL: 3250, 3200, 3150', color: 'blue' },
    { text: '成交额: 8956亿', color: 'blue' },
    { text: '300750.SZ +5.2%', color: 'red' },
    { text: '002475.SZ -1.8%', color: 'green' },
    { text: '上证指数 +0.9%', color: 'red' },
    { text: '深证成指 +1.3%', color: 'red' },
    { text: '002594.SZ +3.6%', color: 'red' },
    { text: '688981.SH -0.9%', color: 'green' },
    { text: 'PE: 15.8 | PB: 1.2', color: 'blue' },
    { text: '换手率: 2.35%', color: 'blue' }
  ];

  const streams: Array<{text: string, color: string, top: number, delay: number, duration: number, fontSize: number}> = [];
  // 优化：减少到20条数据流，降低DOM元素数量
  for (let i = 0; i < 20; i++) {
    const data = dataTypes[Math.floor(Math.random() * dataTypes.length)];
    const duration = 20 + Math.random() * 15; // 持续时间20-35秒，更分散
    streams.push({
      text: data.text,
      color: data.color,
      top: Math.random() * 100,
      // 使用负的延迟时间，让动画一开始就处于进行中的状态
      delay: -(Math.random() * duration),
      duration: duration,
      fontSize: 12 + Math.random() * 6
    });
  }
  dataStreams.value = streams;
}

function goToHome() {
  // 跳转到首页（介绍页）
  router.push('/home')
}

function goToLogin() {
  // 直接跳转到登录页
  router.push('/login')
}

const setup = () => {
  if (!ctnDom.value) return;
  const ctn = ctnDom.value;
  const renderer = new Renderer({
    alpha: true,
    premultipliedAlpha: false,
    antialias: false // 关闭抗锯齿以提升性能
  });
  const gl = renderer.gl;

  gl.enable(gl.BLEND);
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  gl.clearColor(0, 0, 0, 0);

  let program: Program;

  function resize() {
    // 优化：降低渲染分辨率，根据设备性能调整
    const devicePixelRatio = window.devicePixelRatio || 1;
    const scale = Math.min(devicePixelRatio, 1.5) * 0.6; // 提高到75%分辨率以避免显示问题
    renderer.setSize(ctn.offsetWidth * scale, ctn.offsetHeight * scale);
    
    // 关键修复：设置canvas的CSS尺寸为容器的100%
    gl.canvas.style.width = '100%';
    gl.canvas.style.height = '100%';
    
    if (program) {
      program.uniforms.uResolution.value = new Color(
        gl.canvas.width,
        gl.canvas.height,
        gl.canvas.width / gl.canvas.height
      );
    }
  }
  
  // 防抖优化resize事件
  let resizeTimeout: number;
  const debouncedResize = () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = window.setTimeout(resize, 150);
  };
  
  window.addEventListener('resize', debouncedResize, false);
  resize();

  const geometry = new Triangle(gl);
  program = new Program(gl, {
    vertex: vertexShader,
    fragment: fragmentShader,
    uniforms: {
      uTime: { value: 0 },
      uResolution: {
        value: new Color(gl.canvas.width, gl.canvas.height, gl.canvas.width / gl.canvas.height)
      },
      uFocal: { value: new Float32Array([0.5, 0.5]) },
      uRotation: { value: new Float32Array([1.0, 0.0]) },
      uStarSpeed: { value: 0.4 },
      uDensity: { value: 0.4 },
      uHueShift: { value: 120 },
      uSpeed: { value: 0.8 },
      uMouse: {
        value: new Float32Array([smoothMousePos.value.x, smoothMousePos.value.y])
      },
      uGlowIntensity: { value: 0.3 },
      uSaturation: { value: 0.5 },
      uMouseRepulsion: { value: false },
      uTwinkleIntensity: { value: 0.3 },
      uRotationSpeed: { value: 0 },
      uRepulsionStrength: { value: 2 },
      uMouseActiveFactor: { value: 0.0 },
      uAutoCenterRepulsion: { value: 0 },
      uTransparent: { value: true }
    }
  });

  const mesh = new Mesh(gl, { geometry, program });
  let animateId: number;
  
  // 优化：添加帧率控制，目标45FPS以降低性能消耗
  const targetFPS = 45;
  const frameInterval = 1000 / targetFPS;
  let lastFrameTime = 0;

  function update(t: number) {
    animateId = requestAnimationFrame(update);
    
    // 帧率控制：跳过部分帧以降低性能消耗
    const elapsed = t - lastFrameTime;
    if (elapsed < frameInterval) {
      return;
    }
    lastFrameTime = t - (elapsed % frameInterval);
    
    program.uniforms.uTime.value = t * 0.001;
    program.uniforms.uStarSpeed.value = (t * 0.001 * 0.4) / 10.0;

    const lerpFactor = 0.05;
    smoothMousePos.value.x += (targetMousePos.value.x - smoothMousePos.value.x) * lerpFactor;
    smoothMousePos.value.y += (targetMousePos.value.y - smoothMousePos.value.y) * lerpFactor;

    smoothMouseActive.value += (targetMouseActive.value - smoothMouseActive.value) * lerpFactor;

    program.uniforms.uMouse.value[0] = smoothMousePos.value.x;
    program.uniforms.uMouse.value[1] = smoothMousePos.value.y;
    program.uniforms.uMouseActiveFactor.value = smoothMouseActive.value;

    renderer.render({ scene: mesh });
  }
  animateId = requestAnimationFrame(update);
  ctn.appendChild(gl.canvas);

  // 禁用鼠标交互
  // function handleMouseMove(e: MouseEvent) {
  //   const rect = ctn.getBoundingClientRect();
  //   const x = (e.clientX - rect.left) / rect.width;
  //   const y = 1.0 - (e.clientY - rect.top) / rect.height;
  //   targetMousePos.value = { x, y };
  //   targetMouseActive.value = 1.0;
  // }

  // function handleMouseLeave() {
  //   targetMouseActive.value = 0.0;
  // }

  // ctn.addEventListener('mousemove', handleMouseMove);
  // ctn.addEventListener('mouseleave', handleMouseLeave);

  cleanup = () => {
    cancelAnimationFrame(animateId);
    clearTimeout(resizeTimeout);
    window.removeEventListener('resize', debouncedResize);
    // ctn.removeEventListener('mousemove', handleMouseMove);
    // ctn.removeEventListener('mouseleave', handleMouseLeave);
    if (ctn.contains(gl.canvas)) {
      ctn.removeChild(gl.canvas);
    }
    gl.getExtension('WEBGL_lose_context')?.loseContext();
  };
};

onMounted(() => {
  generateDataStreams();
  cleanup?.();
  setup();
});

onUnmounted(() => {
  cleanup?.();
});
</script>

<template>
  <div class="splash-view">
    <div ref="ctnDom" class="financial-canvas"></div>
    
    <!-- 粒子系统 -->
    <!-- <div v-for="i in 100" :key="'particle-' + i" 
         class="particle" 
         :style="{ 
           left: Math.random() * 100 + '%',
           animationDelay: Math.random() * 10 + 's',
           animationDuration: (8 + Math.random() * 8) + 's',
           '--tx': (Math.random() - 0.5) * 200
         }">
    </div> -->

    <!-- K线图 - 优化：减少到25个 -->
    <div v-for="i in 30" :key="'candle-' + i"
         class="candlestick-line"
         :style="{
           left: (i * 4) + '%',
           animationDelay: Math.random() * 3 + 's',
           animationDuration: (2 + Math.random() * 3) + 's'
         }">
    </div>

    <!-- Logo容器 -->
    <div class="logo-container">
      <p class="animated-text-wrapper">
        <span class="top-text">FIN-R1 Empowered Adaptive Quantitative Investment Engine</span>
        <span class="main-text">FinLoom金织</span>
        <span class="bottom-text">FIN-R1赋能的自适应量化投资引擎</span>
      </p>
    </div>

    <!-- 数据流 -->
    <div v-for="(stream, i) in dataStreams" :key="'stream-' + i"
         class="data-stream"
         :class="stream.color"
         :style="{ 
           top: stream.top + '%',
           animationDelay: stream.delay + 's',
           animationDuration: stream.duration + 's',
           fontSize: stream.fontSize + 'px'
         }">
      {{ stream.text }}
    </div>

    <!-- 进入按钮 -->
    <button class="learn-more" @click="goToHome">
      <span class="circle" aria-hidden="true">
        <span class="icon arrow"></span>
      </span>
      <span class="button-text">进入系统</span>
    </button>
  </div>
</template>

<style lang="scss" scoped>
.splash-view {
  position: relative;
  width: 100vw;
  height: 100vh;
  background: #0a0e1a;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* 3D金融数据流背景 */
.financial-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  /* 性能优化：启用硬件加速 */
  transform: translateZ(0);
  backface-visibility: hidden;
  
  /* 修复黑色矩形问题：确保canvas元素正确填充 */
  canvas {
    display: block;
    width: 100% !important;
    height: 100% !important;
    position: absolute;
    top: 0;
    left: 0;
  }
}

/* 粒子系统 */
.particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: rgba(59, 130, 246, 0.8);
  border-radius: 50%;
  pointer-events: none;
  animation: particleFloat 10s linear infinite;
}

@keyframes particleFloat {
  0% {
    transform: translate(0, 100vh) scale(0);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translate(calc(var(--tx) * 1px), -100px) scale(1);
    opacity: 0;
  }
}

/* 动态K线图 - 红涨绿跌 */
.candlestick-line {
  position: absolute;
  bottom: 0;
  width: 4px;
  background: linear-gradient(to top, #10b981, #ef4444);
  border-radius: 2px;
  opacity: 0.3;
  animation: candleGrow 3s ease-in-out infinite;
  /* 性能优化：使用transform和will-change */
  will-change: transform, opacity;
  transform: translateZ(0);
  backface-visibility: hidden;
}

@keyframes candleGrow {
  0%, 100% {
    height: 30px;
    opacity: 0.2;
    transform: translateZ(0) scaleY(0.25);
  }
  50% {
    height: 120px;
    opacity: 0.5;
    transform: translateZ(0) scaleY(1);
  }
}

/* Logo容器 */
.logo-container {
  position: relative;
  z-index: 10;
  margin-bottom: 4rem;
  /* 性能优化 */
  transform: translateZ(0);
  backface-visibility: hidden;
}

/* 动画文字包装器 */
.animated-text-wrapper {
  text-transform: uppercase;
  letter-spacing: 0.5em;
  display: inline-block;
  border: 4px double rgba(255, 255, 255, 0.25);
  border-width: 4px 0;
  padding: 1.5em 0em;
  margin: 0;
  
  span {
    display: block;
    margin: 0 auto;
    text-shadow: 0 0 80px rgba(255, 255, 255, 0.5);
    
    /* Clip Background Image */
    background: url(https://i.ibb.co/RDTnNrT/animated-text-fill.png) repeat-y;
    -webkit-background-clip: text;
    background-clip: text;
    
    /* Animate Background Image */
    -webkit-text-fill-color: transparent;
    -webkit-animation: aitf 80s linear infinite;
    animation: aitf 80s linear infinite;
    
    /* Activate hardware acceleration for smoother animations */
    -webkit-transform: translate3d(0, 0, 0);
    transform: translate3d(0, 0, 0);
    -webkit-backface-visibility: hidden;
    backface-visibility: hidden;
  }
  
  .top-text {
    font-size: 0.8rem;
    font-weight: 400;
    letter-spacing: 0.2em;
    padding: 0.5em 0;
    opacity: 0.8;
  }
  
  .main-text {
    font-size: 5em;
    font-weight: 700;
    letter-spacing: 0;
    padding: 0.25em 0 0.325em;
  }
  
  .bottom-text {
    font-size: 1.2rem;
    font-weight: 400;
    letter-spacing: 0.3em;
    padding: 0.5em 0;
    opacity: 0.9;
  }
}

/* Animate Background Image */
@-webkit-keyframes aitf {
  0% {
    background-position: 0% 50%;
  }
  100% {
    background-position: 100% 50%;
  }
}

@keyframes aitf {
  0% {
    background-position: 0% 50%;
  }
  100% {
    background-position: 100% 50%;
  }
}

/* 数据流文本 - 红涨绿跌 */
.data-stream {
  position: absolute;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  animation: streamMove 20s linear infinite;
  opacity: 0.6;
  z-index: 1;
  /* 性能优化：使用transform硬件加速 */
  will-change: transform;
  transform: translateZ(0);
  backface-visibility: hidden;
  
  &.red {
    color: #ef4444;
    text-shadow: 0 0 10px #ef4444;
  }
  
  &.green {
    color: #10b981;
    text-shadow: 0 0 10px #10b981;
  }
  
  &.blue {
    color: #3b82f6;
    text-shadow: 0 0 10px #3b82f6;
  }
}

@keyframes streamMove {
  0% {
    transform: translateX(-100vw) translateZ(0);
  }
  100% {
    transform: translateX(100vw) translateZ(0);
  }
}

/* 进入按钮 - 新样式 */
button {
  position: relative;
  display: inline-block;
  cursor: pointer;
  outline: none;
  border: 0;
  vertical-align: middle;
  text-decoration: none;
  background: transparent;
  padding: 0;
  font-size: inherit;
  font-family: inherit;
  z-index: 10;
  /* 性能优化 */
  transform: translateZ(0);
  backface-visibility: hidden;
}

button.learn-more {
  width: 12rem;
  height: auto;
}

button.learn-more .circle {
  transition: all 0.45s cubic-bezier(0.65, 0, 0.076, 1);
  position: relative;
  display: block;
  margin: 0;
  width: 3rem;
  height: 3rem;
  background: #f97316;
  border-radius: 1.625rem;
}

button.learn-more .circle .icon {
  transition: all 0.45s cubic-bezier(0.65, 0, 0.076, 1);
  position: absolute;
  top: 0;
  bottom: 0;
  margin: auto;
  background: #fff;
}

button.learn-more .circle .icon.arrow {
  transition: all 0.45s cubic-bezier(0.65, 0, 0.076, 1);
  left: 0.625rem;
  width: 1.125rem;
  height: 0.125rem;
  background: none;
}

button.learn-more .circle .icon.arrow::before {
  position: absolute;
  content: "";
  top: -0.29rem;
  right: 0.0625rem;
  width: 0.625rem;
  height: 0.625rem;
  border-top: 0.125rem solid #fff;
  border-right: 0.125rem solid #fff;
  transform: rotate(45deg);
}

button.learn-more .button-text {
  transition: all 0.45s cubic-bezier(0.65, 0, 0.076, 1);
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 0.75rem 0;
  margin: 0 0 0 1.85rem;
  color: #f97316;
  font-weight: 700;
  line-height: 1.6;
  text-align: center;
  text-transform: uppercase;
}

button:hover .circle {
  width: 100%;
}

button:hover .circle .icon.arrow {
  background: #fff;
  transform: translate(1rem, 0);
}

button:hover .button-text {
  color: #fff;
}

/* 响应式 */
@media (max-width: 768px) {
  .animated-text-wrapper {
    letter-spacing: 0.3em;
    padding: 1em 0;
    
    .top-text {
      font-size: 0.5rem;
      letter-spacing: 0.1em;
    }
    
    .main-text {
      font-size: 3em;
    }
    
    .bottom-text {
      font-size: 0.8rem;
      letter-spacing: 0.2em;
    }
  }
  
  button.learn-more {
    width: 10rem;
  }
  
  .data-stream {
    font-size: 10px;
  }
}
</style>

