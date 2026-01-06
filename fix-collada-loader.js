/**
 * Runtime fix for ColladaLoader "object is not extensible" error
 * 
 * This script patches THREE.Loader to safely register ColladaLoader
 * even when the object is frozen/sealed in production builds.
 * 
 * Usage: Inject this script before the network graph component loads
 */

(function() {
    'use strict';
    
    // Wait for THREE to be available
    if (typeof window === 'undefined' || typeof window.THREE === 'undefined') {
        console.warn('THREE.js not found. ColladaLoader fix will be applied when THREE is available.');
        
        // Retry when THREE becomes available
        const checkThree = setInterval(function() {
            if (typeof window !== 'undefined' && typeof window.THREE !== 'undefined') {
                clearInterval(checkThree);
                applyFix();
            }
        }, 100);
        
        // Stop checking after 10 seconds
        setTimeout(function() {
            clearInterval(checkThree);
        }, 10000);
        
        return;
    }
    
    applyFix();
    
    function applyFix() {
        const THREE = window.THREE;
        
        // Ensure THREE.Loader exists
        if (!THREE.Loader) {
            THREE.Loader = {};
        }
        
        // Patch the ColladaLoader registration
        const originalRegister = function(ColladaLoaderClass) {
            if (!ColladaLoaderClass) {
                console.warn('ColladaLoader class not provided to fix script');
                return false;
            }
            
            // Check if already registered
            if (THREE.Loader.ColladaLoader) {
                console.log('ColladaLoader already registered');
                return true;
            }
            
            // Try direct assignment first (works if object is extensible)
            if (Object.isExtensible(THREE.Loader)) {
                try {
                    THREE.Loader.ColladaLoader = ColladaLoaderClass;
                    console.log('ColladaLoader registered via direct assignment');
                    return true;
                } catch (e) {
                    console.warn('Direct assignment failed, trying defineProperty:', e);
                }
            }
            
            // Use Object.defineProperty as fallback
            try {
                Object.defineProperty(THREE.Loader, 'ColladaLoader', {
                    value: ColladaLoaderClass,
                    writable: true,
                    enumerable: true,
                    configurable: true
                });
                console.log('ColladaLoader registered via Object.defineProperty');
                return true;
            } catch (e) {
                console.warn('Object.defineProperty failed, using alternative namespace:', e);
                
                // Last resort: use alternative namespace
                if (!THREE.ColladaLoader) {
                    THREE.ColladaLoader = ColladaLoaderClass;
                    console.log('ColladaLoader registered to THREE.ColladaLoader (alternative namespace)');
                    
                    // Create a proxy to THREE.Loader.ColladaLoader for compatibility
                    try {
                        Object.defineProperty(THREE.Loader, 'ColladaLoader', {
                            get: function() {
                                return THREE.ColladaLoader;
                            },
                            enumerable: true,
                            configurable: true
                        });
                        console.log('Created proxy from THREE.Loader.ColladaLoader to THREE.ColladaLoader');
                    } catch (proxyError) {
                        console.warn('Could not create proxy:', proxyError);
                    }
                }
                return true;
            }
        };
        
        // Store the fix function globally for use by other scripts
        window.__THREE_LOADER_FIX__ = originalRegister;
        
        // If ColladaLoader is already being registered, intercept it
        const originalDefineProperty = Object.defineProperty;
        Object.defineProperty = function(obj, prop, descriptor) {
            if (obj === THREE.Loader && prop === 'ColladaLoader' && descriptor && descriptor.value) {
                console.log('Intercepted ColladaLoader registration via Object.defineProperty');
                return originalRegister(descriptor.value) ? obj : originalDefineProperty.apply(this, arguments);
            }
            return originalDefineProperty.apply(this, arguments);
        };
        
        // Intercept direct property assignment (if possible)
        const handler = {
            set: function(target, prop, value) {
                if (prop === 'ColladaLoader' && value && value.prototype && value.prototype.load) {
                    console.log('Intercepted ColladaLoader assignment');
                    return originalRegister(value) ? true : Reflect.set(target, prop, value);
                }
                return Reflect.set(target, prop, value);
            }
        };
        
        // Try to create a proxy for THREE.Loader (only if it's not frozen)
        if (Object.isExtensible(THREE.Loader)) {
            try {
                const proxy = new Proxy(THREE.Loader, handler);
                // Note: We can't replace THREE.Loader with the proxy if it's already frozen
                // But we can intercept future assignments
            } catch (e) {
                console.warn('Could not create proxy for THREE.Loader:', e);
            }
        }
        
        console.log('ColladaLoader fix script loaded. Use window.__THREE_LOADER_FIX__(ColladaLoaderClass) to register.');
    }
})();
