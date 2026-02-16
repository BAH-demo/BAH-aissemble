package com.boozallen.aissemble.security.headers;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.FilterConfig;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * STIG V-220641 / NIST SI-11: Security Headers Filter.
 * Adds required security headers to all HTTP responses.
 * Configurable per-deployment via init parameters or SecurityHeadersConfig.
 */
public class SecurityHeadersFilter implements Filter {

    private static final Logger LOG = LoggerFactory.getLogger(SecurityHeadersFilter.class);

    private SecurityHeadersConfig config;

    @Override
    public void init(FilterConfig filterConfig) throws ServletException {
        SecurityHeadersConfig.Builder builder = SecurityHeadersConfig.builder();

        String hsts = filterConfig.getInitParameter("strict-transport-security");
        if (hsts != null && !hsts.isEmpty()) {
            builder.strictTransportSecurity(hsts);
        }

        String xfo = filterConfig.getInitParameter("x-frame-options");
        if (xfo != null && !xfo.isEmpty()) {
            builder.xFrameOptions(xfo);
        }

        String xcto = filterConfig.getInitParameter("x-content-type-options");
        if (xcto != null && !xcto.isEmpty()) {
            builder.xContentTypeOptions(xcto);
        }

        String csp = filterConfig.getInitParameter("content-security-policy");
        if (csp != null && !csp.isEmpty()) {
            builder.contentSecurityPolicy(csp);
        }

        String xxss = filterConfig.getInitParameter("x-xss-protection");
        if (xxss != null && !xxss.isEmpty()) {
            builder.xXssProtection(xxss);
        }

        this.config = builder.build();
        LOG.info("SecurityHeadersFilter initialized with STIG V-220641 compliant headers");
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        if (response instanceof HttpServletResponse) {
            HttpServletResponse httpResponse = (HttpServletResponse) response;
            for (Map.Entry<String, String> entry : config.getHeaders().entrySet()) {
                httpResponse.setHeader(entry.getKey(), entry.getValue());
            }
        }
        chain.doFilter(request, response);
    }

    @Override
    public void destroy() {
        LOG.info("SecurityHeadersFilter destroyed");
    }

    public SecurityHeadersConfig getConfig() {
        return config;
    }

    public void setConfig(SecurityHeadersConfig config) {
        this.config = config;
    }
}
