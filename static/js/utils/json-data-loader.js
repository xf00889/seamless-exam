/**
 * JSON Data Loader Utility
 * Generic utility for loading and parsing JSON data from Django templates
 */

// Only declare JsonDataLoader if it doesn't already exist
if (typeof window.JsonDataLoader === 'undefined') {
    class JsonDataLoader {
        /**
         * Parse JSON data from script tag
         * @param {string} elementId - ID of the script element containing JSON data
         * @returns {Object|null} Parsed JSON data or null if not found
         */
        static parseJsonScript(elementId) {
            try {
                const element = document.getElementById(elementId);
                if (element) {
                    return JSON.parse(element.textContent);
                }
                console.warn(`JSON script element with ID '${elementId}' not found`);
                return null;
            } catch (error) {
                console.error(`Error parsing JSON from element '${elementId}':`, error);
                return null;
            }
        }

        /**
         * Load JSON data and execute callback
         * @param {string} elementId - ID of the script element containing JSON data
         * @param {Function} callback - Callback function to handle the parsed data
         */
        static loadData(elementId, callback) {
            try {
                const data = this.parseJsonScript(elementId);
                if (data && typeof callback === 'function') {
                    callback(data);
                }
            } catch (error) {
                console.error(`Error loading JSON data from '${elementId}':`, error);
            }
        }

        /**
         * Load multiple JSON data sources
         * @param {Object} dataSources - Object mapping data names to element IDs
         * @param {Function} callback - Callback function receiving all parsed data
         */
        static loadMultipleData(dataSources, callback) {
            try {
                const data = {};
                let hasData = false;

                Object.entries(dataSources).forEach(([key, elementId]) => {
                    const parsedData = this.parseJsonScript(elementId);
                    if (parsedData !== null) {
                        data[key] = parsedData;
                        hasData = true;
                    }
                });

                if (hasData && typeof callback === 'function') {
                    callback(data);
                }
            } catch (error) {
                console.error('Error loading multiple JSON data sources:', error);
            }
        }

        /**
         * Set up data attributes for URL passing to JavaScript
         * @param {Object} urlMappings - Object mapping element IDs to URL data attributes
         */
        static setupUrlDataAttributes(urlMappings) {
            Object.entries(urlMappings).forEach(([elementId, urls]) => {
                const element = document.getElementById(elementId);
                if (element) {
                    Object.entries(urls).forEach(([key, url]) => {
                        element.dataset[key] = url;
                    });
                }
            });
        }

        /**
         * Apply configuration to a component
         * @param {string} configElementId - ID of the script element containing configuration JSON
         * @param {Object} component - Component object to configure
         * @param {string} methodName - Method name to call on the component (default: 'setConfig')
         */
        static applyConfiguration(configElementId, component, methodName = 'setConfig') {
            try {
                const config = this.parseJsonScript(configElementId);
                if (config && component && typeof component[methodName] === 'function') {
                    component[methodName](config);
                }
            } catch (error) {
                console.error(`Error applying configuration from '${configElementId}':`, error);
            }
        }

        /**
         * Initialize component with JSON data
         * @param {string} dataElementId - ID of the script element containing data JSON
         * @param {Function} initFunction - Function to initialize with the data
         */
        static initializeWithData(dataElementId, initFunction) {
            try {
                const data = this.parseJsonScript(dataElementId);
                if (data && typeof initFunction === 'function') {
                    initFunction(data);
                }
            } catch (error) {
                console.error(`Error initializing with data from '${dataElementId}':`, error);
            }
        }
    }

    // Make available globally
    window.JsonDataLoader = JsonDataLoader;
}