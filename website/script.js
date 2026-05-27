/* =========================================================================
   CAPTAIN AI - ULTIMATE JAVASCRIPT INTERACTIONS
   Magnetic buttons, premium scroll reveals, parallax elements.
   ========================================================================= */

document.addEventListener('DOMContentLoaded', () => {

    // ---------------------------------------------------------
    // 1. Premium Scroll Reveal (Intersection Observer)
    // ---------------------------------------------------------
    const revealElements = document.querySelectorAll('.reveal');

    const revealOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add('active');
            observer.unobserve(entry.target);
        });
    }, revealOptions);

    revealElements.forEach(el => {
        revealObserver.observe(el);
    });

    // ---------------------------------------------------------
    // 2. Magnetic Buttons (World-Class Interaction)
    // ---------------------------------------------------------
    /* This creates a physical "pull" effect when the cursor is near the button */
    const magneticButtons = document.querySelectorAll('.magnetic');

    magneticButtons.forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            // Calculate distance from center of button
            const x = (e.clientX - rect.left) - (rect.width / 2);
            const y = (e.clientY - rect.top) - (rect.height / 2);

            // Move button slightly towards the cursor (magic number 0.3 controls strength)
            btn.style.transform = `translate(${x * 0.3}px, ${y * 0.3}px)`;

            // Move the inner text slightly farther for a parallax depth effect
            const span = btn.querySelector('span');
            if (span) {
                span.style.transform = `translate(${x * 0.15}px, ${y * 0.15}px)`;
            }
        });

        btn.addEventListener('mouseleave', () => {
            // Snap back with buttery CSS transition
            btn.style.transform = 'translate(0px, 0px)';
            const span = btn.querySelector('span');
            if (span) span.style.transform = 'translate(0px, 0px)';
        });
    });

    // ---------------------------------------------------------
    // 3. Smooth Anchor Scrolling
    // ---------------------------------------------------------
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // ---------------------------------------------------------
    // 4. Form Submission Mock (Cyber UI)
    // ---------------------------------------------------------
    const form = document.querySelector('.terminal-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const btn = form.querySelector('.magnetic');
            const span = btn.querySelector('span');
            const originalText = span.innerText;

            // Cyberpunk "Hacking" accepted state
            span.innerText = "ACCESS GRANTED";
            btn.style.background = "linear-gradient(135deg, #00FF55, #00B33C)";
            btn.style.boxShadow = "0 0 30px rgba(0, 255, 85, 0.4)";

            setTimeout(() => {
                span.innerText = originalText;
                btn.style.background = "";
                btn.style.boxShadow = "";
                form.reset();
            }, 3000);
        });
    }
});
