# Deployment Guide

Complete guide for deploying SheaBot to production.

---

## 🌐 Deployment Options

### Option 1: Vercel (Recommended)

**Best for:** Quick deployments, automatic CI/CD, free tier available

#### Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Import to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import your GitHub repository
   - Configure project settings

3. **Add Environment Variables**
   
   In Vercel dashboard → Settings → Environment Variables:
   ```
   OPENAI_API_KEY=your_key
   GEMINI_API_KEY=your_key
   MONGODB_URI=your_mongodb_connection_string
   ```

4. **Deploy**
   - Click "Deploy"
   - Vercel will build and deploy automatically
   - Future pushes to `main` will auto-deploy

#### Vercel Configuration

**`vercel.json`** (create in root):
```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "regions": ["syd1"]
}
```

---

### Option 2: Docker

**Best for:** Self-hosting, consistent environments

#### Dockerfile

Create `Dockerfile` in root:
```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

#### Build and Run

```bash
# Build image
docker build -t sheabot .

# Run container
docker run -d \
  -p 3000:3000 \
  -e OPENAI_API_KEY=your_key \
  -e GEMINI_API_KEY=your_key \
  -e MONGODB_URI=your_mongodb_uri \
  --name sheabot \
  sheabot
```

#### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  sheabot:
    build: .
    ports:
      - "3000:3000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - MONGODB_URI=mongodb://mongo:27017/sheabot
    depends_on:
      - mongo

  mongo:
    image: mongo:7
    volumes:
      - mongo_data:/data/db
    ports:
      - "27017:27017"

volumes:
  mongo_data:
```

Run:
```bash
docker-compose up -d
```

---

### Option 3: Traditional VPS

**Best for:** Full control, existing infrastructure

#### Requirements

- Ubuntu 22.04+ or similar
- Node.js 20+
- PM2 (process manager)
- Nginx (reverse proxy)
- MongoDB (local or remote)

#### Setup Steps

1. **Install Node.js**
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

2. **Clone and Install**
   ```bash
   git clone <repo-url> /opt/sheabot
   cd /opt/sheabot
   npm ci --only=production
   npm run build
   ```

3. **Set Environment Variables**
   ```bash
   nano .env.local
   # Add your variables
   ```

4. **Setup PM2**
   ```bash
   npm install -g pm2
   pm2 start npm --name "sheabot" -- start
   pm2 save
   pm2 startup
   ```

5. **Configure Nginx**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

6. **SSL with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

---

## 🔒 Security Checklist

- [ ] Environment variables are secure (not in code)
- [ ] MongoDB has authentication enabled
- [ ] HTTPS/SSL is configured
- [ ] API keys are rotated regularly
- [ ] CORS is properly configured
- [ ] Rate limiting is enabled
- [ ] Dependencies are up to date (`npm audit`)

---

## 📊 Monitoring

### Health Check Endpoint

Add to `app/api/health/route.ts`:
```typescript
export async function GET() {
  return Response.json({ 
    status: 'healthy',
    timestamp: new Date().toISOString()
  });
}
```

### Logging

- Use Vercel Analytics (if deployed on Vercel)
- Set up Sentry for error tracking
- Monitor MongoDB performance
- Track API usage and quotas

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build
        run: npm run build
      
      - name: Test
        run: npm run lint
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

---

## 🆘 Troubleshooting

### Build Fails
- Check Node version (`node -v`)
- Clear cache: `rm -rf .next node_modules`
- Reinstall: `npm ci`

### Runtime Errors
- Check environment variables
- Review logs: `pm2 logs sheabot` or Vercel dashboard
- Verify MongoDB connection

### Performance Issues
- Enable Next.js caching
- Use MongoDB indexes
- Consider CDN for static assets

---

## 📞 Support

For deployment issues, open an issue or contact the maintainer.

---

**Last Updated:** March 2026
