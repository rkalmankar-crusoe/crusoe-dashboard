let compareMode = false;

// Refresh dashboard
function refreshDashboard() {
    const btn = event.target;
    btn.style.transform = 'rotate(360deg)';
    btn.style.transition = 'transform 0.5s ease';

    setTimeout(() => {
        location.reload();
    }, 500);
}

// Update timestamp
function updateTimestamp() {
    const now = new Date();
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    };
    const timeString = now.toLocaleString('en-US', options);
    const timeElement = document.getElementById('updateTime');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
}

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

// Animate progress bars on load and update timestamp
window.addEventListener('load', () => {
    document.querySelectorAll('.progress-fill').forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0';
        setTimeout(() => {
            bar.style.width = width;
        }, 100);
    });

    // Update timestamp on load
    updateTimestamp();
});
