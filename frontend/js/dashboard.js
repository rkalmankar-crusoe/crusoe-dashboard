let compareMode = false;

function showDatacenter(id) {
    // Hide comparison view
    document.getElementById('comparisonView').classList.remove('active');

    // Hide all sections
    document.querySelectorAll('.datacenter-section').forEach(section => {
        section.classList.remove('active');
    });

    // Remove active class from all tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected section
    document.getElementById(id).classList.add('active');

    // Add active class to clicked tab
    event.target.classList.add('active');
}

function toggleCompareMode() {
    compareMode = !compareMode;
    const compareBtn = document.querySelector('.compare-btn');
    const comparisonView = document.getElementById('comparisonView');

    if (compareMode) {
        compareBtn.classList.add('active');
        // Hide all datacenter sections
        document.querySelectorAll('.datacenter-section').forEach(section => {
            section.classList.remove('active');
        });
        // Show comparison view
        comparisonView.classList.add('active');
        // Remove active from all tabs
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
    } else {
        compareBtn.classList.remove('active');
        comparisonView.classList.remove('active');
        // Show Dallas by default
        document.getElementById('dallas').classList.add('active');
        document.querySelector('.tab').classList.add('active');
    }
}

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Sticky tabs on scroll
window.addEventListener('scroll', () => {
    const tabs = document.getElementById('mainTabs');
    const placeholder = document.getElementById('tabsPlaceholder');
    const backToTop = document.getElementById('backToTop');

    if (window.scrollY > 300) {
        tabs.classList.add('sticky');
        placeholder.classList.add('active');
        backToTop.classList.add('visible');
    } else {
        tabs.classList.remove('sticky');
        placeholder.classList.remove('active');
        backToTop.classList.remove('visible');
    }
});

// Animate progress bars on load
window.addEventListener('load', () => {
    document.querySelectorAll('.progress-fill').forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0';
        setTimeout(() => {
            bar.style.width = width;
        }, 100);
    });
});
