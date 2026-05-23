/**
 * Data Loader Utility
 * Provides methods for loading data from Django templates into JavaScript
 * Handles JSON script tags and template variable access
 */
class DataLoader {
    /**
     * Load JSON data from a script tag with specified ID
     * @param {string} scriptId - ID of the script tag containing JSON data
     * @returns {Object|null} Parsed JSON data or null if not found/invalid
     */
    static loadJSON(scriptId) {
        try {
            const scriptElement = document.getElementById(scriptId);
            if (!scriptElement) {
                console.warn(`Script element with ID '${scriptId}' not found`);
                return null;
            }
            
            const jsonText = scriptElement.textContent;
            if (!jsonText || jsonText.trim() === '') {
                console.warn(`Script element '${scriptId}' is empty`);
                return null;
            }
            
            return JSON.parse(jsonText);
        } catch (error) {
            console.error(`Error parsing JSON from script '${scriptId}':`, error);
            return null;
        }
    }
    
    /**
     * Load multiple JSON datasets from script tags
     * @param {Array<string>} scriptIds - Array of script tag IDs
     * @returns {Object} Object with script IDs as keys and parsed data as values
     */
    static loadMultipleJSON(scriptIds) {
        const data = {};
        
        scriptIds.forEach(scriptId => {
            data[scriptId] = this.loadJSON(scriptId);
        });
        
        return data;
    }
    
    /**
     * Load data with fallback values
     * @param {string} scriptId - ID of the script tag
     * @param {*} fallback - Fallback value if data not found
     * @returns {*} Loaded data or fallback value
     */
    static loadWithFallback(scriptId, fallback = {}) {
        const data = this.loadJSON(scriptId);
        return data !== null ? data : fallback;
    }
    
    /**
     * Load configuration data commonly used across the application
     * @returns {Object} Configuration object with common settings
     */
    static loadConfig() {
        const config = this.loadWithFallback('app-config', {});
        
        // Set default configuration values
        const defaultConfig = {
            urls: {},
            settings: {
                debug: false,
                timeout: 30000,
                retryAttempts: 3
            },
            validation: {
                passwordMinLength: 8,
                maxFileSize: 50 * 1024 * 1024, // 50MB
                allowedFileTypes: ['.pdf', '.docx', '.doc']
            }
        };
        
        return this.mergeDeep(defaultConfig, config);
    }
    
    /**
     * Load form configuration data
     * @param {string} formId - Form identifier
     * @returns {Object} Form configuration
     */
    static loadFormConfig(formId = 'form-config') {
        return this.loadWithFallback(formId, {
            validation: {
                requiredFields: [],
                patterns: {},
                messages: {}
            },
            urls: {
                submit: '',
                validate: ''
            }
        });
    }
    
    /**
     * Load chart data for dashboard components
     * @param {string} chartId - Chart data identifier
     * @returns {Object} Chart data configuration
     */
    static loadChartData(chartId = 'chart-data') {
        return this.loadWithFallback(chartId, {
            labels: [],
            datasets: [],
            options: {}
        });
    }
    
    /**
     * Get data attribute from an element
     * @param {HTMLElement} element - DOM element
     * @param {string} attribute - Data attribute name (without 'data-' prefix)
     * @param {*} fallback - Fallback value
     * @returns {*} Attribute value or fallback
     */
    static getDataAttribute(element, attribute, fallback = null) {
        if (!element) {
            return fallback;
        }
        
        const value = element.dataset[attribute];
        if (value === undefined) {
            return fallback;
        }
        
        // Try to parse as JSON if it looks like JSON
        if (typeof value === 'string' && (value.startsWith('{') || value.startsWith('['))) {
            try {
                return JSON.parse(value);
            } catch (error) {
                console.warn(`Failed to parse JSON from data-${attribute}:`, error);
                return value;
            }
        }
        
        return value;
    }
    
    /**
     * Deep merge two objects
     * @param {Object} target - Target object
     * @param {Object} source - Source object
     * @returns {Object} Merged object
     */
    static mergeDeep(target, source) {
        const output = Object.assign({}, target);
        
        if (this.isObject(target) && this.isObject(source)) {
            Object.keys(source).forEach(key => {
                if (this.isObject(source[key])) {
                    if (!(key in target)) {
                        Object.assign(output, { [key]: source[key] });
                    } else {
                        output[key] = this.mergeDeep(target[key], source[key]);
                    }
                } else {
                    Object.assign(output, { [key]: source[key] });
                }
            });
        }
        
        return output;
    }
    
    /**
     * Check if value is an object
     * @param {*} item - Value to check
     * @returns {boolean} True if object
     */
    static isObject(item) {
        return item && typeof item === 'object' && !Array.isArray(item);
    }
    
    /**
     * Wait for data to be available
     * @param {string} scriptId - Script tag ID to wait for
     * @param {number} timeout - Timeout in milliseconds
     * @returns {Promise} Promise that resolves when data is available
     */
    static waitForData(scriptId, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            
            const checkData = () => {
                const data = this.loadJSON(scriptId);
                if (data !== null) {
                    resolve(data);
                    return;
                }
                
                if (Date.now() - startTime > timeout) {
                    reject(new Error(`Timeout waiting for data '${scriptId}'`));
                    return;
                }
                
                setTimeout(checkData, 100);
            };
            
            checkData();
        });
    }
}

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataLoader;
}