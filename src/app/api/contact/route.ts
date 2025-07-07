import { NextRequest, NextResponse } from 'next/server'
// import { sendEmail, checkRateLimit } from '@/lib/server'

// Simple validation function
const validateContactForm = (data: any) => {
  const errors: string[] = []
  
  if (!data.name || data.name.length < 2) {
    errors.push('Name must be at least 2 characters')
  }
  
  if (!data.email || !data.email.includes('@')) {
    errors.push('Invalid email address')
  }
  
  if (!data.subject || data.subject.length < 5) {
    errors.push('Subject must be at least 5 characters')
  }
  
  if (!data.message || data.message.length < 10) {
    errors.push('Message must be at least 10 characters')
  }
  
  return errors
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Validate the request body
    const validationErrors = validateContactForm(body)
    
    if (validationErrors.length > 0) {
      return NextResponse.json(
        { 
          error: 'Validation failed', 
          details: validationErrors 
        },
        { status: 400 }
      )
    }

    const { name, email, subject, message } = body

    // Rate limiting (optional)
    // const clientIp = request.ip || 'unknown'
    // if (!checkRateLimit(clientIp)) {
    //   return NextResponse.json(
    //     { error: 'Too many requests' },
    //     { status: 429 }
    //   )
    // }

    // Here you can integrate with your preferred email service:
    // - SendGrid
    // - Nodemailer
    // - Resend
    // - Mailgun
    // - AWS SES
    
    // For now, we'll simulate sending an email
    console.log('Contact form submission:', {
      name,
      email,
      subject,
      message,
      timestamp: new Date().toISOString()
    })

    // You can also save to a database here
    // await saveContactSubmission({ name, email, subject, message })

    // Send email notification
    await sendEmailNotification({
      to: process.env.CONTACT_EMAIL || 'vedant@example.com',
      from: email,
      subject: `Portfolio Contact: ${subject}`,
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #333;">New Contact Form Submission</h2>
          <div style="background: #f5f5f5; padding: 20px; border-radius: 8px;">
            <p><strong>Name:</strong> ${name}</p>
            <p><strong>Email:</strong> ${email}</p>
            <p><strong>Subject:</strong> ${subject}</p>
            <p><strong>Message:</strong></p>
            <p style="background: white; padding: 15px; border-radius: 4px;">${message.replace(/\n/g, '<br>')}</p>
          </div>
          <hr style="margin: 20px 0;">
          <p style="color: #666; font-size: 12px;">Submitted at: ${new Date().toLocaleString()}</p>
        </div>
      `
    })

    return NextResponse.json(
      { 
        message: 'Message sent successfully!',
        success: true
      },
      { status: 200 }
    )

  } catch (error) {
    console.error('Contact form error:', error)
    return NextResponse.json(
      { 
        error: 'Internal server error',
        message: 'Failed to send message. Please try again later.'
      },
      { status: 500 }
    )
  }
}

// Mock email service function
async function sendEmailNotification(params: {
  to: string
  from: string
  subject: string
  html: string
}) {
  // In a real implementation, you would use a service like:
  /*
  // Example with SendGrid
  const msg = {
    to: params.to,
    from: 'noreply@yoursite.com',
    subject: params.subject,
    html: params.html,
    replyTo: params.from
  }
  await sgMail.send(msg)
  */
  
  // For now, just log the email
  console.log('Email would be sent:', params)
  return Promise.resolve()
}
