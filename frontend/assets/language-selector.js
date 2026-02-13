/**
 * Language Selector Component for ReadySetClass™
 * Dropdown selector with flags
 */

function createLanguageSelector(containerId = 'language-selector') {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Container #${containerId} not found`);
        return;
    }

    const languages = window.i18n.getSupportedLanguages();
    const currentLang = window.i18n.getLang();

    // Create selector HTML
    const selectorHTML = `
        <div class="language-selector">
            <button class="lang-button" id="lang-btn" aria-label="Select Language" aria-haspopup="true" aria-expanded="false">
                <span class="lang-flag">${languages[currentLang].flag}</span>
                <span class="lang-name">${languages[currentLang].name}</span>
                <svg class="lang-arrow" width="12" height="8" viewBox="0 0 12 8" fill="none">
                    <path d="M1 1.5L6 6.5L11 1.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
            <div class="lang-dropdown" id="lang-dropdown" role="menu" aria-hidden="true">
                ${Object.entries(languages).map(([code, info]) => `
                    <button
                        class="lang-option ${code === currentLang ? 'active' : ''}"
                        data-lang="${code}"
                        role="menuitem"
                        aria-label="${info.name}">
                        <span class="lang-flag">${info.flag}</span>
                        <span class="lang-name">${info.name}</span>
                        ${code === currentLang ? '<span class="lang-check">✓</span>' : ''}
                    </button>
                `).join('')}
            </div>
        </div>
    `;

    container.innerHTML = selectorHTML;

    // Add styles
    addLanguageSelectorStyles();

    // Add event listeners
    setupLanguageSelectorEvents();
}

function addLanguageSelectorStyles() {
    if (document.getElementById('lang-selector-styles')) return;

    const style = document.createElement('style');
    style.id = 'lang-selector-styles';
    style.textContent = `
        .language-selector {
            position: relative;
            display: inline-block;
        }

        .lang-button {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: white;
            border: 1px solid #E8E8E8;
            border-radius: 8px;
            cursor: pointer;
            font-family: inherit;
            font-size: 0.9rem;
            transition: all 0.2s ease;
        }

        .lang-button:hover {
            background: #FAF8F3;
            border-color: #C9A961;
        }

        .lang-button:focus {
            outline: none;
            box-shadow: 0 0 0 3px rgba(201, 169, 97, 0.2);
        }

        .lang-flag {
            font-size: 1.2rem;
            line-height: 1;
        }

        .lang-name {
            font-weight: 500;
            color: #2C2C2C;
        }

        .lang-arrow {
            margin-left: 0.25rem;
            transition: transform 0.2s ease;
        }

        .lang-button[aria-expanded="true"] .lang-arrow {
            transform: rotate(180deg);
        }

        .lang-dropdown {
            position: absolute;
            top: calc(100% + 0.5rem);
            right: 0;
            min-width: 200px;
            background: white;
            border: 1px solid #E8E8E8;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(30, 58, 95, 0.15);
            opacity: 0;
            visibility: hidden;
            transform: translateY(-10px);
            transition: all 0.2s ease;
            z-index: 1000;
            overflow: hidden;
        }

        .lang-dropdown[aria-hidden="false"] {
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }

        .lang-option {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            width: 100%;
            padding: 0.75rem 1rem;
            background: white;
            border: none;
            border-bottom: 1px solid #F5F5F5;
            cursor: pointer;
            font-family: inherit;
            font-size: 0.9rem;
            text-align: left;
            transition: background 0.15s ease;
        }

        .lang-option:last-child {
            border-bottom: none;
        }

        .lang-option:hover {
            background: #FAF8F3;
        }

        .lang-option.active {
            background: rgba(201, 169, 97, 0.1);
        }

        .lang-option .lang-flag {
            font-size: 1.3rem;
        }

        .lang-option .lang-name {
            flex: 1;
            color: #2C2C2C;
        }

        .lang-check {
            color: #C9A961;
            font-weight: 600;
        }

        /* RTL Support */
        [dir="rtl"] .lang-dropdown {
            right: auto;
            left: 0;
        }

        /* Mobile responsive */
        @media (max-width: 640px) {
            .lang-button .lang-name {
                display: none;
            }

            .lang-dropdown {
                right: auto;
                left: 50%;
                transform: translateX(-50%) translateY(-10px);
            }

            .lang-dropdown[aria-hidden="false"] {
                transform: translateX(-50%) translateY(0);
            }
        }
    `;

    document.head.appendChild(style);
}

function setupLanguageSelectorEvents() {
    const button = document.getElementById('lang-btn');
    const dropdown = document.getElementById('lang-dropdown');

    if (!button || !dropdown) return;

    // Toggle dropdown
    button.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = dropdown.getAttribute('aria-hidden') === 'false';

        if (isOpen) {
            closeDropdown();
        } else {
            openDropdown();
        }
    });

    // Language selection
    dropdown.querySelectorAll('.lang-option').forEach(option => {
        option.addEventListener('click', async (e) => {
            const lang = e.currentTarget.dataset.lang;

            // Show loading state
            button.style.opacity = '0.6';
            button.disabled = true;

            // Change language
            await window.i18n.setLanguage(lang);

            // Update selector UI
            updateSelector(lang);

            // Close dropdown
            closeDropdown();

            // Restore button
            button.style.opacity = '1';
            button.disabled = false;

            // Reload page to update all translations
            // (In production, you'd update translations dynamically)
            window.location.reload();
        });
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.language-selector')) {
            closeDropdown();
        }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && dropdown.getAttribute('aria-hidden') === 'false') {
            closeDropdown();
            button.focus();
        }
    });

    function openDropdown() {
        dropdown.setAttribute('aria-hidden', 'false');
        button.setAttribute('aria-expanded', 'true');
    }

    function closeDropdown() {
        dropdown.setAttribute('aria-hidden', 'true');
        button.setAttribute('aria-expanded', 'false');
    }

    function updateSelector(lang) {
        const languages = window.i18n.getSupportedLanguages();
        const langInfo = languages[lang];

        // Update button
        button.querySelector('.lang-flag').textContent = langInfo.flag;
        button.querySelector('.lang-name').textContent = langInfo.name;

        // Update dropdown options
        dropdown.querySelectorAll('.lang-option').forEach(option => {
            const optionLang = option.dataset.lang;
            const check = option.querySelector('.lang-check');

            if (optionLang === lang) {
                option.classList.add('active');
                if (!check) {
                    option.innerHTML += '<span class="lang-check">✓</span>';
                }
            } else {
                option.classList.remove('active');
                if (check) {
                    check.remove();
                }
            }
        });
    }
}

// Initialize when i18n is ready
window.addEventListener('languageChanged', () => {
    // Refresh selector if it exists
    if (document.getElementById('language-selector')) {
        createLanguageSelector();
    }
});

// Make available globally
window.createLanguageSelector = createLanguageSelector;
