# Vedant Somani's Portfolio

A modern, responsive portfolio website built with Next.js, featuring glassmorphism design and smooth animations.

## 🚀 Features

- **Modern Design**: Glassmorphism UI with gradient backgrounds
- **Responsive**: Works perfectly on all devices
- **Smooth Animations**: Framer Motion powered animations
- **Multi-page**: Clean navigation between sections
- **Theme Toggle**: Dark/Light mode support
- **Interactive**: Animated project cards and smooth scrolling
- **Backend API**: Full-featured API with contact form, analytics
- **Email Integration**: Working contact form with email notifications
- **SEO Optimized**: Meta tags and Open Graph support
- **Security**: Rate limiting, CORS, security headers
- **Analytics**: Built-in event tracking system
- **Deployment Ready**: Vercel, Netlify, and VPS deployment support

## 🛠️ Tech Stack

- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS
- **Animation**: Framer Motion
- **Icons**: Lucide React
- **Language**: TypeScript
- **Backend**: Next.js API Routes
- **Email**: Nodemailer/SendGrid support
- **Deployment**: Vercel, Netlify, VPS ready

## 📁 Project Structure

```
src/
├── app/
│   ├── api/
│   │   ├── contact/
│   │   │   └── route.ts      # Contact form API endpoint
│   │   ├── projects/
│   │   │   └── route.ts      # Projects API with filtering
│   │   ├── skills/
│   │   │   └── route.ts      # Skills API endpoint
│   │   └── analytics/
│   │       └── route.ts      # Analytics tracking API
│   ├── layout.tsx            # Root layout with theme provider
│   ├── page.tsx              # Home page
│   └── globals.css           # Global styles and glassmorphism utilities
├── components/
│   ├── About.tsx             # About section with experience & education
│   ├── Contact.tsx           # Contact form with API integration
│   ├── Hero.tsx              # Landing section with animated intro
│   ├── Navbar.tsx            # Responsive navigation
│   ├── Projects.tsx          # Project showcase with filtering
│   ├── Skills.tsx            # Technical skills with progress bars
│   └── ThemeProvider.tsx     # Theme management
├── data/
│   └── portfolio.ts          # Mock data for content
├── lib/
│   ├── utils.ts              # Utility functions
│   └── server.ts             # Server-side utilities
└── middleware.ts             # Security and CORS middleware
```

## 🎨 Design Features

- **Glassmorphism**: Frosted glass effects with backdrop blur
- **Gradient Backgrounds**: Animated gradient backgrounds
- **Smooth Scrolling**: Scroll-triggered animations
- **Responsive Layout**: Mobile-first design approach
- **Custom Components**: Reusable glass effect components

## 🚀 Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/vedantsomani/portfolio.git
   cd portfolio
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Run the development server**
   ```bash
   npm run dev
   ```

4. **Open your browser**
   Navigate to `http://localhost:3000`

## 📝 Customization

### Update Personal Information
Edit `src/data/portfolio.ts` to update:
- Personal details
- Projects
- Skills
- Experience
- Education

### Modify Colors
Update the color palette in `tailwind.config.js`:
```javascript
colors: {
  primary: {
    // Your custom colors
  }
}
```

### Add New Sections
1. Create a new component in `src/components/`
2. Import and add it to `src/app/page.tsx`
3. Add navigation link to `src/components/Navbar.tsx`

## 🎯 Sections

- **Hero**: Introduction with animated text and social links
- **About**: Personal information, experience, and education
- **Projects**: Filterable project showcase with GitHub integration
- **Skills**: Technical skills with animated progress bars
- **Contact**: Contact form and social media links

## 🔧 Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## 🚀 Deployment

### Vercel (Recommended)
1. Connect your GitHub repository to Vercel
2. Deploy with zero configuration
3. Automatic deployments on push

### Other Platforms
- **Netlify**: Upload build folder
- **GitHub Pages**: Use `next export` for static export

## 📱 Responsive Design

- **Mobile**: Optimized for mobile devices
- **Tablet**: Responsive grid layouts
- **Desktop**: Full-width layouts with animations

## 🎨 Customization Guide

### Adding New Projects
```typescript
// In src/data/portfolio.ts
export const projects = [
  {
    id: 1,
    title: "Your Project",
    description: "Project description",
    technologies: ["React", "Node.js"],
    github: "https://github.com/username/repo",
    demo: "https://your-demo.com",
    category: "Web Dev"
  }
]
```

### Modifying Animations
```typescript
// Example animation variants
const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.8 }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 📧 Contact

- **Email**: vedant@example.com
- **GitHub**: [@vedantsomani](https://github.com/vedantsomani)
- **LinkedIn**: [Vedant Somani](https://linkedin.com/in/vedant-somani)

---

Built with ❤️ by Vedant Somani
