package com.boozallen.aissemble.security.auth;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.Duration;

import static org.junit.jupiter.api.Assertions.*;

class SessionTimeoutManagerTest {

    private SessionTimeoutManager manager;

    @BeforeEach
    void setUp() {
        manager = new SessionTimeoutManager();
    }

    @Test
    void testSessionRegistered() {
        manager.registerSession("session1", "user1");
        assertTrue(manager.isSessionValid("session1"));
    }

    @Test
    void testInvalidSessionReturnsFalse() {
        assertFalse(manager.isSessionValid("nonexistent"));
    }

    @Test
    void testSessionExpiresAfterInactivity() throws InterruptedException {
        SessionTimeoutManager shortTimeout = new SessionTimeoutManager(Duration.ofMillis(100));
        shortTimeout.registerSession("session1", "user1");
        Thread.sleep(200);
        assertFalse(shortTimeout.isSessionValid("session1"));
    }

    @Test
    void testTouchSessionResetsTimer() throws InterruptedException {
        SessionTimeoutManager shortTimeout = new SessionTimeoutManager(Duration.ofMillis(300));
        shortTimeout.registerSession("session1", "user1");
        Thread.sleep(150);
        shortTimeout.touchSession("session1");
        Thread.sleep(150);
        assertTrue(shortTimeout.isSessionValid("session1"));
    }

    @Test
    void testInvalidateSession() {
        manager.registerSession("session1", "user1");
        manager.invalidateSession("session1");
        assertFalse(manager.isSessionValid("session1"));
    }

    @Test
    void testCleanupExpiredSessions() throws InterruptedException {
        SessionTimeoutManager shortTimeout = new SessionTimeoutManager(Duration.ofMillis(100));
        shortTimeout.registerSession("s1", "user1");
        shortTimeout.registerSession("s2", "user2");
        Thread.sleep(200);
        int cleaned = shortTimeout.cleanupExpiredSessions();
        assertEquals(2, cleaned);
        assertEquals(0, shortTimeout.getActiveSessionCount());
    }

    @Test
    void testDefaultTimeout15Minutes() {
        assertEquals(Duration.ofMinutes(15), manager.getInactivityTimeout());
    }

    @Test
    void testActiveSessionCount() {
        manager.registerSession("s1", "user1");
        manager.registerSession("s2", "user2");
        assertEquals(2, manager.getActiveSessionCount());
    }
}
