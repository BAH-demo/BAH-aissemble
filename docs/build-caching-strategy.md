# Maven Build Caching Strategy

This document describes the comprehensive Maven build caching strategy for aiSSEMBLE, covering both CI/CD and local development environments.

## Overview

aiSSEMBLE uses the [Maven Build Cache Extension](https://maven.apache.org/extensions/maven-build-cache-extension/) (v1.2.0) to accelerate builds by caching module outputs and restoring them when source inputs have not changed. The cache uses SHA-256 hashing to compute cache keys based on tracked source files.

### Requirements
- Maven 3.9+ (enforced via `maven-enforcer-plugin`)
- Cache extension declared in `.mvn/extensions.xml`
- Configuration in `.mvn/maven-build-cache-config.xml`

## How Caching Works

### Cache Key Computation

The build cache computes a SHA-256 hash from the following tracked inputs:

**File types (glob pattern):**
`*.java`, `*.json`, `*.groovy`, `*.yaml`, `*.svcd`, `*.proto`, `*.xml`, `*.vm`, `*.ini`, `*.jks`, `*.properties`, `*.sh`, `*.bat`, `*.py`, `Dockerfile`, `*.feature`

**Included directories/files:**
- `src/` - Main and test source directories
- `tests/` - Helm and Python module tests
- `templates/` - Helm module templates
- `pom.xml` - Maven project configuration
- `pyproject.toml` - Python project configuration

**Excluded files:**
- `poetry.lock` - Excluded to avoid unnecessary invalidation
- `Chart.lock` - Excluded to avoid unnecessary invalidation

When any tracked file changes, the cache key changes and the module is rebuilt. When tracked files remain identical, the cached output is restored.

### Cache Storage

The build cache is stored locally at `~/.m2/build-cache`. Only **1 build** is cached per module (`maxBuildsCached=1`) to prevent stale Docker images, since the cache restore process does not restore Docker images from the cache.

## CI/CD Caching (GitHub Actions)

### S3-Backed Cache Storage

The CI/CD pipeline uses [runs-on/cache](https://github.com/runs-on/cache) with an S3 backend to persist caches between workflow runs. The S3 bucket is configured via the `RUNS_ON_S3_BUCKET_CACHE` environment variable (set to `aissemble-github-cache`).

### Cache Layers

The CI workflow maintains three separate cache layers:

| Cache | Path | Key Strategy | Purpose |
|-------|------|-------------|---------|
| Maven Repository | `~/.m2/repository` | `maven-repo-cache-${{ hashFiles('**/pom.xml') }}` | Downloaded dependencies |
| Maven Build Cache | `~/.m2/build-cache` | `maven-build-cache-${{ hashFiles('**/pom.xml', '**/src/**') }}` | Compiled module outputs |
| Poetry Cache | `~/.cache/pypoetry` | `poetry-cache-${{ hashFiles('**/pyproject.toml') }}` | Python dependencies |

### Hash-Based Cache Keys with Fallback

Each cache uses a hash-based primary key with a `restore-keys` fallback:

- **Primary key**: Exact match based on file hashes (e.g., `maven-repo-cache-abc123`)
- **Fallback**: Prefix match (e.g., `maven-repo-cache-`) restores the most recent cache even if the hash doesn't match exactly

This ensures that:
1. An exact cache hit restores the fastest possible build
2. A partial cache hit still provides significant speedup over a cold start
3. Cache is automatically invalidated when dependencies or sources change

### Scheduled Build Behavior

Scheduled builds (daily at 6am UTC) skip cache restoration entirely (`if: ${{ ! github.event.schedule }}`) to ensure a clean build validates that no cached state masks issues.

### Parallel Execution

The CI build uses `-T8` for parallel module execution, which works cooperatively with the build cache. Modules that hit the cache are skipped instantly, freeing threads for modules that need rebuilding.

## Local Development Caching

### Default Behavior

The Maven build cache is **enabled by default** for all local builds. When you run:

```bash
./mvnw clean install
```

The build cache will automatically:
1. Compute cache keys for each module based on tracked source files
2. Restore cached outputs for modules with matching cache keys
3. Rebuild modules whose tracked files have changed
4. Store new cache entries at `~/.m2/build-cache`

### Verifying Your Local Cache

To verify that the build cache is working locally:

1. **Run a full build:**
   ```bash
   ./mvnw clean install
   ```

2. **Run the build again without changes:**
   ```bash
   ./mvnw install
   ```
   You should see `[INFO] Found cached build, restoring...` messages for modules that were cached.

3. **Check cache contents:**
   ```bash
   ls -la ~/.m2/build-cache/v1/
   ```
   You should see directories named after module artifact IDs.

4. **View cache metrics in build output:**
   Look for log lines containing `[INFO] Cache report` at the end of the build.

### Disabling the Cache

To temporarily disable the cache for a single build:

```bash
./mvnw clean install -Dmaven.build.cache.skipCache=true
```

To permanently disable it, edit `.mvn/maven-build-cache-config.xml` and set:
```xml
<enabled>false</enabled>
```

Note: The cache is automatically disabled for release builds via the `aissemble-release` profile.

### The maxBuildsCached=1 Setting

The cache is configured to store only 1 build per module. This is intentional and critical for Docker image freshness:

- The Maven build cache **cannot restore Docker images** from cache
- If multiple builds were cached, a cache hit might restore outdated JAR files that reference Docker images no longer present locally
- With `maxBuildsCached=1`, only the most recent build is cached, ensuring consistency between cached artifacts and local Docker images

This setting applies equally to CI and local development.

## Performance Benchmarks

Expected build time improvements with caching (approximate):

| Scenario | Without Cache | With Cache (hit) | Improvement |
|----------|--------------|-------------------|-------------|
| Full build (no changes) | ~2 hours (CI) | ~15-30 min | 75-85% |
| Single module change | ~2 hours (CI) | ~30-45 min | 60-75% |
| Local rebuild (no changes) | 30-60 min | 5-10 min | 80-90% |
| Local single module | 30-60 min | 10-20 min | 50-70% |

Actual improvements depend on the number of modules affected by changes and the proportion of Docker builds.

## Execution Control

### Goals That Always Run

Certain goals bypass the cache and always execute:

- `maven-install-plugin:install` - Ensures artifacts are always installed to the local repository
- `maven-deploy-plugin:deploy` - Ensures artifacts are always deployed to remote repositories

### Reconciled Properties

The compiler plugin reconciles these properties to determine cache validity:
- `source`, `target`, `debug`, `debuglevel` - Compiler configuration
- `skip` (for enforcer plugin) - Skip enforcement checks

## Archetype Template

New projects generated from the `foundation-archetype` automatically inherit a cache configuration that:
- Enables build caching by default
- Uses the same `maxBuildsCached=1` limit
- Includes the same file tracking patterns (with additional `*.lock` tracking)
- Configures the same execution control rules plus `build-helper-maven-plugin:regex-property`

## Troubleshooting

### Cache Not Working

**Symptom:** Build always rebuilds all modules, no cache hits.

**Solutions:**
1. Verify Maven version is 3.9+: `./mvnw --version`
2. Check that `.mvn/extensions.xml` includes `maven-build-cache-extension`
3. Ensure `.mvn/maven-build-cache-config.xml` has `<enabled>true</enabled>`
4. Check that you're not passing `-Dmaven.build.cache.skipCache=true`
5. Verify `~/.m2/build-cache` directory exists and has write permissions

### Stale Build Artifacts

**Symptom:** Build succeeds but runtime behavior is incorrect.

**Solutions:**
1. Clear the build cache: `rm -rf ~/.m2/build-cache`
2. Run a clean build: `./mvnw clean install -Dmaven.build.cache.skipCache=true`
3. Verify that all source files are tracked in the glob pattern

### Docker Image Issues

**Symptom:** Docker containers use outdated images after a cached build.

**Solutions:**
1. Ensure `maxBuildsCached` is set to `1` (default)
2. Clear the build cache: `rm -rf ~/.m2/build-cache`
3. Run a full clean build including Docker: `./mvnw clean install`
4. Verify Docker images are up to date: `docker images | grep aissemble`

### CI Cache Issues

**Symptom:** CI build does not restore cache or always runs from scratch.

**Solutions:**
1. Verify the S3 bucket `aissemble-github-cache` is accessible
2. Check AWS credentials (`S3_CACHE_USER`, `S3_CACHE_USER_SECRET`) are valid
3. Ensure the build is not a scheduled run (scheduled builds skip cache by design)
4. Check the cache restore step output in GitHub Actions for error messages

### Cache Size Growing Too Large

**Symptom:** `~/.m2/build-cache` is consuming excessive disk space.

**Solutions:**
1. The `maxBuildsCached=1` setting should prevent this
2. Manually clean: `rm -rf ~/.m2/build-cache`
3. The cache auto-evicts older entries when the limit is reached

## Best Practices

1. **Do not modify `maxBuildsCached`** beyond 1 unless you understand the Docker image freshness implications
2. **Use `clean` sparingly** - Running `clean` forces cache invalidation for all modules. Prefer incremental builds when possible
3. **Check cache status** after builds to identify modules that are not caching properly
4. **Run scheduled builds** (or local builds with cache disabled) periodically to catch issues masked by caching
5. **Keep the glob pattern up to date** when adding new file types to the project
6. **Do not manually edit** files in `~/.m2/build-cache` - let Maven manage the cache
7. **Use `-Dmaven.build.cache.skipCache=true`** when debugging build issues to rule out cache-related problems
