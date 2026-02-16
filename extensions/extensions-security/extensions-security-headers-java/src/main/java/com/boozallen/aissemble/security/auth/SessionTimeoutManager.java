package com.boozallen.aissemble.security.auth;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * STIG V-220630 / NIST AC-12: Session Timeout Enforcement.
 * Enforces 15-minute inactivity timeout by default.
 */
public class SessionTimeoutManager {

    private static final Logger LOG = LoggerFactory.getLogger(SessionTimeoutManager.class);

    private final Duration inactivityTimeout;
    private final Map<String, SessionInfo> sessions = new ConcurrentHashMap<>();

    public SessionTimeoutManager() {
        this(Duration.ofMinutes(15));
    }

    public SessionTimeoutManager(Duration inactivityTimeout) {
        this.inactivityTimeout = inactivityTimeout;
        LOG.info("SessionTimeoutManager initialized: inactivityTimeout={}min",
                inactivityTimeout.toMinutes());
    }

    public void registerSession(String sessionId, String userId) {
        sessions.put(sessionId, new SessionInfo(userId, Instant.now()));
        LOG.info("Session registered: {} for user: {}", sessionId, userId);
    }

    public boolean isSessionValid(String sessionId) {
        SessionInfo info = sessions.get(sessionId);
        if (info == null) {
            return false;
        }
        if (Instant.now().isAfter(info.lastActivity.plus(inactivityTimeout))) {
            invalidateSession(sessionId);
            LOG.info("Session expired due to inactivity: {}", sessionId);
            return false;
        }
        return true;
    }

    public void touchSession(String sessionId) {
        SessionInfo info = sessions.get(sessionId);
        if (info != null) {
            info.lastActivity = Instant.now();
        }
    }

    public void invalidateSession(String sessionId) {
        SessionInfo removed = sessions.remove(sessionId);
        if (removed != null) {
            LOG.info("Session invalidated: {} for user: {}", sessionId, removed.userId);
        }
    }

    public int cleanupExpiredSessions() {
        Instant now = Instant.now();
        Set<String> expired = sessions.entrySet().stream()
                .filter(e -> now.isAfter(e.getValue().lastActivity.plus(inactivityTimeout)))
                .map(Map.Entry::getKey)
                .collect(Collectors.toSet());
        expired.forEach(this::invalidateSession);
        if (!expired.isEmpty()) {
            LOG.info("Cleaned up {} expired sessions", expired.size());
        }
        return expired.size();
    }

    public Duration getInactivityTimeout() {
        return inactivityTimeout;
    }

    public int getActiveSessionCount() {
        return sessions.size();
    }

    private static class SessionInfo {
        final String userId;
        Instant lastActivity;

        SessionInfo(String userId, Instant createdAt) {
            this.userId = userId;
            this.lastActivity = createdAt;
        }
    }
}
