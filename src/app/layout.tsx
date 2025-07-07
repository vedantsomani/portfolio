import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Navbar from '@/components/Navbar'
import { ThemeProvider } from '@/components/ThemeProvider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Vedant Somani | AI Developer & Researcher',
  description: 'Portfolio of Vedant Somani - AI Developer, Researcher, and Engineer specializing in cutting-edge artificial intelligence solutions.',
  keywords: ['AI Developer', 'Machine Learning', 'Research', 'Portfolio', 'Vedant Somani'],
  authors: [{ name: 'Vedant Somani' }],
  creator: 'Vedant Somani',
  openGraph: {
    title: 'Vedant Somani | AI Developer & Researcher',
    description: 'Portfolio of Vedant Somani - AI Developer, Researcher, and Engineer',
    url: 'https://vedant-somani.vercel.app',
    siteName: 'Vedant Somani Portfolio',
    images: [
      {
        url: '/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'Vedant Somani Portfolio',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Vedant Somani | AI Developer & Researcher',
    description: 'Portfolio of Vedant Somani - AI Developer, Researcher, and Engineer',
    images: ['/og-image.jpg'],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider>
          <div className="min-h-screen gradient-bg">
            <Navbar />
            <main className="relative z-10">
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  )
}
