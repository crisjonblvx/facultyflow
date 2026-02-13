/**
 * ReadySetClass™ Internationalization (i18n) System
 * Simple, lightweight translation library
 */

class I18n {
    constructor() {
        this.translations = {};
        this.currentLang = 'en';
        this.defaultLang = 'en';
        this.supportedLanguages = {
            'en': { name: 'English', flag: '🇺🇸', dir: 'ltr' },
            'es': { name: 'Español', flag: '🇪🇸', dir: 'ltr' },
            'fr': { name: 'Français', flag: '🇫🇷', dir: 'ltr' },
            'pt': { name: 'Português', flag: '🇧🇷', dir: 'ltr' },
            'ar': { name: 'العربية', flag: '🇸🇦', dir: 'rtl' },
            'zh': { name: '中文', flag: '🇨🇳', dir: 'ltr' }
        };
    }

    /**
     * Initialize i18n with user's preferred language
     */
    async init() {
        // Get saved language or detect from browser
        const savedLang = localStorage.getItem('language');
        const browserLang = navigator.language.split('-')[0];

        // Determine initial language
        const lang = savedLang ||
                    (this.supportedLanguages[browserLang] ? browserLang : this.defaultLang);

        await this.loadLanguage(lang);
    }

    /**
     * Load translation file for a language
     */
    async loadLanguage(lang) {
        if (!this.supportedLanguages[lang]) {
            console.warn(`Language ${lang} not supported, falling back to ${this.defaultLang}`);
            lang = this.defaultLang;
        }

        try {
            const response = await fetch(`/locales/${lang}.json`);
            if (!response.ok) throw new Error(`Failed to load ${lang}`);

            this.translations[lang] = await response.json();
            this.currentLang = lang;

            // Save preference
            localStorage.setItem('language', lang);

            // Set HTML lang and dir attributes
            document.documentElement.lang = lang;
            document.documentElement.dir = this.supportedLanguages[lang].dir;

            // Trigger custom event for UI updates
            window.dispatchEvent(new CustomEvent('languageChanged', {
                detail: { lang, langInfo: this.supportedLanguages[lang] }
            }));

            return true;
        } catch (error) {
            console.error(`Error loading language ${lang}:`, error);
            if (lang !== this.defaultLang) {
                // Fallback to default
                return this.loadLanguage(this.defaultLang);
            }
            return false;
        }
    }

    /**
     * Get translated text by key path (e.g., "nav.home")
     */
    t(keyPath, variables = {}) {
        const keys = keyPath.split('.');
        let value = this.translations[this.currentLang];

        // Navigate through nested object
        for (const key of keys) {
            if (value && typeof value === 'object' && key in value) {
                value = value[key];
            } else {
                // Fallback to default language
                value = this.translations[this.defaultLang];
                for (const k of keys) {
                    if (value && typeof value === 'object' && k in value) {
                        value = value[k];
                    } else {
                        console.warn(`Translation key not found: ${keyPath}`);
                        return keyPath; // Return key as fallback
                    }
                }
                break;
            }
        }

        // Replace variables (e.g., {{name}} -> John)
        if (typeof value === 'string' && Object.keys(variables).length > 0) {
            return value.replace(/\{\{(\w+)\}\}/g, (match, varName) => {
                return variables[varName] !== undefined ? variables[varName] : match;
            });
        }

        return value || keyPath;
    }

    /**
     * Get current language code
     */
    getLang() {
        return this.currentLang;
    }

    /**
     * Get info about current language
     */
    getLangInfo() {
        return this.supportedLanguages[this.currentLang];
    }

    /**
     * Get list of all supported languages
     */
    getSupportedLanguages() {
        return this.supportedLanguages;
    }

    /**
     * Switch to a different language
     */
    async setLanguage(lang) {
        if (lang === this.currentLang) return true;
        return await this.loadLanguage(lang);
    }
}

// Global instance
const i18n = new I18n();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => i18n.init());
} else {
    i18n.init();
}

// Make available globally
window.i18n = i18n;
