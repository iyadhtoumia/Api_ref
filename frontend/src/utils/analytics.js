// Google Analytics utility functions

/**
 * Send a page view event to Google Analytics
 * @param {string} path - The page path
 */
export const trackPageView = (path) => {
  if (typeof window.gtag !== 'undefined') {
    window.gtag('config', import.meta.env.VITE_GA_MEASUREMENT_ID, {
      page_path: path,
    });
  }
};

/**
 * Send a custom event to Google Analytics
 * @param {string} eventName - Name of the event
 * @param {object} eventParams - Event parameters
 */
export const trackEvent = (eventName, eventParams = {}) => {
  if (typeof window.gtag !== 'undefined') {
    window.gtag('event', eventName, eventParams);
  }
};

/**
 * Track user actions
 */
export const trackAction = {
  signIn: (method) => trackEvent('login', { method }),
  signUp: (method) => trackEvent('sign_up', { method }),
  serviceRequest: (serviceName) => trackEvent('service_request', { service_name: serviceName }),
  orderComplete: (orderId, value) => trackEvent('purchase', { 
    transaction_id: orderId,
    value: value,
    currency: 'USD'
  }),
};
