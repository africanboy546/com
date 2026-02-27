// static/js/main.js

// ===== AGE GATE =====
document.addEventListener('DOMContentLoaded', function () {
    // Check if age has been verified
    const ageVerified = localStorage.getItem('age-verified') === 'true';
    const ageGate = document.getElementById('age-gate');

    if (!ageVerified && ageGate) {
        ageGate.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    } else if (ageGate) {
        ageGate.style.display = 'none';
        document.body.style.overflow = 'auto';
    }

    // Age gate buttons
    const enterBtn = document.getElementById('enter-btn');
    const exitBtn = document.getElementById('exit-btn');

    if (enterBtn) {
        enterBtn.addEventListener('click', function () {
            localStorage.setItem('age-verified', 'true');
            ageGate.style.display = 'none';
            document.body.style.overflow = 'auto';
            showToast('🎉 Welcome to VelvetSignals!', 'success');
        });
    }

    if (exitBtn) {
        exitBtn.addEventListener('click', function () {
            window.location.href = 'https://www.google.com';
        });
    }
});

// ===== NAVIGATION =====
document.addEventListener('DOMContentLoaded', function () {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const navMenu = document.getElementById('nav-menu');
    const navbar = document.getElementById('navbar');

    if (mobileMenuBtn && navMenu) {
        mobileMenuBtn.addEventListener('click', function () {
            navMenu.classList.toggle('active');
            const icon = mobileMenuBtn.querySelector('i');
            if (icon) {
                icon.className = navMenu.classList.contains('active')
                    ? 'fas fa-times'
                    : 'fas fa-bars';
            }
        });
    }

    // Close mobile menu when clicking a link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function () {
            if (navMenu && navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                const icon = mobileMenuBtn?.querySelector('i');
                if (icon) icon.className = 'fas fa-bars';
            }
        });
    });

    // Navbar scroll effect
    window.addEventListener('scroll', function () {
        if (navbar) {
            if (window.scrollY > 100) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }
    });

    // Active nav link based on scroll position
    const sections = document.querySelectorAll('section[id]');
    window.addEventListener('scroll', function () {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            const sectionHeight = section.clientHeight;
            if (window.scrollY >= sectionTop && window.scrollY < sectionTop + sectionHeight) {
                current = section.getAttribute('id');
            }
        });

        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
});

// ===== THEME TOGGLE =====
document.addEventListener('DOMContentLoaded', function () {
    const themeToggle = document.getElementById('theme-toggle');
    const html = document.documentElement;

    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        html.classList.remove('dark');
        if (themeToggle) {
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        }
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            const isDark = html.classList.contains('dark');
            if (isDark) {
                html.classList.remove('dark');
                themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
                localStorage.setItem('theme', 'light');
            } else {
                html.classList.add('dark');
                themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
                localStorage.setItem('theme', 'dark');
            }
        });
    }
});

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'info') {
    if (typeof Toastify === 'undefined') {
        console.log('Toastify not loaded');
        return;
    }

    const colors = {
        success: 'linear-gradient(135deg, #10b981, #059669)',
        warning: 'linear-gradient(135deg, #f59e0b, #d97706)',
        info: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
        danger: 'linear-gradient(135deg, #ef4444, #dc2626)'
    };

    Toastify({
        text: message,
        duration: 3000,
        gravity: 'top',
        position: 'right',
        backgroundColor: colors[type] || colors.info,
        stopOnFocus: true,
        style: {
            borderRadius: 'var(--radius-md)',
            fontFamily: 'Inter, sans-serif',
            fontSize: '0.9375rem',
            padding: '1rem 1.5rem',
            boxShadow: 'var(--shadow-lg)'
        }
    }).showToast();
}

// ===== LIVE UPDATES =====
function addNotification(title, message, type = 'info') {
    const updatesContainer = document.getElementById('live-updates');
    if (!updatesContainer) return;

    const icons = {
        welcome: 'fa-party-horn',
        twitter: 'fa-twitter',
        success: 'fa-check-circle',
        info: 'fa-info-circle',
        user: 'fa-user-plus',
        trending: 'fa-fire',
        milestone: 'fa-trophy'
    };

    const notificationId = `notification-${Date.now()}`;
    const icon = icons[type] || icons.info;

    const notification = document.createElement('div');
    notification.className = 'live-notification';
    notification.id = notificationId;
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="fas ${icon}"></i>
        </div>
        <div class="notification-content">
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
            <div class="notification-time">just now</div>
        </div>
        <button class="notification-close" onclick="removeNotification('${notificationId}')">
            <i class="fas fa-times"></i>
        </button>
    `;

    updatesContainer.appendChild(notification);

    // Auto-remove after 8 seconds
    setTimeout(() => {
        removeNotification(notificationId);
    }, 8000);

    // Limit to 5 notifications
    const notifications = updatesContainer.querySelectorAll('.live-notification');
    if (notifications.length > 5) {
        notifications[0].remove();
    }
}

function removeNotification(id) {
    const notification = document.getElementById(id);
    if (notification) {
        notification.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }
}

// ===== SEARCH FUNCTIONALITY =====
function initializeSearch() {
    const searchBox = document.getElementById('search-box');
    const searchResults = document.getElementById('search-results');

    if (!searchBox || !searchResults) return;

    let searchTimeout;

    searchBox.addEventListener('input', function () {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        if (query.length < 2) {
            searchResults.classList.remove('active');
            return;
        }

        searchTimeout = setTimeout(() => {
            fetch(`/api/search?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    displaySearchResults(data.creators);
                })
                .catch(error => {
                    console.error('Search error:', error);
                });
        }, 300);
    });

    // Close search results when clicking outside
    document.addEventListener('click', function (e) {
        if (!searchContainer.contains(e.target)) {
            searchResults.classList.remove('active');
        }
    });
}

function displaySearchResults(creators) {
    const searchResults = document.getElementById('search-results');

    if (!creators || creators.length === 0) {
        searchResults.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search" style="font-size: 2rem; margin-bottom: 1rem; color: var(--gray);"></i>
                <p>No creators found. Try different keywords.</p>
            </div>
        `;
        searchResults.classList.add('active');
        return;
    }

    let resultsHTML = '';

    creators.slice(0, 10).forEach(creator => {
        resultsHTML += `
            <div class="search-result-item" onclick="window.location.href='/creator/${creator.username}'">
                <img src="${creator.avatar}" alt="${creator.name}" class="search-result-avatar">
                <div class="search-result-info">
                    <div class="search-result-name">${creator.name}</div>
                    <div class="search-result-username">@${creator.username}</div>
                </div>
                <div style="color: var(--primary);">
                    <i class="fas fa-arrow-right"></i>
                </div>
            </div>
        `;
    });

    searchResults.innerHTML = resultsHTML;
    searchResults.classList.add('active');
}

// ===== LOAD MORE CREATORS =====
function loadMoreCreators() {
    const button = document.getElementById('load-more');
    if (!button) return;

    const spinner = button.querySelector('.load-more-spinner');
    const text = button.querySelector('.btn-text');
    const currentPage = parseInt(button.dataset.page || '1');

    button.disabled = true;
    if (text) text.style.opacity = '0.5';
    if (spinner) spinner.style.opacity = '1';

    fetch(`/api/creators?page=${currentPage + 1}`)
        .then(response => response.json())
        .then(data => {
            if (data.creators && data.creators.length > 0) {
                renderCreators(data.creators);
                button.dataset.page = data.current_page;

                if (!data.has_next) {
                    button.style.display = 'none';
                }
            } else {
                button.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error loading creators:', error);
            showToast('Error loading creators. Please try again.', 'danger');
        })
        .finally(() => {
            button.disabled = false;
            if (text) text.style.opacity = '1';
            if (spinner) spinner.style.opacity = '0';
        });
}

function renderCreators(creators) {
    const grid = document.getElementById('creators-grid');
    if (!grid) return;

    creators.forEach(creator => {
        const badges = [];
        if (creator.is_featured) badges.push('<span class="badge badge-featured">Featured</span>');
        if (creator.is_verified) badges.push('<span class="badge badge-verified">Verified</span>');

        const card = document.createElement('div');
        card.className = 'creator-card';
        card.innerHTML = `
            <div class="creator-cover">
                <img src="${creator.wallpaper || '/static/images/default-wallpaper.jpg'}" alt="${creator.name}" class="creator-cover-img">
                <div class="creator-badges">
                    ${badges.join('')}
                </div>
                <img src="${creator.avatar}" alt="${creator.name}" class="creator-avatar">
            </div>
            <div class="creator-info">
                <div class="creator-name">
                    <h3>${creator.name}</h3>
                    <span class="creator-username">@${creator.username}</span>
                </div>
                <p class="creator-bio">${creator.bio || 'No bio yet'}</p>
                
                <div class="creator-stats">
                    <div class="stat-item">
                        <span class="stat-label">Followers</span>
                        <span class="stat-value">${creator.followers || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Views</span>
                        <span class="stat-value">${creator.views || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Likes</span>
                        <span class="stat-value">${creator.likes || 0}</span>
                    </div>
                </div>
                
                <div class="creator-actions">
                    <button class="btn btn-primary btn-sm" onclick="window.location.href='/creator/${creator.username}'">
                        <i class="fas fa-eye"></i> View Profile
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="followCreator(${creator.id})">
                        <i class="fas fa-plus"></i> Follow
                    </button>
                </div>
            </div>
        `;

        grid.appendChild(card);
    });
}

// ===== FOLLOW CREATOR =====
function followCreator(creatorId) {
    if (!isAuthenticated) {
        showToast('Please log in to follow creators', 'warning');
        window.location.href = '/auth/login';
        return;
    }

    fetch(`/follow/${creatorId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.action === 'followed') {
                showToast('Successfully followed!', 'success');
            } else {
                showToast('Unfollowed', 'info');
            }
            // Update follow button UI
            updateFollowButton(creatorId, data.action);
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error following creator', 'danger');
        });
}

function updateFollowButton(creatorId, action) {
    const button = document.querySelector(`[onclick="followCreator(${creatorId})"]`);
    if (button) {
        if (action === 'followed') {
            button.innerHTML = '<i class="fas fa-check"></i> Following';
            button.classList.remove('btn-primary');
            button.classList.add('btn-secondary');
        } else {
            button.innerHTML = '<i class="fas fa-plus"></i> Follow';
            button.classList.remove('btn-secondary');
            button.classList.add('btn-primary');
        }
    }
}

// ===== LIKE POST =====
function likePost(postId) {
    if (!isAuthenticated) {
        showToast('Please log in to like posts', 'warning');
        window.location.href = '/auth/login';
        return;
    }

    fetch(`/post/${postId}/like`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
        .then(response => response.json())
        .then(data => {
            const likeButton = document.querySelector(`[onclick="likePost(${postId})"]`);
            if (likeButton) {
                const countSpan = likeButton.querySelector('.like-count');
                if (countSpan) {
                    countSpan.textContent = data.likes;
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// ===== ADD COMMENT =====
function addComment(postId) {
    const input = document.getElementById(`comment-input-${postId}`);
    const content = input.value.trim();

    if (!content) return;

    fetch(`/post/${postId}/comment`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ content: content })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Add comment to UI
                const commentsList = document.getElementById(`comments-${postId}`);
                const commentHtml = `
                <div class="comment-item">
                    <img src="${data.comment.avatar}" alt="${data.comment.author}" class="comment-avatar">
                    <div class="comment-content">
                        <div class="comment-author">${data.comment.author}</div>
                        <div class="comment-text">${data.comment.content}</div>
                        <div class="comment-time">${data.comment.created_at}</div>
                    </div>
                </div>
            `;
                commentsList.insertAdjacentHTML('afterbegin', commentHtml);
                input.value = '';
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// ===== UTILITY FUNCTIONS =====
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function timeAgo(date) {
    const seconds = Math.floor((new Date() - new Date(date)) / 1000);

    let interval = Math.floor(seconds / 31536000);
    if (interval > 1) return interval + ' years ago';

    interval = Math.floor(seconds / 2592000);
    if (interval > 1) return interval + ' months ago';

    interval = Math.floor(seconds / 86400);
    if (interval > 1) return interval + ' days ago';

    interval = Math.floor(seconds / 3600);
    if (interval > 1) return interval + ' hours ago';

    interval = Math.floor(seconds / 60);
    if (interval > 1) return interval + ' minutes ago';

    return 'just now';
}

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function () {
    // Initialize search if element exists
    if (document.getElementById('search-box')) {
        initializeSearch();
    }

    // Initialize load more button
    const loadMoreBtn = document.getElementById('load-more');
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', loadMoreCreators);
    }

    // Auto-hide flash messages
    setTimeout(() => {
        document.querySelectorAll('.flash-message').forEach(msg => {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 300);
        });
    }, 5000);

    // Initialize live updates (demo)
    setInterval(() => {
        if (Math.random() > 0.7) {
            const notifications = [
                { title: 'New Creator Joined', message: 'Welcome to our newest creator!', type: 'user' },
                { title: 'Milestone Reached', message: 'We just hit 10,000 total views!', type: 'milestone' },
                { title: 'Trending Now', message: 'Check out today\'s trending creators', type: 'trending' }
            ];
            const notif = notifications[Math.floor(Math.random() * notifications.length)];
            addNotification(notif.title, notif.message, notif.type);
        }
    }, 30000);
});


// ===== SEARCH FUNCTIONALITY =====
function initializeSearch() {
    const searchBox = document.getElementById('search-box');
    const searchResults = document.getElementById('search-results');

    if (!searchBox || !searchResults) return;

    let searchTimeout;

    searchBox.addEventListener('input', function () {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        if (query.length < 2) {
            searchResults.classList.remove('active');
            return;
        }

        searchTimeout = setTimeout(() => {
            fetch(`/api/search?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    displaySearchResults(data.creators);
                })
                .catch(error => {
                    console.error('Search error:', error);
                });
        }, 300);
    });

    document.addEventListener('click', function (e) {
        if (!searchBox.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.remove('active');
        }
    });
}

function displaySearchResults(creators) {
    const searchResults = document.getElementById('search-results');

    if (!creators || creators.length === 0) {
        searchResults.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search" style="font-size: 2rem; margin-bottom: 1rem; color: var(--gray);"></i>
                <p>No creators found. Try different keywords.</p>
            </div>
        `;
        searchResults.classList.add('active');
        return;
    }

    let resultsHTML = '';

    creators.slice(0, 10).forEach(creator => {
        resultsHTML += `
            <div class="search-result-item" onclick="window.location.href='/creator/${creator.username}'">
                <img src="${creator.avatar}" alt="${creator.name}" class="search-result-avatar">
                <div class="search-result-info">
                    <div class="search-result-name">${creator.name}</div>
                    <div class="search-result-username">@${creator.username}</div>
                </div>
                <div style="color: var(--primary);">
                    <i class="fas fa-arrow-right"></i>
                </div>
            </div>
        `;
    });

    searchResults.innerHTML = resultsHTML;
    searchResults.classList.add('active');
}

// Initialize search on page load
document.addEventListener('DOMContentLoaded', function () {
    initializeSearch();

    // Initialize load more button
    const loadMoreBtn = document.getElementById('load-more');
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', loadMoreCreators);
    }
});

function loadMoreCreators() {
    const button = document.getElementById('load-more');
    const spinner = button.querySelector('.load-more-spinner');
    const text = button.querySelector('.btn-text');
    const currentPage = parseInt(button.dataset.page || '1');

    button.disabled = true;
    if (text) text.style.opacity = '0.5';
    if (spinner) spinner.style.opacity = '1';

    fetch(`/api/creators?page=${currentPage + 1}`)
        .then(response => response.json())
        .then(data => {
            if (data.creators && data.creators.length > 0) {
                renderCreators(data.creators);
                button.dataset.page = data.current_page;

                if (!data.has_next) {
                    button.style.display = 'none';
                }
            } else {
                button.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error loading creators:', error);
            showToast('Error loading creators. Please try again.', 'danger');
        })
        .finally(() => {
            button.disabled = false;
            if (text) text.style.opacity = '1';
            if (spinner) spinner.style.opacity = '0';
        });
}

function renderCreators(creators) {
    const grid = document.getElementById('creators-grid');
    if (!grid) return;

    creators.forEach(creator => {
        const badges = [];
        if (creator.is_featured) badges.push('<span class="badge badge-featured">Featured</span>');
        if (creator.is_verified) badges.push('<span class="badge badge-verified">Verified</span>');

        const card = document.createElement('div');
        card.className = 'creator-card';
        card.onclick = () => window.location.href = `/creator/${creator.username}`;
        card.innerHTML = `
            <div class="creator-cover">
                <img src="${creator.wallpaper || '/static/images/default-wallpaper.jpg'}" alt="${creator.name}" class="creator-cover-img">
                <div class="creator-badges">
                    ${badges.join('')}
                </div>
                <img src="${creator.avatar}" alt="${creator.name}" class="creator-avatar">
            </div>
            <div class="creator-info">
                <div class="creator-name">
                    <h3>${creator.name}</h3>
                    <span class="creator-username">@${creator.username}</span>
                </div>
                <p class="creator-bio">${creator.bio || 'No bio yet'}</p>
                
                <div class="creator-stats">
                    <div class="stat-item">
                        <span class="stat-label">Followers</span>
                        <span class="stat-value">${creator.followers || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Views</span>
                        <span class="stat-value">${creator.views || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Likes</span>
                        <span class="stat-value">${creator.likes || 0}</span>
                    </div>
                </div>
                
                <div class="creator-actions">
                    <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); window.location.href='/creator/${creator.username}'">
                        <i class="fas fa-eye"></i> View Profile
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); followCreator(${creator.id})">
                        <i class="fas fa-plus"></i> Follow
                    </button>
                </div>
            </div>
        `;

        grid.appendChild(card);
    });
}

// Tab switching functions
function showUploadTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.upload-tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.currentTarget.classList.add('active');

    // Show selected content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tab}-upload`).classList.add('active');
}

function showGalleryTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.gallery-tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.currentTarget.classList.add('active');

    // Show selected gallery
    document.querySelectorAll('#images-gallery, #videos-gallery').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tab}-gallery`).classList.add('active');
}

// Media view functions
function viewMedia(url, type) {
    const modal = document.getElementById('mediaModal');
    const body = document.getElementById('mediaModalBody');
    const title = document.getElementById('mediaModalTitle');

    title.textContent = type === 'image' ? 'Image View' : 'Video View';

    if (type === 'image') {
        body.innerHTML = `<img src="${url}" alt="Gallery image">`;
    } else {
        body.innerHTML = `
            <video controls autoplay>
                <source src="${url}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        `;
    }

    modal.classList.add('active');
}

function closeMediaModal() {
    document.getElementById('mediaModal').classList.remove('active');
    document.getElementById('mediaModalBody').innerHTML = '';
}

// Delete function
function deleteImage(imageId) {
    if (confirm('Are you sure you want to delete this media?')) {
        fetch(`/gallery/delete/${imageId}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token() }}'
            }
        })
            .then(response => {
                if (response.ok) {
                    location.reload();
                } else {
                    alert('Failed to delete media');
                }
            });
    }
}

// Load more functions (implement these based on your pagination)
function loadMoreImages() {
    // Implement pagination for images
    console.log('Load more images');
}

function loadMoreVideos() {
    // Implement pagination for videos
    console.log('Load more videos');
}

// Close modal when clicking outside
window.onclick = function (event) {
    const modal = document.getElementById('mediaModal');
    if (event.target == modal) {
        closeMediaModal();
    }
}

// Global variable for authentication status
window.isAuthenticated = document.body.classList.contains('user-authenticated');

// Export functions to global scope
window.showToast = showToast;
window.addNotification = addNotification;
window.removeNotification = removeNotification;
window.followCreator = followCreator;
window.likePost = likePost;
window.addComment = addComment;