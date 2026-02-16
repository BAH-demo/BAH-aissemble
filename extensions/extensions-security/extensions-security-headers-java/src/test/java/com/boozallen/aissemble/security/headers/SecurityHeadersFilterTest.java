package com.boozallen.aissemble.security.headers;

import jakarta.servlet.FilterChain;
import jakarta.servlet.FilterConfig;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class SecurityHeadersFilterTest {

    private SecurityHeadersFilter filter;

    @Mock
    private FilterConfig filterConfig;
    @Mock
    private HttpServletRequest request;
    @Mock
    private HttpServletResponse response;
    @Mock
    private FilterChain chain;

    @BeforeEach
    void setUp() throws Exception {
        MockitoAnnotations.openMocks(this);
        filter = new SecurityHeadersFilter();
        when(filterConfig.getInitParameter(anyString())).thenReturn(null);
        filter.init(filterConfig);
    }

    @Test
    void testDefaultHeadersApplied() throws Exception {
        filter.doFilter(request, response, chain);

        verify(response).setHeader("Strict-Transport-Security", SecurityHeadersConfig.DEFAULT_HSTS);
        verify(response).setHeader("X-Frame-Options", SecurityHeadersConfig.DEFAULT_X_FRAME_OPTIONS);
        verify(response).setHeader("X-Content-Type-Options", SecurityHeadersConfig.DEFAULT_X_CONTENT_TYPE_OPTIONS);
        verify(response).setHeader("Content-Security-Policy", SecurityHeadersConfig.DEFAULT_CSP);
        verify(response).setHeader("X-XSS-Protection", SecurityHeadersConfig.DEFAULT_X_XSS_PROTECTION);
        verify(chain).doFilter(request, response);
    }

    @Test
    void testCustomHeadersFromInitParams() throws Exception {
        when(filterConfig.getInitParameter("strict-transport-security")).thenReturn("max-age=86400");
        when(filterConfig.getInitParameter("x-frame-options")).thenReturn("SAMEORIGIN");

        SecurityHeadersFilter customFilter = new SecurityHeadersFilter();
        customFilter.init(filterConfig);
        customFilter.doFilter(request, response, chain);

        verify(response).setHeader("Strict-Transport-Security", "max-age=86400");
        verify(response).setHeader("X-Frame-Options", "SAMEORIGIN");
    }

    @Test
    void testConfigBuilderCustomValues() {
        SecurityHeadersConfig config = SecurityHeadersConfig.builder()
                .strictTransportSecurity("max-age=86400")
                .xFrameOptions("SAMEORIGIN")
                .contentSecurityPolicy("default-src 'self' https://cdn.example.com")
                .build();

        Map<String, String> headers = config.getHeaders();
        assertEquals("max-age=86400", headers.get("Strict-Transport-Security"));
        assertEquals("SAMEORIGIN", headers.get("X-Frame-Options"));
        assertEquals("default-src 'self' https://cdn.example.com", headers.get("Content-Security-Policy"));
        assertEquals(SecurityHeadersConfig.DEFAULT_X_CONTENT_TYPE_OPTIONS, headers.get("X-Content-Type-Options"));
    }

    @Test
    void testAllFiveRequiredHeaders() {
        SecurityHeadersConfig config = SecurityHeadersConfig.builder().build();
        Map<String, String> headers = config.getHeaders();

        assertTrue(headers.containsKey("Strict-Transport-Security"));
        assertTrue(headers.containsKey("X-Frame-Options"));
        assertTrue(headers.containsKey("X-Content-Type-Options"));
        assertTrue(headers.containsKey("Content-Security-Policy"));
        assertTrue(headers.containsKey("X-XSS-Protection"));
        assertEquals(5, headers.size());
    }

    @Test
    void testHSTSDefaultIncludesSubDomains() {
        SecurityHeadersConfig config = SecurityHeadersConfig.builder().build();
        assertTrue(config.getStrictTransportSecurity().contains("includeSubDomains"));
    }

    @Test
    void testXFrameOptionsDenyByDefault() {
        SecurityHeadersConfig config = SecurityHeadersConfig.builder().build();
        assertEquals("DENY", config.getXFrameOptions());
    }

    @Test
    void testFilterChainContinues() throws Exception {
        filter.doFilter(request, response, chain);
        verify(chain, times(1)).doFilter(request, response);
    }
}
