'use client'

import { motion } from 'framer-motion'
import { ChevronDown, Download, Github, Linkedin, Mail, Twitter } from 'lucide-react'
import { personalInfo } from '@/data/portfolio'

export default function Hero() {
  const handleScrollToNext = () => {
    const nextSection = document.querySelector('#about')
    if (nextSection) {
      nextSection.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <section id="hero" className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-blue-500/20 rounded-full blur-3xl animate-float"></div>
        <div
          className="absolute top-1/3 right-1/4 w-48 h-48 bg-purple-500/20 rounded-full blur-3xl animate-float"
          style={{ animationDelay: '2s' }}
        ></div>
        <div
          className="absolute bottom-1/4 left-1/3 w-56 h-56 bg-pink-500/20 rounded-full blur-3xl animate-float"
          style={{ animationDelay: '4s' }}
        ></div>
      </div>

      <div className="relative z-10 text-center px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="mb-8"
        >
          <motion.h1
            className="text-4xl sm:text-6xl lg:text-7xl font-bold text-white mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            Hi, I&apos;m{' '}
            <motion.span
              className="bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 bg-clip-text text-transparent"
              animate={{ backgroundPosition: ['0%', '100%', '0%'] }}
              transition={{ duration: 5, repeat: Infinity, ease: 'linear' }}
            >
              {personalInfo.name}
            </motion.span>
          </motion.h1>

          <motion.p
            className="text-xl sm:text-2xl text-white/80 mb-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            {personalInfo.role}
          </motion.p>

          <motion.p
            className="text-lg text-white/60 mb-8 max-w-2xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
          >
            {personalInfo.tagline}
          </motion.p>
        </motion.div>

        {/* CTA Buttons */}
        <motion.div
          className="flex flex-col sm:flex-row gap-4 justify-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
        >
          <motion.button
            className="glass-button px-8 py-4 text-white font-semibold flex items-center justify-center space-x-2"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => window.open(personalInfo.resume, '_blank')}
          >
            <Download className="w-5 h-5" />
            <span>Download Resume</span>
          </motion.button>

          <motion.button
            className="glass-button px-8 py-4 text-white font-semibold flex items-center justify-center space-x-2"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleScrollToNext}
          >
            <Mail className="w-5 h-5" />
            <span>Get In Touch</span>
          </motion.button>
        </motion.div>

        {/* Social Links */}
        <motion.div
          className="flex justify-center space-x-6 mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 1 }}
        >
          {[
            { icon: Github, href: personalInfo.github, label: 'GitHub' },
            { icon: Linkedin, href: personalInfo.linkedin, label: 'LinkedIn' },
            { icon: Twitter, href: personalInfo.twitter, label: 'Twitter' },
          ].map((social, i) => (
            <motion.a
              key={social.label}
              href={social.href}
              target="_blank"
              rel="noopener noreferrer"
              className="glass-button p-3 text-white hover:text-blue-400 transition-colors duration-200"
              whileHover={{ scale: 1.1, y: -2 }}
              whileTap={{ scale: 0.95 }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.2 + i * 0.1 }}
            >
              <social.icon className="w-6 h-6" />
              <span className="sr-only">{social.label}</span>
            </motion.a>
          ))}
        </motion.div>

        {/* Scroll indicator */}
        <motion.button
          onClick={handleScrollToNext}
          className="absolute bottom-8 left-1/2 transform -translate-x-1/2 text-white/60 hover:text-white transition-colors duration-200"
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <ChevronDown className="w-8 h-8" />
        </motion.button>
      </div>
    </section>
  )
}
