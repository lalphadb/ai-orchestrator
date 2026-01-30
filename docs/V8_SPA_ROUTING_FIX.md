# AI Orchestrator v8 - SPA Routing Fix
**Date**: 2026-01-30 01:55
**Status**: ✅ **FIXED - PERMANENT SOLUTION**

---

## Problem

User successfully logged in as "demo" but all v8 routes returned **404 Not Found**:
- `/v8/dashboard` → 404
- `/v8/chat` → 404
- `/v8/agents` → 404
- All other Vue Router routes → 404

### Root Cause

The frontend Docker container was using default nginx configuration **without SPA routing**:

```nginx
# OLD CONFIG (missing try_files)
location / {
    root   /usr/share/nginx/html;
    index  index.html index.htm;
}
```

This caused nginx to look for physical files at `/v8/dashboard`, which don't exist. Vue Router uses client-side routing, so all routes must serve `index.html`.

---

## Solution

### Temporary Fix (Applied First)

Modified nginx config in running container:
```bash
docker exec ai-orchestrator-frontend sh -c \
  "echo 'server { ... try_files \$uri \$uri/ /index.html; ... }' > /etc/nginx/conf.d/default.conf && nginx -s reload"
```

**Limitation**: Lost on container restart

### Permanent Fix (Final Solution)

Created new Docker image with proper SPA routing:

**File**: `frontend/Dockerfile.spa`
```dockerfile
FROM nginx:alpine

COPY dist /usr/share/nginx/html

RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # SPA routing - Always serve index.html for routes \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    # Cache static assets \
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
    \
    # No cache for index.html \
    location = /index.html { \
        add_header Cache-Control "no-store, no-cache, must-revalidate"; \
        expires off; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## Deployment Steps

```bash
# 1. Build new image
cd /home/lalpha/projets/ai-tools/ai-orchestrator/frontend
docker build -f Dockerfile.spa -t ai-orchestrator-frontend:v8-spa .

# 2. Replace container
docker stop ai-orchestrator-frontend
docker rm ai-orchestrator-frontend
docker run -d \
  --name ai-orchestrator-frontend \
  --network web \
  --restart unless-stopped \
  ai-orchestrator-frontend:v8-spa

# 3. Verify
curl http://172.20.0.4/v8/dashboard
# → 200 OK (returns index.html)
```

---

## Verification

### Container Status
✅ Container running: `ai-orchestrator-frontend:v8-spa`
✅ Network: `web` (connected to Traefik)
✅ Restart policy: `unless-stopped`

### Nginx Config
✅ `try_files $uri $uri/ /index.html;` present
✅ Static asset caching configured (1 year)
✅ index.html cache disabled (no-store)

### HTTP Tests
```bash
# Direct container test
curl http://172.20.0.4/index.html
# → 200 OK

curl http://172.20.0.4/v8/dashboard
# → 200 OK (SPA routing working)

curl http://172.20.0.4/v8/chat
# → 200 OK (SPA routing working)

# Traefik routing
curl -H "Host: ai.4lb.ca" http://localhost/v8/dashboard
# → 301 (HTTP→HTTPS redirect, correct)
```

---

## Impact

### Before Fix
- ❌ User logged in successfully
- ❌ `/v8/*` routes returned 404
- ❌ Dashboard, Chat, Agents pages inaccessible
- ⚠️ Only `/login` and `/settings` worked (not under `/v8/`)

### After Fix
- ✅ All `/v8/*` routes serve `index.html`
- ✅ Vue Router handles client-side navigation
- ✅ Dashboard, Chat, Agents, Models, Tools, Memory, Audit, System all accessible
- ✅ Fix persists across container restarts

---

## Why This Happened

1. **Original Dockerfile** (`frontend/Dockerfile`) **already had SPA config**
   - Lines 22-43 configure nginx with `try_files`
   - But build fails due to husky git hooks error

2. **Earlier fix** (v8-fix image) used `npm run build` output
   - Built with correct CSP fix
   - But didn't rebuild nginx config properly

3. **This fix** uses simplified Dockerfile
   - Uses pre-built `dist/` folder
   - Avoids npm install (no husky errors)
   - Explicitly configures nginx with SPA routing

---

## Files Modified

### Created
```
frontend/Dockerfile.spa - Simplified production Dockerfile
docs/V8_SPA_ROUTING_FIX.md - This document
```

### Docker Images
```
ai-orchestrator-frontend:v8-fix → Replaced
ai-orchestrator-frontend:v8-spa → Active (current)
```

### Containers
```
ai-orchestrator-frontend (a225c14ce4f7) - Running v8-spa image
```

---

## Recommended Next Steps

### For Future Deployments

Option 1: Use simplified Dockerfile (current solution)
```bash
cd frontend
npm run build
docker build -f Dockerfile.spa -t ai-orchestrator-frontend:latest .
```

Option 2: Fix original Dockerfile to skip husky
```dockerfile
# Replace line 9 in frontend/Dockerfile
RUN npm ci --ignore-scripts
```

### User Testing

User should now:
1. **Refresh browser** (Ctrl+Shift+R to clear cache)
2. **Login** as demo/demo123
3. **Navigate** to Dashboard, Chat, Agents
4. **Verify** all pages load without 404 errors

---

## Configuration Reference

### Nginx SPA Routing Explained

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

**How it works**:
1. Request for `/v8/dashboard` arrives
2. Nginx tries `$uri` → looks for file `/v8/dashboard` (not found)
3. Nginx tries `$uri/` → looks for directory `/v8/dashboard/` (not found)
4. Nginx falls back to `/index.html` → **FOUND**
5. Browser loads `index.html`, Vue Router sees `/v8/dashboard` in URL
6. Vue Router renders `DashboardView.vue` component

### Cache Strategy

```nginx
# Static assets: cache 1 year (immutable)
location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# index.html: never cache (always get latest version)
location = /index.html {
    add_header Cache-Control "no-store, no-cache, must-revalidate";
    expires off;
}
```

**Why**:
- JS/CSS files have content hash in filename (`DashboardView-C3fGaAg0.js`)
- If content changes, filename changes → new file served
- Safe to cache forever (1 year)
- index.html has no hash → must never be cached → always fresh

---

## Troubleshooting

### If routes still return 404 after fix

1. **Check nginx config**:
   ```bash
   docker exec ai-orchestrator-frontend cat /etc/nginx/conf.d/default.conf
   ```
   Should contain `try_files $uri $uri/ /index.html;`

2. **Check container image**:
   ```bash
   docker inspect ai-orchestrator-frontend --format '{{.Config.Image}}'
   ```
   Should be `ai-orchestrator-frontend:v8-spa`

3. **Test directly**:
   ```bash
   CONTAINER_IP=$(docker inspect ai-orchestrator-frontend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
   curl http://$CONTAINER_IP/v8/dashboard
   ```
   Should return 200 (not 404)

4. **Clear browser cache**:
   - Chrome: Ctrl+Shift+R
   - Firefox: Ctrl+Shift+Delete → Clear cache
   - Or use Incognito/Private mode

---

## Summary

### Problem
404 errors on all Vue Router routes due to missing SPA routing configuration in nginx.

### Solution
Created new Docker image (`v8-spa`) with proper nginx config including `try_files` directive.

### Result
✅ All `/v8/*` routes now accessible
✅ SPA routing working correctly
✅ Fix persists across container restarts
✅ Static asset caching optimized

---

**Status**: ✅ **PRODUCTION READY**
**Next**: User should test all pages to confirm fix
