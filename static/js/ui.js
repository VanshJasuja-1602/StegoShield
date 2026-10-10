// StegoShield UI enhancements — presentation only.
// Theme toggle, navbar scroll state, hero comparison instrument, card spotlight,
// scroll reveals and the suspicion-score gauge. Does not touch application logic
// in main.js: it only reads values main.js already renders.

(function () {
    const root = document.documentElement;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // --- 1. Theme toggle ---
    function applyTheme(theme) {
        root.setAttribute('data-theme', theme);
        root.setAttribute('data-bs-theme', theme);
        try { localStorage.setItem('ss-theme', theme); } catch (e) { /* ignore */ }
        document.dispatchEvent(new CustomEvent('ss:themechange', { detail: { theme } }));
    }

    function initThemeToggle() {
        const btn = document.getElementById('themeToggle');
        if (!btn) return;
        const sync = () => {
            const isLight = root.getAttribute('data-theme') === 'light';
            btn.setAttribute('aria-pressed', String(isLight));
            btn.setAttribute('aria-label', isLight ? 'Switch to dark theme' : 'Switch to light theme');
        };
        sync();
        btn.addEventListener('click', () => {
            applyTheme(root.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
            sync();
        });
    }

    // --- 2. Navbar scroll state ---
    function initNavScroll() {
        const nav = document.getElementById('ssNav');
        if (!nav) return;
        let ticking = false;
        const update = () => {
            nav.classList.toggle('is-scrolled', window.scrollY > 8);
            ticking = false;
        };
        window.addEventListener('scroll', () => {
            if (!ticking) {
                ticking = true;
                requestAnimationFrame(update);
            }
        }, { passive: true });
        update();
    }

    // --- 3. Hero comparison instrument (illustrative specimen) ---
    function renderSpecimen(coverCanvas, stegoCanvas) {
        const W = coverCanvas.width;
        const H = coverCanvas.height;
        const cctx = coverCanvas.getContext('2d');
        const sctx = stegoCanvas.getContext('2d');
        const cover = cctx.createImageData(W, H);
        const stego = sctx.createImageData(W, H);
        const c = cover.data;
        const s = stego.data;

        const lerp = (a, b, t) => a + (b - a) * t;
        const clamp = (v) => (v < 0 ? 0 : v > 255 ? 255 : v);

        // Ridge heights for three mountain layers
        const ridge = (x, base, amp, f1, f2, ph) =>
            base + amp * (0.55 * Math.sin(x * f1 + ph) + 0.3 * Math.sin(x * f2 + ph * 1.7) + 0.15 * Math.sin(x * f2 * 2.3 + ph * 0.6));

        const sunX = W * 0.66;
        const sunY = H * 0.5;
        // Rows [0, payloadRows) carry a (randomised) encrypted payload — sequential LSB embedding fills top rows first.
        const payloadRows = Math.round(H * 0.36);

        // Deterministic PRNG so the specimen is stable between loads
        let seed = 1337;
        const rand = () => {
            seed = (seed * 1664525 + 1013904223) >>> 0;
            return seed / 4294967296;
        };

        // Bit-plane palette: 0..3 bits set across R,G,B
        const pal = [
            [9, 11, 24],
            [44, 32, 120],
            [124, 92, 255],
            [140, 236, 255],
        ];

        for (let y = 0; y < H; y++) {
            const ty = y / H;
            for (let x = 0; x < W; x++) {
                const i = (y * W + x) * 4;
                // Sky: midnight -> violet -> icy horizon
                let r, g, b;
                if (ty < 0.55) {
                    const t = ty / 0.55;
                    r = lerp(10, 92, t * t);
                    g = lerp(10, 70, t * t);
                    b = lerp(34, 170, t);
                } else {
                    const t = (ty - 0.55) / 0.45;
                    r = lerp(92, 150, t);
                    g = lerp(70, 190, t);
                    b = lerp(170, 220, t);
                }
                // Sun bloom
                const dx = x - sunX;
                const dy = y - sunY;
                const d = Math.sqrt(dx * dx + dy * dy);
                const bloom = Math.max(0, 1 - d / 190);
                r += 120 * bloom * bloom;
                g += 105 * bloom * bloom;
                b += 90 * bloom * bloom;
                if (d < 34) { r = lerp(r, 250, 0.9); g = lerp(g, 238, 0.9); b = lerp(b, 255, 0.9); }

                // Mountains (far -> near)
                const m1 = ridge(x, H * 0.56, 34, 0.012, 0.031, 0.4);
                const m2 = ridge(x, H * 0.68, 42, 0.009, 0.024, 2.1);
                const m3 = ridge(x, H * 0.82, 30, 0.015, 0.04, 4.2);
                if (y > m1) { const t = Math.min(1, (y - m1) / 120); r = lerp(70, 40, t); g = lerp(62, 36, t); b = lerp(150, 100, t); }
                if (y > m2) { const t = Math.min(1, (y - m2) / 140); r = lerp(36, 20, t); g = lerp(30, 18, t); b = lerp(92, 58, t); }
                if (y > m3) { const t = Math.min(1, (y - m3) / 100); r = lerp(16, 8, t); g = lerp(14, 8, t); b = lerp(44, 24, t); }

                r = clamp(Math.round(r)); g = clamp(Math.round(g)); b = clamp(Math.round(b));
                c[i] = r; c[i + 1] = g; c[i + 2] = b; c[i + 3] = 255;

                // LSB plane: payload rows -> pseudo-random bits, remainder -> natural LSBs
                let bits;
                if (y < payloadRows) {
                    bits = (rand() < 0.5 ? 1 : 0) + (rand() < 0.5 ? 1 : 0) + (rand() < 0.5 ? 1 : 0);
                } else {
                    bits = (r & 1) + (g & 1) + (b & 1);
                }
                const p = pal[bits];
                // Faint ghost of the image so the scene stays legible
                s[i] = clamp(p[0] * 0.82 + r * 0.16);
                s[i + 1] = clamp(p[1] * 0.82 + g * 0.16);
                s[i + 2] = clamp(p[2] * 0.82 + b * 0.16);
                s[i + 3] = 255;
            }
        }

        cctx.putImageData(cover, 0, 0);
        sctx.putImageData(stego, 0, 0);

        // Payload boundary marker
        sctx.save();
        sctx.strokeStyle = 'rgba(165, 243, 252, 0.7)';
        sctx.setLineDash([6, 6]);
        sctx.lineWidth = 1;
        sctx.beginPath();
        sctx.moveTo(0, payloadRows + 0.5);
        sctx.lineTo(W, payloadRows + 0.5);
        sctx.stroke();
        sctx.restore();
    }

    function initCompare() {
        const wrap = document.getElementById('heroCompare');
        const range = document.getElementById('heroCompareRange');
        const coverCanvas = document.getElementById('heroCoverCanvas');
        const stegoCanvas = document.getElementById('heroStegoCanvas');
        if (!wrap || !range || !coverCanvas || !stegoCanvas) return;

        try { renderSpecimen(coverCanvas, stegoCanvas); } catch (e) { /* decorative only */ }

        const setPos = (v) => wrap.style.setProperty('--pos', v + '%');
        range.addEventListener('input', () => setPos(range.value));
        setPos(range.value);

        // Gentle intro sweep to hint at interactivity
        if (!reduceMotion) {
            let start = null;
            let touched = false;
            range.addEventListener('pointerdown', () => { touched = true; }, { once: true });
            range.addEventListener('keydown', () => { touched = true; }, { once: true });
            const from = 50, mid = 30, dur = 1600;
            const step = (ts) => {
                if (touched) return;
                if (start === null) start = ts;
                const t = Math.min(1, (ts - start) / dur);
                const e = 0.5 - 0.5 * Math.cos(Math.PI * 2 * t); // 0 -> 1 -> 0
                const v = from + (mid - from) * e;
                range.value = v;
                setPos(v);
                if (t < 1) requestAnimationFrame(step);
            };
            setTimeout(() => requestAnimationFrame(step), 1200);
        }
    }

    // --- 4. Pointer spotlight on feature cards ---
    function initSpotlight() {
        if (window.matchMedia('(hover: none)').matches) return;
        document.querySelectorAll('[data-spotlight]').forEach((card) => {
            card.addEventListener('pointermove', (e) => {
                const r = card.getBoundingClientRect();
                card.style.setProperty('--mx', `${e.clientX - r.left}px`);
                card.style.setProperty('--my', `${e.clientY - r.top}px`);
            });
        });
    }

    // --- 5. Scroll reveals ---
    function initReveal() {
        const items = document.querySelectorAll('.ss-reveal');
        if (!items.length) return;
        if (reduceMotion || !('IntersectionObserver' in window)) {
            items.forEach((el) => el.classList.add('is-visible'));
            return;
        }
        const io = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    io.unobserve(entry.target);
                }
            });
        }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
        items.forEach((el) => io.observe(el));
    }

    // --- 6. Suspicion-score gauge (reads values main.js renders) ---
    function initGauge() {
        const scoreText = document.getElementById('suspicionScoreText');
        const badge = document.getElementById('riskLevelBadge');
        const score = document.getElementById('ssScore');
        const gauge = document.getElementById('ssGauge');
        if (!scoreText || !badge || !score || !gauge) return;

        const sync = () => {
            const n = parseFloat(scoreText.textContent);
            const value = Number.isFinite(n) ? Math.max(0, Math.min(100, n)) : 0;
            gauge.style.setProperty('--score', value);
            const m = badge.className.match(/bg-(success|warning|danger)/);
            score.setAttribute('data-risk', m ? m[1] : '');
        };

        const mo = new MutationObserver(sync);
        mo.observe(scoreText, { childList: true, characterData: true, subtree: true });
        mo.observe(badge, { attributes: true, attributeFilter: ['class'] });
        sync();
    }

    document.addEventListener('DOMContentLoaded', () => {
        initThemeToggle();
        initNavScroll();
        initCompare();
        initSpotlight();
        initReveal();
        initGauge();
    });
})();
