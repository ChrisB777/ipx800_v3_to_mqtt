# Docker Hub Setup Guide

## GitHub Actions Auto-Build

This repository includes a GitHub Actions workflow that automatically builds and pushes Docker images for both AMD64 and ARM64 architectures.

### Setup Steps

1. **Go to GitHub Repository Settings**
   - https://github.com/ChrisB777/ipx800_v3_to_mqtt/settings

2. **Add Docker Hub Secrets**
   Navigate to **Settings → Secrets and variables → Actions**
   
   Add these two secrets:
   
   | Secret Name | Value |
   |-------------|-------|
   | `DOCKER_USERNAME` | Your Docker Hub username (e.g., `chrisb777`) |
   | `DOCKER_PASSWORD` | Your Docker Hub access token or password |

3. **Trigger Build**
   
   **Option A: Push a tag**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   
   **Option B: Push to main**
   ```bash
   git push origin main
   ```

4. **Check Build Status**
   - Go to: https://github.com/ChrisB777/ipx800_v3_to_mqtt/actions
   - Watch the build progress
   - Image will be pushed to: `chrisb777/ipx800_v3_to_mqtt:v1.0.0`

### Docker Hub Access Token (Recommended)

Instead of your password, create an access token:
1. Go to https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Name: `github-actions`
4. Copy the token and use it as `DOCKER_PASSWORD`

### Result

After the workflow completes, you'll have:
- `chrisb777/ipx800_v3_to_mqtt:v1.0.0` (AMD64 + ARM64)
- `chrisb777/ipx800_v3_to_mqtt:latest` (AMD64 + ARM64)

Both architectures in a single multi-platform image!
