package com.boozallen.aissemble.security.auth;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.Duration;

import static org.junit.jupiter.api.Assertions.*;

class AccountLockoutManagerTest {

    private AccountLockoutManager manager;

    @BeforeEach
    void setUp() {
        manager = new AccountLockoutManager();
    }

    @Test
    void testAccountNotLockedInitially() {
        assertFalse(manager.isLocked("testuser"));
    }

    @Test
    void testAccountLockedAfterFiveFailedAttempts() {
        for (int i = 0; i < 5; i++) {
            manager.recordFailedAttempt("testuser");
        }
        assertTrue(manager.isLocked("testuser"));
    }

    @Test
    void testAccountNotLockedAfterFourFailedAttempts() {
        for (int i = 0; i < 4; i++) {
            manager.recordFailedAttempt("testuser");
        }
        assertFalse(manager.isLocked("testuser"));
    }

    @Test
    void testSuccessfulLoginResetsCounter() {
        for (int i = 0; i < 3; i++) {
            manager.recordFailedAttempt("testuser");
        }
        manager.recordSuccessfulLogin("testuser");
        assertEquals(0, manager.getFailedAttempts("testuser"));
    }

    @Test
    void testFailedAttemptsTracked() {
        manager.recordFailedAttempt("testuser");
        manager.recordFailedAttempt("testuser");
        assertEquals(2, manager.getFailedAttempts("testuser"));
    }

    @Test
    void testLockoutExpirySet() {
        for (int i = 0; i < 5; i++) {
            manager.recordFailedAttempt("testuser");
        }
        assertNotNull(manager.getLockoutExpiry("testuser"));
    }

    @Test
    void testCustomLockoutSettings() {
        AccountLockoutManager custom = new AccountLockoutManager(3, Duration.ofMinutes(30));
        assertEquals(3, custom.getMaxFailedAttempts());
        assertEquals(Duration.ofMinutes(30), custom.getLockoutDuration());
    }

    @Test
    void testDifferentUsersIndependent() {
        for (int i = 0; i < 5; i++) {
            manager.recordFailedAttempt("user1");
        }
        assertTrue(manager.isLocked("user1"));
        assertFalse(manager.isLocked("user2"));
    }

    @Test
    void testLockoutWithShortDurationExpires() throws InterruptedException {
        AccountLockoutManager shortLockout = new AccountLockoutManager(2, Duration.ofMillis(100));
        shortLockout.recordFailedAttempt("testuser");
        shortLockout.recordFailedAttempt("testuser");
        assertTrue(shortLockout.isLocked("testuser"));
        Thread.sleep(200);
        assertFalse(shortLockout.isLocked("testuser"));
    }
}
