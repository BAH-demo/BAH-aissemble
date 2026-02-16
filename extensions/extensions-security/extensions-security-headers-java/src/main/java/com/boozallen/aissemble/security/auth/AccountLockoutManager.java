package com.boozallen.aissemble.security.auth;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * STIG V-220629 / NIST AC-7: Account Lockout Mechanism.
 * Locks accounts after configurable number of failed attempts.
 * Default: 5 failed attempts, 15-minute lockout duration.
 */
public class AccountLockoutManager {

    private static final Logger LOG = LoggerFactory.getLogger(AccountLockoutManager.class);

    private final int maxFailedAttempts;
    private final Duration lockoutDuration;
    private final Map<String, AccountState> accountStates = new ConcurrentHashMap<>();

    public AccountLockoutManager() {
        this(5, Duration.ofMinutes(15));
    }

    public AccountLockoutManager(int maxFailedAttempts, Duration lockoutDuration) {
        this.maxFailedAttempts = maxFailedAttempts;
        this.lockoutDuration = lockoutDuration;
        LOG.info("AccountLockoutManager initialized: maxAttempts={}, lockoutDuration={}min",
                maxFailedAttempts, lockoutDuration.toMinutes());
    }

    public boolean isLocked(String username) {
        AccountState state = accountStates.get(username);
        if (state == null) {
            return false;
        }
        if (state.lockedUntil == null) {
            return false;
        }
        if (Instant.now().isAfter(state.lockedUntil)) {
            state.failedAttempts = 0;
            state.lockedUntil = null;
            LOG.info("Account lockout expired for user: {}", username);
            return false;
        }
        return true;
    }

    public void recordFailedAttempt(String username) {
        AccountState state = accountStates.computeIfAbsent(username, k -> new AccountState());
        state.failedAttempts++;
        state.lastFailedAttempt = Instant.now();
        LOG.warn("Failed login attempt {} for user: {}", state.failedAttempts, username);

        if (state.failedAttempts >= maxFailedAttempts) {
            state.lockedUntil = Instant.now().plus(lockoutDuration);
            LOG.warn("Account locked for user: {} until {}", username, state.lockedUntil);
        }
    }

    public void recordSuccessfulLogin(String username) {
        AccountState state = accountStates.get(username);
        if (state != null) {
            state.failedAttempts = 0;
            state.lockedUntil = null;
        }
    }

    public int getFailedAttempts(String username) {
        AccountState state = accountStates.get(username);
        return state != null ? state.failedAttempts : 0;
    }

    public Instant getLockoutExpiry(String username) {
        AccountState state = accountStates.get(username);
        return state != null ? state.lockedUntil : null;
    }

    public int getMaxFailedAttempts() {
        return maxFailedAttempts;
    }

    public Duration getLockoutDuration() {
        return lockoutDuration;
    }

    private static class AccountState {
        int failedAttempts = 0;
        Instant lastFailedAttempt = null;
        Instant lockedUntil = null;
    }
}
