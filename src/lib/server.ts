import nodemailer from 'nodemailer'

// Email service configuration
export const emailConfig = {
  // SendGrid configuration
  sendgrid: {
    apiKey: process.env.SENDGRID_API_KEY,
  },
  
  // SMTP configuration (Gmail, Outlook, etc.)
  smtp: {
    host: process.env.SMTP_HOST || 'smtp.gmail.com',
    port: parseInt(process.env.SMTP_PORT || '587'),
    secure: false, // true for 465, false for other ports
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
  },
  
  // Resend configuration
  resend: {
    apiKey: process.env.RESEND_API_KEY,
  },
}

// Create email transporter
export const createEmailTransporter = () => {
  if (process.env.SMTP_HOST && process.env.SMTP_USER && process.env.SMTP_PASS) {
    return nodemailer.createTransporter(emailConfig.smtp)
  }
  return null
}

// Send email function
export const sendEmail = async (params: {
  to: string
  from: string
  subject: string
  html: string
  replyTo?: string
}) => {
  const transporter = createEmailTransporter()
  
  if (!transporter) {
    throw new Error('Email transporter not configured')
  }

  try {
    const result = await transporter.sendMail({
      from: process.env.SMTP_USER,
      to: params.to,
      subject: params.subject,
      html: params.html,
      replyTo: params.replyTo || params.from,
    })

    return result
  } catch (error) {
    console.error('Email send error:', error)
    throw error
  }
}

// Rate limiting utility
export const rateLimit = new Map()

export const checkRateLimit = (ip: string, maxRequests = 5, windowMs = 60000) => {
  const now = Date.now()
  const userRequests = rateLimit.get(ip) || { count: 0, resetTime: now + windowMs }

  if (now > userRequests.resetTime) {
    userRequests.count = 1
    userRequests.resetTime = now + windowMs
  } else {
    userRequests.count++
  }

  rateLimit.set(ip, userRequests)

  return userRequests.count <= maxRequests
}
