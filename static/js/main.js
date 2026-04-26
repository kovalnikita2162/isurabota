// ============================================================
// CONSTANTS & STATE
// ============================================================
const PINK  = '#ff375f';
const BLUE  = '#0a84ff';
const GRAPH_BG = '#080810';

const NODE_DEFAULT = { background: '#1c1c2e', border: '#3a3a5c', highlight: { background: '#252540', border: '#0a84ff' } };
const NODE_VISITED = { background: 'rgba(10,132,255,0.25)', border: '#0a84ff', highlight: { background: 'rgba(10,132,255,0.35)', border: '#0a84ff' } };
const NODE_ACTIVE  = { background: 'rgba(255,55,95,0.35)', border: '#ff375f', highlight: { background: 'rgba(255,55,95,0.45)', border: '#ff375f' } };
const EDGE_DEFAULT  = { color: 'rgba(255,255,255,0.12)', highlight: 'rgba(255,255,255,0.3)' };
const EDGE_HIGHLIGHT = { color: PINK, highlight: PINK };
const EDGE_PATH      = { color: BLUE, highlight: BLUE };

// Avatar images — deterministic (picsum seeds)
const AVATAR_SEEDS = [10, 22, 33, 45, 56, 67, 78, 89, 11, 23, 34, 46, 57, 68, 79, 91, 12, 24, 35, 47];
function avatarUrl(i) {
  return `https://i.pravatar.cc/80?img=${(AVATAR_SEEDS[i % AVATAR_SEEDS.length])}`;
}
// Gender: even index = female (pink border), odd = male (blue); adapts to light/dark theme
function nodeColor(i) {
  const light = document.documentElement?.dataset?.theme === 'light';
  return i % 2 === 0
    ? { border: PINK, background: light ? '#f8e8f0' : '#1a1020', highlight: { border: PINK, background: light ? '#f0d8e8' : '#221528' } }
    : { border: BLUE, background: light ? '#e8f0f8' : '#0a1020', highlight: { border: BLUE, background: light ? '#d8e8f8' : '#0d1830' } };
}

// ============================================================
// MATRIX
// ============================================================
let currentMatrix = [];
let showAvatars = true;

function buildMatrix() {
  const el = document.getElementById('matrixSize');
  if (!el) return;
  const n = Math.max(2, Math.min(20, parseInt(el.value) || 4));
  el.value = n;
  currentMatrix = Array.from({ length: n }, () => Array(n).fill(0));
  renderMatrix();
}

function isWeightedTask() {
  return typeof TASK !== 'undefined' && TASK.input_type === 'weighted_matrix';
}

function renderMatrix() {
  const container = document.getElementById('matrixContainer');
  if (!container) return;
  const n = currentMatrix.length;
  const weighted = isWeightedTask();
  let html = '<table class="matrix-table"><tr><td class="clabel"></td>';
  for (let j = 0; j < n; j++) html += `<td class="clabel">${j}</td>`;
  html += '</tr>';
  for (let i = 0; i < n; i++) {
    html += `<tr><td class="clabel">${i}</td>`;
    for (let j = 0; j < n; j++) {
      if (i === j) {
        html += `<td class="cdiag">·</td>`;
      } else {
        const v = currentMatrix[i][j];
        if (weighted) {
          html += `<td class="${v > 0 ? 'cw' : 'c0'}" onclick="editWeight(${i},${j})">${v > 0 ? v : '·'}</td>`;
        } else {
          html += `<td class="${v ? 'c1' : 'c0'}" onclick="toggleCell(${i},${j})">${v}</td>`;
        }
      }
    }
    html += '</tr>';
  }
  html += '</table>';
  container.innerHTML = html;
  drawGraphFromMatrix();
}

function editWeight(i, j) {
  if (i === j) return;
  const cur = currentMatrix[i][j];
  const raw = prompt(`Вес ребра ${i} ↔ ${j}\n(0 = нет ребра, 1–99 = вес):`, cur || '');
  if (raw === null) return;
  const v = Math.max(0, Math.min(99, parseInt(raw) || 0));
  currentMatrix[i][j] = v;
  currentMatrix[j][i] = v;
  renderMatrix();
}

function toggleCell(i, j) {
  if (i === j) return;
  const v = currentMatrix[i][j] === 1 ? 0 : 1;
  currentMatrix[i][j] = v;
  currentMatrix[j][i] = v;
  renderMatrix();
}

// ── Random graph generators ──────────────────────────────────

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// Connected graph: spanning tree + random extra edges
function randomConnected(n, weighted = false, density = 0.35) {
  const mat = Array.from({ length: n }, () => Array(n).fill(0));
  const perm = shuffle(Array.from({ length: n }, (_, i) => i));
  for (let i = 1; i < n; i++) {
    const a = perm[i];
    const b = perm[Math.floor(Math.random() * i)];
    const w = weighted ? Math.floor(Math.random() * 15) + 1 : 1;
    mat[a][b] = mat[b][a] = w;
  }
  const maxExtra = Math.ceil(n * (n - 1) / 2 * density);
  for (let k = 0; k < maxExtra; k++) {
    const i = Math.floor(Math.random() * n);
    const j = Math.floor(Math.random() * n);
    if (i !== j && mat[i][j] === 0) {
      const w = weighted ? Math.floor(Math.random() * 15) + 1 : 1;
      mat[i][j] = mat[j][i] = w;
    }
  }
  return mat;
}

// Disconnected graph with 2–3 components (for component tasks)
function randomMultiComponent(n) {
  const mat = Array.from({ length: n }, () => Array(n).fill(0));
  const numComp = n <= 4 ? 2 : (Math.random() < 0.5 ? 2 : 3);
  const nodes = shuffle(Array.from({ length: n }, (_, i) => i));
  const comps = [];
  let rest = [...nodes];
  for (let c = 0; c < numComp - 1; c++) {
    const size = Math.max(2, Math.floor(n / numComp) + (Math.random() < 0.4 ? 1 : 0));
    comps.push(rest.splice(0, Math.min(size, rest.length - (numComp - c - 1))));
  }
  comps.push(rest);
  for (const comp of comps) {
    if (comp.length < 2) continue;
    const s = shuffle(comp);
    for (let i = 1; i < s.length; i++) mat[s[i-1]][s[i]] = mat[s[i]][s[i-1]] = 1;
    for (let k = 0; k < Math.floor(s.length * 0.4); k++) {
      const a = s[Math.floor(Math.random() * s.length)];
      const b = s[Math.floor(Math.random() * s.length)];
      if (a !== b) mat[a][b] = mat[b][a] = 1;
    }
  }
  return mat;
}

// Random tree via Prüfer sequence (for prufer_encode)
function randomTree(n) {
  if (n === 2) return [[0,1],[1,0]];
  const prufer = Array.from({ length: n - 2 }, () => Math.floor(Math.random() * n));
  const mat = Array.from({ length: n }, () => Array(n).fill(0));
  const deg = Array(n).fill(1);
  for (const v of prufer) deg[v]++;
  for (const v of prufer) {
    let leaf = deg.findIndex(d => d === 1);
    mat[leaf][v] = mat[v][leaf] = 1;
    deg[leaf]--; deg[v]--;
  }
  const last = deg.reduce((acc, d, i) => d === 1 ? [...acc, i] : acc, []);
  if (last.length === 2) mat[last[0]][last[1]] = mat[last[1]][last[0]] = 1;
  return mat;
}

// Main dispatcher — picks generator based on task type
function generateRandomMatrix(n) {
  const algo = typeof TASK !== 'undefined' ? TASK.algorithm : '';
  const weighted = isWeightedTask();
  if (algo === 'prufer_encode')                      return randomTree(n);
  if (algo === 'components' || algo === 'check_components') return randomMultiComponent(n);
  if (algo === 'coloring')                           return randomConnected(n, false, 0.55);
  return randomConnected(n, weighted, 0.35);
}

function fillExample() {
  const n = parseInt(document.getElementById('matrixSize')?.value || 5);
  currentMatrix = generateRandomMatrix(n);
  document.getElementById('matrixSize').value = n;
  renderMatrix();
}

// ============================================================
// VIS-NETWORK
// ============================================================
let network = null, nodesDS = null, edgesDS = null;

function themeEdgeColor() {
  const light = document.documentElement.dataset.theme === 'light';
  return {
    color:     light ? 'rgba(20,20,40,0.20)' : 'rgba(255,255,255,0.12)',
    highlight: light ? 'rgba(20,20,40,0.50)' : 'rgba(255,255,255,0.30)',
  };
}
function themeFontColor() {
  return document.documentElement.dataset.theme === 'light'
    ? 'rgba(20,20,40,0.85)' : '#ffffff';
}

function initGraph() {
  const container = document.getElementById('graphCanvas');
  if (!container) return;
  nodesDS = new vis.DataSet([]);
  edgesDS = new vis.DataSet([]);

  const options = {
    physics: {
      enabled: true,
      solver: 'forceAtlas2Based',
      forceAtlas2Based: { gravitationalConstant: -50, springLength: 120 },
      stabilization: { iterations: 150 },
    },
    edges: {
      color: themeEdgeColor(),
      width: 1.5,
      smooth: { type: 'curvedCW', roundness: 0.15 },
      hoverWidth: 2,
    },
    nodes: {
      shape: 'circularImage',
      size: 26,
      borderWidth: 3,
      borderWidthSelected: 4,
      font: { color: themeFontColor(), size: 11, face: 'Inter' },
      chosen: true,
    },
    interaction: { dragNodes: true, hover: true },
    background: { color: 'transparent' },
  };

  network = new vis.Network(container, { nodes: nodesDS, edges: edgesDS }, options);
}

function drawGraphFromMatrix(matrix) {
  if (!nodesDS || !edgesDS) return;
  const mat = matrix || currentMatrix;
  if (!mat || !mat.length) return;
  const n = mat.length;

  nodesDS.clear();
  edgesDS.clear();

  const ec = themeEdgeColor();
  const fc = themeFontColor();
  const weighted = isWeightedTask();

  const nodes = [];
  for (let i = 0; i < n; i++) {
    nodes.push({
      id: i,
      label: String(i),
      shape: showAvatars ? 'circularImage' : 'circle',
      image: showAvatars ? avatarUrl(i) : undefined,
      color: nodeColor(i),
      font: { color: fc, size: 11, face: 'Inter' },
      title: `Вершина ${i}`,
    });
  }
  nodesDS.add(nodes);

  const edges = [];
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const w = mat[i][j];
      if (w > 0) {
        edges.push({
          id: `e${i}-${j}`, from: i, to: j, color: ec,
          label: weighted ? String(w) : undefined,
          font: weighted ? { color: fc, size: 10, face: 'Inter', align: 'middle', strokeWidth: 2, strokeColor: 'transparent' } : undefined,
        });
      }
    }
  }
  edgesDS.add(edges);
}

// ============================================================
// STEP ANIMATION
// ============================================================
let steps = [];
let currentStep = -1;
let autoTimer = null;
let lastMatrix = null;
let lastN = 0;

function renderStep(idx) {
  if (!steps.length || !nodesDS) return;
  const step = steps[idx];
  const n = lastN;

  // Update node colors
  const updates = [];
  for (let i = 0; i < n; i++) {
    const base = nodeColor(i);
    if (step.active_node === i) {
      updates.push({ id: i, color: { ...base, background: 'rgba(255,55,95,0.4)', border: PINK }, size: 32 });
    } else if (step.visited_nodes?.includes(i)) {
      updates.push({ id: i, color: { ...base, background: 'rgba(10,132,255,0.25)', border: BLUE }, size: 28 });
    } else {
      updates.push({ id: i, color: base, size: 26 });
    }
  }
  nodesDS.update(updates);

  document.getElementById('stepLabel').textContent = `${idx + 1} / ${steps.length}`;
  document.getElementById('btnPrev').disabled = idx <= 0;
  document.getElementById('btnNext').disabled = idx >= steps.length - 1;
  highlightLog(idx);
}

function prevStep() { if (currentStep > 0) renderStep(--currentStep); }
function nextStep() { if (currentStep < steps.length - 1) renderStep(++currentStep); }

function toggleAuto() {
  const btn = document.getElementById('btnAuto');
  if (autoTimer) {
    clearInterval(autoTimer);
    autoTimer = null;
    btn.textContent = '▶';
    btn.classList.remove('text-[#ff375f]');
    return;
  }
  if (currentStep >= steps.length - 1) currentStep = -1;
  btn.textContent = '⏸';
  btn.classList.add('text-[#ff375f]');
  autoTimer = setInterval(() => {
    if (currentStep >= steps.length - 1) {
      clearInterval(autoTimer);
      autoTimer = null;
      btn.textContent = '▶';
      btn.classList.remove('text-[#ff375f]');
      return;
    }
    renderStep(++currentStep);
  }, 900);
}

function jumpStep(idx) {
  if (autoTimer) { clearInterval(autoTimer); autoTimer = null; document.getElementById('btnAuto').textContent = '▶'; }
  currentStep = idx;
  renderStep(idx);
}

function highlightLog(activeIdx) {
  const items = document.querySelectorAll('.log-item');
  items.forEach((el, i) => {
    el.classList.toggle('log-active', i === activeIdx);
    if (i === activeIdx) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  });
}

function renderLogs(logs) {
  const box = document.getElementById('logBox');
  if (!box) return;
  if (!logs?.length) {
    box.innerHTML = '<p class="text-xs text-white/25 text-center pt-4">Нет шагов</p>';
    return;
  }
  box.innerHTML = logs.map((l, i) =>
    `<div class="log-item" onclick="jumpStep(${i})">
      <span class="step-num">${l.step}.</span>${l.log_message}
    </div>`
  ).join('');
}

// ============================================================
// RESULT RENDERING
// ============================================================
function renderResult(result) {
  const box = document.getElementById('resultBox');
  const card = document.getElementById('resultCard');
  const badge = document.getElementById('resultBadge');
  const badgeIcon = document.getElementById('resultIcon');
  const badgeSummary = document.getElementById('resultSummary');
  if (!box) return;

  card?.classList.remove('hidden');
  badge?.classList.remove('hidden');

  if (result.status === 'error') {
    box.innerHTML = `<div class="text-[#ff375f] text-xs">${result.final_result}</div>`;
    badgeIcon.style.background = PINK;
    badgeSummary.textContent = 'Ошибка';
    return;
  }

  const fr = result.final_result;
  box.innerHTML = buildResultHTML(fr);

  // Top badge summary
  if (typeof fr === 'object' && fr !== null && 'is_correct' in fr) {
    const ok = fr.is_correct;
    badgeIcon.style.background = ok ? '#34c759' : PINK;
    badgeSummary.textContent = ok ? 'Верно!' : 'Неверно';
  } else {
    badgeIcon.style.background = BLUE;
    badgeSummary.textContent = 'Готово';
  }
}

function buildResultHTML(fr) {
  if (Array.isArray(fr)) {
    if (Array.isArray(fr[0])) return buildMatrixHTML(fr);
    return `<div class="result-row">
      <span class="result-key">Порядок</span>
      <span class="result-val">[${fr.join(', ')}]</span>
    </div>`;
  }
  if (typeof fr !== 'object' || fr === null) {
    return `<div class="result-row"><span class="result-val">${fr}</span></div>`;
  }

  const SKIP = new Set(['logs']);
  return Object.entries(fr)
    .filter(([k]) => !SKIP.has(k))
    .map(([k, v]) => {
      let valHtml;
      if (typeof v === 'boolean') {
        valHtml = v
          ? `<span class="badge-correct">✓ Да</span>`
          : `<span class="badge-wrong">✗ Нет</span>`;
      } else if (k === 'euler_status') {
        valHtml = `<span class="badge-info">${v}</span>`;
      } else if (k === 'is_bipartite' || k === 'is_complete_bipartite') {
        valHtml = v
          ? `<span class="badge-correct">✓ Да</span>`
          : `<span class="badge-wrong">✗ Нет</span>`;
      } else if (Array.isArray(v) && Array.isArray(v[0])) {
        valHtml = buildMatrixHTML(v);
      } else if (Array.isArray(v)) {
        if (Array.isArray(v[0])) {
          valHtml = buildMatrixHTML(v);
        } else {
          valHtml = `<span class="result-val">[${v.join(', ')}]</span>`;
        }
      } else if (typeof v === 'object' && v !== null) {
        const entries = Object.entries(v);
        if (entries.length <= 6) {
          valHtml = entries.map(([ki, vi]) => `<span class="badge-info">${ki}:${vi}</span>`).join(' ');
        } else {
          valHtml = `<pre class="text-[10px] text-white/50 max-h-24 overflow-auto">${JSON.stringify(v, null, 1)}</pre>`;
        }
      } else {
        valHtml = `<span class="result-val">${v}</span>`;
      }

      const label = LABELS[k] || k;
      return `<div class="result-row"><span class="result-key">${label}</span><div>${valHtml}</div></div>`;
    }).join('');
}

function buildMatrixHTML(mat) {
  let h = '<table class="res-matrix">';
  for (const row of mat) {
    h += '<tr>' + row.map(v => `<td>${v === -1 ? '∞' : v}</td>`).join('') + '</tr>';
  }
  return h + '</table>';
}

const LABELS = {
  degrees: 'Степени', components_count: 'Компоненты', components: 'Компоненты',
  euler_status: 'Эйлер', is_bipartite: 'Двудольный', is_complete_bipartite: 'Полный двудольный',
  bipartite_colors: 'Доли', dfs_order: 'Порядок DFS', bfs_order: 'Порядок BFS',
  is_correct: 'Правильно', correct_order: 'Правильный', user_order: 'Ваш ответ',
  correct_count: 'Правильный', user_count: 'Ваш ответ', message: 'Сообщение',
  mst_edges: 'Рёбра МОД', total_weight: 'Вес', start_node: 'Старт',
  distances: 'Расстояния', paths: 'Пути', distance_matrix: 'Матрица',
  prufer_code: 'Код Прюфера', vertices_count: 'Вершин', edges: 'Рёбра', matrix: 'Матрица',
  colors: 'Цвета', colors_count: 'Хроматическое число',
};

// ============================================================
// POST-RESULT GRAPH DECORATIONS
// ============================================================
function applyResultDecorations(task, result) {
  if (result.status !== 'success') return;
  const fr = result.final_result;

  if (task.algorithm === 'mst' && fr?.mst_edges) {
    fr.mst_edges.forEach(([u, v]) => updateEdgeColor(u, v, PINK));
  }

  if (task.algorithm === 'shortest_paths' && fr?.paths) {
    Object.values(fr.paths).forEach(path => {
      for (let i = 0; i < path.length - 1; i++) updateEdgeColor(path[i], path[i+1], BLUE);
    });
  }

  if (task.algorithm === 'coloring' && fr?.colors && nodesDS) {
    const PALETTE = ['#ff375f','#0a84ff','#34c759','#ff9f0a','#bf5af2','#5ac8fa','#ff6961','#aec6cf'];
    const updates = Object.entries(fr.colors).map(([i, c]) => ({
      id: parseInt(i),
      color: { background: PALETTE[c % PALETTE.length] + '55', border: PALETTE[c % PALETTE.length] },
    }));
    nodesDS.update(updates);
  }

  if (task.algorithm === 'basic' && fr?.bipartite_colors && nodesDS) {
    const updates = Object.entries(fr.bipartite_colors).map(([i, c]) => ({
      id: parseInt(i),
      color: { background: c === 0 ? 'rgba(255,55,95,0.25)' : 'rgba(10,132,255,0.25)',
               border: c === 0 ? PINK : BLUE },
    }));
    nodesDS.update(updates);
  }

  if ((task.algorithm === 'prufer_decode') && fr?.matrix) {
    drawGraphFromMatrix(fr.matrix);
  }
}

function updateEdgeColor(u, v, color) {
  if (!edgesDS) return;
  const id = u < v ? `e${u}-${v}` : `e${v}-${u}`;
  try { edgesDS.update({ id, color: { color, highlight: color }, width: 3 }); } catch {}
}

// ============================================================
// MAIN RUN
// ============================================================
async function runTask() {
  const task = typeof TASK !== 'undefined' ? TASK : null;
  if (!task) return;

  const btn = document.getElementById('runBtnText');
  const spinner = document.getElementById('runSpinner');
  btn.textContent = 'Считаем...';
  spinner?.classList.remove('hidden');

  const payload = { algorithm: task.algorithm };

  if (task.input_type === 'matrix') {
    if (!currentMatrix?.length) { alert('Постройте матрицу.'); resetBtn(); return; }
    payload.matrix = currentMatrix;
  }
  if (task.input_type === 'prufer') {
    const raw = document.getElementById('pruferInput')?.value.trim();
    if (!raw) { alert('Введите код Прюфера.'); resetBtn(); return; }
    payload.prufer_code = raw.split(/\s+/).map(Number);
  }
  if (task.needs_start_node) {
    payload.start_node = parseInt(document.getElementById('startNode')?.value ?? 0);
  }
  if (task.needs_user_order) {
    const raw = document.getElementById('userOrder')?.value.trim();
    if (!raw) { alert('Введите порядок обхода.'); resetBtn(); return; }
    payload.user_order = raw.split(/\s+/).map(Number);
  }
  if (task.needs_components_count) {
    const v = document.getElementById('userComponentsCount')?.value;
    if (!v) { alert('Введите число компонент.'); resetBtn(); return; }
    payload.user_components_count = parseInt(v);
  }

  let result;
  try {
    const resp = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    result = await resp.json();
  } catch (e) {
    document.getElementById('resultBox').textContent = 'Ошибка соединения: ' + e.message;
    document.getElementById('resultCard')?.classList.remove('hidden');
    resetBtn();
    return;
  }

  // Reset graph to current matrix before showing steps
  lastMatrix = task.input_type === 'matrix' ? currentMatrix : null;
  lastN = lastMatrix ? lastMatrix.length : 0;

  if (lastMatrix) drawGraphFromMatrix(lastMatrix);

  steps = result.logs || [];
  currentStep = steps.length > 0 ? 0 : -1;
  renderLogs(steps);
  renderResult(result);

  if (steps.length > 0) renderStep(0);

  // Apply post-result decorations after a short delay (so final state is visible)
  setTimeout(() => applyResultDecorations(task, result), steps.length > 0 ? 800 : 0);

  resetBtn();
}

function resetBtn() {
  const btn = document.getElementById('runBtnText');
  const spinner = document.getElementById('runSpinner');
  if (btn) btn.textContent = 'Запустить';
  spinner?.classList.add('hidden');
}

// ============================================================
// TAB BAR CAROUSEL
// ============================================================
const TAB_SCROLL_STEP = 220;

function scrollTabs(dir) {
  const el = document.getElementById('tabScroll');
  if (!el) return;
  el.scrollBy({ left: dir * TAB_SCROLL_STEP, behavior: 'smooth' });
  setTimeout(updateTabArrows, 320);
}

function updateTabArrows() {
  const el = document.getElementById('tabScroll');
  const prev = document.getElementById('tabPrev');
  const next = document.getElementById('tabNext');
  if (!el || !prev || !next) return;
  prev.disabled = el.scrollLeft <= 2;
  next.disabled = el.scrollLeft + el.clientWidth >= el.scrollWidth - 2;
  prev.style.opacity = prev.disabled ? '0.2' : '1';
  next.style.opacity = next.disabled ? '0.2' : '1';
}

function initTabCarousel() {
  const el = document.getElementById('tabScroll');
  if (!el) return;

  const active = el.querySelector('.tab-active');
  if (active) {
    setTimeout(() => {
      active.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' });
      setTimeout(updateTabArrows, 350);
    }, 100);
  }
  updateTabArrows();
  el.addEventListener('scroll', updateTabArrows, { passive: true });

  // Drag-to-scroll: only capture pointer after threshold to preserve link clicks
  let isDown = false, hasDragged = false, startX = 0, scrollStart = 0;
  const DRAG_THRESHOLD = 6;

  el.addEventListener('pointerdown', (e) => {
    isDown = true;
    hasDragged = false;
    startX = e.clientX;
    scrollStart = el.scrollLeft;
  });

  el.addEventListener('pointermove', (e) => {
    if (!isDown) return;
    const delta = startX - e.clientX;
    if (!hasDragged && Math.abs(delta) > DRAG_THRESHOLD) {
      hasDragged = true;
      el.setPointerCapture(e.pointerId);
      el.style.cursor = 'grabbing';
    }
    if (hasDragged) el.scrollLeft = scrollStart + delta;
  });

  el.addEventListener('pointerup', () => { isDown = false; el.style.cursor = ''; updateTabArrows(); });
  el.addEventListener('pointercancel', () => { isDown = false; hasDragged = false; el.style.cursor = ''; });

  // If drag happened, swallow the resulting click so links don't fire
  el.addEventListener('click', (e) => {
    if (hasDragged) { e.preventDefault(); e.stopPropagation(); hasDragged = false; }
  }, true);
}

// ============================================================
// THEME (light / dark)
// ============================================================
function initTheme() {
  setTheme(localStorage.getItem('graphlab-theme') || 'dark');
}

function toggleTheme() {
  setTheme(document.documentElement.dataset.theme === 'light' ? 'dark' : 'light');
}

function setTheme(theme) {
  if (theme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
  } else {
    document.documentElement.removeAttribute('data-theme');
  }
  localStorage.setItem('graphlab-theme', theme);
  const btn = document.getElementById('themeToggle');
  if (btn) {
    btn.querySelector('.icon-sun').style.display  = theme === 'dark'  ? '' : 'none';
    btn.querySelector('.icon-moon').style.display = theme === 'light' ? '' : 'none';
  }
  applyThemeToNetwork();
}

function applyThemeToNetwork() {
  if (!network) return;
  const ec = themeEdgeColor();
  const fc = themeFontColor();
  network.setOptions({
    edges: { color: ec },
    nodes: { font: { color: fc } },
  });
  if (edgesDS && edgesDS.length > 0) {
    edgesDS.update(edgesDS.getIds().map(id => ({ id, color: ec })));
  }
  if (nodesDS && nodesDS.length > 0) {
    nodesDS.update(nodesDS.getIds().map(id => ({
      id, color: nodeColor(id), font: { color: fc },
    })));
  }
}

function toggleNodeMode() {
  showAvatars = !showAvatars;
  const btn = document.getElementById('nodeToggle');
  if (btn) {
    btn.querySelector('.icon-face').style.display = showAvatars  ? '' : 'none';
    btn.querySelector('.icon-nums').style.display = !showAvatars ? '' : 'none';
    btn.title = showAvatars ? 'Показать цифры' : 'Показать аватарки';
  }
  if (!nodesDS || nodesDS.length === 0) return;
  const fc = themeFontColor();
  nodesDS.update(nodesDS.getIds().map(id => ({
    id,
    shape: showAvatars ? 'circularImage' : 'circle',
    image: showAvatars ? avatarUrl(id) : undefined,
    font: { color: fc },
  })));
}

// Run init after DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => { initTabCarousel(); initTheme(); });
} else {
  initTabCarousel();
  initTheme();
}
