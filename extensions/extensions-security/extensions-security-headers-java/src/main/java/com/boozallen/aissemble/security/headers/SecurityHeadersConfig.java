package com.boozallen.aissemble.security.headers;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * STIG V-220641: Configuration for security response headers.
 * Provides STIG-compliant defaults with per-deployment override capability.
 */
public class SecurityHeadersConfig {

    public static final String DEFAULT_HSTS = "max-age=31536000; includeSubDomains";
    public static final String DEFAULT_X_FRAME_OPTIONS = "DENY";
    public static final String DEFAULT_X_CONTENT_TYPE_OPTIONS = "nosniff";
    public static final String DEFAULT_CSP = "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'";
    public static final String DEFAULT_X_XSS_PROTECTION = "1; mode=block";

    private final String strictTransportSecurity;
    private final String xFrameOptions;
    private final String xContentTypeOptions;
    private final String contentSecurityPolicy;
    private final String xXssProtection;

    private SecurityHeadersConfig(Builder builder) {
        this.strictTransportSecurity = builder.strictTransportSecurity;
        this.xFrameOptions = builder.xFrameOptions;
        this.xContentTypeOptions = builder.xContentTypeOptions;
        this.contentSecurityPolicy = builder.contentSecurityPolicy;
        this.xXssProtection = builder.xXssProtection;
    }

    public Map<String, String> getHeaders() {
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("Strict-Transport-Security", strictTransportSecurity);
        headers.put("X-Frame-Options", xFrameOptions);
        headers.put("X-Content-Type-Options", xContentTypeOptions);
        headers.put("Content-Security-Policy", contentSecurityPolicy);
        headers.put("X-XSS-Protection", xXssProtection);
        return Collections.unmodifiableMap(headers);
    }

    public String getStrictTransportSecurity() {
        return strictTransportSecurity;
    }

    public String getXFrameOptions() {
        return xFrameOptions;
    }

    public String getXContentTypeOptions() {
        return xContentTypeOptions;
    }

    public String getContentSecurityPolicy() {
        return contentSecurityPolicy;
    }

    public String getXXssProtection() {
        return xXssProtection;
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private String strictTransportSecurity = DEFAULT_HSTS;
        private String xFrameOptions = DEFAULT_X_FRAME_OPTIONS;
        private String xContentTypeOptions = DEFAULT_X_CONTENT_TYPE_OPTIONS;
        private String contentSecurityPolicy = DEFAULT_CSP;
        private String xXssProtection = DEFAULT_X_XSS_PROTECTION;

        public Builder strictTransportSecurity(String value) {
            this.strictTransportSecurity = value;
            return this;
        }

        public Builder xFrameOptions(String value) {
            this.xFrameOptions = value;
            return this;
        }

        public Builder xContentTypeOptions(String value) {
            this.xContentTypeOptions = value;
            return this;
        }

        public Builder contentSecurityPolicy(String value) {
            this.contentSecurityPolicy = value;
            return this;
        }

        public Builder xXssProtection(String value) {
            this.xXssProtection = value;
            return this;
        }

        public SecurityHeadersConfig build() {
            return new SecurityHeadersConfig(this);
        }
    }
}
