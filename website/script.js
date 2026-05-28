/* =========================================================================
   CAPTAIN AI - GSAP & LENIS ARCHITECTURE (AWWWARDS GRADE)
   ========================================================================= */

// Ensure GSAP plugins are registered
gsap.registerPlugin(ScrollTrigger);

document.addEventListener("DOMContentLoaded", () => {
    
    // ---------------------------------------------------------
    // 1. Lenis Smooth Scroll Initialization
    // ---------------------------------------------------------
    const lenis = new Lenis({
        duration: 1.2,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), // https://www.desmos.com/calculator/brs54l4xou
        direction: 'vertical',
        gestureDirection: 'vertical',
        smooth: true,
        mouseMultiplier: 1,
        smoothTouch: false,
        touchMultiplier: 2,
        infinite: false,
    });

    // Keep GSAP ScrollTrigger in sync with Lenis
    lenis.on('scroll', ScrollTrigger.update);

    gsap.ticker.add((time) => {
        lenis.raf(time * 1000);
    });

    gsap.ticker.lagSmoothing(0);

    // Prevent scrolling while preloader is active
    lenis.stop();


    // ---------------------------------------------------------
    // 2. Custom Magnetic Cursor
    // ---------------------------------------------------------
    const cursor = document.querySelector('.cursor');
    const follower = document.querySelector('.cursor-follower');
    
    // Use GSAP QuickSetter for massive performance boost on mouse move
    const setCursorX = gsap.quickSetter(cursor, "x", "px");
    const setCursorY = gsap.quickSetter(cursor, "y", "px");
    const setFollowerX = gsap.quickSetter(follower, "x", "px");
    const setFollowerY = gsap.quickSetter(follower, "y", "px");

    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let followerX = window.innerWidth / 2;
    let followerY = window.innerHeight / 2;

    window.addEventListener('mousemove', e => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        setCursorX(mouseX);
        setCursorY(mouseY);
    });

    // Ticker loop for the follower (gives it the "drag" feeling)
    gsap.ticker.add(() => {
        const dt = 1.0 - Math.pow(1.0 - 0.2, gsap.ticker.deltaRatio());
        followerX += (mouseX - followerX) * dt;
        followerY += (mouseY - followerY) * dt;
        setFollowerX(followerX);
        setFollowerY(followerY);
    });

    // Cursor Hover States
    const interactiveElements = document.querySelectorAll('a, button, .hover-magnet, .magnetic');
    interactiveElements.forEach(el => {
        el.addEventListener('mouseenter', () => {
            cursor.classList.add('hover-state');
            follower.classList.add('hover-state');
        });
        el.addEventListener('mouseleave', () => {
            cursor.classList.remove('hover-state');
            follower.classList.remove('hover-state');
            // Reset magnetic transform
            gsap.to(el, { x: 0, y: 0, duration: 0.5, ease: "power2.out" });
            if (el.querySelector('.magnetic-text')) {
                gsap.to(el.querySelector('.magnetic-text'), { x: 0, y: 0, duration: 0.5, ease: "power2.out" });
            }
        });

        // Magnetic Logic
        if (el.classList.contains('magnetic')) {
            el.addEventListener('mousemove', (e) => {
                const rect = el.getBoundingClientRect();
                const h = rect.width / 2;
                const v = rect.height / 2;
                const x = e.clientX - rect.left - h;
                const y = e.clientY - rect.top - v;
                
                const strength = el.dataset.strength || 20;

                gsap.to(el, {
                    x: (x / h) * strength,
                    y: (y / v) * strength,
                    duration: 0.5,
                    ease: "power2.out"
                });

                const text = el.querySelector('.magnetic-text');
                if (text) {
                    gsap.to(text, {
                        x: (x / h) * (strength / 2),
                        y: (y / v) * (strength / 2),
                        duration: 0.5,
                        ease: "power2.out"
                    });
                }
            });
        }
    });


    // ---------------------------------------------------------
    // 3. Preloader Sequence & Hero Entrance
    // ---------------------------------------------------------
    const preloaderTL = gsap.timeline();
    let loadProgress = { val: 0 };
    const percentageText = document.querySelector('.loading-percentage');

    preloaderTL.to(loadProgress, {
        val: 100,
        duration: 2.5,
        ease: "power3.inOut",
        onUpdate: function() {
            percentageText.innerText = Math.floor(loadProgress.val);
            gsap.set('.loading-bar', { width: loadProgress.val + '%' });
        }
    })
    .to('.loading-text', { opacity: 0, duration: 0.5 }, "-=0.2")
    .to('.loading-bar-container', { scaleX: 0, transformOrigin: "center", duration: 0.8, ease: "power3.inOut" }, "-=0.3")
    .to('.preloader-logo', { y: -20, opacity: 0, duration: 0.6, ease: "power2.in" }, "-=0.6")
    .to('.preloader', {
        yPercent: -100,
        duration: 1.2,
        ease: "expo.inOut",
        onComplete: () => {
            lenis.start(); // Unlock scrolling
            heroEntranceTL.play(); // Trigger hero
        }
    });


    // Hero Entrance Timeline (Paused initially)
    const heroEntranceTL = gsap.timeline({ paused: true });
    
    heroEntranceTL
        .to('.liquid-nav', { opacity: 1, y: 0, duration: 1, ease: "power3.out" }, 0.2)
        .to('.headline', { opacity: 1, y: 0, duration: 1.5, ease: "power4.out" }, 0.4)
        .to('.hero .fade-up', { opacity: 1, y: 0, duration: 1, stagger: 0.2, ease: "power3.out" }, 0.8)
        .to('.scroll-indicator', { opacity: 1, y: 0, duration: 1 }, 1.5);

    // Initial setup for hero elements (GSAP handles this better than CSS for complex sequencing)
    gsap.set('.liquid-nav', { y: -50 });
    gsap.set('.headline', { y: 100 });
    gsap.set('.hero .fade-up', { y: 40 });
    gsap.set('.scroll-indicator', { y: 20 });


    // ---------------------------------------------------------
    // 4. ScrollTrigger Animations
    // ---------------------------------------------------------
    
    // Generic Fade Ups
    const fadeUps = document.querySelectorAll('.matrix-section .fade-up');
    fadeUps.forEach(el => {
        gsap.from(el, {
            scrollTrigger: {
                trigger: el,
                start: "top 85%",
            },
            y: 60,
            opacity: 0,
            duration: 1,
            ease: "power3.out"
        });
    });

    // Heading Line Stretches
    const lines = document.querySelectorAll('.stretch-line');
    lines.forEach(line => {
        gsap.to(line, {
            scrollTrigger: {
                trigger: line,
                start: "top 90%",
            },
            width: "60px",
            duration: 1,
            ease: "power3.out"
        });
    });

    // Liquid Cards Staggered Reveal
    gsap.from('.liquid-card', {
        scrollTrigger: {
            trigger: '.asymmetric-grid',
            start: "top 80%",
        },
        y: 100,
        opacity: 0,
        duration: 1.2,
        stagger: 0.15,
        ease: "power4.out"
    });

    // Architecture Pinning
    // We pin the left text while the right side code visualizer scrolls into view
    ScrollTrigger.matchMedia({
        // Desktop only
        "(min-width: 1025px)": function() {
            gsap.to('.arch-left', {
                scrollTrigger: {
                    trigger: '.arch-container',
                    start: "top top+=150",
                    end: "bottom bottom",
                    pin: '.arch-left',
                    pinSpacing: false
                }
            });
        }
    });

    // Parallax Elements
    const parallaxCards = document.querySelectorAll('.parallax-card');
    parallaxCards.forEach(card => {
        const speed = card.dataset.speed || 1.1;
        gsap.to(card, {
            scrollTrigger: {
                trigger: card,
                start: "top bottom",
                end: "bottom top",
                scrub: true
            },
            y: (i, target) => -ScrollTrigger.maxScroll(window) * (speed - 1),
            ease: "none"
        });
    });


    // ---------------------------------------------------------
    // 5. Terminal Mock Interaction
    // ---------------------------------------------------------
    const form = document.querySelector('.terminal-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const btn = form.querySelector('button');
            const span = btn.querySelector('span');
            const originalText = span.innerText;

            span.innerText = "UPLINK ESTABLISHED";
            gsap.to(btn, {
                background: "linear-gradient(135deg, #00FF55, #00B33C)",
                boxShadow: "0 0 30px rgba(0, 255, 85, 0.4)",
                duration: 0.3
            });

            setTimeout(() => {
                span.innerText = originalText;
                gsap.to(btn, {
                    background: "#FFFFFF",
                    boxShadow: "none",
                    duration: 0.3
                });
                form.reset();
            }, 3000);
        });
    }

});
