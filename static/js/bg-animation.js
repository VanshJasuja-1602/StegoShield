// StegoShield Background Constellation — a sparse, slow field of data points.
// Decorative only: theme-aware, DPR-aware, pauses when the tab is hidden and
// renders a single static frame when the user prefers reduced motion.

document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('particle-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let width = 0;
    let height = 0;
    let particles = [];
    let rafId = null;
    let palette = getPalette();

    function getPalette() {
        const light = document.documentElement.getAttribute('data-theme') === 'light';
        return light
            ? { dots: ['91, 61, 245', '8, 145, 178', '74, 47, 224'], line: '91, 61, 245', dotAlpha: 0.32, lineAlpha: 0.08 }
            : { dots: ['180, 162, 255', '103, 232, 249', '226, 232, 255'], line: '160, 150, 255', dotAlpha: 0.55, lineAlpha: 0.11 };
    }

    function resize() {
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = Math.floor(width * dpr);
        canvas.height = Math.floor(height * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        const count = Math.min(46, Math.floor((width * height) / 32000));
        particles = Array.from({ length: count }, makeParticle);
    }

    function makeParticle() {
        return {
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.12,
            vy: (Math.random() - 0.5) * 0.12,
            r: Math.random() * 1.1 + 0.4,
            c: Math.floor(Math.random() * 3),
            a: Math.random() * 0.6 + 0.4,
            tw: Math.random() * Math.PI * 2,
        };
    }

    function draw(t) {
        ctx.clearRect(0, 0, width, height);
        const maxDist = 140;

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            for (let j = i + 1; j < particles.length; j++) {
                const q = particles[j];
                const dx = p.x - q.x;
                const dy = p.y - q.y;
                const d2 = dx * dx + dy * dy;
                if (d2 < maxDist * maxDist) {
                    const alpha = (1 - Math.sqrt(d2) / maxDist) * palette.lineAlpha;
                    ctx.strokeStyle = `rgba(${palette.line}, ${alpha})`;
                    ctx.lineWidth = 0.6;
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(q.x, q.y);
                    ctx.stroke();
                }
            }
        }

        for (const p of particles) {
            const twinkle = 0.75 + 0.25 * Math.sin(t * 0.0012 + p.tw);
            ctx.fillStyle = `rgba(${palette.dots[p.c]}, ${palette.dotAlpha * p.a * twinkle})`;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function step(t) {
        for (const p of particles) {
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < -10) p.x = width + 10;
            if (p.x > width + 10) p.x = -10;
            if (p.y < -10) p.y = height + 10;
            if (p.y > height + 10) p.y = -10;
        }
        draw(t);
        rafId = requestAnimationFrame(step);
    }

    function start() {
        if (reduceMotion) { draw(0); return; }
        if (rafId === null) rafId = requestAnimationFrame(step);
    }

    function stop() {
        if (rafId !== null) cancelAnimationFrame(rafId);
        rafId = null;
    }

    let resizeTimer = null;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => { resize(); if (reduceMotion) draw(0); }, 150);
    });

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) stop(); else start();
    });

    document.addEventListener('ss:themechange', () => {
        palette = getPalette();
        if (reduceMotion) draw(0);
    });

    resize();
    start();
});
