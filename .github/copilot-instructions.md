<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Vedant Somani's Portfolio - Copilot Instructions

This is a Next.js portfolio website with the following architecture:

## Tech Stack
- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS with custom glassmorphism theme
- **Animation**: Framer Motion for smooth animations
- **TypeScript**: Full type safety
- **Icons**: Lucide React

## Design System
- **Theme**: Glassmorphism with gradient backgrounds
- **Colors**: Blue, purple, pink gradient palette
- **Glass effects**: Backdrop blur with transparency
- **Animations**: Smooth scroll-triggered animations

## Component Structure
- `Hero`: Landing section with animated intro
- `About`: Personal info, experience, education
- `Projects`: Filterable project showcase
- `Skills`: Technical skills with progress bars
- `Contact`: Contact form and information
- `Navbar`: Responsive navigation with theme toggle
- `ThemeProvider`: Dark/light theme management

## Key Features
- Responsive design for all screen sizes
- Smooth scroll navigation
- Theme toggle (dark/light)
- Animated project cards
- Contact form with validation
- Social media integration
- SEO optimization

## Code Style
- Use TypeScript for all components
- Implement proper accessibility (ARIA labels, keyboard navigation)
- Use Framer Motion for animations
- Follow React best practices
- Use custom Tailwind classes for glassmorphism effects

## Data Structure
- Mock data stored in `src/data/portfolio.ts`
- Modular data structure for easy content updates
- Type-safe interfaces for all data structures
