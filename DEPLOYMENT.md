# Deployment Guide

This guide covers deploying your Next.js portfolio with full backend functionality.

## 🚀 Deployment Options

### 1. Vercel (Recommended)

Vercel is the easiest way to deploy your Next.js application with zero configuration.

#### Steps:
1. **Connect to GitHub**
   - Push your code to GitHub
   - Connect your repository to Vercel
   - Vercel will automatically detect Next.js

2. **Environment Variables**
   - Go to your Vercel dashboard
   - Navigate to Settings > Environment Variables
   - Add the following variables:
   ```
   SENDGRID_API_KEY=your_sendgrid_key (optional)
   SMTP_HOST=smtp.gmail.com
   SMTP_USER=your_email@gmail.com
   SMTP_PASS=your_app_password
   CONTACT_EMAIL=your_contact_email@gmail.com
   ```

3. **Deploy**
   - Vercel will automatically deploy on every push
   - Your site will be live at `https://your-project.vercel.app`

### 2. Netlify

#### Steps:
1. **Build Settings**
   - Build command: `npm run build`
   - Publish directory: `out`
   - Node version: 18.x

2. **Static Export Configuration**
   - Add to `next.config.js`:
   ```javascript
   const nextConfig = {
     output: 'export',
     trailingSlash: true,
     images: { unoptimized: true }
   }
   ```

3. **API Routes**
   - Netlify Functions for API routes
   - Move API routes to `netlify/functions/`

### 3. Traditional VPS/Cloud Server

#### Requirements:
- Node.js 18+
- PM2 for process management
- Nginx for reverse proxy
- SSL certificate (Let's Encrypt)

#### Steps:
1. **Server Setup**
   ```bash
   # Install dependencies
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs nginx
   npm install -g pm2
   ```

2. **Deploy Application**
   ```bash
   # Clone repository
   git clone https://github.com/username/portfolio.git
   cd portfolio
   
   # Install dependencies
   npm install
   
   # Build application
   npm run build
   
   # Start with PM2
   pm2 start npm --name "portfolio" -- start
   pm2 save
   pm2 startup
   ```

3. **Nginx Configuration**
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

## 📧 Email Service Setup

### Option 1: Gmail SMTP
1. Enable 2-factor authentication
2. Generate an app password
3. Use these settings:
   - SMTP_HOST: smtp.gmail.com
   - SMTP_PORT: 587
   - SMTP_USER: your_email@gmail.com
   - SMTP_PASS: your_app_password

### Option 2: SendGrid
1. Create a SendGrid account
2. Generate an API key
3. Set SENDGRID_API_KEY environment variable

### Option 3: Resend
1. Create a Resend account
2. Generate an API key
3. Set RESEND_API_KEY environment variable

## 🔐 Security Considerations

### Environment Variables
- Never commit `.env` files to version control
- Use platform-specific environment variable settings
- Rotate API keys regularly

### Rate Limiting
- Implement rate limiting for API endpoints
- Use Redis or memory store for production
- Set appropriate limits (5 requests per minute)

### CORS Configuration
- Configure CORS headers for API routes
- Restrict origins in production
- Use HTTPS in production

## 🔧 Production Optimizations

### Performance
- Enable Next.js image optimization
- Use CDN for static assets
- Implement caching strategies
- Compress responses

### Monitoring
- Set up error tracking (Sentry)
- Monitor API performance
- Set up uptime monitoring
- Configure logging

### SEO
- Generate sitemap.xml
- Add robots.txt
- Implement structured data
- Optimize meta tags

## 📊 Analytics Setup

### Google Analytics
```javascript
// Add to _app.tsx or layout.tsx
gtag('config', 'GA_MEASUREMENT_ID');
```

### Custom Analytics
- Use the `/api/analytics` endpoint
- Track page views, form submissions
- Monitor user interactions

## 🧪 Testing Before Deployment

### Local Testing
```bash
# Test production build locally
npm run build
npm start
```

### API Testing
```bash
# Test contact form
curl -X POST http://localhost:3000/api/contact \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","subject":"Test","message":"Test message"}'
```

## 🔄 Continuous Deployment

### GitHub Actions
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
```

## 📱 Domain Setup

### Custom Domain
1. Purchase domain from registrar
2. Add domain to deployment platform
3. Configure DNS records
4. Set up SSL certificate

### DNS Records
- A record: Point to server IP
- CNAME: www subdomain
- MX records: Email routing

## 🆘 Troubleshooting

### Common Issues
1. **Build Failures**: Check Node.js version compatibility
2. **API Errors**: Verify environment variables
3. **Email Not Sending**: Check SMTP credentials
4. **Performance Issues**: Optimize images and assets

### Debug Commands
```bash
# Check build output
npm run build

# Test API endpoints
npm run dev

# Check environment variables
printenv | grep -i smtp
```

## 📞 Support

For deployment issues:
- Check platform documentation
- Review error logs
- Test locally first
- Contact support if needed

Your portfolio is now ready for production deployment! 🚀
